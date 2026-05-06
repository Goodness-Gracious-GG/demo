-- Migration: Create conversations table for Supabase
-- This file contains the SQL to set up the conversations table
-- with Row Level Security policies for user data isolation

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT,
    messages JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on user_id for faster queries
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);

-- Create index on updated_at for sorting
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);

-- Create trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_conversations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updated_at
CREATE TRIGGER update_conversations_updated_at_trigger
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_conversations_updated_at();

-- Create function to append message to conversation
CREATE OR REPLACE FUNCTION append_message_to_conversation(
    conv_id UUID,
    new_message JSONB
)
RETURNS conversations AS $$
DECLARE
    updated_conversation conversations;
BEGIN
    UPDATE conversations
    SET messages = messages || new_message,
        updated_at = NOW()
    WHERE id = conv_id
    RETURNING * INTO updated_conversation;
    
    RETURN updated_conversation;
END;
$$ LANGUAGE plpgsql;

-- Enable Row Level Security on conversations table
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Policy 1: Users can view their own conversations
CREATE POLICY "Users can view their own conversations"
    ON conversations FOR SELECT
    USING (auth.uid() = user_id);

-- Policy 2: Users can create their own conversations
CREATE POLICY "Users can create their own conversations"
    ON conversations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy 3: Users can update their own conversations
CREATE POLICY "Users can update their own conversations"
    ON conversations FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Policy 4: Users can delete their own conversations
CREATE POLICY "Users can delete their own conversations"
    ON conversations FOR DELETE
    USING (auth.uid() = user_id);

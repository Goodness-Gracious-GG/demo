"""
Supabase Integration Example

This file demonstrates how to use the Supabase integration
for authentication and conversation management.
"""

from supabase_client import (
    supabase,
    sign_up,
    sign_in,
    sign_out,
    get_session,
    get_current_user,
    create_conversation,
    get_conversation,
    get_user_conversations,
    update_conversation,
    delete_conversation,
    add_message_to_conversation,
    is_authenticated
)


def example_authentication():
    """Example: User authentication flow."""
    
    print("=== Authentication Example ===")
    
    # 1. Sign up a new user
    print("\n1. Signing up a new user...")
    try:
        result = sign_up(
            email="test@example.com",
            password="SecurePassword123!",
            options={"data": {"full_name": "Test User"}}
        )
        print(f"   User created: {result['user']['email']}")
        print(f"   Session: {result['session']['access_token'][:20]}...")
    except Exception as e:
        print(f"   Sign up failed (user may already exist): {e}")
    
    # 2. Sign in
    print("\n2. Signing in...")
    try:
        result = sign_in(
            email="test@example.com",
            password="SecurePassword123!"
        )
        user = result['user']
        session = result['session']
        print(f"   Signed in as: {user['email']}")
        print(f"   User ID: {user['id']}")
    except Exception as e:
        print(f"   Sign in failed: {e}")
        return
    
    # 3. Get current session
    print("\n3. Getting current session...")
    session_data = get_session()
    if session_data:
        print(f"   Session is valid")
    
    # 4. Get current user
    print("\n4. Getting current user...")
    current_user = get_current_user()
    if current_user:
        print(f"   Current user: {current_user['email']}")
    
    # 5. Check if authenticated
    print("\n5. Checking authentication status...")
    if is_authenticated():
        print("   User is authenticated")
    
    # 6. Sign out
    print("\n6. Signing out...")
    sign_out()
    print("   Signed out successfully")


def example_conversation_crud(user_id):
    """Example: Conversation CRUD operations."""
    
    print("\n=== Conversation CRUD Example ===")
    
    # 1. Create a conversation
    print("\n1. Creating a conversation...")
    messages = [
        {
            "role": "user",
            "content": "What does this code do?",
            "timestamp": "2026-05-06T10:00:00"
        },
        {
            "role": "assistant",
            "content": "This code finds the maximum value in an array.",
            "timestamp": "2026-05-06T10:00:01"
        }
    ]
    
    conversation = create_conversation(
        user_id=user_id,
        messages=messages,
        title="Array Max Example"
    )
    
    if conversation:
        conv_id = conversation['id']
        print(f"   Created conversation: {conv_id}")
        print(f"   Title: {conversation['title']}")
        print(f"   Messages: {len(conversation['messages'])}")
    else:
        print("   Failed to create conversation")
        return
    
    # 2. Get the conversation
    print("\n2. Retrieving conversation...")
    retrieved = get_conversation(
        conversation_id=conv_id,
        user_id=user_id
    )
    if retrieved:
        print(f"   Retrieved: {retrieved['title']}")
        print(f"   Messages: {len(retrieved['messages'])}")
    
    # 3. List all conversations
    print("\n3. Listing all conversations...")
    conversations = get_user_conversations(
        user_id=user_id,
        limit=10,
        offset=0
    )
    print(f"   Total conversations: {len(conversations)}")
    for conv in conversations:
        print(f"   - {conv['title']} ({len(conv['messages'])} messages)")
    
    # 4. Add a message to the conversation
    print("\n4. Adding a message...")
    new_message = {
        "role": "user",
        "content": "Can you explain the time complexity?",
        "timestamp": "2026-05-06T10:05:00"
    }
    
    updated = add_message_to_conversation(
        conversation_id=conv_id,
        message=new_message,
        user_id=user_id
    )
    if updated:
        print(f"   Messages now: {len(updated['messages'])}")
    
    # 5. Update the conversation
    print("\n5. Updating conversation title...")
    updated = update_conversation(
        conversation_id=conv_id,
        messages=updated['messages'] if updated else messages,
        title="Array Max - Time Complexity Discussion",
        user_id=user_id
    )
    if updated:
        print(f"   New title: {updated['title']}")
    
    # 6. Delete the conversation
    print("\n6. Deleting conversation...")
    success = delete_conversation(
        conversation_id=conv_id,
        user_id=user_id
    )
    if success:
        print("   Conversation deleted")
    
    # 7. Verify deletion
    print("\n7. Verifying deletion...")
    conversations = get_user_conversations(user_id=user_id)
    print(f"   Remaining conversations: {len(conversations)}")


def example_with_real_supabase():
    """
    Example using the actual Supabase client.
    
    This shows how to use the supabase client directly
    for more advanced operations.
    """
    
    print("\n=== Direct Supabase Client Example ===")
    
    # Direct query example
    try:
        result = supabase.table('conversations').select('count').execute()
        print(f"   Total conversations in DB: {result.data}")
    except Exception as e:
        print(f"   Query failed (may need auth): {e}")
    
    # Using RLS with authenticated client
    print("\n   Note: For RLS to work properly, you need to:")
    print("   1. Set the auth header: supabase.auth.set_session(token)")
    print("   2. Or use the helper functions in supabase_client.py")


if __name__ == "__main__":
    print("Supabase Integration Examples")
    print("=" * 50)
    
    # Run authentication example
    example_authentication()
    
    # Note: For conversation examples, you need a valid user_id
    # Uncomment and modify with a real user_id to test:
    # example_conversation_crud("your-user-id-here")
    
    # Run direct client example
    example_with_real_supabase()
    
    print("\n" + "=" * 50)
    print("Examples completed!")

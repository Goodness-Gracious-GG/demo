import { createClient } from '@supabase/supabase-js'

// ============================================================
// SUPABASE CLIENT INITIALIZATION
// ============================================================
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY

const supabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// ============================================================
// APPLICATION STATE
// ============================================================
let currentUser = null;
let currentConversationId = null;
let currentConversationTitle = null;
let isAuthModalOpen = false;
let isSignUpMode = false;

// ============================================================
// DOM ELEMENTS
// ============================================================
const codeInput = document.querySelector('.code-input');
const chatMessages = document.querySelector('.chat-messages');
const chatInput = document.querySelector('.chat-input');
const chatSend = document.querySelector('.chat-send');
const clearBtn = document.querySelector('.clear-btn');
const authModal = document.getElementById('authModal');
const authForm = document.getElementById('authForm');
const authEmail = document.getElementById('authEmail');
const authPassword = document.getElementById('authPassword');
const authError = document.getElementById('authError');
const authSubmit = document.getElementById('authSubmit');
const authModalTitle = document.getElementById('authModalTitle');
const authToggle = document.getElementById('authToggle');
const signInBtn = document.getElementById('signInBtn');
const signOutBtn = document.getElementById('signOutBtn');
const userEmail = document.getElementById('userEmail');
const conversationSidebar = document.getElementById('conversationSidebar');
const conversationList = document.getElementById('conversationList');
const newConversationBtn = document.getElementById('newConversationBtn');

// ============================================================
// AUTH FUNCTIONS
// ============================================================

async function handleSignUp(email, password) {
  try {
    const { data, error } = await supabaseClient.auth.signUp({
      email: email,
      password: password
    });
    
    if (error) throw error;
    
    if (data.user) {
      showMessage('Account created! Please check your email to verify.', 'success');
      // Auto sign in
      await handleSignIn(email, password);
    }
  } catch (error) {
    showError(error.message);
  }
}

async function handleSignIn(email, password) {
  try {
    const { data, error } = await supabaseClient.auth.signInWithPassword({
      email: email,
      password: password
    });
    
    if (error) throw error;
    
    if (data.user) {
      currentUser = data.user;
      updateAuthUI();
      closeAuthModal();
      loadConversations();
      showMessage('Signed in successfully!', 'success');
    }
  } catch (error) {
    showError(error.message);
  }
}

async function handleSignOut() {
  try {
    const { error } = await supabaseClient.auth.signOut();
    if (error) throw error;
    
    currentUser = null;
    currentConversationId = null;
    updateAuthUI();
    clearConversationList();
    conversationSidebar.style.display = 'none';
    chatMessages.innerHTML = '';
    showMessage('Signed out successfully', 'success');
  } catch (error) {
    showError(error.message);
  }
}

async function checkAuthSession() {
  try {
    const { data: { session }, error } = await supabaseClient.auth.getSession();
    
    if (error) throw error;
    
    if (session?.user) {
      currentUser = session.user;
      updateAuthUI();
      loadConversations();
    }
  } catch (error) {
    console.error('Error checking auth session:', error);
  }
}

// ============================================================
// CONVERSATION FUNCTIONS
// ============================================================

async function createConversation(messages, title) {
  if (!currentUser) return null;
  
  try {
    const { data, error } = await supabaseClient
      .from('conversations')
      .insert([
        {
          user_id: currentUser.id,
          messages: messages,
          title: title || `Conversation ${new Date().toLocaleString()}`
        }
      ])
      .select()
      .single();
    
    if (error) throw error;
    
    return data;
  } catch (error) {
    console.error('Error creating conversation:', error);
    return null;
  }
}

async function loadConversations() {
  if (!currentUser) return;
  
  try {
    const { data, error } = await supabaseClient
      .from('conversations')
      .select('*')
      .eq('user_id', currentUser.id)
      .order('updated_at', { ascending: false });
    
    if (error) throw error;
    
    renderConversationList(data);
  } catch (error) {
    console.error('Error loading conversations:', error);
  }
}

async function loadConversation(conversationId) {
  if (!currentUser) return;
  
  try {
    const { data, error } = await supabaseClient
      .from('conversations')
      .select('*')
      .eq('id', conversationId)
      .eq('user_id', currentUser.id)
      .single();
    
    if (error) throw error;
    
    return data;
  } catch (error) {
    console.error('Error loading conversation:', error);
    return null;
  }
}

async function updateConversation(conversationId, messages, title) {
  if (!currentUser) return null;
  
  try {
    const { data, error } = await supabaseClient
      .from('conversations')
      .update({
        messages: messages,
        title: title,
        updated_at: new Date().toISOString()
      })
      .eq('id', conversationId)
      .eq('user_id', currentUser.id)
      .select()
      .single();
    
    if (error) throw error;
    
    return data;
  } catch (error) {
    console.error('Error updating conversation:', error);
    return null;
  }
}

async function deleteConversation(conversationId) {
  if (!currentUser) return false;
  
  try {
    const { error } = await supabaseClient
      .from('conversations')
      .delete()
      .eq('id', conversationId)
      .eq('user_id', currentUser.id);
    
    if (error) throw error;
    
    return true;
  } catch (error) {
    console.error('Error deleting conversation:', error);
    return false;
  }
}

// ============================================================
// UI FUNCTIONS
// ============================================================

function updateAuthUI() {
  if (currentUser) {
    userEmail.textContent = currentUser.email;
    signInBtn.style.display = 'none';
    signOutBtn.style.display = 'inline-block';
    userEmail.style.display = 'inline-block';
    conversationSidebar.style.display = 'block';
  } else {
    userEmail.textContent = '';
    signInBtn.style.display = 'inline-block';
    signOutBtn.style.display = 'none';
    userEmail.style.display = 'none';
    conversationSidebar.style.display = 'none';
  }
}

function renderConversationList(conversations) {
  conversationList.innerHTML = '';
  
  if (!conversations || conversations.length === 0) {
    conversationList.innerHTML = '<div class="empty-state">No conversations yet</div>';
    return;
  }
  
  conversations.forEach(conv => {
    const convEl = document.createElement('div');
    convEl.className = 'conversation-item' + (conv.id === currentConversationId ? ' active' : '');
    convEl.innerHTML = `
      <div class="conversation-title">${conv.title || 'Untitled'}</div>
      <div class="conversation-date">${new Date(conv.updated_at).toLocaleDateString()}</div>
      <button class="delete-conv-btn" data-id="${conv.id}">×</button>
    `;
    
    convEl.addEventListener('click', (e) => {
      if (!e.target.classList.contains('delete-conv-btn')) {
        loadConversationById(conv.id);
      }
    });
    
    const deleteBtn = convEl.querySelector('.delete-conv-btn');
    deleteBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (confirm('Delete this conversation?')) {
        deleteConversation(conv.id).then(() => {
          loadConversations();
          if (currentConversationId === conv.id) {
            currentConversationId = null;
            chatMessages.innerHTML = '';
          }
        });
      }
    });
    
    conversationList.appendChild(convEl);
  });
}

function clearConversationList() {
  conversationList.innerHTML = '<div class="empty-state">No conversations yet</div>';
}

async function loadConversationById(conversationId) {
  const conv = await loadConversation(conversationId);
  
  if (conv) {
    currentConversationId = conv.id;
    currentConversationTitle = conv.title;
    
    // Render messages
    chatMessages.innerHTML = '';
    if (conv.messages && Array.isArray(conv.messages)) {
      conv.messages.forEach(msg => {
        if (msg.role === 'user') {
          addMessage(msg.content, true);
        } else if (msg.role === 'assistant') {
          addMessage(msg.content, false);
        }
      });
    }
    
    // Update active state
    document.querySelectorAll('.conversation-item').forEach(el => {
      el.classList.remove('active');
    });
    document.querySelector(`[data-id="${conv.id}"]`)?.parentElement.classList.add('active');
  }
}

function showAuthModal(isSignUp = false) {
  isSignUpMode = isSignUp;
  authModalTitle.textContent = isSignUp ? 'Sign Up' : 'Sign In';
  authSubmit.textContent = isSignUp ? 'Sign Up' : 'Sign In';
  authToggle.innerHTML = isSignUp 
    ? 'Already have an account? <a href="#" id="toggleAuth">Sign In</a>'
    : 'Don\'t have an account? <a href="#" id="toggleAuth">Sign Up</a>';
  authModal.style.display = 'block';
  authEmail.value = '';
  authPassword.value = '';
  authError.textContent = '';
}

function closeAuthModal() {
  authModal.style.display = 'none';
  authError.textContent = '';
}

function showError(message) {
  authError.textContent = message;
}

function showMessage(message, type = 'info') {
  const msgEl = document.createElement('div');
  msgEl.className = `message-${type}`;
  msgEl.textContent = message;
  document.body.appendChild(msgEl);
  setTimeout(() => msgEl.remove(), 3000);
}

// ============================================================
// CHAT FUNCTIONS
// ============================================================

function addMessage(text, isUser = false) {
  const messageDiv = document.createElement('div');
  messageDiv.className = isUser ? 'user-message' : 'ai-message';
  messageDiv.innerHTML = formatMessage(text);
  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatMessage(text) {
  return text
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>')
    .replace(/### (.+?)\n/g, '<h3>$1</h3>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
}

async function analyzeCode(userText) {
  const code = codeInput.value.trim();
  const message = userText || code;
  if (!message) return;

  const userMessage = {
    role: 'user',
    content: message,     // ← fixed
    timestamp: new Date().toISOString()
  };
  
  // Save current conversation messages array
  let conversationMessages = currentConversationId ? 
    (await loadConversation(currentConversationId))?.messages || [] : [];
  conversationMessages.push(userMessage);
  
  addMessage(message, true);
  addMessage('Analyzing your code...', false);
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    
    const response = await fetch('http://localhost:8000/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code: code,
        language: 'python'
      }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    const data = await response.json();
    
    if (!response.ok) {
      addMessage('Error: ' + (data.detail || 'Unknown error'), false);
      return;
    }
    
    // Remove "Analyzing..." message
    const lastMsg = chatMessages.lastChild;
    if (lastMsg && lastMsg.textContent.includes('Analyzing')) {
      lastMsg.remove();
    }
    
    // Build response
    let fullResponse = '';
    fullResponse += '🧠 Understanding:\n' + (data.understanding || 'No understanding provided') + '\n\n';
    
    if (data.observations && data.observations.length > 0) {
      fullResponse += '⚠️ Observations:\n';
      data.observations.forEach(obs => fullResponse += '  - ' + obs + '\n');
    } else {
      fullResponse += '⚠️ Observations: None\n';
    }
    
    fullResponse += '\n';
    
    if (data.questions && data.questions.length > 0) {
      fullResponse += '❓ Questions:\n';
      data.questions.forEach(q => fullResponse += '  - ' + q + '\n');
    } else {
      fullResponse += '❓ Questions: None\n';
    }
    
    fullResponse += '\n';
    
    if (data.suggestions && data.suggestions.length > 0) {
      fullResponse += '💡 Suggestions:\n';
      data.suggestions.forEach(s => fullResponse += '  - ' + s + '\n');
    } else {
      fullResponse += '💡 Suggestions: None\n';
    }
    
    addMessage(fullResponse, false);
    
    // Save assistant message
    const assistantMessage = {
      role: 'assistant',
      content: fullResponse,
      timestamp: new Date().toISOString()
    };
    conversationMessages.push(assistantMessage);
    
    // Create or update conversation
    if (currentUser) {
      if (currentConversationId) {
        await updateConversation(currentConversationId, conversationMessages, currentConversationTitle || 'New Conversation');
      } else {
        const newConv = await createConversation(conversationMessages, 'New Conversation');
        if (newConv) {
          currentConversationId = newConv.id;
          loadConversations();
        }
      }
    }
    
  } catch (error) {
    if (error.name === 'AbortError') {
      addMessage('Error: Request timed out.', false);
    } else {
      addMessage('Error: ' + error.message, false);
    }
  }
}

// ============================================================
// EVENT LISTENERS
// ============================================================

// Auth modal close
document.querySelector('.close').addEventListener('click', closeAuthModal);
window.addEventListener('click', (e) => {
  if (e.target === authModal) closeAuthModal();
});

// Auth form toggle (using event delegation since toggleAuth is dynamically replaced)
authModal.addEventListener('click', (e) => {
  if (e.target.id === 'toggleAuth') {
    e.preventDefault();
    showAuthModal(!isSignUpMode);
  }
});

// Auth form submit
authForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const email = authEmail.value.trim();
  const password = authPassword.value.trim();
  
  if (!email || !password) {
    showError('Please fill in all fields');
    return;
  }
  
  if (isSignUpMode) {
    handleSignUp(email, password);
  } else {
    handleSignIn(email, password);
  }
});

// Sign in/out buttons
signInBtn.addEventListener('click', () => showAuthModal(false));
signOutBtn.addEventListener('click', handleSignOut);

// New conversation button
newConversationBtn.addEventListener('click', async () => {
  if (!currentUser) {
    showAuthModal(false);
    return;
  }
  currentConversationId = null;
  currentConversationTitle = null;
  codeInput.value = '';
  chatMessages.innerHTML = '';
  loadConversations();
});

// Chat send button
chatSend.addEventListener('click', () => {
  analyzeCode();
  chatInput.value = "";
});

// Chat input enter key
chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    analyzeCode();
    chatInput.value = "";
  }
});

// Clear code button (if exists)
if (clearBtn) {
  clearBtn.addEventListener('click', () => {
    codeInput.value = '';
  });
}

// ============================================================
// INITIALIZATION
// ============================================================

checkAuthSession();
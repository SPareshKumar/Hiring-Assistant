import streamlit as st
import os
from dotenv import load_dotenv
from chatbot import TechnicalInterviewChatbot
import time

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="TechHire AI Interview Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simplified and working CSS
st.markdown("""
<style>
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Main styling */
    .main > div {
        padding-top: 1rem;
    }
    
    /* Header */
    .app-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .app-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        color: white !important;
    }
    
    .app-subtitle {
        font-size: 1.2rem;
        margin-top: 0.5rem;
        color: white !important;
    }
    
    /* Status bar */
    .status-bar {
        background: white;
        border: 2px solid #e1e8ed;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .status-badge {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .progress-container {
        background: #f0f0f0;
        border-radius: 10px;
        height: 8px;
        width: 200px;
        margin: 0 1rem;
    }
    
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        border-radius: 10px;
        transition: width 0.3s ease;
    }
    
    /* Chat messages */
    .chat-message {
        margin-bottom: 1rem;
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
    }
    
    .chat-message.user {
        flex-direction: row-reverse;
        justify-content: flex-start;
    }
    
    .message-content {
        max-width: 70%;
        padding: 1rem 1.2rem;
        border-radius: 18px;
        word-wrap: break-word;
        line-height: 1.5;
    }
    
    .message-content.user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-bottom-right-radius: 8px;
    }
    
    .message-content.bot {
        background: white;
        color: #333;
        border: 1px solid #e1e8ed;
        border-bottom-left-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .message-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        flex-shrink: 0;
    }
    
    .avatar-user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .avatar-bot {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
    }
    
    /* Welcome message */
    .welcome-message {
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 15px;
        color: white;
        margin: 2rem 0;
    }
    
    /* Completion card */
    .completion-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    /* Hide empty sidebar containers */
    .css-1d391kg .element-container:empty {
        display: none !important;
    }
    
    .css-1d391kg .stMarkdown:empty {
        display: none !important;
    }
    
    /* Sidebar sections */
    .sidebar-section {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(10px);
    }
    
    .sidebar-title {
        color: white !important;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(255, 255, 255, 0.3);
    }
    
    .info-item {
        display: flex;
        align-items: flex-start;
        margin-bottom: 0.8rem;
        color: white;
    }
    
    .info-icon {
        margin-right: 0.8rem;
        font-size: 1rem;
        flex-shrink: 0;
        margin-top: 0.2rem;
    }
    
    .info-value {
        font-weight: 500;
        color: white !important;
        word-wrap: break-word;
        flex: 1;
    }
    
    .info-label {
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.8) !important;
        margin-bottom: 0.2rem;
    }
    
    /* Force sidebar text to be white */
    .css-1d391kg, .css-1rs6os, .element-container, .stMarkdown {
        color: white !important;
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 1rem;
        background: white;
        border-radius: 18px;
        border: 1px solid #e1e8ed;
        margin-bottom: 1rem;
        max-width: 200px;
        border-bottom-left-radius: 8px;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #999;
        animation: bounce 1.4s infinite ease-in-out;
    }
    
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes bounce {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'chatbot' not in st.session_state:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            st.error("❌ Google API key not found. Please set GOOGLE_API_KEY in your .env file.")
            st.stop()
        st.session_state.chatbot = TechnicalInterviewChatbot(api_key)
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'interview_started' not in st.session_state:
        st.session_state.interview_started = False
    
    if 'interview_completed' not in st.session_state:
        st.session_state.interview_completed = False
    
    if 'show_typing' not in st.session_state:
        st.session_state.show_typing = False

def display_header():
    """Display the application header."""
    st.markdown("""
    <div class="app-header">
        <h1 class="app-title">🤖 TechHire AI Interview Assistant</h1>
        <p class="app-subtitle">Streamlined Technical Interviews with AI-Powered Assessment</p>
    </div>
    """, unsafe_allow_html=True)

def display_status():
    """Display the current interview status."""
    # Fix: Access chatbot from session state
    chatbot = st.session_state.chatbot
    state = chatbot.get_conversation_state()
    current_state = state['current_state']  # Extract the string value
    
    status_map = {
        'greeting': ("👋 Welcome", 5),
        'collecting_info': ("📝 Collecting Information", 25),
        'tech_stack': ("🔍 Analyzing Profile", 35), 
        'technical_questions': ("💻 Technical Interview", 70),
        'completed': ("✅ Completed", 100)
    }
    
    # Use current_state (the string), NOT state (the dict)
    current_status, progress = status_map.get(current_state, ("🔄 In Progress", 0))
    
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-badge">{current_status}</div>
        <div class="progress-container">
            <div class="progress-bar" style="width: {progress}%"></div>
        </div>
        <div style="font-weight: 600; color: #666; font-size: 0.9rem;">{progress}%</div>
    </div>
    """, unsafe_allow_html=True)

def display_message(role, content):
    """Display a single message in the chat."""
    # Clean content
    content = content.strip().replace('\n', '<br>')
    
    # Basic markdown formatting
    import re
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
    content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)
    
    if role == "user":
        st.markdown(f"""
        <div class="chat-message user">
            <div class="message-content user">{content}</div>
            <div class="message-avatar avatar-user">👤</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message bot">
            <div class="message-avatar avatar-bot">🤖</div>
            <div class="message-content bot">{content}</div>
        </div>
        """, unsafe_allow_html=True)

def display_chat_interface():
    """Display the main chat interface."""
    # Display messages
    if len(st.session_state.messages) == 0:
        st.markdown("""
        <div class="welcome-message">
            <h3>Welcome to TechHire AI Interview</h3>
            <p>Click the button below to start your personalized technical interview session.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for message in st.session_state.messages:
            display_message(message["role"], message["content"])
    
    # Show typing indicator
    if st.session_state.show_typing:
        st.markdown("""
        <div class="chat-message bot">
            <div class="message-avatar avatar-bot">🤖</div>
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <span style="margin-left: 0.5rem; color: #999; font-size: 0.9rem;">AI is thinking...</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

def handle_user_input():
    """Handle user input and chatbot response."""
    chatbot = st.session_state.chatbot
    
    # Start interview button
    if not st.session_state.interview_started:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Interview", type="primary", use_container_width=True):
                greeting = chatbot.get_greeting_message()
                st.session_state.messages.append({"role": "assistant", "content": greeting})
                st.session_state.interview_started = True
                st.rerun()
        return
    
    # Check if interview is completed
    if chatbot.get_conversation_state()['current_state'] == "completed":
        st.session_state.interview_completed = True
        display_completion_card()
        return
    
    # Chat input
    user_input = st.chat_input(
        "Type your message here...", 
        disabled=st.session_state.interview_completed
    )
    
    if user_input and user_input.strip():
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Show typing and process response
        st.session_state.show_typing = True
        st.rerun()

def process_bot_response():
    """Process bot response after user input."""
    if st.session_state.show_typing and len(st.session_state.messages) > 0:
        chatbot = st.session_state.chatbot
        last_message = st.session_state.messages[-1]
        
        if last_message["role"] == "user":
            try:
                bot_response = chatbot.process_message(last_message["content"])
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                st.session_state.show_typing = False
                st.rerun()
            except Exception as e:
                error_message = f"Sorry, I encountered an error: {str(e)}. Please try again."
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                st.session_state.show_typing = False
                st.rerun()

def display_completion_card():
    """Display interview completion message."""
    st.markdown("""
    <div class="completion-card">
        <h2>🎉 Interview Completed Successfully!</h2>
        <p>Thank you for completing the technical interview. Your responses have been saved and our team will review them shortly.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Start New Interview", type="secondary", use_container_width=True):
            # Reset session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

def display_sidebar_content():
    """Display sidebar content without empty containers."""
    chatbot = st.session_state.chatbot
    
    # Candidate Info Section
    if hasattr(chatbot, 'candidate_info') and chatbot.candidate_info:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<h4 class="sidebar-title">👤 Candidate Profile</h4>', unsafe_allow_html=True)
        
        info_items = [
            ('full_name', '👤', 'Name'),
            ('email', '📧', 'Email'),
            ('phone', '📱', 'Phone'),
            ('experience_years', '💼', 'Experience'),
            ('desired_positions', '🎯', 'Position'),
            ('location', '📍', 'Location'),
            ('tech_stack', '💻', 'Tech Stack')
        ]
        
        for key, icon, label in info_items:
            if key in chatbot.candidate_info and chatbot.candidate_info[key]:
                value = chatbot.candidate_info[key]
                if key == 'experience_years' and value:
                    try:
                        experience_level = chatbot.get_experience_level(value)
                        value = f"{value} years ({experience_level.title()})"
                    except:
                        value = f"{value} years"
                
                st.markdown(f"""
                <div class="info-item">
                    <span class="info-icon">{icon}</span>
                    <div>
                        <div class="info-label">{label}</div>
                        <div class="info-value">{value}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Help Section
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<h4 class="sidebar-title">💡 Help & Tips</h4>', unsafe_allow_html=True)
    
    st.markdown("""
    **Commands:**
    - Type "exit", "quit", or "bye" to end
    - Type "skip" to skip a question
    
    **Tips:**
    - Be specific about your tech stack
    - Provide detailed answers
    - Mention specific projects/examples
    - Maximum 6 questions per interview
    
    **Features:**
    - Adaptive questions based on experience
    - Dynamic follow-up questions
    - Real-time assessment
    - Personalized interview flow
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # About Section
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<h4 class="sidebar-title">ℹ️ About</h4>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center;">
        <strong>TechHire AI Assistant</strong><br>
        <em>Version 2.0</em><br><br>
        Powered by Google Gemini AI<br>
        Built with Streamlit<br><br>
        🔒 Secure • 🚀 Fast • 🎯 Accurate
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()

    # Sidebar - use single container to avoid empty boxes
    with st.sidebar:
        display_sidebar_content()

    # Main content
    display_header()
    display_status()
    display_chat_interface()
    handle_user_input()
    process_bot_response()

if __name__ == "__main__":
    main()
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
    initial_sidebar_state="collapsed"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .user-message {
        background-color: #e8f4f8;
        border-left: 4px solid #1f77b4;
        color: #000 !important;
    }
    
    .bot-message {
        background-color: #f0f8e8;
        border-left: 4px solid #2ca02c;
        color: #000 !important;
    }
    
    .title {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    
    .header-info {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border-left: 4px solid #17a2b8;
        color: #000 !important;
    }
    
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: #fafafa;
    }
    
    .status-info {
        background-color: #fff3cd;
        padding: 0.75rem;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
        margin-bottom: 1rem;
        color: #000 !important;
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

def display_header():
    """Display the application header."""
    st.markdown("<h1 class='title'>🤖 TechHire AI Interview Assistant</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='header-info'>
        <h3>📋 Interview Process Overview</h3>
        <ul>
            <li><strong>Step 1:</strong> Personal Information Collection</li>
            <li><strong>Step 2:</strong> Technical Skills Assessment</li>
            <li><strong>Step 3:</strong> Tailored Technical Questions</li>
            <li><strong>Step 4:</strong> Interview Completion & Next Steps</li>
        </ul>
        <p><em>💡 Tip: You can type 'exit', 'quit', or 'bye' at any time to end the interview.</em></p>
    </div>
    """, unsafe_allow_html=True)

def display_status():
    """Display current interview status."""
    chatbot = st.session_state.chatbot
    state = chatbot.get_conversation_state()
    
    status_map = {
        "greeting": "🚀 Ready to Start",
        "collecting_info": "📝 Collecting Information",
        "tech_stack": "💻 Tech Stack Assessment",
        "technical_questions": "❓ Technical Interview",
        "completed": "✅ Interview Completed"
    }
    
    current_status = status_map.get(state, "🔄 In Progress")
    
    # Progress calculation
    progress = 0
    if state == "greeting":
        progress = 0
    elif state == "collecting_info":
        progress = 25
    elif state == "tech_stack":
        progress = 50
    elif state == "technical_questions":
        progress = 75
    elif state == "completed":
        progress = 100

    # Make "Current Status" text always black
    st.markdown(f"""
    <div class='status-info'>
        <strong style="color: #000 !important;">Current Status:</strong> <span style="color: #000 !important;">{current_status}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.progress(progress / 100)

def display_chat_history():
    """Display chat message history."""
    st.markdown("<h3>💬 Conversation</h3>", unsafe_allow_html=True)
    
    chat_container = st.container()
    with chat_container:
        interview_completed = st.session_state.get("interview_completed", False)
        
        for message in st.session_state.messages:
            # Remove the "customized" message if interview is completed
            if (
                interview_completed
                and message["role"] == "assistant"
                and "The interview has been customized based on your responses and technical background." in message["content"]
            ):
                # Remove the line from the message content
                content = message["content"].replace(
                    "*The interview has been customized based on your responses and technical background.*", ""
                ).replace(
                    "The interview has been customized based on your responses and technical background.", ""
                ).strip()
                # Remove any trailing/leading newlines
                content = content.strip("\n")
            else:
                content = message["content"]
            
            # Clean and normalize content
            content = content.strip()
            
            # Remove any HTML tags that might have been accidentally added
            import re
            content = re.sub(r'<[^>]*>', '', content)
            
            # Convert markdown-style formatting to HTML for display
            content = content.replace('**', '<strong>').replace('**', '</strong>')
            content = content.replace('\n', '<br>')
            
            if message["role"] == "user":
                st.markdown(f"""
                <div class='stChatMessage user-message' style='color: #000 !important;'>
                    <strong>You:</strong> {content}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class='stChatMessage bot-message' style='color: #000 !important;'>
                    <strong>🤖 Assistant:</strong> {content}
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
    if chatbot.get_conversation_state() == "completed":
        st.session_state.interview_completed = True
        st.markdown("""
        <div style='text-align: center; padding: 2rem; background-color: #d4edda; 
                    border-radius: 10px; border: 1px solid #c3e6cb; margin: 2rem 0; color: #000 !important;'>
            <h3 style='color: #155724; margin-bottom: 1rem;'>🎉 Interview Completed Successfully!</h3>
            <p style='color: #155724; margin-bottom: 1rem;'>Thank you for completing the technical interview.</p>
            <p style='color: #155724; font-size: 0.9rem;'>Your responses have been saved and our team will review them shortly.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Option to start a new interview
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Start New Interview", type="secondary", use_container_width=True):
                # Reset session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        return
    
    # Chat input
    if user_input := st.chat_input("Type your message here...", disabled=st.session_state.interview_completed):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Get bot response
        with st.spinner("🤖 Thinking..."):
            try:
                bot_response = chatbot.process_message(user_input)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                
                # Small delay for better UX
                time.sleep(0.5)
                
            except Exception as e:
                error_message = f"Sorry, I encountered an error: {str(e)}. Please try again."
                st.session_state.messages.append({"role": "assistant", "content": error_message})
        
        st.rerun()

def display_sentiment_analysis():
    """Display real-time sentiment analysis in sidebar."""
    chatbot = st.session_state.chatbot
    
    if hasattr(chatbot, 'responses') and len(chatbot.responses) > 0:
        st.sidebar.markdown("### 🎭 Sentiment Analysis")
        
        # Get recent responses for analysis
        recent_responses = chatbot.responses[-3:] if len(chatbot.responses) >= 3 else chatbot.responses
        
        if recent_responses:
            # Perform quick sentiment analysis on recent responses
            try:
                recent_analysis = chatbot.sentiment_analyzer.analyze_all_responses(recent_responses)
                
                # Display key metrics
                col1, col2 = st.sidebar.columns(2)
                
                with col1:
                    sentiment_emoji = {
                        "positive": "😊",
                        "negative": "😟", 
                        "neutral": "😐"
                    }
                    current_sentiment = recent_analysis.get('overall_sentiment', 'neutral')
                    st.metric(
                        "Mood", 
                        f"{sentiment_emoji.get(current_sentiment, '😐')} {current_sentiment.title()}"
                    )
                
                with col2:
                    confidence = recent_analysis.get('average_confidence', 0) * 100
                    st.metric("Confidence", f"{confidence:.0f}%")
                
                # Engagement level
                engagement = recent_analysis.get('dominant_engagement_level', 'medium')
                engagement_emoji = {"high": "🚀", "medium": "👍", "low": "📉"}
                st.sidebar.markdown(f"**Engagement:** {engagement_emoji.get(engagement, '👍')} {engagement.title()}")
                
                # Emotional tone
                tone = recent_analysis.get('dominant_emotional_tone', 'calm')
                tone_emoji = {
                    "confident": "💪", "enthusiastic": "⭐", "nervous": "😰",
                    "frustrated": "😤", "uncertain": "❓", "calm": "😌"
                }
                st.sidebar.markdown(f"**Tone:** {tone_emoji.get(tone, '😌')} {tone.title()}")
                
                # Quick insights
                insights = recent_analysis.get('insights', [])
                if insights:
                    st.sidebar.markdown("**Recent Insights:**")
                    for insight in insights[:2]:  # Show top 2 insights
                        st.sidebar.markdown(f"• {insight}")
                        
            except Exception as e:
                st.sidebar.markdown("*Analyzing responses...*")
    
    # Show final sentiment analysis if interview is completed
    if hasattr(chatbot, 'sentiment_analysis') and chatbot.sentiment_analysis:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Final Analysis")
        
        analysis = chatbot.sentiment_analysis
        
        # Sentiment distribution chart
        if st.sidebar.checkbox("Show Sentiment Breakdown"):
            sentiment_data = analysis.get('sentiment_distribution', {})
            if sentiment_data:
                st.sidebar.markdown("**Sentiment Distribution:**")
                for sentiment, percentage in sentiment_data.items():
                    if percentage > 0:
                        st.sidebar.progress(percentage/100)
                        st.sidebar.markdown(f"{sentiment.title()}: {percentage:.1f}%")

def display_candidate_info():
    """Display collected candidate information in sidebar."""
    chatbot = st.session_state.chatbot
    
    if hasattr(chatbot, 'candidate_info') and chatbot.candidate_info:
        st.sidebar.markdown("### 📋 Candidate Information")
        
        info_display = {
            'full_name': '👤 Name',
            'email': '📧 Email',
            'phone': '📱 Phone',
            'experience_years': '💼 Experience',
            'desired_positions': '🎯 Position',
            'location': '📍 Location',
            'tech_stack': '💻 Tech Stack'
        }
        
        for key, label in info_display.items():
            if key in chatbot.candidate_info:
                value = chatbot.candidate_info[key]
                if key == 'experience_years':
                    experience_level = chatbot.get_experience_level(value)
                    value = f"{value} years ({experience_level.title()})"
                st.sidebar.markdown(f"**{label}:** {value}")
    
    # Display technical questions progress with dynamic info
    if hasattr(chatbot, 'responses') and chatbot.responses:
        st.sidebar.markdown("### ❓ Interview Progress")
        total_questions = len(chatbot.responses)
        
        # Show question types
        main_questions = sum(1 for r in chatbot.responses if not r.get('is_followup', False))
        followup_questions = total_questions - main_questions
        
        st.sidebar.markdown(f"**Questions Asked:** {total_questions}")
        st.sidebar.markdown(f"• Main Questions: {main_questions}")
        if followup_questions > 0:
            st.sidebar.markdown(f"• Follow-up Questions: {followup_questions}")
        
        # Show answered vs skipped
        answered = sum(1 for r in chatbot.responses if r['answer'] != 'Skipped')
        skipped = total_questions - answered
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Answered", answered)
        with col2:
            st.metric("Skipped", skipped)
        
        # Show recent questions
        if len(chatbot.responses) > 0:
            st.sidebar.markdown("### 📝 Recent Questions")
            for i, response in enumerate(chatbot.responses[-3:], 1):  # Last 3 questions
                question_preview = response['question'][:50] + "..." if len(response['question']) > 50 else response['question']
                status = "✅" if response['answer'] != 'Skipped' else "⏭️"
                st.sidebar.markdown(f"{status} **Q{len(chatbot.responses)-3+i}:** {question_preview}")
    
    # Display sentiment analysis
    display_sentiment_analysis()
    
    # Display interview insights
    if hasattr(chatbot, 'candidate_info') and 'tech_stack' in chatbot.candidate_info:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🎯 Interview Insights")
        
        tech_stack = chatbot.candidate_info.get('tech_stack', '')
        experience_years = chatbot.candidate_info.get('experience_years', '0')
        experience_level = chatbot.get_experience_level(experience_years)
        
        st.sidebar.markdown(f"**Difficulty Level:** {experience_level.title()}")
        
        # Show covered technologies
        if hasattr(chatbot, 'responses') and chatbot.responses:
            covered_techs = set()
            for response in chatbot.responses:
                question_lower = response['question'].lower()
                for tech in tech_stack.split(','):
                    tech = tech.strip().lower()
                    if tech in question_lower:
                        covered_techs.add(tech.title())
            
            if covered_techs:
                st.sidebar.markdown(f"**Technologies Covered:** {', '.join(list(covered_techs)[:3])}")

def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # Create layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Display header
        display_header()
        
        # Display status
        display_status()
        
        # Display chat history
        if st.session_state.messages:
            display_chat_history()
        
        # Handle user input
        handle_user_input()
    
    with col2:
        # Display candidate information
        display_candidate_info()
        
        # Help section
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 💡 Help & Tips")
        st.sidebar.markdown("""
        **Commands:**
        - `exit`, `quit`, `bye` - End interview
        - `skip` - Skip current question
        
        **Dynamic Features:**
        - Questions adapt to your experience level
        - Follow-up questions based on your answers
        - Tech stack specific questions
        - Maximum 6 questions per interview
        
        **Tips:**
        - Be specific about your tech stack
        - Provide detailed answers for better follow-ups
        - Mention specific projects/examples
        
        **Support:**
        If you encounter issues, please refresh the page and try again.
        """)
        
        # Footer
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 About")
        st.sidebar.markdown("""
        **TechHire AI Assistant v1.0**
        
        Powered by Google Gemini AI
        
        Built with Streamlit
        """)

if __name__ == "__main__":
    main()
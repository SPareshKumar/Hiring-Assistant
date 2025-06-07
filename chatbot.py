import google.generativeai as genai
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import re

class TechnicalInterviewChatbot:
    def __init__(self, api_key: str):
        """Initialize the chatbot with Google Gemini API."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Conversation states
        self.GREETING = "greeting"
        self.COLLECTING_INFO = "collecting_info"
        self.TECH_STACK = "tech_stack"
        self.TECHNICAL_QUESTIONS = "technical_questions"
        self.COMPLETED = "completed"
        
        self.current_state = self.GREETING
        self.candidate_info = {}
        self.tech_questions = []
        self.current_question_index = 0
        self.responses = []
        
        # Information fields to collect
        self.info_fields = [
            "full_name",
            "email",
            "phone",
            "experience_years",
            "desired_positions",
            "location",
            "tech_stack"
        ]
        self.current_field_index = 0
        
        # Exit keywords
        self.exit_keywords = ["exit", "quit", "bye", "goodbye", "end", "stop"]
        
    def get_greeting_message(self) -> str:
        """Return the initial greeting message."""
        return """🤖 **Welcome to TechHire AI Interview Assistant!** 

I'm here to help streamline your technical interview process. I'll:
- Collect your basic information
- Understand your technical expertise
- Ask relevant technical questions based on your skills
- Provide a structured interview experience

Let's get started! 

**Type 'exit' or 'quit' at any time to end the conversation.**

May I have your full name?"""
    
    def is_exit_command(self, user_input: str) -> bool:
        """Check if user wants to exit."""
        return user_input.lower().strip() in self.exit_keywords
    
    def get_exit_message(self) -> str:
        """Return exit message."""
        return """
Thank you for using TechHire AI Interview Assistant! 👋

Your responses have been saved. Our team will review your information and get back to you within 2-3 business days.

Have a great day!
        """
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        # Remove spaces, dashes, and parentheses
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        # Check if it contains only digits and is of reasonable length
        return cleaned.isdigit() and 10 <= len(cleaned) <= 15
    
    def validate_experience(self, experience: str) -> bool:
        """Validate years of experience."""
        try:
            years = float(experience)
            return 0 <= years <= 50
        except ValueError:
            return False
    
    def get_field_prompt(self, field: str) -> str:
        """Get prompt for each information field."""
        prompts = {
            "full_name": "What's your full name?",
            "email": "What's your email address?",
            "phone": "What's your phone number?",
            "experience_years": "How many years of professional experience do you have? (Enter a number)",
            "desired_positions": "What position(s) are you interested in? (You can list multiple)",
            "location": "What's your current location (city, state/country)?",
            "tech_stack": "What technologies do you work with? Please list your tech stack (programming languages, frameworks, databases, tools, etc.)"
        }
        return prompts.get(field, "Please provide the requested information.")
    
    def validate_field_input(self, field: str, value: str) -> tuple[bool, str]:
        """Validate input for specific fields."""
        if field == "email":
            if not self.validate_email(value):
                return False, "Please enter a valid email address (e.g., john@example.com)"
        elif field == "phone":
            if not self.validate_phone(value):
                return False, "Please enter a valid phone number (10-15 digits)"
        elif field == "experience_years":
            if not self.validate_experience(value):
                return False, "Please enter a valid number of years (0-50)"
        elif field == "full_name":
            if len(value.strip()) < 2:
                return False, "Please enter your full name (at least 2 characters)"
        elif field in ["desired_positions", "location", "tech_stack"]:
            if len(value.strip()) < 2:
                return False, "Please provide more detailed information"
        
        return True, ""
    
    def get_experience_level(self, years_str: str) -> str:
        """Determine experience level based on years."""
        try:
            years = float(years_str)
            if years < 2:
                return "junior"
            elif years < 5:
                return "mid-level"
            elif years < 10:
                return "senior"
            else:
                return "expert"
        except:
            return "mid-level"
    
    def generate_initial_question(self, tech_stack: str, experience_years: str) -> str:
        """Generate the first technical question based on tech stack and experience."""
        experience_level = self.get_experience_level(experience_years)
        
        try:
            prompt = f"""
            You are conducting a technical interview for a {experience_level} developer.
            
            Candidate's Tech Stack: {tech_stack}
            Years of Experience: {experience_years}
            
            Generate ONE specific technical question that:
            1. Tests their knowledge of their PRIMARY technology from the tech stack
            2. Is appropriate for a {experience_level} developer
            3. Allows for follow-up questions based on their answer
            4. Is practical and scenario-based
            
            Experience level guidelines:
            - Junior (0-2 years): Basic concepts, syntax, simple problem-solving
            - Mid-level (2-5 years): Design patterns, best practices, debugging
            - Senior (5-10 years): Architecture, scalability, complex problem-solving
            - Expert (10+ years): System design, optimization, leadership scenarios
            
            Return ONLY the question, no numbering or additional text.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            # Fallback based on experience level
            primary_tech = tech_stack.split(',')[0].strip()
            fallback_questions = {
                "junior": f"Can you explain the basic concepts of {primary_tech} and walk me through a simple project you've built with it?",
                "mid-level": f"How would you optimize performance in a {primary_tech} application? Share an example from your experience.",
                "senior": f"Design a scalable system using {primary_tech}. What architectural decisions would you make and why?",
                "expert": f"You're leading a team migrating a legacy system to {primary_tech}. What's your strategy and how do you handle challenges?"
            }
            return fallback_questions.get(experience_level, fallback_questions["mid-level"])
    
    def analyze_answer_and_generate_followup(self, question: str, answer: str, tech_stack: str, experience_level: str) -> tuple[str, bool]:
        """Analyze the candidate's answer and generate a follow-up question if needed."""
        if answer.lower() == "skipped":
            return "", False
            
        try:
            prompt = f"""
            You are a technical interviewer analyzing a candidate's response.
            
            Original Question: {question}
            Candidate's Answer: {answer}
            Tech Stack: {tech_stack}
            Experience Level: {experience_level}
            
            Analyze the answer and determine:
            1. Does the answer show good understanding? (yes/no)
            2. Are there areas that need deeper exploration?
            3. Should you ask a follow-up question?
            
            If a follow-up is needed, generate ONE specific follow-up question that:
            - Digs deeper into their answer
            - Tests practical application
            - Explores edge cases or advanced concepts
            - Is relevant to their experience level
            
            Respond in this format:
            FOLLOWUP_NEEDED: yes/no
            QUESTION: [your follow-up question or "none"]
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse response
            lines = response_text.split('\n')
            followup_needed = False
            followup_question = ""
            
            for line in lines:
                if line.startswith('FOLLOWUP_NEEDED:'):
                    followup_needed = 'yes' in line.lower()
                elif line.startswith('QUESTION:'):
                    followup_question = line.replace('QUESTION:', '').strip()
                    if followup_question.lower() == 'none':
                        followup_question = ""
            
            return followup_question, followup_needed
            
        except Exception as e:
            return "", False
    
    def generate_next_question(self, previous_questions: List[dict], tech_stack: str, experience_level: str) -> str:
        """Generate the next question based on previous Q&A context."""
        try:
            # Prepare context of previous questions and answers
            qa_context = ""
            for i, qa in enumerate(previous_questions[-3:], 1):  # Last 3 Q&As for context
                qa_context += f"Q{i}: {qa['question']}\nA{i}: {qa['answer']}\n\n"
            
            remaining_topics = self.get_remaining_topics(previous_questions, tech_stack)
            
            prompt = f"""
            You are conducting a technical interview. Here's the context:
            
            Tech Stack: {tech_stack}
            Experience Level: {experience_level}
            Questions Asked So Far: {len(previous_questions)}
            
            Previous Q&A Context:
            {qa_context}
            
            Remaining Topics to Cover: {remaining_topics}
            
            Generate the NEXT technical question that:
            1. Covers a different aspect/technology from their tech stack
            2. Builds upon their previous answers when relevant
            3. Is appropriate for their experience level
            4. Explores areas not yet covered in depth
            5. Is practical and scenario-based
            
            Avoid repeating similar concepts from previous questions.
            Return ONLY the question, no additional text.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            # Fallback question
            tech_list = [t.strip() for t in tech_stack.split(',')]
            if len(previous_questions) < len(tech_list):
                unused_tech = tech_list[len(previous_questions)]
                return f"Tell me about your experience with {unused_tech} and how you've used it in real projects."
            else:
                return "How do you stay updated with new technologies and what's your approach to continuous learning?"
    
    def get_remaining_topics(self, previous_questions: List[dict], tech_stack: str) -> str:
        """Identify remaining topics to cover based on tech stack."""
        tech_list = [t.strip().lower() for t in tech_stack.split(',')]
        covered_topics = []
        
        for qa in previous_questions:
            question_lower = qa['question'].lower()
            for tech in tech_list:
                if tech in question_lower:
                    covered_topics.append(tech)
        
        remaining = [tech for tech in tech_list if tech not in covered_topics]
        return ', '.join(remaining) if remaining else "Advanced concepts and best practices"
    
    def get_fallback_response(self) -> str:
        """Get fallback response for unexpected inputs."""
        if self.current_state == self.COLLECTING_INFO:
            current_field = self.info_fields[self.current_field_index]
            return f"I didn't quite understand that. {self.get_field_prompt(current_field)}"
        elif self.current_state == self.TECHNICAL_QUESTIONS:
            return "Please provide your answer to the technical question, or type 'skip' if you'd like to move to the next question."
        else:
            return "I'm not sure how to help with that. Could you please clarify or try again?"
    
    def process_message(self, user_input: str) -> str:
        """Process user message and return appropriate response."""
        user_input = user_input.strip()
        
        # Check for exit command
        if self.is_exit_command(user_input):
            self.save_candidate_data()
            self.current_state = self.COMPLETED
            return self.get_exit_message()
        
        # Handle different conversation states
        if self.current_state == self.GREETING:
            return self.handle_greeting(user_input)
        elif self.current_state == self.COLLECTING_INFO:
            return self.handle_info_collection(user_input)
        elif self.current_state == self.TECHNICAL_QUESTIONS:
            return self.handle_technical_questions(user_input)
        elif self.current_state == self.COMPLETED:
            return "The interview has been completed. Thank you!"
        
        return self.get_fallback_response()
    
    def handle_greeting(self, user_input: str) -> str:
        """Handle the greeting state."""
        if user_input:
            self.candidate_info["full_name"] = user_input
            self.current_field_index = 1  # Move to next field (email)
            self.current_state = self.COLLECTING_INFO
            return f"Nice to meet you, {user_input}! {self.get_field_prompt('email')}"
        return "Please tell me your full name to get started."
    
    def handle_info_collection(self, user_input: str) -> str:
        """Handle information collection state."""
        if self.current_field_index >= len(self.info_fields):
            # All info collected, move to technical questions
            self.current_state = self.TECH_STACK
            return self.start_technical_questions()
        
        current_field = self.info_fields[self.current_field_index]
        
        # Validate input
        is_valid, error_message = self.validate_field_input(current_field, user_input)
        if not is_valid:
            return error_message
        
        # Store the information
        self.candidate_info[current_field] = user_input
        self.current_field_index += 1
        
        # Check if we've collected all info
        if self.current_field_index >= len(self.info_fields):
            return self.start_technical_questions()
        
        # Ask for next field
        next_field = self.info_fields[self.current_field_index]
        return f"Great! {self.get_field_prompt(next_field)}"
    
    def start_technical_questions(self) -> str:
        """Start the technical questions phase with dynamic question generation."""
        tech_stack = self.candidate_info.get("tech_stack", "")
        experience_years = self.candidate_info.get("experience_years", "0")
        
        # Generate first question based on tech stack and experience
        first_question = self.generate_initial_question(tech_stack, experience_years)
        self.tech_questions = [first_question]  # Start with first question only
        self.current_question_index = 0
        self.current_state = self.TECHNICAL_QUESTIONS
        
        experience_level = self.get_experience_level(experience_years)
        
        return f"""
Perfect! I have all your information. Now let's move to the technical questions.

Based on your tech stack ({tech_stack}) and {experience_years} years of experience, I've tailored questions for a {experience_level} developer.

**Question 1:**
{first_question}

Please provide your answer. You can type 'skip' if you'd like to move to the next question.
        """
    
    def handle_technical_questions(self, user_input: str) -> str:
        """Handle technical questions phase with dynamic follow-ups."""
        current_question = self.tech_questions[self.current_question_index]
        
        # Store the response
        response_entry = {
            "question": current_question,
            "answer": user_input if user_input.lower() != 'skip' else "Skipped",
            "question_number": len(self.responses) + 1,
            "timestamp": datetime.now().isoformat()
        }
        self.responses.append(response_entry)
        
        tech_stack = self.candidate_info.get("tech_stack", "")
        experience_years = self.candidate_info.get("experience_years", "0")
        experience_level = self.get_experience_level(experience_years)
        
        # Check if we should ask a follow-up question
        if user_input.lower() != 'skip' and len(self.responses) <= 6:  # Max 6 questions total
            followup_question, needs_followup = self.analyze_answer_and_generate_followup(
                current_question, user_input, tech_stack, experience_level
            )
            
            if needs_followup and followup_question:
                # Add follow-up question
                self.tech_questions.append(followup_question)
                self.current_question_index += 1
                
                return f"""
Thank you for your response! 

**Follow-up Question {len(self.responses) + 1}:**
{followup_question}

Please elaborate on your answer.
                """
        
        # Generate next main question or complete interview
        if len(self.responses) >= 6:  # Maximum questions reached
            self.current_state = self.COMPLETED
            self.save_candidate_data()
            return self.get_completion_message()
        
        # Generate next question based on context
        next_question = self.generate_next_question(self.responses, tech_stack, experience_level)
        self.tech_questions.append(next_question)
        self.current_question_index += 1
        
        return f"""
Thank you for your response!

**Question {len(self.responses) + 1}:**
{next_question}

Please provide your answer, or type 'skip' to move to the next question.
        """
    
    def get_completion_message(self) -> str:
        """Get completion message with dynamic content."""
        total_questions = len(self.responses)
        skipped_count = sum(1 for r in self.responses if r['answer'] == 'Skipped')
        answered_count = total_questions - skipped_count
        
        return f"""
🎉 **Technical Interview Completed!**

Thank you, {self.candidate_info.get('full_name', 'candidate')}, for completing the technical interview!

**Interview Summary:**
- ✅ Profile information collected
- ✅ {total_questions} technical questions presented
- ✅ {answered_count} questions answered
- ✅ {skipped_count} questions skipped
- ✅ Responses saved successfully

**Your Experience Level:** {self.get_experience_level(self.candidate_info.get('experience_years', '0')).title()}
**Tech Stack Covered:** {self.candidate_info.get('tech_stack', 'N/A')}

**Next Steps:**
1. Our technical team will review your personalized responses
2. We'll contact you at {self.candidate_info.get('email', 'your email')} within 2-3 business days
3. Questions were tailored to your experience level and previous answers
4. If your profile matches our requirements, we'll schedule a detailed technical interview

Thank you for your time and interest in our company! 🚀

*The interview has been customized based on your responses and technical background.*
        """
    
    def save_candidate_data(self) -> None:
        """Save candidate data to JSON file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs("candidate_responses", exist_ok=True)
            
            # Prepare data to save
            data = {
                "timestamp": datetime.now().isoformat(),
                "candidate_info": self.candidate_info,
                "technical_responses": self.responses,
                "interview_status": "completed" if self.current_state == self.COMPLETED else "incomplete"
            }
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            candidate_name = self.candidate_info.get('full_name', 'unknown').replace(' ', '_')
            filename = f"candidate_responses/{candidate_name}_{timestamp}.json"
            
            # Save to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving candidate data: {e}")
    
    def get_conversation_state(self) -> str:
        """Get current conversation state for debugging."""
        return self.current_state
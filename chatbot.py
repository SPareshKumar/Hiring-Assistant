import google.generativeai as genai
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re
from sentiment_analyzer import SentimentAnalyzer

class TechnicalInterviewChatbot:
    def __init__(self, api_key: str):
        """Initialize the chatbot with Google Gemini API."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Initialize sentiment analyzer
        self.sentiment_analyzer = SentimentAnalyzer(self.model)
        self.sentiment_analysis = None
        self.individual_sentiments = []  # Store individual response sentiments

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
        
        # Enhanced candidate profile analysis
        self.candidate_profile = {}
        self.question_strategy = {}
        self.technical_areas_covered = set()
        self.skill_depth_assessment = {}
        
        # Question tracking to prevent duplicates
        self.asked_questions = set()
        self.asked_questions_raw = []
        
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
        
        # Enhanced position-specific question templates
        self.position_question_templates = {
            "frontend": ["ui/ux implementation", "responsive design", "state management", "performance optimization", "accessibility"],
            "backend": ["api design", "database optimization", "scalability", "security", "microservices"],
            "fullstack": ["system architecture", "api integration", "database design", "deployment", "testing"],
            "devops": ["ci/cd", "containerization", "monitoring", "infrastructure", "automation"],
            "mobile": ["platform specifics", "performance", "offline handling", "native features", "app store"],
            "data": ["data pipeline", "analytics", "ml models", "data visualization", "etl processes"],
            "qa": ["test automation", "test strategies", "bug tracking", "performance testing", "security testing"]
        }
    
    def analyze_candidate_profile(self) -> Dict:
        """Deeply analyze candidate profile to create personalized question strategy."""
        tech_stack = self.candidate_info.get("tech_stack", "")
        experience_years = self.candidate_info.get("experience_years", "0")
        desired_positions = self.candidate_info.get("desired_positions", "").lower()
        
        try:
            profile_analysis_prompt = f"""
            Analyze this candidate's profile in detail:
            
            Tech Stack: {tech_stack}
            Experience: {experience_years} years
            Desired Positions: {desired_positions}
            
            Provide a comprehensive analysis in JSON format:
            {{
                "primary_technologies": ["list of 3-4 main technologies"],
                "secondary_technologies": ["list of supporting technologies"],
                "experience_level_per_tech": {{"tech": "beginner/intermediate/advanced/expert"}},
                "position_category": "frontend/backend/fullstack/devops/mobile/data/qa/other",
                "specialization_areas": ["list of specialized areas based on tech stack"],
                "likely_project_types": ["types of projects they likely worked on"],
                "knowledge_gaps": ["potential areas to probe deeper"],
                "question_focus_areas": ["specific technical areas to focus questions on"],
                "complexity_level": "junior/mid/senior/expert",
                "interview_approach": "hands-on/theoretical/scenario-based/architecture-focused"
            }}
            """
            
            response = self.model.generate_content(profile_analysis_prompt)
            analysis = json.loads(response.text.strip())
            
            # Store the analysis
            self.candidate_profile = analysis
            return analysis
            
        except Exception as e:
            print(f"Error analyzing candidate profile: {e}")
            # Fallback analysis
            return {
                "primary_technologies": tech_stack.split(',')[:3],
                "experience_level_per_tech": {},
                "position_category": "fullstack",
                "complexity_level": self.get_experience_level(experience_years),
                "interview_approach": "scenario-based"
            }
    
    def analyze_response_sentiment(self, response_text: str) -> Dict:
        """Analyze sentiment of individual response with better error handling."""
        if not response_text or response_text.lower() in ["skipped", "skip"]:
            return {
                "overall_sentiment": "Neutral",
                "confidence_indicators": "Not Available",
                "technical_depth": "Not Assessed",
                "communication_style": "Not Available",
                "engagement_level": "Not Available"
            }
        
        try:
            # Use the sentiment analyzer
            sentiment_result = self.sentiment_analyzer.analyze_sentiment(response_text)
            
            if sentiment_result and isinstance(sentiment_result, dict):
                return sentiment_result
            else:
                # Fallback analysis using simple keyword detection
                return self.fallback_sentiment_analysis(response_text)
                
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return self.fallback_sentiment_analysis(response_text)
    
    def fallback_sentiment_analysis(self, text: str) -> Dict:
        """Fallback sentiment analysis using keyword detection."""
        text_lower = text.lower()
        
        # Confidence indicators
        confident_words = ["definitely", "certainly", "absolutely", "sure", "confident", "know", "experienced"]
        uncertain_words = ["maybe", "perhaps", "think", "believe", "probably", "not sure", "guess"]
        
        confident_count = sum(1 for word in confident_words if word in text_lower)
        uncertain_count = sum(1 for word in uncertain_words if word in text_lower)
        
        # Technical depth indicators
        technical_words = ["implement", "architecture", "database", "algorithm", "optimization", "framework", "api"]
        technical_count = sum(1 for word in technical_words if word in text_lower)
        
        # Determine overall sentiment
        if confident_count > uncertain_count:
            overall_sentiment = "Confident"
        elif uncertain_count > confident_count:
            overall_sentiment = "Cautious"
        else:
            overall_sentiment = "Balanced"
        
        # Determine confidence level
        if confident_count >= 2:
            confidence_level = "High"
        elif uncertain_count >= 2:
            confidence_level = "Low"
        else:
            confidence_level = "Moderate"
        
        # Technical depth
        if technical_count >= 3:
            technical_depth = "Deep"
        elif technical_count >= 1:
            technical_depth = "Moderate"
        else:
            technical_depth = "Surface"
        
        return {
            "overall_sentiment": overall_sentiment,
            "confidence_indicators": confidence_level,
            "technical_depth": technical_depth,
            "communication_style": "Professional",
            "engagement_level": "Good" if len(text) > 100 else "Brief"
        }

    def generate_personalized_first_question(self) -> str:
        """Generate highly personalized first question based on detailed profile analysis."""
        profile = self.candidate_profile
        tech_stack = self.candidate_info.get("tech_stack", "")
        experience_years = self.candidate_info.get("experience_years", "0")
        desired_positions = self.candidate_info.get("desired_positions", "")
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                first_question_prompt = f"""
                Generate a highly specific first technical question for this candidate:
                
                CANDIDATE PROFILE:
                - Tech Stack: {tech_stack}
                - Experience: {experience_years} years
                - Target Role: {desired_positions}
                - Primary Technologies: {profile.get('primary_technologies', [])}
                - Position Category: {profile.get('position_category', 'fullstack')}
                - Specialization Areas: {profile.get('specialization_areas', [])}
                - Complexity Level: {profile.get('complexity_level', 'mid')}
                - Interview Approach: {profile.get('interview_approach', 'scenario-based')}
                
                REQUIREMENTS:
                1. Question must be SPECIFIC to their PRIMARY technology and target role
                2. Must match their experience level complexity
                3. Should be scenario-based and practical
                4. Should allow for follow-up questions based on their answer
                5. Must be relevant to real-world {desired_positions} challenges
                6. Must be UNIQUE and not similar to any previously asked questions
                
                Generate ONE specific question that combines their primary technology, target role requirements, experience level complexity, and a realistic work scenario.
                
                Return ONLY the question, no additional text.
                """
                
                response = self.model.generate_content(first_question_prompt)
                question = response.text.strip()
                
                # Check if question is duplicate
                if not self.is_question_duplicate(question):
                    # Add to tracking
                    self.add_question_to_tracking(question)
                    
                    # Mark the primary technology as covered
                    if profile.get('primary_technologies'):
                        self.technical_areas_covered.add(profile['primary_technologies'][0].lower())
                    
                    return question
                    
            except Exception as e:
                print(f"Error generating first question (attempt {attempt + 1}): {e}")
        
        # Enhanced fallback based on profile
        primary_tech = tech_stack.split(',')[0].strip() if tech_stack else "programming"
        experience_level = self.get_experience_level(experience_years)
        
        fallback_questions = {
            "junior": f"Walk me through how you would build a simple {desired_positions} feature using {primary_tech}. What would be your step-by-step approach?",
            "mid-level": f"You're tasked with optimizing a slow-performing {primary_tech} application in a {desired_positions} role. What's your debugging and optimization strategy?",
            "senior": f"Design a scalable {primary_tech} solution for a {desired_positions} team handling 100k+ users. What architectural decisions would you make?",
            "expert": f"You're leading a {desired_positions} team migrating from legacy {primary_tech} to modern stack. How do you plan and execute this transition?"
        }
    
        fallback_question = fallback_questions.get(experience_level, fallback_questions["mid-level"])
        self.add_question_to_tracking(fallback_question)
        return fallback_question

    def normalize_question(self, question: str) -> str:
        """Normalize question for duplicate detection."""
        normalized = question.lower()
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        normalized = re.sub(r'[.!?]+$', '', normalized)
        normalized = re.sub(r'\[q-\d+\]', '', normalized)
        normalized = re.sub(r'question \d+:', '', normalized)
        stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words = normalized.split()
        normalized = ' '.join([word for word in words if word not in stop_words])
        return normalized

    def get_conversation_state(self) -> Dict:
        """Get current conversation state for UI display."""
        return {
            "current_state": self.current_state,
            "candidate_info": self.candidate_info,
            "questions_asked": len(self.responses),
            "current_question_index": self.current_question_index,
            "tech_questions": self.tech_questions,
            "responses": self.responses,
            "technical_areas_covered": list(self.technical_areas_covered),
            "skill_depth_assessment": self.skill_depth_assessment,
            "candidate_profile": self.candidate_profile,
            "progress_percentage": self.get_progress_percentage(),
            "interview_completed": self.current_state == self.COMPLETED
        }
    
    def process_message(self, user_input: str) -> str:
        """Process user message and return chatbot response."""
        return self.process_input(user_input)

    def get_progress_percentage(self) -> int:
        """Calculate interview progress percentage."""
        if self.current_state == self.GREETING:
            return 5
        elif self.current_state == self.COLLECTING_INFO:
            info_fields_completed = len([k for k, v in self.candidate_info.items() if v])
            return 10 + (info_fields_completed * 10)  # 10-70%
        elif self.current_state == self.TECHNICAL_QUESTIONS:
            questions_completed = len(self.responses)
            return 70 + min(questions_completed * 4, 25)  # 70-95%
        elif self.current_state == self.COMPLETED:
            return 100
        else:
            return 0
    
    def is_question_duplicate(self, new_question: str) -> bool:
        """Check if a question is duplicate or too similar to existing ones."""
        if not new_question or not new_question.strip():
            return True
        normalized_new = self.normalize_question(new_question)
        if normalized_new in self.asked_questions:
            return True
        for existing_question in self.asked_questions:
            similarity = self.calculate_question_similarity(normalized_new, existing_question)
            if similarity > 0.8:
                return True
        return False

    def calculate_question_similarity(self, question1: str, question2: str) -> float:
        """Calculate similarity between two questions using simple word overlap."""
        words1 = set(question1.split())
        words2 = set(question2.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity

    def add_question_to_tracking(self, question: str):
        """Add question to tracking sets."""
        if question and question.strip():
            normalized = self.normalize_question(question)
            self.asked_questions.add(normalized)
            self.asked_questions_raw.append(question)

    def get_question_uniqueness_constraint(self) -> str:
        """Get constraint text for AI prompts to avoid duplicate questions."""
        if not self.asked_questions_raw:
            return "This is the first question."
        constraint = "PREVIOUSLY ASKED QUESTIONS (DO NOT repeat or create similar questions):\n"
        for i, question in enumerate(self.asked_questions_raw, 1):
            constraint += f"{i}. {question}\n"
        constraint += "\nThe new question MUST be completely different from all above questions."
        return constraint

    def analyze_response_depth_and_generate_followup(self, question: str, answer: str) -> Tuple[str, bool, Dict]:
        """Analyze response depth and generate targeted follow-up questions."""
        if answer.lower() == "skipped":
            return "", False, {}
        
        profile = self.candidate_profile
        tech_stack = self.candidate_info.get("tech_stack", "")
        experience_years = self.candidate_info.get("experience_years", "0")
        desired_positions = self.candidate_info.get("desired_positions", "")
        
        try:
            analysis_prompt = f"""
            Analyze this candidate's technical response in detail:
            
            CANDIDATE CONTEXT:
            - Tech Stack: {tech_stack}
            - Experience: {experience_years} years  
            - Target Role: {desired_positions}
            - Expected Complexity: {profile.get('complexity_level', 'mid')}
            
            QUESTION: {question}
            ANSWER: {answer}
            
            PREVIOUS RESPONSES CONTEXT: {len(self.responses)} questions asked so far
            AREAS ALREADY COVERED: {list(self.technical_areas_covered)}
            
            AVOID DUPLICATE QUESTIONS:
            {self.get_question_uniqueness_constraint()}
            
            Provide detailed analysis in JSON format:
            {{
                "response_quality": "excellent/good/average/poor",
                "technical_depth": "deep/moderate/shallow",
                "knowledge_level_shown": "expert/advanced/intermediate/beginner",
                "specific_strengths": ["list specific technical strengths shown"],
                "knowledge_gaps": ["areas where knowledge seems limited"],
                "follow_up_opportunities": ["specific areas to probe deeper"],
                "buzzwords_vs_understanding": "genuine_understanding/surface_level/mixed",
                "practical_experience_evident": true/false,
                "needs_followup": true/false,
                "followup_type": "clarification/deeper_dive/practical_application/edge_cases",
                "suggested_followup": "specific follow-up question if needed - must be UNIQUE from all previous questions"
            }}
            """
            
            response = self.model.generate_content(analysis_prompt)
            analysis = json.loads(response.text.strip())
            
            # Store skill assessment
            question_tech = self.extract_technology_from_question(question)
            if question_tech:
                self.skill_depth_assessment[question_tech] = {
                    "level": analysis.get("knowledge_level_shown", "intermediate"),
                    "quality": analysis.get("response_quality", "average"),
                    "depth": analysis.get("technical_depth", "moderate")
                }
            
            followup_needed = analysis.get("needs_followup", False)
            suggested_followup = analysis.get("suggested_followup", "")
            
            # Check if suggested follow-up is duplicate
            if followup_needed and suggested_followup:
                if not self.is_question_duplicate(suggested_followup):
                    self.add_question_to_tracking(suggested_followup)
                    return suggested_followup, True, analysis
                else:
                    # Generate alternative if suggested followup is duplicate
                    return "", False, analysis
            
            return "", False, analysis
            
        except Exception as e:
            print(f"Error analyzing response: {e}")
            return "", False, {}

    def generate_context_aware_next_question(self) -> str:
        """Generate next question based on comprehensive context analysis."""
        profile = self.candidate_profile
        tech_stack = self.candidate_info.get("tech_stack", "")
        experience_years = self.candidate_info.get("experience_years", "0")
        desired_positions = self.candidate_info.get("desired_positions", "")
        
        # Analyze previous responses for patterns
        response_analysis = self.analyze_response_patterns()
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                next_question_prompt = f"""
                Generate the next highly specific technical question based on comprehensive context:
                
                CANDIDATE PROFILE:
                - Tech Stack: {tech_stack}
                - Experience: {experience_years} years
                - Target Role: {desired_positions}
                - Position Category: {profile.get('position_category', 'fullstack')}
                - Complexity Level: {profile.get('complexity_level', 'mid')}
                
                INTERVIEW PROGRESS:
                - Questions Asked: {len(self.responses)}
                - Technical Areas Covered: {list(self.technical_areas_covered)}
                - Uncovered Technologies: {self.get_uncovered_technologies()}
                - Skill Assessments So Far: {json.dumps(self.skill_depth_assessment, indent=2)}
                
                RESPONSE PATTERNS ANALYSIS:
                {json.dumps(response_analysis, indent=2)}
                
                PREVIOUS Q&A CONTEXT (last 2):
                {self.get_recent_qa_context()}
                
                CRITICAL - AVOID DUPLICATE QUESTIONS:
                {self.get_question_uniqueness_constraint()}
                
                Generate ONE highly specific question that addresses an uncovered technical area, matches their demonstrated competency level, is directly relevant to {desired_positions} work, allows assessment of practical experience, and is COMPLETELY UNIQUE from all previous questions.
                
                Return ONLY the question, no additional text.
                """
                
                response = self.model.generate_content(next_question_prompt)
                question = response.text.strip()
                
                # Check if question is duplicate
                if not self.is_question_duplicate(question):
                    # Add to tracking
                    self.add_question_to_tracking(question)
                    
                    # Update covered areas
                    new_tech = self.extract_technology_from_question(question)
                    if new_tech:
                        self.technical_areas_covered.add(new_tech.lower())
                    
                    return question
                    
            except Exception as e:
                print(f"Error generating next question (attempt {attempt + 1}): {e}")
        
        # Fallback with uniqueness check
        return self.get_fallback_next_question()
    
    def analyze_response_patterns(self) -> Dict:
        """Analyze patterns in candidate's responses to inform next questions."""
        if not self.responses:
            return {"pattern": "no_data"}
        
        patterns = {
            "average_response_length": sum(len(r['answer']) for r in self.responses) / len(self.responses),
            "theoretical_vs_practical": self.assess_theoretical_vs_practical(),
            "confidence_indicators": self.count_confidence_indicators(),
            "technology_mentions": self.count_technology_mentions(),
            "experience_indicators": self.count_experience_indicators()
        }
        
        return patterns
    
    def assess_theoretical_vs_practical(self) -> str:
        """Assess if candidate gives theoretical or practical answers."""
        practical_indicators = ["project", "implemented", "built", "deployed", "used", "worked with", "experience"]
        theoretical_indicators = ["should", "would", "could", "theory", "concept", "generally", "typically"]
        
        practical_count = 0
        theoretical_count = 0
        
        for response in self.responses:
            answer_lower = response['answer'].lower()
            practical_count += sum(1 for indicator in practical_indicators if indicator in answer_lower)
            theoretical_count += sum(1 for indicator in theoretical_indicators if indicator in answer_lower)
        
        if practical_count > theoretical_count * 1.5:
            return "practical_focused"
        elif theoretical_count > practical_count * 1.5:
            return "theoretical_focused"
        else:
            return "balanced"
    
    def count_confidence_indicators(self) -> Dict:
        """Count indicators of confidence in responses."""
        confident_phrases = ["I have", "I've done", "I built", "I implemented", "I led", "I designed"]
        uncertain_phrases = ["I think", "maybe", "probably", "I'm not sure", "I believe", "I guess"]
        
        confident_count = 0
        uncertain_count = 0
        
        for response in self.responses:
            answer_lower = response['answer'].lower()
            confident_count += sum(1 for phrase in confident_phrases if phrase in answer_lower)
            uncertain_count += sum(1 for phrase in uncertain_phrases if phrase in answer_lower)
        
        return {
            "confident_indicators": confident_count,
            "uncertain_indicators": uncertain_count,
            "confidence_ratio": confident_count / max(uncertain_count, 1)
        }
    
    def count_technology_mentions(self) -> Dict:
        """Count specific technology mentions in responses."""
        tech_mentions = {}
        tech_list = [t.strip().lower() for t in self.candidate_info.get("tech_stack", "").split(',')]
        
        for response in self.responses:
            answer_lower = response['answer'].lower()
            for tech in tech_list:
                if tech in answer_lower:
                    tech_mentions[tech] = tech_mentions.get(tech, 0) + 1
        
        return tech_mentions
    
    def count_experience_indicators(self) -> Dict:
        """Count indicators of real-world experience."""
        experience_indicators = {
            "project_work": ["project", "application", "system", "platform"],
            "team_work": ["team", "collaborated", "worked with", "led", "managed"],
            "problem_solving": ["problem", "issue", "bug", "fixed", "solved", "optimized"],
            "production": ["production", "deployed", "live", "users", "scale"]
        }
        
        indicator_counts = {category: 0 for category in experience_indicators}
        
        for response in self.responses:
            answer_lower = response['answer'].lower()
            for category, indicators in experience_indicators.items():
                indicator_counts[category] += sum(1 for indicator in indicators if indicator in answer_lower)
        
        return indicator_counts
    
    def get_uncovered_technologies(self) -> List[str]:
        """Get technologies from their stack that haven't been covered yet."""
        tech_list = [t.strip().lower() for t in self.candidate_info.get("tech_stack", "").split(',')]
        return [tech for tech in tech_list if tech not in self.technical_areas_covered]
    
    def extract_technology_from_question(self, question: str) -> Optional[str]:
        """Extract the primary technology being asked about from the question."""
        tech_list = [t.strip().lower() for t in self.candidate_info.get("tech_stack", "").split(',')]
        question_lower = question.lower()
        
        for tech in tech_list:
            if tech in question_lower:
                return tech
        return None
    
    def get_recent_qa_context(self) -> str:
        """Get context from recent Q&A pairs."""
        if len(self.responses) < 2:
            return "Limited context available"
        
        recent_responses = self.responses[-2:]
        context = ""
        for i, response in enumerate(recent_responses, 1):
            context += f"Q{i}: {response['question']}\nA{i}: {response['answer'][:200]}...\n\n"
        
        return context
    
    def get_position_specific_focus_areas(self, position: str) -> str:
        """Get focus areas specific to the target position."""
        position_lower = position.lower()
        
        focus_areas = {
            "frontend": "Component architecture, state management, performance optimization, responsive design, accessibility, browser compatibility, build tools, testing frameworks",
            "backend": "API design, database optimization, security, scalability, microservices, caching strategies, error handling, monitoring",
            "fullstack": "System architecture, API integration, database design, deployment strategies, performance optimization, security across stack",
            "devops": "CI/CD pipelines, containerization, orchestration, monitoring, infrastructure as code, automation, security, cloud services",
            "mobile": "Platform-specific optimization, offline capabilities, native features, app store guidelines, performance, user experience, device compatibility",
            "data": "Data pipeline design, ETL processes, data modeling, analytics, visualization, machine learning, big data technologies, data governance",
            "qa": "Test automation, test strategy, bug tracking, performance testing, security testing, continuous testing, test data management"
        }
        
        for key, areas in focus_areas.items():
            if key in position_lower:
                return areas
        
        return "General software development practices, problem-solving, code quality, collaboration, continuous learning"
    
    def get_fallback_next_question(self) -> str:
        """Generate fallback question when AI generation fails."""
        uncovered_techs = self.get_uncovered_technologies()
        desired_positions = self.candidate_info.get("desired_positions", "developer")
        
        # Try different fallback approaches
        fallback_templates = [
            f"Tell me about a challenging problem you solved using {uncovered_techs[0] if uncovered_techs else 'your preferred technology'} in the context of {desired_positions} work. What was your approach?",
            f"Describe the most complex {desired_positions} project you've worked on. What technical challenges did you face and how did you overcome them?",
            f"How do you approach code reviews and quality assurance in {desired_positions} projects?",
            f"What's your experience with testing strategies in {desired_positions} development?",
            f"How do you handle performance optimization in your {desired_positions} work?"
        ]
        
        # Find a unique fallback question
        for template in fallback_templates:
            if not self.is_question_duplicate(template):
                self.add_question_to_tracking(template)
                return template
        
        # Last resort - generate a timestamp-based unique question
        import time
        unique_question = f"Based on your {desired_positions} experience, describe a recent technical decision you made and why you chose that approach. [Q-{int(time.time())}]"
        self.add_question_to_tracking(unique_question)
        return unique_question

    def get_greeting_message(self) -> str:
        """Return the initial greeting message."""
        return """🤖 **Welcome to TechHire AI Interview Assistant!** 

I'm here to help streamline your technical interview process with personalized questions. I'll:
- Collect your detailed profile information
- Analyze your technical expertise and target role
- Generate highly specific questions based on your experience and goals
- Adapt questions based on your responses for maximum relevance

Let's get started! 

**Type 'exit' or 'quit' at any time to end the conversation.**

May I have your full name?"""
    
    def start_technical_questions(self) -> str:
        """Start the technical questions phase with enhanced personalization."""
        # Analyze candidate profile comprehensively
        self.analyze_candidate_profile()
        
        # Generate highly personalized first question
        first_question = self.generate_personalized_first_question()
        self.tech_questions = [first_question]
        self.current_question_index = 0
        self.current_state = self.TECHNICAL_QUESTIONS
        
        tech_stack = self.candidate_info.get("tech_stack", "")
        experience_years = self.candidate_info.get("experience_years", "0")
        desired_positions = self.candidate_info.get("desired_positions", "")
        
        return f"""
Perfect! I have all your information and have analyzed your profile.

**Personalized Interview Strategy:**
- **Target Role:** {desired_positions}
- **Tech Stack:** {tech_stack}
- **Experience Level:** {self.get_experience_level(experience_years).title()}
- **Question Approach:** {self.candidate_profile.get('interview_approach', 'scenario-based').title()}

I've tailored questions specifically for your background and career goals. Each question will build on your previous responses.

**Question 1:**
{first_question}

Please provide a detailed answer. You can type 'skip' if you'd like to move to the next question.
        """
    
    def handle_technical_questions(self, user_input: str) -> str:
        """Handle technical questions phase with enhanced context awareness and sentiment analysis."""
        current_question = self.tech_questions[self.current_question_index]
        
        # Analyze sentiment of current response
        current_sentiment = self.analyze_response_sentiment(user_input)
        
        # Store the response with sentiment
        response_entry = {
            "question": current_question,
            "answer": user_input if user_input.lower() != 'skip' else "Skipped",
            "question_number": len(self.responses) + 1,
            "timestamp": datetime.now().isoformat(),
            "sentiment_analysis": current_sentiment
        }
        self.responses.append(response_entry)
        self.individual_sentiments.append(current_sentiment)
        
        # Format sentiment analysis for display
        response_sentiment = ""
        if user_input.lower() != 'skip' and current_sentiment:
            response_sentiment = f"""
📊 **Response Analysis:**
- **Communication Tone:** {current_sentiment.get('overall_sentiment', 'Neutral')}
- **Confidence Level:** {current_sentiment.get('confidence_indicators', 'Moderate')}
- **Technical Depth:** {current_sentiment.get('technical_depth', 'Good')}
- **Engagement:** {current_sentiment.get('engagement_level', 'Good')}
            """
        
        # Enhanced response analysis and follow-up generation
        if user_input.lower() != 'skip' and len(self.responses) <= 6:
            followup_question, needs_followup, analysis = self.analyze_response_depth_and_generate_followup(
                current_question, user_input
            )
            
            if needs_followup and followup_question:
                self.tech_questions.append(followup_question)
                self.current_question_index += 1
                
                return f"""
Thank you for your detailed response! 

**Technical Assessment:** {analysis.get('response_quality', 'Good').title()} quality response showing {analysis.get('technical_depth', 'moderate')} technical depth.

{response_sentiment}

**Follow-up Question:**
{followup_question}
                """
        
        # Check if we should continue with more questions
        if len(self.responses) < 7:  # Continue for up to 7 questions
            next_question = self.generate_context_aware_next_question()
            self.tech_questions.append(next_question)
            self.current_question_index += 1
            
            return f"""
Thank you for your response!

{response_sentiment}

**Question {len(self.responses) + 1}:**
{next_question}
            """
        else:
            # End the interview
            self.current_state = self.COMPLETED
            return self.generate_final_report()
    
    def generate_final_report(self) -> str:
        """Generate comprehensive final interview report."""
        # Perform overall sentiment analysis
        self.sentiment_analysis = self.analyze_overall_sentiment()
        
        # Generate detailed assessment
        assessment = self.generate_comprehensive_assessment()
        
        return f"""
🎯 **Technical Interview Completed!**

Thank you for participating in this comprehensive technical interview. Here's your detailed assessment:

{assessment}

**Next Steps:**
- Review the feedback provided
- Focus on identified improvement areas
- Keep building practical experience
- Continue learning and growing in your tech stack

Good luck with your job search! 🚀
        """
    
    def analyze_overall_sentiment(self) -> Dict:
        """Analyze overall sentiment across all responses."""
        if not self.individual_sentiments:
            return {"overall": "No responses to analyze"}
        
        try:
            overall_prompt = f"""
            Analyze the overall interview performance based on individual response sentiments:
            
            Individual Response Sentiments: {json.dumps(self.individual_sentiments, indent=2)}
            
            Provide overall assessment in JSON format:
            {{
                "overall_confidence": "high/medium/low",
                "technical_competency": "excellent/good/average/needs_improvement",
                "communication_clarity": "excellent/good/average/poor",
                "interview_performance": "strong/satisfactory/weak",
                "key_strengths": ["list main strengths"],
                "areas_for_improvement": ["list improvement areas"],
                "hiring_recommendation": "strong_yes/yes/maybe/no",
                "summary": "brief overall summary"
            }}
            """
            
            response = self.model.generate_content(overall_prompt)
            return json.loads(response.text.strip())
            
        except Exception as e:
            print(f"Error in overall sentiment analysis: {e}")
            return {"overall": "Analysis error", "summary": "Unable to complete analysis"}
    
    def generate_comprehensive_assessment(self) -> str:
        """Generate detailed assessment report."""
        candidate_name = self.candidate_info.get("full_name", "Candidate")
        tech_stack = self.candidate_info.get("tech_stack", "")
        experience_years = self.candidate_info.get("experience_years", "0")
        desired_positions = self.candidate_info.get("desired_positions", "")
        
        report = f"""
📋 **TECHNICAL INTERVIEW ASSESSMENT REPORT**

**Candidate:** {candidate_name}
**Target Role:** {desired_positions}
**Experience:** {experience_years} years
**Tech Stack:** {tech_stack}
**Interview Date:** {datetime.now().strftime('%Y-%m-%d')}

**📊 OVERALL PERFORMANCE:**
"""
        
        if self.sentiment_analysis:
            report += f"""
- **Technical Competency:** {self.sentiment_analysis.get('technical_competency', 'Good').title()}
- **Communication:** {self.sentiment_analysis.get('communication_clarity', 'Good').title()}
- **Confidence Level:** {self.sentiment_analysis.get('overall_confidence', 'Medium').title()}
- **Interview Performance:** {self.sentiment_analysis.get('interview_performance', 'Satisfactory').title()}

**💪 KEY STRENGTHS:**
"""
            for strength in self.sentiment_analysis.get('key_strengths', []):
                report += f"- {strength}\n"
            
            report += f"""
**🎯 AREAS FOR IMPROVEMENT:**
"""
            for improvement in self.sentiment_analysis.get('areas_for_improvement', []):
                report += f"- {improvement}\n"
            
            report += f"""
**🏆 HIRING RECOMMENDATION:** {self.sentiment_analysis.get('hiring_recommendation', 'Maybe').replace('_', ' ').title()}

**📝 SUMMARY:**
{self.sentiment_analysis.get('summary', 'Candidate showed reasonable technical knowledge and communication skills.')}
"""
        
        # Add technical areas assessment
        if self.skill_depth_assessment:
            report += f"""

**🔧 TECHNICAL SKILLS ASSESSMENT:**
"""
            for tech, assessment in self.skill_depth_assessment.items():
                report += f"- **{tech.title()}:** {assessment['level'].title()} level ({assessment['quality']} quality responses)\n"
        
        report += f"""

**📈 DETAILED QUESTION ANALYSIS:**
"""
        for i, response in enumerate(self.responses, 1):
            sentiment = response.get('sentiment_analysis', {})
            report += f"""
**Q{i}:** {response['question'][:100]}...
**Response Quality:** {sentiment.get('technical_depth', 'Good')}
**Confidence:** {sentiment.get('confidence_indicators', 'Moderate')}
---
"""
        
        return report
    
    def get_experience_level(self, years: str) -> str:
        """Convert years of experience to level category."""
        try:
            years_int = int(years)
            if years_int <= 2:
                return "junior"
            elif years_int <= 5:
                return "mid-level"
            elif years_int <= 10:
                return "senior"
            else:
                return "expert"
        except:
            return "mid-level"
    
    def process_input(self, user_input: str) -> str:
        """Main method to process user input based on current state."""
        user_input = user_input.strip()
        
        # Check for exit commands
        if user_input.lower() in self.exit_keywords:
            return "Thank you for using TechHire AI Interview Assistant! Goodbye! 👋"
        
        if self.current_state == self.GREETING:
            return self.handle_greeting(user_input)
        elif self.current_state == self.COLLECTING_INFO:
            return self.handle_info_collection(user_input)
        elif self.current_state == self.TECHNICAL_QUESTIONS:
            return self.handle_technical_questions(user_input)
        elif self.current_state == self.COMPLETED:
            return "Interview completed! Thank you for your participation. Type 'exit' to end."
        
        return "I'm not sure how to help with that. Please try again."
    
    def handle_greeting(self, user_input: str) -> str:
        """Handle the greeting phase."""
        self.candidate_info["full_name"] = user_input
        self.current_state = self.COLLECTING_INFO
        return f"Nice to meet you, {user_input}! What's your email address?"
    
    def handle_info_collection(self, user_input: str) -> str:
        """Handle information collection phase."""
        field_prompts = {
            "email": "What's your phone number?",
            "phone": "How many years of professional experience do you have?",
            "experience_years": "What positions are you targeting? (e.g., Frontend Developer, Backend Engineer, etc.)",
            "desired_positions": "What's your preferred location or work arrangement?",
            "location": "Please list your technical skills and technologies (comma-separated):"
        }
        
        current_field = list(field_prompts.keys())[self.current_field_index - 1] if self.current_field_index > 0 else "email"
        self.candidate_info[current_field] = user_input
        
        self.current_field_index += 1
        
        if self.current_field_index < len(field_prompts):
            next_field = list(field_prompts.keys())[self.current_field_index - 1]
            return field_prompts[next_field]
        else:
            # Store tech stack and start technical questions
            self.candidate_info["tech_stack"] = user_input
            return self.start_technical_questions()
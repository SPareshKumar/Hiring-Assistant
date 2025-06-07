
# 🧠 Hiring Assistant – AI-Powered Technical Interview Chatbot

Hiring Assistant is an AI-driven, context-aware technical interview chatbot built using Google Gemini Pro. It simulates an intelligent interviewer that dynamically generates personalized, role-specific technical questions based on the candidate’s profile, experience level, and responses.

## 🚀 Project Overview

This project aims to streamline the technical interview process by automating the most time-consuming aspect — generating relevant, thoughtful, and challenging interview questions tailored to each candidate. It conducts adaptive interviews, analyzes responses in real time, and follows up with deeper questions, simulating the expertise of a senior technical interviewer.

### Key Capabilities:
- Collects and validates candidate information interactively.
- Analyzes tech stack and experience to generate a candidate profile.
- Crafts unique, scenario-based questions based on seniority, desired role, and real-world use cases.
- Dynamically adapts follow-up questions using response analysis.
- Stores complete interview session data for review.

## ⚙️ Installation Instructions

### Prerequisites
- Python 3.9+
- A valid Google Gemini API Key
- Virtual Environment (recommended)

### Setup Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SPareshKumar/Hiring-Assistant.git
   cd Hiring-Assistant
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_google_gemini_api_key
   ```

5. **Run the chatbot**:
   ```bash
   python chatbot.py
   ```

## 🧑‍💻 Usage Guide

Once the bot is running, it will:
1. Greet the user and collect key information (name, email, experience, tech stack, etc.).
2. Analyze the candidate's background to determine complexity and role-specific focus.
3. Ask technical questions tailored to your expertise.
4. Analyze your answers in real time, offering follow-up questions or diving deeper as needed.
5. Save the entire session in a structured JSON file for later review.

To exit the session anytime, simply type `exit` or `quit`.

## 🧰 Technical Details

### Core Libraries & Tools:
- `google-generativeai` – Google Gemini Pro integration
- `datetime`, `json`, `re` – standard data handling
- `dotenv` – for managing API keys
- Custom `SentimentAnalyzer` – for response tone analysis (optional module)

### Design & Architecture:
- Modular class-based architecture for clarity and extensibility.
- Finite state machine design to manage chatbot conversation states.
- Response analysis layer to guide dynamic question generation and follow-ups.
- JSON output logger for saving structured candidate data.

## ✍️ Prompt Design Philosophy

Crafting effective prompts was central to this project. Prompts were engineered to:
- Encourage scenario-based, real-world questions (e.g., “How would you scale X…”)
- Adapt question style based on experience: junior (implementation), mid (design), senior (architecture), expert (strategic decisions)
- Emulate human interviewers by using multi-step evaluation logic (e.g., checking tech stack, analyzing prior answers)
- Leverage role-specific focus areas (e.g., DevOps asks CI/CD, Frontend asks about performance, etc.)

Prompts are detailed, contextual, and consistent — ensuring questions feel both personalized and professional.

## ⚔️ Challenges & Solutions

### ❌ Challenge: Personalized, High-Quality Question Generation  
**Problem:** Generating deeply personalized questions that weren’t generic or repetitive was a core challenge.  
**Solution:** Implemented detailed prompt templates that dynamically integrated:  
- Tech stack  
- Experience level  
- Target position  
- Previous answers  
- Skill analysis from prior responses  
This allowed each question to build logically on the last, creating a unique flow per user.

### ❌ Challenge: Maintaining Question Diversity  
**Problem:** Risk of generating similar questions for overlapping tech stacks.  
**Solution:** Tracked technologies already covered and ensured each new question targeted an uncovered skill or angle. Also incorporated fallbacks to handle API failures and improve robustness.

### ❌ Challenge: Ensuring Relevance and Depth  
**Problem:** Sometimes questions were too surface-level.  
**Solution:** Incorporated response quality evaluation and follow-up strategies (e.g., deeper dive, clarification, or edge-case exploration) to maintain depth and nuance.

import google.generativeai as genai
from typing import Dict, List, Tuple
import statistics
import json
from datetime import datetime

class SentimentAnalyzer:
    def __init__(self, gemini_model):
        """Initialize sentiment analyzer with Gemini model."""
        self.model = gemini_model
        
    def analyze_single_response(self, question: str, answer: str) -> Dict:
        """Analyze sentiment of a single response."""
        if answer.lower() == "skipped" or len(answer.strip()) < 5:
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "emotional_tone": "neutral",
                "engagement_level": "low",
                "technical_confidence": "unknown"
            }
        
        try:
            prompt = f"""
            Analyze the sentiment and emotional tone of this technical interview response:
            
            Question: {question}
            Answer: {answer}
            
            Please analyze and provide:
            1. Overall sentiment (positive, negative, neutral)
            2. Confidence level in the answer (high, medium, low)
            3. Emotional tone (confident, uncertain, enthusiastic, nervous, calm, frustrated)
            4. Engagement level (high, medium, low)
            5. Technical confidence shown (high, medium, low, unknown)
            
            Respond in this exact JSON format:
            {{
                "sentiment": "positive/negative/neutral",
                "confidence": 0.8,
                "emotional_tone": "confident/uncertain/enthusiastic/nervous/calm/frustrated",
                "engagement_level": "high/medium/low",
                "technical_confidence": "high/medium/low/unknown",
                "key_indicators": ["specific words or phrases that indicate sentiment"]
            }}
            """
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            
            # Validate and set defaults
            valid_sentiments = ["positive", "negative", "neutral"]
            valid_tones = ["confident", "uncertain", "enthusiastic", "nervous", "calm", "frustrated"]
            valid_levels = ["high", "medium", "low"]
            
            if result.get("sentiment") not in valid_sentiments:
                result["sentiment"] = "neutral"
            if result.get("emotional_tone") not in valid_tones:
                result["emotional_tone"] = "calm"
            if result.get("engagement_level") not in valid_levels:
                result["engagement_level"] = "medium"
            if result.get("technical_confidence") not in valid_levels + ["unknown"]:
                result["technical_confidence"] = "unknown"
            
            return result
            
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            # Return default values
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "emotional_tone": "calm",
                "engagement_level": "medium",
                "technical_confidence": "unknown",
                "key_indicators": []
            }
    
    def analyze_all_responses(self, responses: List[Dict]) -> Dict:
        """Analyze sentiment across all responses and provide summary."""
        if not responses:
            return self._get_empty_analysis()
        
        # Filter out skipped responses
        valid_responses = [r for r in responses if r['answer'].lower() != 'skipped']
        
        if not valid_responses:
            return self._get_empty_analysis()
        
        # Analyze each response
        individual_analyses = []
        for response in valid_responses:
            analysis = self.analyze_single_response(response['question'], response['answer'])
            analysis['question_number'] = response.get('question_number', 0)
            individual_analyses.append(analysis)
        
        # Calculate overall statistics
        overall_analysis = self._calculate_overall_sentiment(individual_analyses)
        overall_analysis['individual_analyses'] = individual_analyses
        overall_analysis['total_responses'] = len(responses)
        overall_analysis['analyzed_responses'] = len(valid_responses)
        overall_analysis['skipped_responses'] = len(responses) - len(valid_responses)
        
        return overall_analysis
    
    def _calculate_overall_sentiment(self, analyses: List[Dict]) -> Dict:
        """Calculate overall sentiment statistics."""
        if not analyses:
            return self._get_empty_analysis()
        
        # Count sentiments
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        confidence_scores = []
        engagement_levels = {"high": 0, "medium": 0, "low": 0}
        technical_confidence_levels = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
        emotional_tones = {}
        
        for analysis in analyses:
            sentiment_counts[analysis['sentiment']] += 1
            confidence_scores.append(analysis['confidence'])
            engagement_levels[analysis['engagement_level']] += 1
            technical_confidence_levels[analysis['technical_confidence']] += 1
            
            tone = analysis['emotional_tone']
            emotional_tones[tone] = emotional_tones.get(tone, 0) + 1
        
        # Calculate percentages
        total = len(analyses)
        sentiment_percentages = {k: (v/total)*100 for k, v in sentiment_counts.items()}
        
        # Determine dominant patterns
        dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get)
        dominant_engagement = max(engagement_levels, key=engagement_levels.get)
        dominant_tone = max(emotional_tones, key=emotional_tones.get) if emotional_tones else "calm"
        
        # Calculate average confidence
        avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.5
        
        # Generate insights
        insights = self._generate_insights(
            dominant_sentiment, dominant_tone, dominant_engagement, 
            avg_confidence, sentiment_percentages
        )
        
        return {
            "overall_sentiment": dominant_sentiment,
            "sentiment_distribution": sentiment_percentages,
            "average_confidence": round(avg_confidence, 2),
            "dominant_emotional_tone": dominant_tone,
            "dominant_engagement_level": dominant_engagement,
            "emotional_tone_distribution": emotional_tones,
            "technical_confidence_distribution": technical_confidence_levels,
            "insights": insights,
            "confidence_trend": self._analyze_confidence_trend(analyses)
        }
    
    def _analyze_confidence_trend(self, analyses: List[Dict]) -> str:
        """Analyze if confidence increased or decreased over time."""
        if len(analyses) < 2:
            return "insufficient_data"
        
        # Sort by question number
        sorted_analyses = sorted(analyses, key=lambda x: x.get('question_number', 0))
        confidences = [a['confidence'] for a in sorted_analyses]
        
        # Simple trend analysis
        first_half = confidences[:len(confidences)//2]
        second_half = confidences[len(confidences)//2:]
        
        if not first_half or not second_half:
            return "stable"
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        if second_avg > first_avg + 0.1:
            return "increasing"
        elif second_avg < first_avg - 0.1:
            return "decreasing"
        else:
            return "stable"
    
    def _generate_insights(self, sentiment: str, tone: str, engagement: str, 
                          confidence: float, sentiment_dist: Dict) -> List[str]:
        """Generate human-readable insights."""
        insights = []
        
        # Sentiment insights
        if sentiment == "positive":
            insights.append("😊 The candidate showed a positive attitude throughout the interview")
        elif sentiment == "negative":
            insights.append("😟 The candidate showed some signs of stress or negativity")
        else:
            insights.append("😐 The candidate maintained a neutral tone throughout")
        
        # Confidence insights
        if confidence >= 0.8:
            insights.append("💪 High confidence level demonstrated in technical responses")
        elif confidence >= 0.6:
            insights.append("👍 Moderate confidence shown in answering questions")
        else:
            insights.append("🤔 Lower confidence levels - might need more support or different question approach")
        
        # Engagement insights
        if engagement == "high":
            insights.append("🚀 High engagement level - candidate was actively participating")
        elif engagement == "low":
            insights.append("📉 Lower engagement detected - candidate might have been disinterested or overwhelmed")
        
        # Emotional tone insights
        tone_insights = {
            "confident": "💼 Candidate displayed strong self-assurance",
            "enthusiastic": "⭐ Great enthusiasm and passion for technology",
            "nervous": "😰 Some nervousness detected - normal for interview situations",
            "frustrated": "😤 Signs of frustration - questions might have been too challenging",
            "uncertain": "❓ Some uncertainty in responses - might need clearer questions",
            "calm": "😌 Maintained calm and composed throughout"
        }
        
        if tone in tone_insights:
            insights.append(tone_insights[tone])
        
        return insights
    
    def _get_empty_analysis(self) -> Dict:
        """Return empty analysis for when no valid responses exist."""
        return {
            "overall_sentiment": "neutral",
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 100},
            "average_confidence": 0.0,
            "dominant_emotional_tone": "neutral",
            "dominant_engagement_level": "low",
            "emotional_tone_distribution": {},
            "technical_confidence_distribution": {"unknown": 1},
            "insights": ["No valid responses to analyze"],
            "confidence_trend": "no_data",
            "individual_analyses": [],
            "total_responses": 0,
            "analyzed_responses": 0,
            "skipped_responses": 0
        }
    
    def format_sentiment_report(self, analysis: Dict, candidate_name: str = "") -> str:
        """Format sentiment analysis into a readable report."""
        if not analysis or analysis.get('analyzed_responses', 0) == 0:
            return """
### 📊 Sentiment Analysis Report
No responses available for sentiment analysis.
"""
        
        report = f"""
### 📊 Sentiment Analysis Report {f"for {candidate_name}" if candidate_name else ""}

#### Overall Assessment
- **Primary Sentiment:** {analysis['overall_sentiment'].title()} 
- **Confidence Level:** {analysis['average_confidence']*100:.1f}%
- **Emotional Tone:** {analysis['dominant_emotional_tone'].title()}
- **Engagement Level:** {analysis['dominant_engagement_level'].title()}

#### Response Statistics
- **Total Questions:** {analysis['total_responses']}
- **Responses Analyzed:** {analysis['analyzed_responses']}
- **Questions Skipped:** {analysis['skipped_responses']}

#### Sentiment Distribution
- **Positive Responses:** {analysis['sentiment_distribution']['positive']:.1f}%
- **Neutral Responses:** {analysis['sentiment_distribution']['neutral']:.1f}%
- **Negative Responses:** {analysis['sentiment_distribution']['negative']:.1f}%

#### Key Insights
"""
        
        for insight in analysis['insights']:
            report += f"- {insight}\n"
        
        # Confidence trend
        trend_messages = {
            "increasing": "📈 Confidence improved throughout the interview",
            "decreasing": "📉 Confidence declined during the interview", 
            "stable": "➡️ Confidence remained consistent throughout",
            "insufficient_data": "📊 Not enough data to determine confidence trend",
            "no_data": "❌ No confidence trend data available"
        }
        
        trend = analysis.get('confidence_trend', 'no_data')
        if trend in trend_messages:
            report += f"\n#### Confidence Trend\n- {trend_messages[trend]}\n"
        
        return report
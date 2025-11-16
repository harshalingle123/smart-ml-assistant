from typing import List, Dict, Optional, Any
import google.generativeai as genai
from app.core.config import settings
import json


class GeminiService:
    def __init__(self):
        self.model = None
        if settings.GOOGLE_GEMINI_API_KEY:
            genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    def is_available(self) -> bool:
        return self.model is not None

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> str:
        if not self.is_available():
            raise ValueError("Gemini API is not configured. Please set GOOGLE_GEMINI_API_KEY in environment variables.")

        if system_prompt is None:
            system_prompt = """You are AutoML, an AI specialized in machine learning,
data analysis, and sentiment analysis. You help users with:

- Text classification and sentiment analysis
- Data preprocessing and analysis
- Model recommendations and fine-tuning guidance
- Explaining ML concepts clearly
- Providing code examples when helpful

Be concise, helpful, and technical when appropriate. If users upload datasets,
analyze the data and provide insights. Suggest fine-tuning when the dataset shows
unique patterns that could benefit from custom model training."""

        try:
            chat_history = []

            for msg in messages[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({
                    "role": role,
                    "parts": [msg["content"]]
                })

            chat = self.model.start_chat(history=chat_history)

            user_message = messages[-1]["content"]
            full_prompt = f"{system_prompt}\n\nUser: {user_message}"

            response = chat.send_message(full_prompt)

            return response.text

        except Exception as e:
            raise Exception(f"Error calling Gemini API: {str(e)}")

    async def analyze_dataset_query(self, user_message: str) -> Dict[str, any]:
        user_lower = user_message.lower()

        dataset_search_keywords = [
            "find dataset", "search dataset", "get dataset", "need dataset",
            "dataset for", "download dataset", "kaggle dataset", "looking for dataset",
            "want dataset", "show me dataset", "suggest dataset"
        ]

        data_analysis_keywords = [
            "analyze", "distribution", "correlation", "statistics",
            "visualize", "plot", "chart"
        ]

        needs_dataset_search = any(keyword in user_lower for keyword in dataset_search_keywords)

        is_data_analysis = any(keyword in user_lower for keyword in data_analysis_keywords)

        result = {
            "query_type": "dataset_search" if needs_dataset_search else ("data_analysis" if is_data_analysis else "simple"),
            "task_type": "other",
            "needs_kaggle_search": needs_dataset_search,
            "search_query": ""
        }

        if "sentiment" in user_lower:
            result["task_type"] = "sentiment_analysis"
            if needs_dataset_search:
                result["search_query"] = "sentiment analysis"
        elif "classif" in user_lower:
            result["task_type"] = "text_classification"
            if needs_dataset_search:
                result["search_query"] = "text classification"
        elif "nlp" in user_lower or "natural language" in user_lower:
            result["task_type"] = "nlp"
            if needs_dataset_search:
                result["search_query"] = "nlp"
        elif "image" in user_lower or "computer vision" in user_lower:
            result["task_type"] = "computer_vision"
            if needs_dataset_search:
                result["search_query"] = "image classification"
        elif "time series" in user_lower:
            result["task_type"] = "time_series"
            if needs_dataset_search:
                result["search_query"] = "time series"
        elif needs_dataset_search:
            words = user_lower.split()
            if "for" in words:
                idx = words.index("for")
                result["search_query"] = " ".join(words[idx+1:idx+4])
            elif "about" in words:
                idx = words.index("about")
                result["search_query"] = " ".join(words[idx+1:idx+4])
            else:
                result["search_query"] = user_message[:50]

        return result

    async def extract_intent_from_natural_language(self, user_query: str) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("Gemini API is not configured")

        prompt = f"""Analyze this user query and extract the ML intent as structured data:

Query: "{user_query}"

Extract and return ONLY a JSON object with these fields:
{{
    "task_type": "text_classification|sentiment_analysis|object_detection|regression|clustering",
    "domain": "e-commerce|healthcare|finance|customer_support|general",
    "input_type": "text|image|audio|tabular",
    "output_type": "binary|multi_class|continuous|bbox",
    "constraints": {{
        "max_latency_ms": number or null,
        "min_accuracy": number or null,
        "budget_usd": number or null,
        "max_model_size_mb": number or null
    }},
    "business_context": "brief description of what user wants to achieve",
    "urgency_level": "low|medium|high|critical"
}}

Return only valid JSON, no explanations."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            return json.loads(text)
        except Exception as e:
            return {
                "task_type": "unknown",
                "domain": "general",
                "input_type": "text",
                "output_type": "multi_class",
                "constraints": {},
                "business_context": user_query[:200],
                "urgency_level": "medium"
            }

    async def structure_requirements(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("Gemini API is not configured")

        prompt = f"""Given this ML intent, structure it into technical requirements:

Intent: {json.dumps(intent, indent=2)}

Return ONLY a JSON object with:
{{
    "dataset_requirements": {{
        "min_samples": number,
        "required_columns": ["column names"],
        "data_quality_threshold": number between 0-1
    }},
    "model_recommendations": [
        {{
            "model_name": "model name",
            "reason": "why this model",
            "estimated_accuracy": number,
            "estimated_cost_usd": number,
            "estimated_training_hours": number
        }}
    ],
    "preprocessing_steps": ["step1", "step2"],
    "evaluation_metrics": ["metric1", "metric2"],
    "deployment_strategy": "serverless|container|edge"
}}

Return only valid JSON."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            return json.loads(text)
        except Exception:
            return {
                "dataset_requirements": {
                    "min_samples": 1000,
                    "required_columns": ["text", "label"],
                    "data_quality_threshold": 0.8
                },
                "model_recommendations": [],
                "preprocessing_steps": ["clean_text", "tokenize", "remove_stopwords"],
                "evaluation_metrics": ["accuracy", "f1_score"],
                "deployment_strategy": "serverless"
            }

    async def generate_clarifying_questions(self, requirements: Dict[str, Any]) -> List[str]:
        if not self.is_available():
            raise ValueError("Gemini API is not configured")

        prompt = f"""Based on these requirements, generate 2-4 clarifying questions:

Requirements: {json.dumps(requirements, indent=2)}

Generate questions to clarify:
- Data availability
- Performance priorities
- Budget constraints
- Use case specifics

Return as JSON array of strings: ["question1", "question2", ...]

Return only valid JSON array."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            questions = json.loads(text)
            return questions if isinstance(questions, list) else []
        except Exception:
            return [
                "Do you have an existing dataset or need help finding one?",
                "What is your priority: speed, accuracy, or cost?",
                "What is your approximate budget for this project?",
                "What is your expected prediction volume per day?"
            ]

    async def explain_technical_decision_business_friendly(self, decision: Dict[str, Any]) -> str:
        if not self.is_available():
            raise ValueError("Gemini API is not configured")

        prompt = f"""Explain this technical ML decision in business-friendly language:

Decision: {json.dumps(decision, indent=2)}

Provide a clear, non-technical explanation that:
- Explains the choice in simple terms
- Highlights business benefits
- Mentions any tradeoffs
- Keeps it under 100 words

Return plain text explanation, no formatting."""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            return "We've selected an optimal model based on your requirements, balancing performance, cost, and speed."

    async def generate_progress_update(self, training_job: Dict[str, Any], phase: str) -> str:
        if not self.is_available():
            raise ValueError("Gemini API is not configured")

        prompt = f"""Generate a friendly progress update for this training job:

Job: {json.dumps(training_job, indent=2)}
Current Phase: {phase}

Provide a brief, encouraging update (2-3 sentences) that:
- States current status
- Estimates remaining time if applicable
- Mentions what's next

Return plain text, conversational tone."""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            status_messages = {
                "preparing": "Getting your training environment ready. This usually takes a few minutes.",
                "training": "Training is in progress. Your model is learning from the data.",
                "evaluating": "Evaluating model performance on test data. Almost there!",
                "deploying": "Deploying your model to production. Final steps in progress.",
                "completed": "Training completed successfully! Your model is ready to use."
            }
            return status_messages.get(phase, "Processing your request...")


gemini_service = GeminiService()

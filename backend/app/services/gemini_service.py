import asyncio
import json
import logging
from typing import List, Dict, Optional, Any, Union

import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)

DEFAULT_MODELS = [
    settings.GEMINI_MODEL,
    "gemini-1.5-flash",
    "gemini-pro",
]

class GeminiService:
    """
    Service for interacting with Google's Gemini API.
    Handles model initialization, chat generation, and various ML-assistant tasks.
    """

    def __init__(self) -> None:
        """Initialize the GeminiService and load the model."""
        self.model: Optional[genai.GenerativeModel] = self._load_model()

    def _load_model(self) -> Optional[genai.GenerativeModel]:
        """
        Attempt to load a Gemini model from the fallback list.
        
        Returns:
            genai.GenerativeModel or None if initialization fails.
        """
        if not settings.GOOGLE_GEMINI_API_KEY:
            logger.warning("GOOGLE_GEMINI_API_KEY not set. Gemini service will be unavailable.")
            return None

        try:
            genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
            return None

        for model_name in DEFAULT_MODELS:
            if not model_name:
                continue
            try:
                logger.info(f"Attempting to load Gemini model: {model_name}")
                model = genai.GenerativeModel(model_name)
                # Test the model with a lightweight call or just assume it works if no error
                logger.info(f"Successfully loaded {model_name}")
                return model
            except Exception as e:
                logger.warning(f"Failed to load {model_name}: {e}")

        logger.error("All fallback models failed. Gemini service is unavailable.")
        return None

    def is_available(self) -> bool:
        """Check if the Gemini model is successfully loaded."""
        return self.model is not None

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a response from the Gemini model based on chat history.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            system_prompt: Optional system prompt to guide the model's behavior.

        Returns:
            The generated response string.

        Raises:
            ValueError: If the API is not configured.
            Exception: If an API error occurs (quota, rate limit, etc.).
        """
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

            user_message = messages[-1]["content"]
            full_prompt = f"{system_prompt}\n\nUser: {user_message}"

            # Run blocking I/O in a separate thread
            response = await asyncio.to_thread(
                self._run_chat, chat_history, full_prompt
            )
            return response

        except Exception as e:
            error_str = str(e).lower()
            is_quota_error = any(keyword in error_str for keyword in [
                'quota', 'rate limit', 'resource exhausted', '429',
                'exceeded', 'billing', 'free tier', 'api key', 'leaked',
                '403', 'forbidden', 'invalid api key', 'unauthorized'
            ])

            if is_quota_error:
                logger.error(f"Gemini Quota/Auth Error: {e}")
                raise Exception("We're experiencing high demand at the moment. For assistance, please contact us at info@darshix.com")
            else:
                logger.error(f"Gemini General Error: {e}")
                raise Exception("We're experiencing technical difficulties. Please try again or contact us at info@darshix.com for support.")

    def _run_chat(self, history: List[Dict[str, Any]], prompt: str) -> str:
        """Helper to run chat generation synchronously."""
        if not self.model:
            raise ValueError("Model not initialized")
        chat = self.model.start_chat(history=history)
        response = chat.send_message(prompt)
        return response.text

    async def analyze_dataset_query(self, user_message: str) -> Dict[str, Any]:
        """
        Analyze a user's query using LLM to determine query type and intent.

        Args:
            user_message: The raw user message.

        Returns:
            A dictionary containing query type, task type, and search parameters.
        """
        if not self.is_available():
            return self._fallback_query_analysis(user_message)

        prompt = f"""Analyze this user query and classify it into categories.

Query: "{user_message}"

Return ONLY a JSON object with these exact fields:
{{
    "query_type": "dataset_search|data_analysis|simple",
    "task_type": "sentiment_analysis|text_classification|nlp|computer_vision|time_series|regression|clustering|other",
    "needs_kaggle_search": true|false,
    "search_query": "optimized search query for dataset search (empty string if not dataset search)",
    "intent_summary": "brief summary of what the user wants to accomplish"
}}

Classification guidelines:
- query_type is "dataset_search" if user wants to find/download/search for datasets
- query_type is "data_analysis" if user wants to analyze, visualize, or get statistics
- query_type is "simple" for general questions or conversations
- needs_kaggle_search should be true only if query_type is "dataset_search"
- search_query should be optimized keywords for finding relevant datasets
- task_type should identify the ML task domain

Return only valid JSON, no markdown."""

        try:
            response_text = await asyncio.to_thread(self._generate_content_sync, prompt)
            result = self._parse_json(response_text)

            logger.info(f"LLM query analysis: {result.get('query_type')} - {result.get('task_type')}")

            return {
                "query_type": result.get("query_type", "simple"),
                "task_type": result.get("task_type", "other"),
                "needs_kaggle_search": result.get("needs_kaggle_search", False),
                "search_query": result.get("search_query", ""),
                "intent_summary": result.get("intent_summary", user_message[:100])
            }

        except Exception as e:
            logger.warning(f"LLM query analysis failed: {e}, falling back to keyword matching")
            return self._fallback_query_analysis(user_message)

    def _fallback_query_analysis(self, user_message: str) -> Dict[str, Any]:
        """
        Fallback keyword-based query analysis when LLM is unavailable.

        Args:
            user_message: The raw user message.

        Returns:
            A dictionary containing query type, task type, and search parameters.
        """
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
            "search_query": "",
            "intent_summary": user_message[:100]
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
                try:
                    idx = words.index("for")
                    result["search_query"] = " ".join(words[idx+1:idx+4])
                except IndexError:
                    result["search_query"] = user_message[:50]
            elif "about" in words:
                try:
                    idx = words.index("about")
                    result["search_query"] = " ".join(words[idx+1:idx+4])
                except IndexError:
                    result["search_query"] = user_message[:50]
            else:
                result["search_query"] = user_message[:50]

        return result

    async def extract_intent_from_natural_language(self, user_query: str) -> Dict[str, Any]:
        """
        Use LLM to extract structured ML intent from a natural language query.
        """
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
            response_text = await asyncio.to_thread(self._generate_content_sync, prompt)
            return self._parse_json(response_text)
        except Exception as e:
            logger.error(f"Error extracting intent: {e}")
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
        """
        Generate technical requirements based on the extracted intent.
        """
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
            response_text = await asyncio.to_thread(self._generate_content_sync, prompt)
            return self._parse_json(response_text)
        except Exception as e:
            logger.error(f"Error structuring requirements: {e}")
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
        """
        Generate questions to clarify missing or ambiguous requirements.
        """
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
            response_text = await asyncio.to_thread(self._generate_content_sync, prompt)
            questions = self._parse_json(response_text)
            return questions if isinstance(questions, list) else []
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return [
                "Do you have an existing dataset or need help finding one?",
                "What is your priority: speed, accuracy, or cost?",
                "What is your approximate budget for this project?",
                "What is your expected prediction volume per day?"
            ]

    async def explain_technical_decision_business_friendly(self, decision: Dict[str, Any]) -> str:
        """
        Explain a technical decision in simple, business-friendly terms.
        """
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
            return await asyncio.to_thread(self._generate_content_sync, prompt)
        except Exception as e:
            logger.error(f"Error explaining decision: {e}")
            return "We've selected an optimal model based on your requirements, balancing performance, cost, and speed."

    async def generate_progress_update(self, training_job: Dict[str, Any], phase: str) -> str:
        """
        Generate a friendly progress update message.
        """
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
            return await asyncio.to_thread(self._generate_content_sync, prompt)
        except Exception as e:
            logger.error(f"Error generating progress update: {e}")
            status_messages = {
                "preparing": "Getting your training environment ready. This usually takes a few minutes.",
                "training": "Training is in progress. Your model is learning from the data.",
                "evaluating": "Evaluating model performance on test data. Almost there!",
                "deploying": "Deploying your model to production. Final steps in progress.",
                "completed": "Training completed successfully! Your model is ready to use."
            }
            return status_messages.get(phase, "Processing your request...")

    async def extract_spec(self, user_query: str) -> Dict[str, Any]:
        """
        Uses Gemini to fix typos and extract search keywords for dataset search.
        """
        if not self.is_available():
            return {"fixed_query": user_query, "keywords": [user_query]}

        logger.info(f"Analyzing query: '{user_query}'...")
        
        # Use a specific model for extraction if possible, or fallback to main model
        # The original code used 'gemini-2.5-flash', which might be a typo or specific version.
        # We'll try to use the configured model or a lightweight one.
        
        prompt = f"""
        Act as a search query optimizer for a dataset recommendation engine.

        Task:
        1. Analyze the User Query: "{user_query}"
        2. Fix any spelling mistakes (e.g., "dibetes" -> "diabetes", "santiment" -> "sentiment", "analussi" -> "analysis").

        Return ONLY valid JSON with no markdown formatting:
        {{
            "fixed_query": "corrected query string",
            "keywords": ["keyword1", "keyword2", "keyword3"]
        }}
        """

        try:
            # We use the main model here to avoid instantiating a new one every time
            # unless we really need a specific one. 
            response_text = await asyncio.to_thread(self._generate_content_sync, prompt)
            result = self._parse_json(response_text)
            logger.info(f"✓ Fixed query: '{result.get('fixed_query', user_query)}'")
            logger.info(f"✓ Keywords: {result.get('keywords', [])}")
            return result

        except Exception as e:
            logger.warning(f"Gemini Extraction Warning: {e}")
            return {"fixed_query": user_query, "keywords": [user_query]}

    async def rank_candidates(
        self,
        query: str,
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Ranks datasets using Gemini Embeddings and Cosine Similarity.
        """
        if not candidates:
            return []

        if not self.is_available():
            logger.warning("Gemini not available, returning unranked candidates")
            return candidates

        logger.info("Ranking candidates using embeddings...")
        try:
            return await asyncio.to_thread(self._rank_candidates_sync, query, candidates)
        except Exception as e:
            logger.error(f"Ranking failed: {e}")
            return candidates

    def _rank_candidates_sync(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Synchronous helper for ranking."""
        # 1. Embed Query
        query_emb = genai.embed_content(
            model="models/text-embedding-004",
            content=query,
            task_type="retrieval_query"
        )['embedding']

        # 2. Embed Candidates
        texts = [f"{c.get('title', '')}: {str(c.get('description', ''))[:500]}" for c in candidates]

        batch_emb = genai.embed_content(
            model="models/text-embedding-004",
            content=texts,
            task_type="retrieval_document"
        )['embedding']

        # 3. Compute Similarity
        scores = cosine_similarity([query_emb], batch_emb)[0]

        for idx, score in enumerate(scores):
            candidates[idx]['score'] = float(score)

        # Sort descending
        return sorted(candidates, key=lambda x: x.get('score', 0), reverse=True)

    async def rank_datasets_by_relevance(
        self,
        query: str,
        datasets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Backward compatibility wrapper for rank_candidates().
        Maps 'relevance_score' to 'score' for existing code.
        """
        ranked = await self.rank_candidates(query, datasets)
        for ds in ranked:
            if 'score' in ds:
                ds['relevance_score'] = ds['score']
        return ranked

    def _generate_content_sync(self, prompt: str) -> str:
        """Helper to generate content synchronously."""
        if not self.model:
            raise ValueError("Model not initialized")
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def _parse_json(self, text: str) -> Any:
        """Helper to clean and parse JSON from LLM response."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())

# Global instance for backward compatibility
gemini_service = GeminiService()

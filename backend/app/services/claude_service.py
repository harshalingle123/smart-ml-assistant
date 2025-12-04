from typing import List, Dict, Optional
from anthropic import Anthropic
from app.core.config import settings


class ClaudeService:
    """Service for interacting with Claude AI API"""

    def __init__(self):
        self.client = None
        if settings.ANTHROPIC_API_KEY:
            try:
                self.client = Anthropic(
                    api_key=settings.ANTHROPIC_API_KEY,
                    max_retries=2,
                    timeout=60.0
                )
            except TypeError as e:
                if "proxies" in str(e):
                    print(f"Warning: Anthropic client initialization failed with 'proxies' error. Trying basic initialization.")
                    try:
                        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                    except Exception as e2:
                        print(f"Warning: Failed to initialize Claude client: {e2}")
                        self.client = None
                else:
                    print(f"Warning: Failed to initialize Claude client: {e}")
                    self.client = None
            except Exception as e:
                print(f"Warning: Failed to initialize Claude client: {e}")
                self.client = None

    def is_available(self) -> bool:
        """Check if Claude API is configured and available"""
        return self.client is not None

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a response from Claude based on conversation history

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt to guide Claude's behavior
            max_tokens: Maximum tokens in response (defaults to settings)

        Returns:
            Claude's response as a string
        """
        if not self.is_available():
            raise ValueError("Claude API is not configured. Please set ANTHROPIC_API_KEY in environment variables.")

        # Default system prompt for ML assistant
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
            response = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=max_tokens or settings.CLAUDE_MAX_TOKENS,
                system=system_prompt,
                messages=messages
            )

            # Extract text content from response
            if response.content and len(response.content) > 0:
                return response.content[0].text

            return "I apologize, but I couldn't generate a response. Please try again."

        except Exception as e:
            raise Exception(f"Error calling Claude API: {str(e)}")

    async def analyze_dataset_query(self, user_message: str) -> Dict[str, any]:
        """
        Analyze a user's query using LLM to determine query type and intent.

        Args:
            user_message: The raw user message.

        Returns:
            A dictionary containing query type, task type, and search parameters.
        """
        if not self.is_available():
            return self._fallback_query_analysis(user_message)

        analysis_prompt = f"""Analyze this user query and classify it into categories.

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
- query_type is "dataset_search" if user wants to find/download/search for datasets OR if they're asking about building/training ML models (which typically need datasets)
- query_type is "data_analysis" if user wants to analyze, visualize, or get statistics on existing data
- query_type is "simple" for general questions or conversations
- needs_kaggle_search should be true if query_type is "dataset_search" (including ML task queries that would benefit from datasets)
- search_query should be optimized keywords for finding relevant datasets (e.g., "sentiment analysis", "customer support tickets classification", etc.)
- task_type should identify the ML task domain

Important: If user mentions ML tasks like "classify", "train", "predict", "build model", etc., treat it as a dataset_search query because they likely need datasets for training.

Return only valid JSON, no markdown."""

        try:
            response = await self.generate_response(
                messages=[{"role": "user", "content": analysis_prompt}],
                system_prompt="You are a query classifier that analyzes ML and data science queries.",
                max_tokens=300
            )

            import json
            result = json.loads(response.strip().strip('```json').strip('```').strip())

            return {
                "query_type": result.get("query_type", "simple"),
                "task_type": result.get("task_type", "other"),
                "needs_kaggle_search": result.get("needs_kaggle_search", False),
                "search_query": result.get("search_query", ""),
                "intent_summary": result.get("intent_summary", user_message[:100])
            }

        except Exception as e:
            print(f"LLM query analysis failed: {e}, falling back to keyword matching")
            return self._fallback_query_analysis(user_message)

    def _fallback_query_analysis(self, user_message: str) -> Dict[str, any]:
        """
        Fallback keyword-based query analysis when LLM is unavailable.

        Args:
            user_message: The raw user message.

        Returns:
            A dictionary containing query type, task type, and search parameters.
        """
        user_lower = user_message.lower()

        # Explicit dataset search keywords
        dataset_search_keywords = [
            "find dataset", "search dataset", "get dataset", "need dataset",
            "dataset for", "download dataset", "kaggle dataset", "looking for dataset",
            "want dataset", "show me dataset", "suggest dataset"
        ]

        # ML task keywords that typically need datasets
        ml_task_keywords = [
            "classify", "classification", "train", "model", "predict", "prediction",
            "build model", "create model", "fine-tune", "finetune", "train a model",
            "ml for", "machine learning for", "sentiment analysis", "text classification",
            "image classification", "object detection", "regression", "clustering"
        ]

        data_analysis_keywords = [
            "analyze", "distribution", "correlation", "statistics",
            "visualize", "plot", "chart"
        ]

        # Check for both explicit dataset requests AND ML task queries
        has_explicit_dataset_request = any(keyword in user_lower for keyword in dataset_search_keywords)
        has_ml_task = any(keyword in user_lower for keyword in ml_task_keywords)
        is_data_analysis = any(keyword in user_lower for keyword in data_analysis_keywords)

        # Treat both explicit dataset requests AND ML task queries as dataset searches
        needs_dataset_search = has_explicit_dataset_request or has_ml_task

        result = {
            "query_type": "dataset_search" if needs_dataset_search else ("data_analysis" if is_data_analysis else "simple"),
            "task_type": "other",
            "needs_kaggle_search": needs_dataset_search,
            "search_query": "",
            "intent_summary": user_message[:100]
        }

        # Generate search query based on detected task type
        if "sentiment" in user_lower:
            result["task_type"] = "sentiment_analysis"
            result["search_query"] = "sentiment analysis"
        elif "classif" in user_lower:
            result["task_type"] = "text_classification"
            # Extract context for better search (e.g., "customer support tickets")
            if "support" in user_lower or "ticket" in user_lower:
                result["search_query"] = "customer support tickets classification"
            elif "customer" in user_lower:
                result["search_query"] = "customer text classification"
            else:
                result["search_query"] = "text classification"
        elif "nlp" in user_lower or "natural language" in user_lower:
            result["task_type"] = "nlp"
            result["search_query"] = "nlp"
        elif "image" in user_lower or "computer vision" in user_lower:
            result["task_type"] = "computer_vision"
            result["search_query"] = "image classification"
        elif "time series" in user_lower:
            result["task_type"] = "time_series"
            result["search_query"] = "time series"
        elif needs_dataset_search:
            # Extract search query from context
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
                # Use the full query as search term
                result["search_query"] = user_message[:50]

        return result


# Singleton instance
claude_service = ClaudeService()

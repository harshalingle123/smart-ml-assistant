from typing import List, Dict, Optional
from anthropic import Anthropic
from app.core.config import settings


class ClaudeService:
    """Service for interacting with Claude AI API"""

    def __init__(self):
        self.client = None
        if settings.ANTHROPIC_API_KEY:
            try:
                self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
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
            system_prompt = """You are Smart ML Assistant, an AI specialized in machine learning,
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
        Analyze if a user query involves dataset analysis

        Returns:
            Dict with query_type and suggestions
        """
        analysis_prompt = f"""Analyze this user message and determine:
1. Is this a simple query or does it involve dataset analysis?
2. What kind of ML task is this (sentiment analysis, classification, etc.)?

User message: {user_message}

Respond in this exact format:
query_type: [simple/data_based]
task_type: [sentiment_analysis/text_classification/other]
requires_fine_tuning: [yes/no]"""

        try:
            response = await self.generate_response(
                messages=[{"role": "user", "content": analysis_prompt}],
                system_prompt="You are a classifier that analyzes ML queries.",
                max_tokens=200
            )

            # Parse the response
            lines = response.strip().split('\n')
            result = {
                "query_type": "simple",
                "task_type": "other",
                "requires_fine_tuning": False
            }

            for line in lines:
                if "query_type:" in line.lower():
                    result["query_type"] = "data_based" if "data_based" in line.lower() else "simple"
                elif "task_type:" in line.lower():
                    if "sentiment" in line.lower():
                        result["task_type"] = "sentiment_analysis"
                    elif "classification" in line.lower():
                        result["task_type"] = "text_classification"
                elif "requires_fine_tuning:" in line.lower():
                    result["requires_fine_tuning"] = "yes" in line.lower()

            return result

        except Exception as e:
            # Fallback to simple heuristics
            user_lower = user_message.lower()
            is_data_based = any(word in user_lower for word in ["dataset", "csv", "analyze", "data", "file"])

            return {
                "query_type": "data_based" if is_data_based else "simple",
                "task_type": "sentiment_analysis" if "sentiment" in user_lower else "other",
                "requires_fine_tuning": is_data_based
            }


# Singleton instance
claude_service = ClaudeService()

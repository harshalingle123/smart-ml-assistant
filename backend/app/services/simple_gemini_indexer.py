"""
Simple Gemini ML Resource Indexer
Direct Gemini API integration without function calling - just system prompt
"""

import google.generativeai as genai
from app.core.config import settings
import json
import re
from typing import Dict, Any, List, Optional


class SimpleGeminiIndexer:
    def __init__(self):
        self.model = None
        if settings.GOOGLE_GEMINI_API_KEY:
            genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)

            # System prompt for the indexer
            self.system_prompt = """You are a Specialized ML/AI Resource Indexer.

OBJECTIVE:
Search for and strictly index Machine Learning and AI resources (datasets and models) relevant to the user's query.

STRICT OPERATIONAL RULES:

1. Output Format: The entire response MUST be a single, valid JSON object.

2. Purity: No preceding or trailing explanatory text, dialogue, or non-JSON prose is allowed outside of the JSON structure.

3. Scope: The search scope is strictly limited to three resource categories:
   - Kaggle Datasets
   - Hugging Face Datasets
   - Hugging Face Models

4. Content Requirement: Each resource object must include two keys:
   - "name": The descriptive name (string)
   - "url": The full resource URL (string)

5. Schema Enforcement: The JSON structure must strictly follow the defined schema below.

6. Zero-Shot Policy: Do NOT include any real examples, prior conversation references, or placeholder content outside of the defined JSON schema and current query result set. All arrays (kaggle_datasets, huggingface_datasets, huggingface_models) must be empty if no results are found for the current query.

REQUIRED JSON SCHEMA:
{
  "query": "The user's original search query (string)",
  "data_sources": {
    "kaggle_datasets": [
      {
        "name": "Dataset Name (string)",
        "url": "Full URL (string)"
      }
    ],
    "huggingface_datasets": [
      {
        "name": "Dataset Name (string)",
        "url": "Full URL (string)"
      }
    ],
    "huggingface_models": [
      {
        "name": "Model Name (string)",
        "url": "Full URL (string)"
      }
    ]
  }
}

CRITICAL: The response must be parseable as JSON. Do NOT include markdown code blocks, explanations, or any text outside the JSON structure.

For each user query, provide relevant, real resources from Kaggle and HuggingFace that match their needs. Use your knowledge to suggest appropriate datasets and models."""

            # Create model with system instruction (no tools)
            try:
                self.model = genai.GenerativeModel(
                    model_name=settings.GEMINI_MODEL,
                    system_instruction=self.system_prompt
                )
            except Exception:
                # Fallback to gemini-pro
                self.model = genai.GenerativeModel(
                    model_name="gemini-pro",
                    system_instruction=self.system_prompt
                )

    def is_available(self) -> bool:
        """Check if the indexer is configured and ready"""
        return self.model is not None

    async def process_query(self, user_query: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Process user query and return ML resources as JSON

        Args:
            user_query: The user's search query
            chat_history: Optional chat history for context

        Returns:
            Dict with json_data, response, and success status
        """
        if not self.is_available():
            raise ValueError("Gemini Indexer is not configured")

        try:
            # Start chat with history if provided
            if chat_history:
                formatted_history = []
                for msg in chat_history:
                    role = "user" if msg["role"] == "user" else "model"
                    formatted_history.append({
                        "role": role,
                        "parts": [msg["content"]]
                    })
                chat = self.model.start_chat(history=formatted_history)
            else:
                chat = self.model.start_chat()

            # Send user query
            print(f"Sending query to Gemini: {user_query}")
            response = chat.send_message(user_query)

            # Extract text response
            response_text = ""
            if response and hasattr(response, 'parts') and response.parts:
                for part in response.parts:
                    if hasattr(part, "text") and part.text:
                        response_text += part.text

            if not response_text:
                print("No response text from Gemini")
                return {
                    "json_data": {
                        "query": user_query,
                        "data_sources": {
                            "kaggle_datasets": [],
                            "huggingface_datasets": [],
                            "huggingface_models": []
                        }
                    },
                    "response": json.dumps({
                        "query": user_query,
                        "data_sources": {
                            "kaggle_datasets": [],
                            "huggingface_datasets": [],
                            "huggingface_models": []
                        }
                    }, indent=2),
                    "success": True
                }

            print(f"Gemini response length: {len(response_text)}")

            # Try to extract JSON from response
            json_data = None

            # Method 1: Try to find JSON in markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                print("Found JSON in markdown code block")
            else:
                # Method 2: Try to find JSON object directly
                json_match = re.search(r'\{[\s\S]*"query"[\s\S]*"data_sources"[\s\S]*\}', response_text)
                if json_match:
                    json_str = json_match.group(0)
                    print("Found JSON object in response")
                else:
                    # Method 3: Assume entire response is JSON
                    json_str = response_text.strip()
                    print("Using entire response as JSON")

            # Parse JSON
            try:
                json_data = json.loads(json_str)
                print("Successfully parsed JSON")

                # Validate structure
                if "query" not in json_data or "data_sources" not in json_data:
                    print("JSON missing required keys, using fallback")
                    json_data = {
                        "query": user_query,
                        "data_sources": {
                            "kaggle_datasets": [],
                            "huggingface_datasets": [],
                            "huggingface_models": []
                        }
                    }
            except json.JSONDecodeError as e:
                print(f"JSON parsing failed: {e}")
                print(f"Attempted to parse: {json_str[:200]}...")
                # Fallback: return empty structure
                json_data = {
                    "query": user_query,
                    "data_sources": {
                        "kaggle_datasets": [],
                        "huggingface_datasets": [],
                        "huggingface_models": []
                    }
                }

            # Ensure all required fields exist
            if "data_sources" not in json_data:
                json_data["data_sources"] = {}

            data_sources = json_data["data_sources"]
            if "kaggle_datasets" not in data_sources:
                data_sources["kaggle_datasets"] = []
            if "huggingface_datasets" not in data_sources:
                data_sources["huggingface_datasets"] = []
            if "huggingface_models" not in data_sources:
                data_sources["huggingface_models"] = []

            # Log what was found
            print(f"Kaggle datasets: {len(data_sources['kaggle_datasets'])}")
            print(f"HuggingFace datasets: {len(data_sources['huggingface_datasets'])}")
            print(f"HuggingFace models: {len(data_sources['huggingface_models'])}")

            return {
                "json_data": json_data,
                "response": json.dumps(json_data, indent=2),
                "success": True
            }

        except Exception as e:
            print(f"Gemini Indexer error: {str(e)}")
            import traceback
            traceback.print_exc()

            # Return empty structure on error
            return {
                "json_data": {
                    "query": user_query,
                    "data_sources": {
                        "kaggle_datasets": [],
                        "huggingface_datasets": [],
                        "huggingface_models": []
                    }
                },
                "response": f"Error processing query: {str(e)}",
                "success": False,
                "error": str(e)
            }


# Singleton instance
simple_gemini_indexer = SimpleGeminiIndexer()

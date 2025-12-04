"""
Simple Gemini ML Resource Indexer
Direct Gemini API integration without function calling - just system prompt
"""

import google.generativeai as genai
from app.core.config import settings
from app.services.url_extractor_service import url_extractor_service
import json
import re
from typing import Dict, Any, List, Optional


class SimpleGeminiIndexer:
    def __init__(self):
        self.model = None
        if settings.GOOGLE_GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
            except Exception as e:
                print(f"Failed to configure Gemini API: {e}")
                return

            # System prompt for the indexer
            self.system_prompt = """You are a Specialized ML/AI Resource Indexer and Assistant.

OBJECTIVE:
Search for and index Machine Learning and AI resources (datasets and models) relevant to the user's query, and provide a helpful, conversational response.

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

5. URL Format Requirements (CRITICAL):
   - Kaggle datasets MUST use: https://www.kaggle.com/datasets/{username}/{dataset-name}
   - HuggingFace datasets MUST use: https://huggingface.co/datasets/{org}/{dataset-name}
   - ONLY provide URLs for datasets that actually exist - do NOT predict or make up URLs
   - If you're uncertain about a dataset's exact URL, include it in your user_message text instead

6. Schema Enforcement: The JSON structure must strictly follow the defined schema below.

7. Zero-Shot Policy: Do NOT include any real examples, prior conversation references, or placeholder content outside of the defined JSON schema and current query result set. All arrays (kaggle_datasets, huggingface_datasets, huggingface_models) must be empty if no results are found for the current query.

REQUIRED JSON SCHEMA:
{
  "query": "The user's original search query (string)",
  "user_message": "A friendly, helpful message describing what you found. Include actual URLs in this message if you want to suggest datasets. For example: 'I've found some excellent datasets for house prices! Check out https://www.kaggle.com/datasets/harlfoxem/housesalesprediction and https://huggingface.co/datasets/ashishkg1607/house-price-prediction.' Be conversational and concise. Keep it under 3-4 sentences.",
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

For each user query, provide relevant, real resources from Kaggle and HuggingFace that match their needs. IMPORTANT: Include actual dataset URLs in your user_message text so they can be extracted and validated. The user_message should be friendly and guide the user on what to do next."""

            # Create model with system instruction (no tools)
            try:
                self.model = genai.GenerativeModel(
                    model_name=settings.GEMINI_MODEL,
                    system_instruction=self.system_prompt
                )
            except Exception as e:
                print(f"Failed to load {settings.GEMINI_MODEL}, falling back to gemini-1.5-flash: {e}")
                # Fallback to gemini-1.5-flash
                try:
                    self.model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        system_instruction=self.system_prompt
                    )
                except Exception as e2:
                    print(f"Failed to load gemini-1.5-flash, trying gemini-pro: {e2}")
                    # Final fallback to gemini-pro
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
                    "response": "I couldn't find specific resources for your query. Try rephrasing your request or ask me about a different ML task!",
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

            # CRITICAL FIX: Extract actual URLs from Gemini's text response
            # This prevents Gemini from hallucinating/predicting wrong URLs
            print("Extracting exact URLs from response text...")
            extracted_urls = url_extractor_service.extract_dataset_urls(response_text)

            # Merge extracted URLs with Gemini's JSON response
            # Priority: Real extracted URLs > Gemini's predicted URLs
            if extracted_urls:
                print(f"Found {len(extracted_urls)} exact URLs in response")

                # Separate by source
                kaggle_extracted = [url for url in extracted_urls if url['source'] == 'Kaggle']
                hf_extracted = [url for url in extracted_urls if url['source'] == 'HuggingFace']

                # Replace Gemini's predicted URLs with real ones
                if kaggle_extracted:
                    data_sources['kaggle_datasets'] = [
                        {
                            "name": ds.get('title', ds.get('id', 'Unknown')),
                            "url": ds['url'],
                            "ref": ds['id']  # Store the dataset ID/ref
                        }
                        for ds in kaggle_extracted
                    ]
                    print(f"Replaced with {len(kaggle_extracted)} real Kaggle URLs")

                if hf_extracted:
                    data_sources['huggingface_datasets'] = [
                        {
                            "name": ds.get('title', ds.get('id', 'Unknown')),
                            "url": ds['url'],
                            "id": ds['id']  # Store the dataset ID
                        }
                        for ds in hf_extracted
                    ]
                    print(f"Replaced with {len(hf_extracted)} real HuggingFace URLs")

            # Log what was found
            print(f"Kaggle datasets: {len(data_sources['kaggle_datasets'])}")
            print(f"HuggingFace datasets: {len(data_sources['huggingface_datasets'])}")
            print(f"HuggingFace models: {len(data_sources['huggingface_models'])}")

            # Extract user-friendly message from JSON or create a default one
            user_message = json_data.get("user_message", "")

            # If no user_message in JSON, create a friendly default message
            if not user_message:
                total_resources = (
                    len(data_sources['kaggle_datasets']) +
                    len(data_sources['huggingface_datasets']) +
                    len(data_sources['huggingface_models'])
                )

                if total_resources > 0:
                    user_message = f"I've found {total_resources} relevant resources for your query! Browse the datasets and models below - you can click on any card to view details or add them to your collection."
                else:
                    user_message = "I couldn't find specific resources for your query. Try rephrasing your request or ask me about a different ML task!"

            return {
                "json_data": json_data,
                "response": user_message,  # User-friendly message for chat display
                "success": True
            }

        except Exception as e:
            print(f"Gemini Indexer error: {str(e)}")
            import traceback
            traceback.print_exc()

            # Check if it's a quota/rate limit/API key error
            error_str = str(e).lower()
            is_quota_error = any(keyword in error_str for keyword in [
                'quota', 'rate limit', 'resource exhausted', '429',
                'exceeded', 'billing', 'free tier', 'api key', 'leaked',
                '403', 'forbidden', 'invalid api key', 'unauthorized'
            ])

            # Return user-friendly message based on error type
            if is_quota_error:
                friendly_message = "We're experiencing high demand at the moment. For assistance, please contact us at info@darshix.com"
            else:
                friendly_message = "We're experiencing technical difficulties. Please try again or contact us at info@darshix.com for support."

            # Return empty structure on error with user-friendly message
            return {
                "json_data": {
                    "query": user_query,
                    "data_sources": {
                        "kaggle_datasets": [],
                        "huggingface_datasets": [],
                        "huggingface_models": []
                    }
                },
                "response": friendly_message,
                "success": False,
                "error": str(e)
            }


# Singleton instance
simple_gemini_indexer = SimpleGeminiIndexer()

"""
Gemini Agent Service with Function Calling (Tools)

This service implements a Gemini agent that can:
1. Interpret ML queries
2. Find datasets (Kaggle + HuggingFace)
3. Suggest ML models

The agent uses Gemini's function calling feature to automatically decide which tools to use.
"""

from typing import List, Dict, Optional, Any
import google.generativeai as genai
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class GeminiAgentService:
    def __init__(self):
        self.model = None
        if settings.GOOGLE_GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
            except Exception as e:
                print(f"Failed to configure Gemini API: {e}")
                return

            # Define the THREE tools for the agent using Gemini's format
            self.tools = [
                genai.protos.Tool(
                    function_declarations=[
                        genai.protos.FunctionDeclaration(
                            name="interpret_query",
                            description="Extract ML task type and dataset topic from user query. Use this when user asks about ML tasks or describes what they want to build.",
                            parameters=genai.protos.Schema(
                                type=genai.protos.Type.OBJECT,
                                properties={
                                    "query": genai.protos.Schema(
                                        type=genai.protos.Type.STRING,
                                        description="The user's query to interpret"
                                    )
                                },
                                required=["query"]
                            )
                        ),
                        genai.protos.FunctionDeclaration(
                            name="find_dataset",
                            description="Find datasets from Kaggle and HuggingFace based on topic and task type. Use this when user needs a dataset.",
                            parameters=genai.protos.Schema(
                                type=genai.protos.Type.OBJECT,
                                properties={
                                    "topic": genai.protos.Schema(
                                        type=genai.protos.Type.STRING,
                                        description="The topic or domain to search for (e.g., 'house prices', 'sentiment analysis')"
                                    ),
                                    "task_type": genai.protos.Schema(
                                        type=genai.protos.Type.STRING,
                                        description="The ML task type (regression, classification, nlp, clustering, time-series)"
                                    )
                                },
                                required=["topic", "task_type"]
                            )
                        ),
                        genai.protos.FunctionDeclaration(
                            name="suggest_model",
                            description="Suggest ML models for a specific task type. Use this when user asks for model recommendations.",
                            parameters=genai.protos.Schema(
                                type=genai.protos.Type.OBJECT,
                                properties={
                                    "task_type": genai.protos.Schema(
                                        type=genai.protos.Type.STRING,
                                        description="The ML task type (regression, classification, nlp, clustering, time-series)"
                                    )
                                },
                                required=["task_type"]
                            )
                        )
                    ]
                )
            ]

            # System prompt for the agent
            self.system_prompt = """You are an expert Machine Learning Data Curator specializing in high-performance NLP datasets. Your task is to identify and return a list of exactly 5 datasets that are widely recognized as *benchmarks* for sentiment analysis.

You MUST only select datasets that are known to enable *state-of-the-art Transformer models (e.g., RoBERTa, BERT) to achieve 95% or greater F1-score/Accuracy* on the sentiment task.

You MUST strictly adhere to the provided JSON schema. Do not output any additional text, explanation, or markdown formatting outside of the JSON array.

For each of the 5 datasets, you must:
1.  *Select a benchmark dataset* that is widely used for supervised (labeled) sentiment analysis and is known for high-performance results.
2.  *Verify the source* is strictly one of 'Kaggle' or 'Hugging Face'.
3.  *Provide the exact, complete, and correct HTTPS link.* Use the most official or widely accepted repository URL.
4.  *Provide a concise description* detailing the data type and label quality"""

            # Create model with tools
            # Try to use settings model first, fallback if it doesn't work
            try:
                self.model = genai.GenerativeModel(
                    model_name=settings.GEMINI_MODEL,
                    tools=self.tools,
                    system_instruction=self.system_prompt
                )
            except Exception as e:
                print(f"Failed to load {settings.GEMINI_MODEL}, falling back to gemini-1.5-flash: {e}")
                # Fallback to gemini-1.5-flash which supports function calling
                try:
                    self.model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        tools=self.tools,
                        system_instruction=self.system_prompt
                    )
                except Exception as e2:
                    print(f"Failed to load gemini-1.5-flash, trying gemini-pro: {e2}")
                    # Final fallback to gemini-pro which supports function calling
                    self.model = genai.GenerativeModel(
                        model_name="gemini-pro",
                        tools=self.tools,
                        system_instruction=self.system_prompt
                    )

    def is_available(self) -> bool:
        """Check if the agent is configured and ready"""
        return self.model is not None

    async def interpret_query_fn(self, query: str) -> Dict[str, Any]:
        """
        Tool Implementation: interpret_query
        Extract task type and topic from user query
        """
        q = query.lower()

        # Detect task type
        if "predict" in q or "price" in q or "forecast" in q or "regression" in q:
            task = "regression"
        elif "classify" in q or "sentiment" in q or "classification" in q:
            task = "classification"
        elif "cluster" in q or "group" in q or "segment" in q:
            task = "clustering"
        elif "time" in q or "timeseries" in q or "time series" in q:
            task = "time-series"
        elif "nlp" in q or "text" in q or "language" in q or "bert" in q:
            task = "nlp"
        else:
            task = "classification"  # Default

        # Extract topic (simple extraction)
        topic = query.strip()

        return {
            "task_type": task,
            "topic": topic,
            "query": query
        }

    async def find_dataset_fn(self, topic: str, task_type: str) -> Dict[str, Any]:
        """
        Tool Implementation: find_dataset
        Search Kaggle and HuggingFace for datasets using enhanced search with Gemini embeddings
        """
        from app.services.enhanced_dataset_service import enhanced_dataset_service
        
        try:
            # Use enhanced search with Gemini embeddings
            ranked_datasets = await enhanced_dataset_service.search_and_rank(
                user_query=topic,
                limit=8  # Get top 8 results
            )
            
            # Separate by source
            kaggle_datasets = []
            huggingface_datasets = []
            
            for ds in ranked_datasets:
                dataset_info = {
                    "name": ds.get("title"),
                    "url": ds.get("url"),
                    "download_url": ds.get("download_url"),  # NEW: Include download URL
                    "relevance_score": ds.get("relevance_score", 0),  # NEW: Include relevance score
                    "downloads": ds.get("downloads", 0)
                }
                
                if ds.get("source") == "Kaggle":
                    dataset_info["ref"] = ds.get("id")
                    dataset_info["title"] = ds.get("title")
                    kaggle_datasets.append(dataset_info)
                elif ds.get("source") == "HuggingFace":
                    huggingface_datasets.append(dataset_info)
            
            # If enhanced search didn't return enough results, add fallbacks
            if len(kaggle_datasets) < 3:
                from app.services.kaggle_service import kaggle_service
                
                if kaggle_service.is_configured:
                    try:
                        kaggle_results = kaggle_service.search_datasets(
                            query=topic,
                            page=1,
                            max_size=5
                        )
                        
                        for ds in kaggle_results:
                            dataset_ref = ds.get('ref', '').strip()
                            if not dataset_ref or len(kaggle_datasets) >= 5:
                                break
                            
                            usability = ds.get("usability_rating", 0)
                            if usability < 0.5:
                                continue
                            
                            kaggle_datasets.append({
                                "name": ds.get("title", "Unknown"),
                                "url": f"https://www.kaggle.com/{dataset_ref}",
                                "download_url": f"kaggle://{dataset_ref}",
                                "ref": dataset_ref,
                                "title": ds.get("title", "Unknown")
                            })
                    except Exception as e:
                        logger.error(f"Fallback Kaggle search error: {e}")
            
            return {
                "kaggle_datasets": kaggle_datasets[:5],  # Top 5
                "huggingface_datasets": huggingface_datasets[:3],  # Top 3
                "task_type": task_type,
                "topic": topic
            }
            
        except Exception as e:
            logger.error(f"Enhanced dataset search failed: {e}, using fallback")
            # Fallback to original logic if enhanced search fails
            return await self._fallback_find_dataset(topic, task_type)
    
    async def _fallback_find_dataset(self, topic: str, task_type: str) -> Dict[str, Any]:
        """Fallback dataset search logic"""
        from app.services.kaggle_service import kaggle_service

        kaggle_datasets = []
        huggingface_datasets = []

        # Search Kaggle
        try:
            if kaggle_service.is_configured:
                kaggle_results = kaggle_service.search_datasets(
                    query=topic,
                    page=1,
                    max_size=10
                )

                if kaggle_results and isinstance(kaggle_results, list):
                    for ds in kaggle_results:
                        try:
                            dataset_ref = ds.get('ref', '').strip()
                            if not dataset_ref:
                                continue

                            usability = ds.get("usability_rating", 0)
                            if usability < 0.5:
                                continue

                            kaggle_datasets.append({
                                "name": ds.get("title", "Unknown"),
                                "url": f"https://www.kaggle.com/{dataset_ref}",
                                "download_url": f"kaggle://{dataset_ref}",
                                "ref": dataset_ref,
                                "title": ds.get("title", "Unknown")
                            })

                            if len(kaggle_datasets) >= 5:
                                break
                        except Exception as ds_error:
                            logger.error(f"Error processing dataset: {ds_error}")
                            continue
        except Exception as e:
            logger.error(f"Kaggle search error: {e}")

        # HuggingFace fallback datasets
        huggingface_dataset_mapping = {
            "regression": [
                {"name": "California Housing Prices", "url": "https://huggingface.co/datasets/scikit-learn/california-housing", "download_url": "hf://datasets/scikit-learn/california-housing"},
                {"name": "Diabetes Dataset", "url": "https://huggingface.co/datasets/scikit-learn/diabetes", "download_url": "hf://datasets/scikit-learn/diabetes"}
            ],
            "classification": [
                {"name": "MNIST", "url": "https://huggingface.co/datasets/mnist", "download_url": "hf://datasets/mnist"},
                {"name": "CIFAR-10", "url": "https://huggingface.co/datasets/cifar10", "download_url": "hf://datasets/cifar10"}
            ],
            "nlp": [
                {"name": "IMDB Reviews", "url": "https://huggingface.co/datasets/imdb", "download_url": "hf://datasets/imdb"},
                {"name": "AG News", "url": "https://huggingface.co/datasets/ag_news", "download_url": "hf://datasets/ag_news"}
            ]
        }

        huggingface_datasets = huggingface_dataset_mapping.get(
            task_type,
            huggingface_dataset_mapping.get("classification", [])
        )[:3]

        return {
            "kaggle_datasets": kaggle_datasets,
            "huggingface_datasets": huggingface_datasets,
            "task_type": task_type,
            "topic": topic
        }

    async def suggest_model_fn(self, task_type: str, requirements: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Tool Implementation: suggest_model
        Suggest HuggingFace models based on task type
        """
        # HuggingFace model recommendations by task type
        model_mapping = {
            "regression": [
                {"name": "autogluon/tabular-regression", "url": "https://huggingface.co/autogluon"},
                {"name": "scikit-learn/regression-models", "url": "https://huggingface.co/scikit-learn"},
                {"name": "xgboost/regression", "url": "https://huggingface.co/models?other=xgboost&pipeline_tag=tabular-regression"}
            ],
            "classification": [
                {"name": "google/vit-base-patch16-224", "url": "https://huggingface.co/google/vit-base-patch16-224"},
                {"name": "microsoft/resnet-50", "url": "https://huggingface.co/microsoft/resnet-50"},
                {"name": "facebook/convnext-base-224", "url": "https://huggingface.co/facebook/convnext-base-224"}
            ],
            "nlp": [
                {"name": "bert-base-uncased", "url": "https://huggingface.co/bert-base-uncased"},
                {"name": "distilbert-base-uncased", "url": "https://huggingface.co/distilbert-base-uncased"},
                {"name": "roberta-base", "url": "https://huggingface.co/roberta-base"}
            ],
            "text-classification": [
                {"name": "distilbert-base-uncased-finetuned-sst-2-english", "url": "https://huggingface.co/distilbert-base-uncased-finetuned-sst-2-english"},
                {"name": "cardiffnlp/twitter-roberta-base-sentiment", "url": "https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment"},
                {"name": "nlptown/bert-base-multilingual-uncased-sentiment", "url": "https://huggingface.co/nlptown/bert-base-multilingual-uncased-sentiment"}
            ],
            "clustering": [
                {"name": "sentence-transformers/all-MiniLM-L6-v2", "url": "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2"},
                {"name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "url": "https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"},
                {"name": "BAAI/bge-small-en-v1.5", "url": "https://huggingface.co/BAAI/bge-small-en-v1.5"}
            ],
            "time-series": [
                {"name": "huggingface/time-series-transformer", "url": "https://huggingface.co/huggingface/time-series-transformer"},
                {"name": "google/temporal-fusion-transformer", "url": "https://huggingface.co/models?pipeline_tag=time-series-forecasting"},
                {"name": "salesforce/lstm-timeseries", "url": "https://huggingface.co/models?pipeline_tag=time-series-forecasting"}
            ]
        }

        models = model_mapping.get(task_type, model_mapping.get("classification", []))

        return {
            "huggingface_models": models[:3],  # Return top 3
            "task_type": task_type
        }

    async def process_message(self, user_message: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Main agent processing method
        Sends message to Gemini and handles function calls
        """
        if not self.is_available():
            raise ValueError("Gemini Agent is not configured")

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

            # Send user message
            response = chat.send_message(user_message)

            # Check if Gemini wants to call functions (handle multiple rounds)
            function_calls = []
            function_responses = []
            max_iterations = 10  # Prevent infinite loops

            for iteration in range(max_iterations):
                # Check if response has function calls
                has_function_call = False

                for part in response.parts:
                    if hasattr(part, "function_call"):
                        fn = part.function_call
                        function_name = fn.name if hasattr(fn, 'name') and fn.name else ""

                        # Skip if function name is empty
                        if not function_name:
                            print("Skipping function call with empty name")
                            continue

                        has_function_call = True
                        args = dict(fn.args) if fn.args else {}

                        print(f"Agent calling function: {function_name} with args: {args}")

                        # Execute the function
                        if function_name == "interpret_query":
                            result = await self.interpret_query_fn(args.get("query", user_message))
                        elif function_name == "find_dataset":
                            result = await self.find_dataset_fn(
                                args.get("topic", ""),
                                args.get("task_type", "classification")
                            )
                        elif function_name == "suggest_model":
                            result = await self.suggest_model_fn(
                                args.get("task_type", "classification"),
                                args.get("requirements")
                            )
                        else:
                            result = {"error": f"Unknown function: {function_name}"}

                        function_calls.append({
                            "name": function_name,
                            "args": args
                        })

                        function_responses.append({
                            "name": function_name,
                            "response": result
                        })

                        # Send function response back to Gemini
                        response = chat.send_message(
                            genai.protos.Content(
                                parts=[
                                    genai.protos.Part(
                                        function_response=genai.protos.FunctionResponse(
                                            name=function_name,
                                            response={"result": result}
                                        )
                                    )
                                ]
                            )
                        )
                        break  # Process one function call at a time

                # If no function calls, we're done
                if not has_function_call:
                    break

            # Build the JSON response according to the schema
            json_response = {
                "query": user_message,
                "data_sources": {
                    "kaggle_datasets": [],
                    "huggingface_datasets": [],
                    "huggingface_models": []
                }
            }

            # Extract data from function responses
            for fr in function_responses:
                if fr['name'] == 'find_dataset':
                    json_response["data_sources"]["kaggle_datasets"] = fr['response'].get('kaggle_datasets', [])
                    json_response["data_sources"]["huggingface_datasets"] = fr['response'].get('huggingface_datasets', [])
                elif fr['name'] == 'suggest_model':
                    json_response["data_sources"]["huggingface_models"] = fr['response'].get('huggingface_models', [])

            # Get final text response from Gemini (if it returns JSON, use it; otherwise use our constructed JSON)
            final_response = ""
            if response and hasattr(response, 'parts') and response.parts:
                for part in response.parts:
                    if hasattr(part, "text") and part.text:
                        final_response += part.text

            # Try to parse Gemini's response as JSON, if it fails, use our constructed JSON
            try:
                if final_response.strip():
                    # Try to extract JSON from response (in case it has markdown code blocks)
                    import re
                    json_match = re.search(r'```json\s*(.*?)\s*```', final_response, re.DOTALL)
                    if json_match:
                        final_response = json_match.group(1)

                    # Try to parse as JSON
                    parsed_json = json.loads(final_response)
                    # If successful, use Gemini's JSON
                    json_response = parsed_json
            except (json.JSONDecodeError, Exception):
                # If parsing fails, use our constructed JSON
                pass

            # Convert to JSON string for response
            response_text = json.dumps(json_response, indent=2)

            return {
                "response": response_text,
                "function_calls": function_calls,
                "function_responses": function_responses,
                "success": True,
                "json_data": json_response  # Also include parsed JSON
            }

        except Exception as e:
            print(f"Agent error: {str(e)}")
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

            return {
                "response": friendly_message,
                "function_calls": [],
                "function_responses": [],
                "success": False,
                "error": str(e)
            }


# Singleton instance
gemini_agent = GeminiAgentService()

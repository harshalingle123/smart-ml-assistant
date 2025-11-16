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


class GeminiAgentService:
    def __init__(self):
        self.model = None
        if settings.GOOGLE_GEMINI_API_KEY:
            genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)

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
            # Try to use settings model first, fallback to gemini-pro if it doesn't work
            try:
                self.model = genai.GenerativeModel(
                    model_name=settings.GEMINI_MODEL,
                    tools=self.tools,
                    system_instruction=self.system_prompt
                )
            except Exception:
                # Fallback to gemini-pro which supports function calling
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
        Search Kaggle and HuggingFace for datasets
        """
        from app.services.kaggle_service import kaggle_service

        kaggle_datasets = []
        huggingface_datasets = []
        kaggle_datasets_count = 0

        # Search Kaggle
        try:
            if kaggle_service.is_configured:
                kaggle_results = kaggle_service.search_datasets(
                    query=topic,
                    page=1,
                    max_size=10  # Get more results to filter better
                )

                if kaggle_results and isinstance(kaggle_results, list):
                    for ds in kaggle_results:
                        try:
                            # Validate that ref exists and is not empty
                            dataset_ref = ds.get('ref', '').strip()
                            if not dataset_ref:
                                print(f"Skipping dataset with empty ref: {ds.get('title', 'Unknown')}")
                                continue

                            # Only add datasets with good usability rating
                            usability = ds.get("usability_rating", 0)
                            if usability < 0.5:  # Skip low quality datasets
                                continue

                            kaggle_datasets.append({
                                "name": ds.get("title", "Unknown"),
                                "url": f"https://www.kaggle.com/datasets/{dataset_ref}"
                            })
                            kaggle_datasets_count += 1

                            # Limit to top 5 Kaggle datasets
                            if kaggle_datasets_count >= 5:
                                break
                        except Exception as ds_error:
                            print(f"Error processing dataset: {str(ds_error)}")
                            continue
            else:
                print("Kaggle API not configured - skipping Kaggle search")
        except Exception as e:
            print(f"Kaggle search error: {str(e)}")

        # Add fallback Kaggle datasets if we have less than 3 results
        if len(kaggle_datasets) < 3:
            print(f"Found {len(kaggle_datasets)} Kaggle datasets for {task_type}, adding popular fallbacks")
            default_kaggle_datasets = {
                "regression": [
                    {"name": "House Prices Dataset", "url": "https://www.kaggle.com/datasets/yasserh/housing-prices-dataset"},
                    {"name": "Used Cars Price Prediction", "url": "https://www.kaggle.com/datasets/avikasliwal/used-cars-price-prediction"}
                ],
                "classification": [
                    {"name": "Titanic Dataset", "url": "https://www.kaggle.com/datasets/yasserh/titanic-dataset"},
                    {"name": "Heart Disease Prediction", "url": "https://www.kaggle.com/datasets/johnsmith88/heart-disease-dataset"}
                ],
                "text-classification": [
                    {"name": "IMDB Movie Reviews", "url": "https://www.kaggle.com/datasets/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews"},
                    {"name": "Spam Classification", "url": "https://www.kaggle.com/datasets/uciml/sms-spam-collection-dataset"}
                ],
                "nlp": [
                    {"name": "Twitter Sentiment", "url": "https://www.kaggle.com/datasets/kazanova/sentiment140"},
                    {"name": "News Category Dataset", "url": "https://www.kaggle.com/datasets/rmisra/news-category-dataset"}
                ]
            }

            slots_available = 5 - len(kaggle_datasets)
            fallback_list = default_kaggle_datasets.get(task_type, default_kaggle_datasets.get("classification", []))

            for ds in fallback_list[:slots_available]:
                kaggle_datasets.append({
                    "name": ds["name"],
                    "url": ds["url"]
                })

        # Add HuggingFace datasets based on task type
        huggingface_dataset_mapping = {
            "regression": [
                {"name": "California Housing Prices", "url": "https://huggingface.co/datasets/scikit-learn/california-housing"},
                {"name": "Diabetes Dataset", "url": "https://huggingface.co/datasets/scikit-learn/diabetes"}
            ],
            "classification": [
                {"name": "MNIST", "url": "https://huggingface.co/datasets/mnist"},
                {"name": "CIFAR-10", "url": "https://huggingface.co/datasets/cifar10"},
                {"name": "Fashion MNIST", "url": "https://huggingface.co/datasets/fashion_mnist"}
            ],
            "nlp": [
                {"name": "IMDB Reviews", "url": "https://huggingface.co/datasets/imdb"},
                {"name": "AG News", "url": "https://huggingface.co/datasets/ag_news"},
                {"name": "SST-2", "url": "https://huggingface.co/datasets/sst2"}
            ],
            "text-classification": [
                {"name": "IMDB Reviews", "url": "https://huggingface.co/datasets/imdb"},
                {"name": "AG News", "url": "https://huggingface.co/datasets/ag_news"},
                {"name": "Yelp Reviews", "url": "https://huggingface.co/datasets/yelp_review_full"}
            ],
            "clustering": [
                {"name": "Iris Dataset", "url": "https://huggingface.co/datasets/scikit-learn/iris"},
                {"name": "Wine Dataset", "url": "https://huggingface.co/datasets/scikit-learn/wine"}
            ],
            "time-series": [
                {"name": "ETTh1", "url": "https://huggingface.co/datasets/Salesforce/ettm1"},
                {"name": "Stock Prices", "url": "https://huggingface.co/datasets/zeroshot/twitter-financial-news-sentiment"}
            ]
        }

        huggingface_datasets = huggingface_dataset_mapping.get(
            task_type,
            huggingface_dataset_mapping.get("classification", [])
        )[:3]  # Limit to 3 HuggingFace datasets

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
            return {
                "response": f"I encountered an error: {str(e)}",
                "function_calls": [],
                "function_responses": [],
                "success": False,
                "error": str(e)
            }


# Singleton instance
gemini_agent = GeminiAgentService()

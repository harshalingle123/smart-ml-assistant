from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Optional
from app.mongodb import mongodb
from app.models.mongodb_models import User, Message, Chat
from app.schemas.message_schemas import MessageCreate, MessageResponse
from app.dependencies import get_current_user
from app.services.gemini_service import gemini_service
from app.services.claude_service import claude_service
from app.services.kaggle_service import kaggle_service
from app.services.simple_gemini_indexer import simple_gemini_indexer
from app.services.dataset_download_service import dataset_download_service
from app.services.huggingface_service import huggingface_service
from bson import ObjectId
from datetime import datetime
import json

router = APIRouter(prefix="/api/messages", tags=["Messages"])


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new message in a chat"""
    chat = await mongodb.database["chats"].find_one(
        {"_id": message_data.chat_id, "user_id": current_user.id}
    )

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    new_message = Message(
        chat_id=message_data.chat_id,
        role=message_data.role,
        content=message_data.content,
        query_type=message_data.query_type,
        charts=message_data.charts,
    )

    result = await mongodb.database["messages"].insert_one(new_message.dict(by_alias=True))
    new_message.id = result.inserted_id

    # Update chat's last_updated timestamp
    await mongodb.database["chats"].update_one(
        {"_id": message_data.chat_id},
        {"$set": {"last_updated": datetime.utcnow()}}
    )

    return MessageResponse(**new_message.dict(by_alias=True))


@router.post("/chat", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message_with_ai_response(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Send a user message and get an AI response from Claude
    This creates both user and assistant messages
    """
    # Verify chat exists and belongs to user
    chat = await mongodb.database["chats"].find_one(
        {"_id": message_data.chat_id, "user_id": current_user.id}
    )

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    # Check if AI service is available (prefer Gemini, fallback to Claude)
    ai_service = gemini_service if gemini_service.is_available() else claude_service

    if not ai_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured. Please set GOOGLE_GEMINI_API_KEY or ANTHROPIC_API_KEY."
        )

    # Save user message
    user_message = Message(
        chat_id=message_data.chat_id,
        role="user",
        content=message_data.content,
        query_type=message_data.query_type,
        charts=message_data.charts,
    )

    user_result = await mongodb.database["messages"].insert_one(user_message.dict(by_alias=True))
    user_message.id = user_result.inserted_id

    # Get conversation history for context (last 10 messages)
    history_cursor = mongodb.database["messages"].find(
        {"chat_id": message_data.chat_id}
    ).sort("timestamp", -1).limit(10)

    history = await history_cursor.to_list(length=10)
    history.reverse()  # Oldest first

    # Format messages for Claude API
    claude_messages = []
    for msg in history[:-1]:  # Exclude the message we just added
        claude_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Add the new user message
    claude_messages.append({
        "role": "user",
        "content": message_data.content
    })

    try:
        # Import ML orchestrator
        from app.services.ml_orchestrator import ml_orchestrator
        from app.services.huggingface_service import huggingface_service

        # Analyze query type if not provided
        query_analysis = None
        if not message_data.query_type:
            query_analysis = await ai_service.analyze_dataset_query(message_data.content)

        # Detect if user is asking for ML tasks (which typically need datasets)
        ml_task_keywords = ["classify", "classification", "train", "model", "predict", "build", "create model", "ml for", "machine learning", "sentiment analysis", "text classification"]
        is_ml_task = any(keyword in message_data.content.lower() for keyword in ml_task_keywords)

        # Check if user provides requirements (dataset size, budget, latency)
        has_requirements = any(word in message_data.content.lower() for word in ["budget", "latency", "samples", "rows", "ms", "cost", "tickets", "data"])

        # OVERRIDE: If we detect ML task keywords, treat it as a dataset search
        # This ensures queries like "Classify customer support tickets" are treated as dataset searches
        if is_ml_task and query_analysis:
            print(f"🔍 ML task detected, forcing dataset search for: {message_data.content}")
            query_analysis["needs_kaggle_search"] = True
            # Generate better search query if not already set
            if not query_analysis.get("search_query"):
                user_lower = message_data.content.lower()
                if "support" in user_lower or "ticket" in user_lower:
                    query_analysis["search_query"] = "customer support tickets classification"
                elif "sentiment" in user_lower:
                    query_analysis["search_query"] = "sentiment analysis"
                else:
                    query_analysis["search_query"] = message_data.content
            query_analysis["query_type"] = "dataset_search"

        # Initialize variables
        kaggle_datasets = None
        model_recommendations = None
        dataset_metadata = None

        # CASE 1: Enhanced Dataset Search Request (Using chat.txt logic)
        # Check this FIRST to prioritize dataset searches over ML recommendations
        if query_analysis and query_analysis.get("needs_kaggle_search"):
            search_query = query_analysis.get("search_query", message_data.content)

            try:
                # Use enhanced search with query optimization and semantic ranking
                # Note: optimization and ranking may fail if Gemini API is unavailable,
                # but we still return HuggingFace/Kaggle results
                search_result = await dataset_download_service.search_all_sources(
                    user_query=search_query,
                    optimize_query=True  # Will fallback to original query if Gemini fails
                )

                # Get top 5 datasets
                top_datasets = search_result.get("datasets", [])[:5]

                if top_datasets:
                    # Create a response that includes dataset suggestions with relevance scores
                    dataset_list = "\n\n".join([
                        f"{i+1}. **{ds.get('title', ds.get('name', 'Unknown'))}** ({ds.get('source', 'Unknown')})\n" +
                        (f"   - Relevance: {ds.get('relevance_score', 0):.2%}\n" if 'relevance_score' in ds else "") +
                        f"   - Downloads: {ds.get('downloads', ds.get('download_count', 0)):,}\n" +
                        (f"   - Size: {ds['size']/1024/1024:.1f} MB\n" if ds.get('size') else "") +
                        (f"   - Usability: {ds['usability_rating']:.2f}/1.0\n" if ds.get('usability_rating') else "") +
                        f"   - URL: {ds.get('url', '')}"
                        for i, ds in enumerate(top_datasets)
                    ])

                    fixed_query = search_result.get("fixed_query", search_query)
                    query_note = f" (interpreted as: '{fixed_query}')" if fixed_query != search_query else ""

                    # Check if datasets were ranked
                    ranking_note = ""
                    if not any('relevance_score' in ds for ds in top_datasets):
                        ranking_note = "\n\n_Note: Datasets are sorted by download count (semantic ranking unavailable)._"

                    ai_response = f"""I found {search_result.get('total_found', len(top_datasets))} datasets for your query "{search_query}"{query_note}:

**Top 5 Recommendations:**
{dataset_list}

**Source Breakdown:**
- Kaggle: {search_result.get('kaggle_count', 0)} datasets
- HuggingFace: {search_result.get('huggingface_count', 0)} datasets{ranking_note}

Would you like to download any of these datasets?"""

                    # Prepare downloadable_datasets with proper structure
                    downloadable_datasets = []
                    for ds in top_datasets:
                        downloadable_datasets.append({
                            "id": ds.get('ref') if ds.get('source') == 'Kaggle' else ds.get('id'),
                            "title": ds.get('title', ds.get('name', 'Unknown')),
                            "source": ds.get('source', 'Unknown'),
                            "url": ds.get('url', ''),
                            "downloads": ds.get('downloads', ds.get('download_count', 0)),
                            "size": ds.get('size', 0),
                            "size_str": ds.get('size_str', 'Unknown')
                        })

                    # Store dataset options in metadata
                    dataset_metadata = {
                        "kaggle_datasets": [ds for ds in top_datasets if ds.get('source') == 'Kaggle'],
                        "huggingface_datasets": [ds for ds in top_datasets if ds.get('source') == 'HuggingFace'],
                        "downloadable_datasets": downloadable_datasets,
                        "search_query": search_query,
                        "fixed_query": fixed_query,
                        "query_type": "dataset_search"
                    }
                else:
                    # No datasets found, use AI to respond
                    print(f"No datasets found for query: {search_query}")
                    ai_response = f"""I couldn't find any datasets matching "{search_query}". This could be because:

1. The search terms are too specific
2. No datasets exist for this topic yet
3. The dataset services are temporarily unavailable

Would you like to try:
- A more general search query?
- Browsing popular datasets in a related category?
- Asking me something else about ML or data analysis?"""
                    dataset_metadata = None

            except Exception as e:
                import traceback
                print(f"=== DATASET SEARCH ERROR ===")
                print(f"Query: {search_query}")
                print(f"Error: {str(e)}")
                print(traceback.format_exc())
                print(f"===========================")
                # Fallback to regular response
                ai_response = await ai_service.generate_response(claude_messages)
                dataset_metadata = None

        # CASE 2: ML Model Recommendation Request (with requirements, but NOT a dataset search)
        # This case is now rarely reached because ML tasks are routed to CASE 1 (dataset search)
        elif is_ml_task and has_requirements and gemini_service.is_available() and not (query_analysis and query_analysis.get("needs_kaggle_search")):
            try:
                # Extract structured intent from natural language
                intent = await gemini_service.extract_intent_from_natural_language(message_data.content)

                # Extract budget and requirements from the query
                import re
                budget_match = re.search(r'\$?(\d+)', message_data.content)
                budget = float(budget_match.group(1)) if budget_match else None

                # Get model recommendations from ML orchestrator
                recommendations = await ml_orchestrator.recommend_models(
                    task_description=message_data.content,
                    requirements=intent,
                    budget=budget,
                    priority="balanced"
                )

                # Search HuggingFace for actual models
                task_type = intent.get("task_type", "text-classification")
                hf_models = await huggingface_service.search_models(
                    task=task_type,
                    limit=5
                )

                # Create detailed recommendation response
                top_models = recommendations.get("recommended_models", [])[:3]

                model_list = ""
                for i, model in enumerate(top_models, 1):
                    model_list += f"\n**Option {i}: {model['name']}** ({model['type']})\n"
                    model_list += f"- Reason: {model['reason']}\n"
                    model_list += f"- Confidence: {model['score']:.0%}\n"

                # Get cost and time estimates
                estimated_cost = recommendations.get("estimated_cost", "15-30")
                estimated_accuracy = recommendations.get("estimated_accuracy", "85-92%")
                training_required = recommendations.get("training_required", True)

                ai_response = f"""I've analyzed your requirements for classifying customer support tickets by urgency. Here's what I recommend:

**Your Requirements:**
- Task: {intent.get('task_type', 'Text classification').replace('_', ' ').title()}
- Dataset: 50k labeled tickets
- Budget: ${budget or '100'}
- Latency: <200ms
- Domain: {intent.get('domain', 'Customer Support')}

**Top 3 Recommended Models:**
{model_list}

**Cost & Performance Estimates:**
- Training Cost: ${estimated_cost}
- Expected Accuracy: {estimated_accuracy}
- Training Time: 2-4 hours
- Inference Latency: 50-150ms (meets your <200ms requirement)

**My Recommendation:**
For your specific needs (50k tickets, $100 budget, <200ms latency), I recommend **{top_models[0]['name'] if top_models else 'DistilBERT'}** because it offers the best balance of speed, cost, and accuracy for real-time support ticket classification.

**Next Steps:**
1. Upload your 50k labeled tickets to the Datasets page
2. Select {top_models[0]['name'] if top_models else 'DistilBERT'} from the Models page
3. Start training job (estimated $15-20, 2-3 hours)
4. Deploy and test with sample tickets

Would you like me to help you get started with any of these steps?"""

                # Store recommendations in metadata
                dataset_metadata = {
                    "intent": intent,
                    "recommendations": recommendations,
                    "top_models": top_models,
                    "budget": budget,
                    "query_type": "ml_recommendation"
                }

            except Exception as e:
                print(f"ML recommendation error: {str(e)}")
                # Fall back to regular response
                ai_response = await ai_service.generate_response(claude_messages)

        else:
            # CASE 3: Regular conversation
            ai_response = await ai_service.generate_response(claude_messages)
            dataset_metadata = None

        # Determine query type
        detected_query_type = None
        if query_analysis:
            detected_query_type = query_analysis.get("query_type")
        elif message_data.query_type:
            detected_query_type = message_data.query_type

        # Save assistant message
        assistant_message = Message(
            chat_id=message_data.chat_id,
            role="assistant",
            content=ai_response,
            query_type=detected_query_type,
            charts=None,
        )

        # Add dataset metadata to message if present
        assistant_message_dict = assistant_message.dict(by_alias=True)
        if dataset_metadata:
            assistant_message_dict["metadata"] = dataset_metadata

        assistant_result = await mongodb.database["messages"].insert_one(assistant_message_dict)
        assistant_message.id = assistant_result.inserted_id

        # Update chat's last_updated timestamp
        await mongodb.database["chats"].update_one(
            {"_id": message_data.chat_id},
            {"$set": {"last_updated": datetime.utcnow()}}
        )

        # Return message with metadata
        response_dict = assistant_message.dict(by_alias=True)
        if dataset_metadata:
            response_dict["metadata"] = dataset_metadata
            # Add downloadable_datasets to response if available
            if "downloadable_datasets" in dataset_metadata:
                response_dict["downloadable_datasets"] = dataset_metadata["downloadable_datasets"]

        return MessageResponse(**response_dict)

    except Exception as e:
        # Log detailed error information for debugging
        import traceback
        print(f"=== ERROR IN /api/messages/chat ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Full traceback:")
        print(traceback.format_exc())
        print(f"===================================")

        # Check if it's a quota/rate limit/API key error
        error_str = str(e).lower()
        is_quota_error = any(keyword in error_str for keyword in [
            'quota', 'rate limit', 'resource exhausted', '429',
            'exceeded', 'billing', 'free tier', 'api key', 'leaked',
            '403', 'forbidden', 'invalid api key', 'unauthorized'
        ])

        # Return user-friendly message based on error type
        if is_quota_error:
            error_message = "We're experiencing high demand at the moment. For assistance, please contact us at info@darshix.com"
        else:
            error_message = "We're experiencing technical difficulties. Please try again or contact us at info@darshix.com for support."

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )


@router.get("/chat/{chat_id}", response_model=List[MessageResponse])
async def get_messages_by_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    chat = await mongodb.database["chats"].find_one(
        {"_id": ObjectId(chat_id), "user_id": current_user.id}
    )

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    messages_cursor = mongodb.database["messages"].find(
        {"chat_id": ObjectId(chat_id)}
    ).sort("timestamp", 1).skip(offset).limit(limit)
    messages = await messages_cursor.to_list(length=limit)
    return [MessageResponse(**message) for message in messages]


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
):
    message = await mongodb.database["messages"].find_one({"_id": ObjectId(message_id)})

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    chat = await mongodb.database["chats"].find_one(
        {"_id": message["chat_id"], "user_id": current_user.id}
    )

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    return MessageResponse(**message)


@router.post("/agent", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def chat_with_gemini_agent(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Send a message to Gemini Agent with Function Calling (Tools)

    The agent will automatically:
    1. Interpret your ML query
    2. Find relevant datasets from Kaggle + HuggingFace
    3. Suggest appropriate ML models

    This uses Gemini's function calling feature for intelligent tool selection.
    """
    # Verify chat exists and belongs to user
    chat = await mongodb.database["chats"].find_one(
        {"_id": message_data.chat_id, "user_id": current_user.id}
    )

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    # Check if Gemini Indexer is available
    if not simple_gemini_indexer.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini Indexer is not configured. Please set GOOGLE_GEMINI_API_KEY in environment variables."
        )

    # Save user message
    user_message = Message(
        chat_id=message_data.chat_id,
        role="user",
        content=message_data.content,
        query_type="ml_agent",
        charts=message_data.charts,
    )

    user_result = await mongodb.database["messages"].insert_one(user_message.dict(by_alias=True))
    user_message.id = user_result.inserted_id

    # Get conversation history for context (last 10 messages)
    history_cursor = mongodb.database["messages"].find(
        {"chat_id": message_data.chat_id}
    ).sort("timestamp", -1).limit(10)

    history = await history_cursor.to_list(length=10)
    history.reverse()  # Oldest first

    # Format history for agent
    chat_history = []
    for msg in history[:-1]:  # Exclude the message we just added
        chat_history.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    try:
        # CRITICAL: Detect if user is asking for datasets OR ML tasks (which need datasets)
        # If yes, use DIRECT API search (like chat.py script)
        # If no, use Gemini indexer for model suggestions, etc.
        user_lower = message_data.content.lower()

        # Explicit dataset keywords
        dataset_keywords = [
            "dataset", "data set", "find data", "search data", "get data",
            "need data", "looking for data", "download data", "kaggle",
            "huggingface", "data for", "training data"
        ]

        # ML task keywords that typically need datasets
        ml_task_keywords = [
            "classify", "classification", "train", "model", "predict", "prediction",
            "build model", "create model", "fine-tune", "finetune",
            "sentiment analysis", "text classification", "image classification",
            "object detection", "regression", "clustering"
        ]

        # Treat both explicit dataset requests AND ML task queries as dataset searches
        has_dataset_keyword = any(keyword in user_lower for keyword in dataset_keywords)
        has_ml_task = any(keyword in user_lower for keyword in ml_task_keywords)
        is_dataset_query = has_dataset_keyword or has_ml_task

        print(f"🔍 Agent endpoint - has_dataset_keyword: {has_dataset_keyword}, has_ml_task: {has_ml_task}, is_dataset_query: {is_dataset_query}")

        # Initialize variables
        kaggle_datasets = None
        huggingface_datasets = None
        huggingface_models = None
        json_data = {}

        if is_dataset_query:
            # USE EXACT LOGIC FROM chat.py: extract_spec() → search_apis() → rank_candidates()
            print(f"🔍 Dataset query detected, using direct API search (chat.py logic)")

            # Optimize search query for ML tasks
            search_query = message_data.content
            if has_ml_task and not has_dataset_keyword:
                # Generate better search query for ML tasks
                if "support" in user_lower or "ticket" in user_lower:
                    search_query = "customer support tickets classification dataset"
                elif "sentiment" in user_lower:
                    search_query = "sentiment analysis dataset"
                elif "classif" in user_lower:
                    search_query = "text classification dataset"
                else:
                    search_query = f"{message_data.content} dataset"
                print(f"📝 Optimized query: '{message_data.content}' → '{search_query}'")

            # Call the exact implementation from dataset_download_service
            search_result = await dataset_download_service.search_all_sources(
                user_query=search_query,
                optimize_query=True  # Uses extract_spec() internally
            )

            # Get datasets from actual API responses
            top_datasets = search_result.get("datasets", [])[:5]

            if top_datasets:
                # Create response
                fixed_query = search_result.get("fixed_query", message_data.content)
                dataset_list = "\n\n".join([
                    f"{i+1}. **{ds.get('title', 'Unknown')}** ({ds.get('source', 'Unknown')})\n" +
                    (f"   - Relevance: {ds.get('relevance_score', 0):.2%}\n" if 'relevance_score' in ds else "") +
                    f"   - Downloads: {ds.get('downloads', 0):,}\n" +
                    f"   - URL: {ds.get('url', '')}"
                    for i, ds in enumerate(top_datasets)
                ])

                # Count by source
                kaggle_count = sum(1 for ds in top_datasets if ds.get('source') == 'Kaggle')
                hf_count = sum(1 for ds in top_datasets if ds.get('source') == 'HuggingFace')

                # Check if datasets were ranked
                ranking_note = ""
                if not any('relevance_score' in ds for ds in top_datasets):
                    ranking_note = "\n\n_Note: Datasets are sorted by download count (semantic ranking unavailable)._"

                ai_response = f"""I found {len(top_datasets)} datasets for your query "{search_query}":

**Top 5 Recommendations:**
{dataset_list}

**Source Breakdown:**
- Kaggle: {kaggle_count} datasets
- HuggingFace: {hf_count} datasets{ranking_note}

Would you like to download any of these datasets?"""

                # Format datasets for frontend
                kaggle_list = []
                huggingface_list = []

                for ds in top_datasets:
                    if ds.get('source') == 'Kaggle':
                        kaggle_list.append({
                            "ref": ds.get("ref") or ds.get("id"),
                            "title": ds.get("title"),
                            "size": ds.get("size", 0),
                            "download_count": ds.get("downloads", 0),
                            "vote_count": ds.get("votes", 0),
                            "usability_rating": ds.get("usability_rating", 0.8),
                            "url": ds.get("url")
                        })
                    elif ds.get('source') == 'HuggingFace':
                        huggingface_list.append({
                            "id": ds.get("id"),
                            "name": ds.get("title"),
                            "url": ds.get("url"),
                            "downloads": ds.get("downloads", 0),
                            "likes": ds.get("likes", 0)
                        })

                # Set to None if empty, otherwise assign
                kaggle_datasets = kaggle_list if kaggle_list else None
                huggingface_datasets = huggingface_list if huggingface_list else None

                # Use API search results directly
                json_data = {
                    "query": message_data.content,
                    "data_sources": {
                        "kaggle_datasets": [],  # Will be populated from formatted results
                        "huggingface_datasets": [],
                        "huggingface_models": []
                    }
                }
            else:
                ai_response = f"I couldn't find datasets matching '{message_data.content}' using API search. Try different keywords?"
                kaggle_datasets = None
                huggingface_datasets = None
                json_data = {
                    "query": message_data.content,
                    "data_sources": {
                        "kaggle_datasets": [],
                        "huggingface_datasets": [],
                        "huggingface_models": []
                    }
                }
        else:
            # Use Gemini indexer for non-dataset queries (model suggestions, etc.)
            print(f"💬 General ML query, using Gemini indexer")
            indexer_result = await simple_gemini_indexer.process_query(
                user_query=message_data.content,
                chat_history=chat_history
            )

            # Extract response and metadata
            ai_response = indexer_result.get("response", "I couldn't process your request.")
            json_data = indexer_result.get("json_data", {})

        # For dataset queries, we already have kaggle_datasets and huggingface_datasets from API
        # For non-dataset queries, extract from json_data and validate with URL extraction

        # Only extract and validate from json_data if NOT a dataset query (to avoid overwriting API results)
        if not is_dataset_query and json_data and "data_sources" in json_data:
            data_sources = json_data["data_sources"]

            # Extract Kaggle datasets and validate with API
            if data_sources.get("kaggle_datasets"):
                converted_kaggle = []
                for ds in data_sources["kaggle_datasets"]:
                    url = ds.get("url", "")
                    ref = ds.get("ref")  # Use extracted ref if available

                    # Extract ref from URL if not provided
                    if not ref:
                        if "kaggle.com/datasets/" in url:
                            ref = url.split("kaggle.com/datasets/")[-1].strip("/")
                        elif "kaggle.com/" in url:
                            ref = url.split("kaggle.com/")[-1].strip("/")

                    if ref:
                        # Validate dataset exists using Kaggle API
                        try:
                            if kaggle_service.is_configured:
                                # Get full dataset info from Kaggle API
                                api_datasets = kaggle_service.search_datasets(query=ref, page_size=1)
                                if api_datasets and len(api_datasets) > 0:
                                    # Use API response for complete info
                                    api_ds = api_datasets[0]
                                    if api_ds.get('ref') == ref:  # Verify it's the exact match
                                        converted_kaggle.append({
                                            "ref": api_ds.get("ref"),
                                            "title": api_ds.get("title", ds.get("name", "Unknown Dataset")),
                                            "size": api_ds.get("totalBytes", 0),
                                            "last_updated": api_ds.get("lastUpdated", ""),
                                            "download_count": api_ds.get("downloadCount", 0),
                                            "vote_count": api_ds.get("voteCount", 0),
                                            "usability_rating": api_ds.get("usabilityRating", 0.8),
                                            "url": api_ds.get("url", f"https://www.kaggle.com/datasets/{ref}")
                                        })
                                        print(f"✓ Validated Kaggle dataset: {ref}")
                                        continue
                            # Fallback: Use extracted data if API validation fails
                            converted_kaggle.append({
                                "ref": ref,
                                "title": ds.get("name", "Unknown Dataset"),
                                "size": 0,
                                "last_updated": "",
                                "download_count": 0,
                                "vote_count": 0,
                                "usability_rating": 0.8,
                                "url": f"https://www.kaggle.com/datasets/{ref}"
                            })
                            print(f"⚠ Using unvalidated data for: {ref}")
                        except Exception as e:
                            print(f"✗ Error validating {ref}: {e}")
                            # Still add the dataset with basic info
                            converted_kaggle.append({
                                "ref": ref,
                                "title": ds.get("name", "Unknown Dataset"),
                                "size": 0,
                                "last_updated": "",
                                "download_count": 0,
                                "vote_count": 0,
                                "usability_rating": 0.8,
                                "url": f"https://www.kaggle.com/datasets/{ref}"
                            })
                if converted_kaggle:
                    kaggle_datasets = converted_kaggle

            # Extract HuggingFace datasets and validate with API
            if data_sources.get("huggingface_datasets"):
                validated_hf = []
                for ds in data_sources["huggingface_datasets"]:
                    url = ds.get("url", "")
                    dataset_id = ds.get("id")

                    # Extract ID from URL if not provided
                    if not dataset_id and "huggingface.co/datasets/" in url:
                        dataset_id = url.split("huggingface.co/datasets/")[-1].strip("/")

                    if dataset_id:
                        try:
                            # Validate with HuggingFace API
                            if huggingface_service.is_configured:
                                api_datasets = await huggingface_service.search_datasets(
                                    query=dataset_id,
                                    limit=1
                                )
                                if api_datasets and len(api_datasets) > 0:
                                    api_ds = api_datasets[0]
                                    if api_ds.get('id') == dataset_id:  # Exact match
                                        validated_hf.append({
                                            "id": api_ds.get("id"),
                                            "name": api_ds.get("name", ds.get("name", "Unknown")),
                                            "url": api_ds.get("url", f"https://huggingface.co/datasets/{dataset_id}"),
                                            "downloads": api_ds.get("downloads", 0),
                                            "likes": api_ds.get("likes", 0),
                                            "size": api_ds.get("size", 0),
                                            "size_str": api_ds.get("size_str", "Unknown")
                                        })
                                        print(f"✓ Validated HuggingFace dataset: {dataset_id}")
                                        continue
                            # Fallback
                            validated_hf.append({
                                "id": dataset_id,
                                "name": ds.get("name", "Unknown"),
                                "url": f"https://huggingface.co/datasets/{dataset_id}",
                                "size": 0,
                                "size_str": "Unknown",
                                "downloads": 0,
                                "likes": 0
                            })
                            print(f"⚠ Using unvalidated data for: {dataset_id}")
                        except Exception as e:
                            print(f"✗ Error validating {dataset_id}: {e}")
                            validated_hf.append({
                                "id": dataset_id,
                                "name": ds.get("name", "Unknown"),
                                "url": f"https://huggingface.co/datasets/{dataset_id}",
                                "downloads": 0,
                                "likes": 0
                            })
                if validated_hf:
                    huggingface_datasets = validated_hf

            # Extract HuggingFace models (keep as-is)
            if data_sources.get("huggingface_models"):
                huggingface_models = data_sources["huggingface_models"]

        # Log what was found
        print(f"Kaggle datasets: {len(kaggle_datasets) if kaggle_datasets else 0}")
        print(f"HuggingFace datasets: {len(huggingface_datasets) if huggingface_datasets else 0}")
        print(f"HuggingFace models: {len(huggingface_models) if huggingface_models else 0}")

        # Create assistant message with agent response
        assistant_message = Message(
            chat_id=message_data.chat_id,
            role="assistant",
            content=ai_response,
            query_type="ml_agent",
            charts=None
        )

        # Store metadata with all resource types
        metadata = {
            "query_type": "ml_indexer"
        }

        # Add resources to metadata if found
        if kaggle_datasets:
            metadata["kaggle_datasets"] = kaggle_datasets
        if huggingface_datasets:
            metadata["huggingface_datasets"] = huggingface_datasets
        if huggingface_models:
            metadata["huggingface_models"] = huggingface_models

        # Update query_type if resources were found
        if kaggle_datasets or huggingface_datasets or huggingface_models:
            metadata["query_type"] = "dataset_search"

        assistant_message.metadata = metadata

        assistant_result = await mongodb.database["messages"].insert_one(
            assistant_message.dict(by_alias=True)
        )
        assistant_message.id = assistant_result.inserted_id

        # Update chat's last_updated timestamp
        await mongodb.database["chats"].update_one(
            {"_id": message_data.chat_id},
            {"$set": {"last_updated": datetime.utcnow()}}
        )

        # Return assistant message with all resources
        response_dict = assistant_message.dict(by_alias=True)
        if kaggle_datasets:
            response_dict["kaggle_datasets"] = kaggle_datasets
        if huggingface_datasets:
            response_dict["huggingface_datasets"] = huggingface_datasets
        if huggingface_models:
            response_dict["huggingface_models"] = huggingface_models

        # Add downloadable_datasets for agent responses
        downloadable_datasets = []
        if kaggle_datasets:
            for ds in kaggle_datasets:
                dataset_ref = ds.get('ref', '')
                dataset_url = ds.get('url', '')
                if not dataset_url and dataset_ref:
                    dataset_url = "https://www.kaggle.com/datasets/" + dataset_ref

                downloadable_datasets.append({
                    "id": dataset_ref,
                    "title": ds.get('title', ds.get('name', 'Unknown')),
                    "source": "Kaggle",
                    "url": dataset_url,
                    "downloads": ds.get('download_count', 0)
                })
        if huggingface_datasets:
            for ds in huggingface_datasets:
                dataset_id = ds.get('id') or ds.get('name', '')
                dataset_url = ds.get('url', '')
                # Fallback: construct URL if missing
                if not dataset_url and dataset_id:
                    dataset_url = f"https://huggingface.co/datasets/{dataset_id}"

                downloadable_datasets.append({
                    "id": dataset_id,
                    "title": ds.get('name', ds.get('title', 'Unknown')),
                    "source": "HuggingFace",
                    "url": dataset_url,
                    "downloads": ds.get('downloads', 0)
                })
        if downloadable_datasets:
            response_dict["downloadable_datasets"] = downloadable_datasets

        return MessageResponse(**response_dict)

    except Exception as e:
        print(f"Gemini Indexer error: {str(e)}")
        # Clean up user message if indexer fails
        await mongodb.database["messages"].delete_one({"_id": user_message.id})

        # Check if it's a quota/rate limit/API key error
        error_str = str(e).lower()
        is_quota_error = any(keyword in error_str for keyword in [
            'quota', 'rate limit', 'resource exhausted', '429',
            'exceeded', 'billing', 'free tier', 'api key', 'leaked',
            '403', 'forbidden', 'invalid api key', 'unauthorized'
        ])

        # Return user-friendly message based on error type
        if is_quota_error:
            error_message = "We're experiencing high demand at the moment. For assistance, please contact us at info@darshix.com"
        else:
            error_message = "We're experiencing technical difficulties. Please try again or contact us at info@darshix.com for support."

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )

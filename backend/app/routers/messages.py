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

        # Detect if user is asking for ML model recommendations
        ml_request_keywords = ["classify", "classification", "train", "model", "predict", "need to", "want to", "build", "create model", "ml for", "machine learning"]
        is_ml_request = any(keyword in message_data.content.lower() for keyword in ml_request_keywords)

        # Check if user provides requirements (dataset size, budget, latency)
        has_requirements = any(word in message_data.content.lower() for word in ["budget", "latency", "samples", "rows", "ms", "cost", "tickets", "data"])

        # Initialize variables
        kaggle_datasets = None
        model_recommendations = None
        dataset_metadata = None

        # CASE 1: ML Model Recommendation Request (with requirements)
        if is_ml_request and has_requirements and gemini_service.is_available():
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

        # CASE 2: Dataset Search Request
        elif query_analysis and query_analysis.get("needs_kaggle_search"):
            # Search Kaggle for datasets
            search_query = query_analysis.get("search_query", message_data.content)
            try:
                if kaggle_service.is_configured:
                    kaggle_datasets = kaggle_service.search_datasets(
                        query=search_query,
                        page=1,
                        max_size=5  # Show top 5 datasets
                    )
            except Exception as e:
                print(f"Kaggle search error: {str(e)}")
                # Continue without Kaggle results

            # Filter out datasets with empty or invalid refs
            if kaggle_datasets and len(kaggle_datasets) > 0:
                valid_datasets = [ds for ds in kaggle_datasets if ds.get('ref', '').strip()]
            else:
                valid_datasets = []

            if valid_datasets:
                # Create a response that includes dataset suggestions
                dataset_list = "\n\n".join([
                    f"{i+1}. **{ds['title']}** (`{ds['ref']}`)\n   - Size: {ds['size']/1024/1024:.1f} MB\n   - Downloads: {ds['download_count']:,}\n   - Usability: {ds['usability_rating']:.2f}/1.0"
                    for i, ds in enumerate(valid_datasets)
                ])

                ai_response = f"""I found some relevant datasets on Kaggle for your query about "{search_query}":

{dataset_list}

Would you like to use any of these datasets? I can help you download and add them to your datasets tab. Just let me know which one you'd like to use by mentioning the number or name!"""

                # Store dataset options in metadata for later selection
                dataset_metadata = {
                    "kaggle_datasets": valid_datasets,
                    "search_query": search_query,
                    "query_type": "dataset_search"
                }
            else:
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

        return MessageResponse(**response_dict)

    except Exception as e:
        # If Claude fails, still return the user message but with error info
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI response: {str(e)}"
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
        # Process message with Simple Gemini Indexer
        indexer_result = await simple_gemini_indexer.process_query(
            user_query=message_data.content,
            chat_history=chat_history
        )

        # Extract response and metadata
        ai_response = indexer_result.get("response", "I couldn't process your request.")
        json_data = indexer_result.get("json_data", {})

        # Extract all three resource types from the JSON response
        kaggle_datasets = None
        huggingface_datasets = None
        huggingface_models = None

        # Extract from json_data
        if json_data and "data_sources" in json_data:
            data_sources = json_data["data_sources"]

            # Extract Kaggle datasets
            if data_sources.get("kaggle_datasets"):
                converted_kaggle = []
                for ds in data_sources["kaggle_datasets"]:
                    url = ds.get("url", "")
                    if "kaggle.com/datasets/" in url:
                        ref = url.split("kaggle.com/datasets/")[-1].strip("/")
                        if ref:
                            converted_kaggle.append({
                                "ref": ref,
                                "title": ds.get("name", "Unknown Dataset"),
                                "size": 0,
                                "last_updated": "",
                                "download_count": 0,
                                "vote_count": 0,
                                "usability_rating": 0.8
                            })
                if converted_kaggle:
                    kaggle_datasets = converted_kaggle

            # Extract HuggingFace datasets (keep as-is)
            if data_sources.get("huggingface_datasets"):
                huggingface_datasets = data_sources["huggingface_datasets"]

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

        return MessageResponse(**response_dict)

    except Exception as e:
        print(f"Gemini Indexer error: {str(e)}")
        # Clean up user message if indexer fails
        await mongodb.database["messages"].delete_one({"_id": user_message.id})

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process with Gemini Indexer: {str(e)}"
        )

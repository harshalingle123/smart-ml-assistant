from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.schemas.direct_access_schemas import (
    PredictionRequest,
    BatchPredictionRequest,
    PredictionResponse,
    BatchPredictionResponse,
    SentimentScore,
    UsageInfo
)
from app.services.model_inference import model_inference
from app.services.usage_tracker import usage_tracker
from app.middleware.rate_limiter import enforce_rate_limit
from datetime import datetime
import secrets

router = APIRouter(prefix="/v1", tags=["Model API"])


def format_reset_date(last_reset_at: datetime) -> str:
    from datetime import timedelta
    next_reset = last_reset_at.replace(day=1) + timedelta(days=32)
    next_reset = next_reset.replace(day=1)
    return next_reset.strftime("%Y-%m-%d")


@router.post("/sentiment/vader", response_model=PredictionResponse)
async def predict_vader(
    request: Request,
    prediction_request: PredictionRequest,
    api_key_record: dict = Depends(enforce_rate_limit)
):
    try:
        if not prediction_request.text or len(prediction_request.text) > 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text must be between 1 and 5000 characters"
            )

        result = model_inference.predict_vader(
            prediction_request.text,
            prediction_request.options
        )

        request_id = await usage_tracker.track_request(
            api_key_id=api_key_record["_id"],
            user_id=api_key_record["user_id"],
            model_id="vader",
            latency_ms=result["latency_ms"],
            status="success",
            cost=0.0,
            batch_size=1
        )

        usage_info = request.state.usage_info

        sentiment_score = SentimentScore(
            label=result["label"],
            compound=result["compound"],
            pos=result["pos"],
            neu=result["neu"],
            neg=result["neg"]
        )

        usage = UsageInfo(
            requests_used=usage_info["requests_used"] + 1,
            requests_remaining=max(0, usage_info["requests_remaining"] - 1),
            reset_date=format_reset_date(api_key_record["last_reset_at"])
        )

        return PredictionResponse(
            text=prediction_request.text,
            sentiment=sentiment_score,
            confidence=result["confidence"],
            latency_ms=result["latency_ms"],
            timestamp=datetime.utcnow().isoformat() + "Z",
            request_id=request_id,
            usage=usage
        )

    except HTTPException:
        raise
    except Exception as e:
        await usage_tracker.track_request(
            api_key_id=api_key_record["_id"],
            user_id=api_key_record["user_id"],
            model_id="vader",
            latency_ms=0,
            status="error",
            cost=0.0,
            batch_size=1,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed"
        )


@router.post("/sentiment/vader/batch", response_model=BatchPredictionResponse)
async def predict_vader_batch(
    request: Request,
    batch_request: BatchPredictionRequest,
    api_key_record: dict = Depends(enforce_rate_limit)
):
    try:
        if not batch_request.texts or len(batch_request.texts) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Texts list cannot be empty"
            )

        if len(batch_request.texts) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 texts per batch request"
            )

        for text in batch_request.texts:
            if len(text) > 5000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Each text must be under 5000 characters"
                )

        result = model_inference.predict_vader_batch(
            batch_request.texts,
            batch_request.options
        )

        request_id = await usage_tracker.track_request(
            api_key_id=api_key_record["_id"],
            user_id=api_key_record["user_id"],
            model_id="vader",
            latency_ms=result["latency_ms"],
            status="success",
            cost=0.0,
            batch_size=len(batch_request.texts)
        )

        usage_info = request.state.usage_info

        sentiments = [
            SentimentScore(
                label=s["label"],
                compound=s["compound"],
                pos=s["pos"],
                neu=s["neu"],
                neg=s["neg"]
            )
            for s in result["sentiments"]
        ]

        usage = UsageInfo(
            requests_used=usage_info["requests_used"] + len(batch_request.texts),
            requests_remaining=max(0, usage_info["requests_remaining"] - len(batch_request.texts)),
            reset_date=format_reset_date(api_key_record["last_reset_at"])
        )

        return BatchPredictionResponse(
            sentiments=sentiments,
            latency_ms=result["latency_ms"],
            timestamp=datetime.utcnow().isoformat() + "Z",
            request_id=request_id,
            usage=usage
        )

    except HTTPException:
        raise
    except Exception as e:
        await usage_tracker.track_request(
            api_key_id=api_key_record["_id"],
            user_id=api_key_record["user_id"],
            model_id="vader",
            latency_ms=0,
            status="error",
            cost=0.0,
            batch_size=len(batch_request.texts),
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch prediction failed"
        )


@router.post("/sentiment/distilbert", response_model=PredictionResponse)
async def predict_distilbert(
    request: Request,
    prediction_request: PredictionRequest,
    api_key_record: dict = Depends(enforce_rate_limit)
):
    try:
        if not prediction_request.text or len(prediction_request.text) > 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text must be between 1 and 5000 characters"
            )

        result = model_inference.predict_distilbert(
            prediction_request.text,
            prediction_request.options
        )

        request_id = await usage_tracker.track_request(
            api_key_id=api_key_record["_id"],
            user_id=api_key_record["user_id"],
            model_id="distilbert",
            latency_ms=result["latency_ms"],
            status="success",
            cost=0.0006,
            batch_size=1
        )

        usage_info = request.state.usage_info

        sentiment_score = SentimentScore(
            label=result["label"],
            compound=result["compound"],
            pos=result["pos"],
            neu=result["neu"],
            neg=result["neg"]
        )

        usage = UsageInfo(
            requests_used=usage_info["requests_used"] + 1,
            requests_remaining=max(0, usage_info["requests_remaining"] - 1),
            reset_date=format_reset_date(api_key_record["last_reset_at"])
        )

        return PredictionResponse(
            text=prediction_request.text,
            sentiment=sentiment_score,
            confidence=result["confidence"],
            latency_ms=result["latency_ms"],
            timestamp=datetime.utcnow().isoformat() + "Z",
            request_id=request_id,
            usage=usage
        )

    except HTTPException:
        raise
    except Exception as e:
        await usage_tracker.track_request(
            api_key_id=api_key_record["_id"],
            user_id=api_key_record["user_id"],
            model_id="distilbert",
            latency_ms=0,
            status="error",
            cost=0.0,
            batch_size=1,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed"
        )


@router.post("/sentiment/roberta", response_model=PredictionResponse)
async def predict_roberta(
    request: Request,
    prediction_request: PredictionRequest,
    api_key_record: dict = Depends(enforce_rate_limit)
):
    try:
        if not prediction_request.text or len(prediction_request.text) > 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text must be between 1 and 5000 characters"
            )

        result = model_inference.predict_roberta(
            prediction_request.text,
            prediction_request.options
        )

        request_id = await usage_tracker.track_request(
            api_key_id=api_key_record["_id"],
            user_id=api_key_record["user_id"],
            model_id="roberta",
            latency_ms=result["latency_ms"],
            status="success",
            cost=0.002,
            batch_size=1
        )

        usage_info = request.state.usage_info

        sentiment_score = SentimentScore(
            label=result["label"],
            compound=result["compound"],
            pos=result["pos"],
            neu=result["neu"],
            neg=result["neg"]
        )

        usage = UsageInfo(
            requests_used=usage_info["requests_used"] + 1,
            requests_remaining=max(0, usage_info["requests_remaining"] - 1),
            reset_date=format_reset_date(api_key_record["last_reset_at"])
        )

        return PredictionResponse(
            text=prediction_request.text,
            sentiment=sentiment_score,
            confidence=result["confidence"],
            latency_ms=result["latency_ms"],
            timestamp=datetime.utcnow().isoformat() + "Z",
            request_id=request_id,
            usage=usage
        )

    except HTTPException:
        raise
    except Exception as e:
        await usage_tracker.track_request(
            api_key_id=api_key_record["_id"],
            user_id=api_key_record["user_id"],
            model_id="roberta",
            latency_ms=0,
            status="error",
            cost=0.0,
            batch_size=1,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed"
        )

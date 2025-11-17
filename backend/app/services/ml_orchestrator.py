from typing import Dict, List, Optional, Any
import google.generativeai as genai
from app.core.config import settings
from app.mongodb import mongodb
from app.services.huggingface_service import huggingface_service
from bson import ObjectId


class MLOrchestrator:

    def __init__(self):
        self.model = None
        if settings.GOOGLE_GEMINI_API_KEY:
            genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
            try:
                self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
            except Exception as e:
                print(f"Failed to load {settings.GEMINI_MODEL}, falling back to gemini-1.5-flash: {e}")
                try:
                    self.model = genai.GenerativeModel("gemini-1.5-flash")
                except Exception as e2:
                    print(f"Failed to load gemini-1.5-flash, trying gemini-pro: {e2}")
                    self.model = genai.GenerativeModel("gemini-pro")

    def is_available(self) -> bool:
        return self.model is not None

    async def recommend_models(
        self,
        task_description: str,
        dataset_id: Optional[str] = None,
        requirements: Optional[Dict[str, Any]] = None,
        budget: Optional[float] = None,
        priority: str = "balanced"
    ) -> Dict[str, Any]:

        if not self.is_available():
            raise ValueError("Gemini API is not configured")

        dataset_info = ""
        if dataset_id and ObjectId.is_valid(dataset_id):
            dataset = await mongodb.database["datasets"].find_one({"_id": ObjectId(dataset_id)})
            if dataset:
                dataset_info = f"\nDataset: {dataset['name']} - {dataset['row_count']} rows, {dataset['column_count']} columns"

        task_type = self._detect_task_type(task_description)

        hf_models = await huggingface_service.search_models(
            task=task_type,
            limit=10
        )

        prebuilt_models = await mongodb.database["prebuilt_models"].find({
            "task_type": task_type
        }).limit(3).to_list(length=3)

        prompt = f"""You are an ML expert advisor. Analyze this ML task and recommend the best models.

Task Description: {task_description}
{dataset_info}
Priority: {priority} (speed/cost/accuracy)
Budget: ${budget if budget else 'not specified'}
Requirements: {requirements if requirements else 'none specified'}

Available HuggingFace Models:
{self._format_hf_models(hf_models[:5])}

Available Pre-built Models:
{self._format_prebuilt_models(prebuilt_models)}

Provide:
1. Top 3 recommended models (with model_id, reasoning, pros/cons)
2. Whether training is needed or pre-built is sufficient
3. Estimated cost (low/medium/high)
4. Expected accuracy range
5. One-sentence summary

Format as JSON."""

        try:
            response = self.model.generate_content(prompt)

            recommendation = {
                "recommended_models": self._extract_top_models(hf_models, prebuilt_models, priority),
                "reasoning": response.text[:500] if response.text else "Unable to generate detailed reasoning",
                "estimated_cost": self._estimate_cost(task_type, budget),
                "estimated_accuracy": self._estimate_accuracy(priority),
                "training_required": self._needs_training(task_description, dataset_id),
                "prebuilt_alternative": prebuilt_models[0]["name"] if prebuilt_models else None
            }

            return recommendation

        except Exception as e:
            return {
                "recommended_models": self._extract_top_models(hf_models, prebuilt_models, priority),
                "reasoning": f"Recommendation based on task type and model popularity. {str(e)[:100]}",
                "estimated_cost": self._estimate_cost(task_type, budget),
                "estimated_accuracy": self._estimate_accuracy(priority),
                "training_required": self._needs_training(task_description, dataset_id),
                "prebuilt_alternative": prebuilt_models[0]["name"] if prebuilt_models else None
            }

    async def make_decision(
        self,
        task_description: str,
        dataset_id: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:

        if not self.is_available():
            raise ValueError("Gemini API is not configured")

        if not ObjectId.is_valid(dataset_id):
            raise ValueError("Invalid dataset ID")

        dataset = await mongodb.database["datasets"].find_one({"_id": ObjectId(dataset_id)})
        if not dataset:
            raise ValueError("Dataset not found")

        task_type = self._detect_task_type(task_description)

        hf_models = await huggingface_service.search_models(task=task_type, limit=5)
        prebuilt_models = await mongodb.database["prebuilt_models"].find({
            "task_type": task_type
        }).limit(3).to_list(length=3)

        prompt = f"""You are an AI decision engine. Make the optimal model selection decision.

Task: {task_description}
Dataset: {dataset['name']} ({dataset['row_count']} rows, {dataset['column_count']} columns)
Constraints: {constraints if constraints else 'none'}

HuggingFace Options: {len(hf_models)} available
Pre-built Options: {len(prebuilt_models)} available

Analyze and decide:
1. Best single model to use (provide model_id)
2. Justification (2-3 sentences)
3. Confidence score (0-1)
4. Top 2 alternatives
5. Next steps (3 action items)

Consider: accuracy, speed, cost, ease of use."""

        try:
            response = self.model.generate_content(prompt)

            selected_model = hf_models[0] if hf_models else (prebuilt_models[0] if prebuilt_models else None)

            if not selected_model:
                raise ValueError("No suitable models found")

            decision = {
                "decision": "use_pretrained" if not self._needs_training(task_description, dataset_id) else "fine_tune_required",
                "selected_model": {
                    "model_id": selected_model.get("model_id") or str(selected_model.get("_id")),
                    "name": selected_model.get("name"),
                    "type": "huggingface" if "model_id" in selected_model else "prebuilt",
                    "downloads": selected_model.get("downloads", 0),
                    "task": task_type
                },
                "reasoning": response.text[:300] if response.text else "Selected based on popularity and task match",
                "confidence_score": self._calculate_confidence(selected_model, dataset),
                "alternatives": [
                    {
                        "model_id": m.get("model_id"),
                        "name": m.get("name"),
                        "score": round(m.get("downloads", 0) / 1000000, 2)
                    }
                    for m in hf_models[1:3]
                ],
                "next_steps": self._generate_next_steps(selected_model, dataset)
            }

            return decision

        except Exception as e:
            selected_model = hf_models[0] if hf_models else prebuilt_models[0]

            return {
                "decision": "use_pretrained",
                "selected_model": {
                    "model_id": selected_model.get("model_id") or str(selected_model.get("_id")),
                    "name": selected_model.get("name"),
                    "type": "huggingface" if "model_id" in selected_model else "prebuilt"
                },
                "reasoning": f"Automated selection based on task match. {str(e)[:100]}",
                "confidence_score": 0.7,
                "alternatives": [],
                "next_steps": ["Deploy selected model", "Test with sample data", "Monitor performance"]
            }

    def _detect_task_type(self, description: str) -> str:
        desc_lower = description.lower()

        if any(word in desc_lower for word in ["sentiment", "emotion", "opinion"]):
            return "text-classification"
        elif any(word in desc_lower for word in ["summarize", "summary", "summarization"]):
            return "summarization"
        elif any(word in desc_lower for word in ["translate", "translation"]):
            return "translation"
        elif any(word in desc_lower for word in ["question", "qa", "answer"]):
            return "question-answering"
        elif any(word in desc_lower for word in ["classify", "classification", "categorize"]):
            return "text-classification"
        elif any(word in desc_lower for word in ["image", "vision", "object detection"]):
            return "image-classification"
        else:
            return "text-classification"

    def _format_hf_models(self, models: List[Dict]) -> str:
        return "\n".join([
            f"- {m['name']} ({m['model_id']}): {m['downloads']} downloads, {m['likes']} likes"
            for m in models[:5]
        ])

    def _format_prebuilt_models(self, models: List[Dict]) -> str:
        if not models:
            return "None available"
        return "\n".join([
            f"- {m['name']}: {m['description'][:50]}..."
            for m in models
        ])

    def _extract_top_models(
        self,
        hf_models: List[Dict],
        prebuilt_models: List[Dict],
        priority: str
    ) -> List[Dict[str, Any]]:

        recommendations = []

        if priority == "speed" and prebuilt_models:
            for m in prebuilt_models[:2]:
                recommendations.append({
                    "model_id": str(m["_id"]),
                    "name": m["name"],
                    "type": "prebuilt",
                    "score": 0.95,
                    "reason": "Pre-built, instant deployment"
                })

        for m in hf_models[:3]:
            recommendations.append({
                "model_id": m["model_id"],
                "name": m["name"],
                "type": "huggingface",
                "score": min(0.9, m["downloads"] / 1000000),
                "reason": f"{m['downloads']} downloads, popular choice"
            })

        return sorted(recommendations, key=lambda x: x["score"], reverse=True)[:3]

    def _estimate_cost(self, task_type: str, budget: Optional[float]) -> float:
        base_costs = {
            "text-classification": 10.0,
            "summarization": 25.0,
            "translation": 20.0,
            "question-answering": 15.0,
            "image-classification": 30.0
        }

        cost = base_costs.get(task_type, 15.0)

        if budget and budget < cost:
            return budget * 0.8

        return cost

    def _estimate_accuracy(self, priority: str) -> str:
        accuracy_map = {
            "speed": "70-80%",
            "cost": "75-85%",
            "accuracy": "85-95%",
            "balanced": "80-90%"
        }
        return accuracy_map.get(priority, "80-90%")

    def _needs_training(self, task_description: str, dataset_id: Optional[str]) -> bool:
        if not dataset_id:
            return False

        custom_keywords = ["custom", "specific", "unique", "specialized", "domain-specific", "proprietary"]
        return any(keyword in task_description.lower() for keyword in custom_keywords)

    def _calculate_confidence(self, model: Dict, dataset: Dict) -> float:
        confidence = 0.7

        if model.get("downloads", 0) > 1000000:
            confidence += 0.1

        if model.get("likes", 0) > 100:
            confidence += 0.1

        if dataset.get("row_count", 0) > 1000:
            confidence += 0.1

        return min(confidence, 0.99)

    def _generate_next_steps(self, model: Dict, dataset: Dict) -> List[str]:
        return [
            f"Deploy {model.get('name')} model",
            f"Test with {dataset.get('name')} dataset",
            "Monitor accuracy metrics",
            "Set up API endpoint",
            "Configure auto-scaling"
        ]


ml_orchestrator = MLOrchestrator()

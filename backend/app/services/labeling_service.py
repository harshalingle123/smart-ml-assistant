import asyncio
import json
import logging
import base64
import io
from typing import List, Dict, Optional, Any
from datetime import datetime

import google.generativeai as genai
from PIL import Image

from app.core.config import settings
from app.models.mongodb_models import LabelData

logger = logging.getLogger(__name__)

class LabelingService:
    """Service for AI-powered file labeling using Google Gemini"""

    def __init__(self):
        """Initialize the labeling service with Gemini"""
        self.model = None
        self._initialize_gemini()

    def _initialize_gemini(self):
        """Initialize Gemini API"""
        if not settings.GOOGLE_GEMINI_API_KEY:
            logger.warning("GOOGLE_GEMINI_API_KEY not set. Labeling service will be unavailable.")
            return

        try:
            genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
            # Use gemini-2.0-flash-exp for multimodal capabilities
            self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
            logger.info("Labeling service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini for labeling: {e}")

    def is_available(self) -> bool:
        """Check if the service is available"""
        return self.model is not None

    def _get_task_prompt(self, task: str, target_labels: Optional[List[str]] = None) -> str:
        """Generate task-specific prompt"""

        base_prompts = {
            "general_analysis": """Analyze this content comprehensively and provide:
- A concise summary
- Main topics/themes
- Key entities (people, organizations, locations)
- Overall sentiment (positive, negative, neutral)
- Any safety concerns or content flags""",

            "object_detection": """Detect and identify all objects in this image/video. For each object provide:
- Label (object name)
- Confidence score (0-1)
- Location description
- Bounding box coordinates [ymin, xmin, ymax, xmax] if possible""",

            "segmentation": """Perform semantic segmentation on this image/video. Identify distinct regions and provide:
- Region labels
- Confidence scores
- Descriptions of each segment""",

            "image_captioning": """Generate a detailed caption for this image that describes:
- Main subjects and objects
- Actions and relationships
- Setting and context
- Artistic style or mood (if applicable)""",

            "sentiment_analysis": """Analyze the sentiment of this content. Provide:
- Overall sentiment (positive, negative, neutral)
- Sentiment intensity (0-1 scale)
- Key phrases contributing to sentiment
- Emotional tone""",

            "transcription": """Transcribe this audio/video content. Provide:
- Full transcription
- Speaker diarization (if multiple speakers)
- Timestamps for key moments
- Summary of main points""",

            "entity_extraction": """Extract named entities from this content. For each entity provide:
- Entity name
- Entity type (PERSON, ORGANIZATION, LOCATION, DATE, etc.)
- Context/relevance""",

            "summarization": """Summarize this content concisely. Provide:
- Main summary (2-3 sentences)
- Key points (bullet list)
- Important details
- Conclusion or takeaway"""
        }

        prompt = base_prompts.get(task, base_prompts["general_analysis"])

        if target_labels:
            prompt += f"\n\nIMPORTANT: Classify this content using ONLY these labels: {', '.join(target_labels)}"
            prompt += "\nYour 'topics' field must ONLY contain values from this list."

        prompt += "\n\nProvide your response in strict JSON format with these fields:"
        prompt += "\n{\"summary\": string, \"sentiment\": string, \"objects\": [{\"label\": string, \"confidence\": number, \"location\": string, \"box_2d\": [number, number, number, number]}], \"topics\": [string], \"events\": [{\"timestamp\": string, \"description\": string}], \"entities\": [{\"name\": string, \"type\": string}], \"safety_flags\": [string]}"
        prompt += "\n\nOnly include fields that are relevant to the content type. Return valid JSON only, no markdown."

        return prompt

    async def generate_labels(
        self,
        file_content: bytes,
        media_type: str,
        task: str,
        filename: str,
        target_labels: Optional[List[str]] = None,
        text_content: Optional[str] = None,
    ) -> Optional[LabelData]:
        """
        Generate labels for a file using Gemini

        Args:
            file_content: File bytes
            media_type: Type of media (image, video, audio, text, pdf)
            task: Labeling task type
            filename: Original filename
            target_labels: Optional constrained vocabulary
            text_content: Optional text content for text files

        Returns:
            LabelData object or None if failed
        """
        if not self.is_available():
            raise ValueError("Labeling service is not available. Gemini API not configured.")

        prompt = self._get_task_prompt(task, target_labels)

        try:
            # Prepare content based on media type
            content_parts = [prompt]

            if media_type == "image":
                # Resize image if too large
                image = Image.open(io.BytesIO(file_content))

                # Resize to max 1536px width for optimization
                max_width = 1536
                if image.width > max_width:
                    ratio = max_width / image.width
                    new_size = (max_width, int(image.height * ratio))
                    image = image.resize(new_size, Image.Resampling.LANCZOS)

                # Convert to bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format=image.format or 'PNG')
                img_byte_arr = img_byte_arr.getvalue()

                content_parts.append({
                    "mime_type": "image/jpeg" if image.format == "JPEG" else "image/png",
                    "data": base64.b64encode(img_byte_arr).decode()
                })

            elif media_type == "video":
                # For video, upload to Gemini file API
                # Note: This is simplified - in production, you'd use the File API
                content_parts.append(f"\n\nVideo file: {filename}")
                content_parts.append("\nNote: Video analysis requires file upload - provide summary based on filename.")

            elif media_type == "audio":
                # Similar to video
                content_parts.append(f"\n\nAudio file: {filename}")
                content_parts.append("\nNote: Audio analysis requires file upload - provide summary based on filename.")

            elif media_type == "text":
                # Add text content directly
                if text_content:
                    content_parts.append(f"\n\nText content:\n{text_content[:800000]}")  # Max 800k chars
                else:
                    text = file_content.decode('utf-8', errors='ignore')
                    content_parts.append(f"\n\nText content:\n{text[:800000]}")

            elif media_type == "pdf":
                # For PDF, extract text (simplified - you'd use a PDF library)
                content_parts.append(f"\n\nPDF file: {filename}")
                content_parts.append("\nNote: PDF text extraction needed - provide summary based on filename.")

            # Generate with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = await asyncio.to_thread(
                        self.model.generate_content,
                        content_parts,
                        generation_config=genai.GenerationConfig(
                            temperature=0.1,
                            max_output_tokens=2048,
                        )
                    )

                    # Parse JSON response
                    response_text = response.text.strip()

                    # Remove markdown code blocks if present
                    if response_text.startswith("```json"):
                        response_text = response_text[7:]
                    if response_text.startswith("```"):
                        response_text = response_text[3:]
                    if response_text.endswith("```"):
                        response_text = response_text[:-3]
                    response_text = response_text.strip()

                    # Parse JSON
                    result_data = json.loads(response_text)

                    # Create LabelData object
                    label_data = LabelData(
                        summary=result_data.get("summary"),
                        sentiment=result_data.get("sentiment"),
                        objects=result_data.get("objects"),
                        topics=result_data.get("topics"),
                        events=result_data.get("events"),
                        entities=result_data.get("entities"),
                        safety_flags=result_data.get("safety_flags")
                    )

                    logger.info(f"Successfully labeled file: {filename}")
                    return label_data

                except genai.types.generation_types.StopCandidateException as e:
                    logger.warning(f"Gemini stopped generation (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return None

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Gemini response as JSON (attempt {attempt + 1}): {e}")
                    logger.error(f"Response was: {response.text[:500]}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    return None

                except Exception as e:
                    logger.error(f"Error during labeling (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    return None

            return None

        except Exception as e:
            logger.error(f"Failed to label file {filename}: {e}")
            return None

    async def get_label_suggestions(
        self,
        filenames: List[str],
        task: str
    ) -> List[str]:
        """
        Get AI-suggested labels based on filenames

        Args:
            filenames: List of filenames
            task: Labeling task type

        Returns:
            List of suggested label strings
        """
        if not self.is_available():
            return []

        try:
            prompt = f"""Based on these filenames and the task '{task}', suggest 8-12 relevant classification labels.

Filenames:
{chr(10).join(f'- {fn}' for fn in filenames[:20])}

Task: {task}

Provide a JSON array of suggested labels. Labels should be:
- Relevant to the content type indicated by filenames
- Specific and actionable
- Commonly used categories
- Diverse and comprehensive

Return ONLY a JSON array like: ["label1", "label2", "label3", ...]"""

            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=512,
                )
            )

            response_text = response.text.strip()

            # Remove markdown if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            suggestions = json.loads(response_text)

            if isinstance(suggestions, list):
                return suggestions[:12]  # Max 12 suggestions
            return []

        except Exception as e:
            logger.error(f"Failed to get label suggestions: {e}")
            return []

    async def refine_analysis(
        self,
        file_content: bytes,
        media_type: str,
        task: str,
        filename: str,
        verified_labels: List[str],
        text_content: Optional[str] = None
    ) -> Optional[LabelData]:
        """
        Re-analyze content after user manually adjusts labels

        Args:
            file_content: File bytes
            media_type: Type of media
            task: Labeling task
            filename: Original filename
            verified_labels: User-verified labels
            text_content: Optional text content

        Returns:
            Updated LabelData
        """
        # Similar to generate_labels but with verified labels enforced
        return await self.generate_labels(
            file_content=file_content,
            media_type=media_type,
            task=task,
            filename=filename,
            target_labels=verified_labels,
            text_content=text_content
        )


# Global instance
labeling_service = LabelingService()

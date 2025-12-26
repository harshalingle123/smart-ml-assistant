import asyncio
import json
import logging
from typing import List, Dict, Any, Union
from io import BytesIO

from PIL import Image

from app.services.gemini_service import gemini_service
from app.schemas.labeling_schemas import (
    LabelingConfig,
    LabelingTaskType,
    ImageLabel,
    TextLabel,
    EntityExtraction,
    Transcript,
    DetectedObject,
    Entity
)

logger = logging.getLogger(__name__)


class LabelingService:
    """Service for AI-powered data labeling using Google Gemini"""

    def __init__(self):
        """Initialize the labeling service with Gemini"""
        self.gemini_service = gemini_service
        self.max_retries = 3
        self.retry_delay_base = 2  # seconds

    async def label_images(
        self,
        image_files: List[tuple],  # List of (filename, bytes)
        config: LabelingConfig
    ) -> List[ImageLabel]:
        """
        Label images using Gemini vision capabilities

        Args:
            image_files: List of tuples (filename, image_bytes)
            config: Labeling configuration

        Returns:
            List of ImageLabel objects
        """
        results = []

        for filename, image_bytes in image_files:
            try:
                # Optimize image
                optimized_bytes = self._optimize_image(image_bytes)

                # Generate labels based on task type
                if config.task_type == LabelingTaskType.IMAGE_CLASSIFICATION:
                    label = await self._classify_image(filename, optimized_bytes, config)
                elif config.task_type == LabelingTaskType.OBJECT_DETECTION:
                    label = await self._detect_objects(filename, optimized_bytes, config)
                else:
                    raise ValueError(f"Unsupported task type for images: {config.task_type}")

                results.append(label)

            except Exception as e:
                logger.error(f"Error labeling image {filename}: {str(e)}")
                # Add error label
                results.append(ImageLabel(
                    filename=filename,
                    task_type=config.task_type.value,
                    classification="ERROR",
                    confidence=0.0
                ))

        return results

    async def label_text(
        self,
        texts: List[tuple],  # List of (filename/id, text_content)
        config: LabelingConfig
    ) -> List[TextLabel]:
        """
        Label text using Gemini

        Args:
            texts: List of tuples (identifier, text_content)
            config: Labeling configuration

        Returns:
            List of TextLabel objects
        """
        results = []

        for identifier, text_content in texts:
            try:
                if config.task_type == LabelingTaskType.TEXT_CLASSIFICATION:
                    label = await self._classify_text(text_content, config)
                elif config.task_type == LabelingTaskType.SENTIMENT_ANALYSIS:
                    label = await self._analyze_sentiment(text_content, config)
                else:
                    raise ValueError(f"Unsupported task type for text: {config.task_type}")

                results.append(label)

            except Exception as e:
                logger.error(f"Error labeling text {identifier}: {str(e)}")
                results.append(TextLabel(
                    text=text_content[:100],
                    label="ERROR",
                    confidence=0.0
                ))

        return results

    async def extract_entities(
        self,
        texts: List[tuple],  # List of (filename/id, text_content)
        config: LabelingConfig
    ) -> List[EntityExtraction]:
        """
        Extract named entities from text

        Args:
            texts: List of tuples (identifier, text_content)
            config: Labeling configuration

        Returns:
            List of EntityExtraction objects
        """
        results = []

        for identifier, text_content in texts:
            try:
                extraction = await self._extract_entities(text_content, config)
                results.append(extraction)

            except Exception as e:
                logger.error(f"Error extracting entities from {identifier}: {str(e)}")
                results.append(EntityExtraction(
                    text=text_content[:100],
                    entities=[]
                ))

        return results

    async def transcribe_audio_video(
        self,
        files: List[tuple],  # List of (filename, bytes)
        config: LabelingConfig
    ) -> List[Transcript]:
        """
        Transcribe audio/video files

        Note: This is a placeholder as Gemini's audio support may be limited

        Args:
            files: List of tuples (filename, file_bytes)
            config: Labeling configuration

        Returns:
            List of Transcript objects
        """
        results = []

        for filename, file_bytes in files:
            try:
                # For now, return a placeholder
                # In production, you would integrate with Gemini's audio API or another service
                results.append(Transcript(
                    filename=filename,
                    transcript="[Audio transcription requires additional setup]",
                    confidence=0.0,
                    summary="Audio transcription is not yet fully implemented"
                ))

            except Exception as e:
                logger.error(f"Error transcribing {filename}: {str(e)}")
                results.append(Transcript(
                    filename=filename,
                    transcript="ERROR",
                    confidence=0.0
                ))

        return results

    async def refine_labels(
        self,
        labels: List[Union[ImageLabel, TextLabel, EntityExtraction, Transcript]],
        feedback: str
    ) -> List[Union[ImageLabel, TextLabel, EntityExtraction, Transcript]]:
        """
        Refine labels based on user feedback

        Args:
            labels: Current labels
            feedback: User feedback or corrections

        Returns:
            Refined labels
        """
        try:
            # Build prompt for refinement
            prompt = self._build_refinement_prompt(labels, feedback)

            # Call Gemini
            response = await self._call_gemini_with_retry(prompt)

            # Parse and return refined labels
            # For simplicity, return original labels with added explanation
            # In production, you would parse the response and update labels
            return labels

        except Exception as e:
            logger.error(f"Error refining labels: {str(e)}")
            return labels

    def _optimize_image(self, image_bytes: bytes) -> bytes:
        """
        Optimize image for Gemini API
        - Resize to max 1536px
        - Convert to JPEG
        - Compress to reduce size
        """
        try:
            img = Image.open(BytesIO(image_bytes))

            # Resize if larger than 1536px
            max_size = 1536
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Convert to RGB (handle RGBA, grayscale, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Save as JPEG with compression
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()

        except Exception as e:
            logger.error(f"Error optimizing image: {str(e)}")
            return image_bytes

    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response by removing markdown code blocks"""
        # Remove markdown code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        return response.strip()

    async def _classify_image(
        self,
        filename: str,
        image_bytes: bytes,
        config: LabelingConfig
    ) -> ImageLabel:
        """Classify an image"""
        # Build prompt
        prompt = self._build_image_classification_prompt(config)

        # Call Gemini with image
        response = await self._call_gemini_with_image(prompt, image_bytes)

        # Clean and parse response
        try:
            cleaned_response = self._clean_json_response(response)
            data = json.loads(cleaned_response)
            return ImageLabel(
                filename=filename,
                task_type=config.task_type.value,
                classification=data.get("classification", "unknown"),
                scene_description=data.get("description"),
                confidence=data.get("confidence", 0.8)
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for {filename}: {response}")
            # Fallback: use text response as classification
            return ImageLabel(
                filename=filename,
                task_type=config.task_type.value,
                classification=response.split('\n')[0][:100] if response else "error",
                confidence=0.5
            )

    async def _detect_objects(
        self,
        filename: str,
        image_bytes: bytes,
        config: LabelingConfig
    ) -> ImageLabel:
        """Detect objects in an image"""
        prompt = self._build_object_detection_prompt(config)

        response = await self._call_gemini_with_image(prompt, image_bytes)

        try:
            cleaned_response = self._clean_json_response(response)
            data = json.loads(cleaned_response)
            objects = [
                DetectedObject(
                    label=obj.get("label", "unknown"),
                    confidence=obj.get("confidence", 0.8),
                    bounding_box=obj.get("bounding_box")
                )
                for obj in data.get("objects", [])
            ]

            return ImageLabel(
                filename=filename,
                task_type=config.task_type.value,
                objects=objects,
                scene_description=data.get("description"),
                confidence=data.get("confidence", 0.8)
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for {filename}: {response}")
            return ImageLabel(
                filename=filename,
                task_type=config.task_type.value,
                objects=[],
                scene_description=response[:200] if response else "error",
                confidence=0.5
            )

    async def _classify_text(
        self,
        text: str,
        config: LabelingConfig
    ) -> TextLabel:
        """Classify text"""
        prompt = self._build_text_classification_prompt(text, config)
        response = await self._call_gemini_with_retry(prompt)

        try:
            cleaned_response = self._clean_json_response(response)
            data = json.loads(cleaned_response)
            return TextLabel(
                text=text,
                label=data.get("label", "unknown"),
                confidence=data.get("confidence", 0.8),
                explanation=data.get("explanation")
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response}")
            return TextLabel(
                text=text,
                label=response.split('\n')[0][:50],
                confidence=0.7
            )

    async def _analyze_sentiment(
        self,
        text: str,
        config: LabelingConfig
    ) -> TextLabel:
        """Analyze sentiment of text"""
        prompt = self._build_sentiment_analysis_prompt(text, config)
        response = await self._call_gemini_with_retry(prompt)

        try:
            cleaned_response = self._clean_json_response(response)
            data = json.loads(cleaned_response)
            return TextLabel(
                text=text,
                label=data.get("label", "neutral"),
                sentiment=data.get("sentiment", "neutral"),
                confidence=data.get("confidence", 0.8),
                explanation=data.get("explanation")
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response}")
            # Fallback: simple sentiment detection
            response_lower = response.lower()
            if "positive" in response_lower:
                sentiment = "positive"
            elif "negative" in response_lower:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            return TextLabel(
                text=text,
                label=sentiment,
                sentiment=sentiment,
                confidence=0.7
            )

    async def _extract_entities(
        self,
        text: str,
        config: LabelingConfig
    ) -> EntityExtraction:
        """Extract named entities from text"""
        prompt = self._build_entity_extraction_prompt(text, config)
        response = await self._call_gemini_with_retry(prompt)

        try:
            cleaned_response = self._clean_json_response(response)
            data = json.loads(cleaned_response)
            entities = [
                Entity(
                    text=ent.get("text", ""),
                    type=ent.get("type", "UNKNOWN"),
                    start_index=ent.get("start_index", 0),
                    end_index=ent.get("end_index", 0),
                    confidence=ent.get("confidence", 0.8)
                )
                for ent in data.get("entities", [])
            ]

            return EntityExtraction(
                text=text,
                entities=entities,
                summary=data.get("summary")
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response}")
            return EntityExtraction(
                text=text,
                entities=[],
                summary=response[:200]
            )

    def _build_image_classification_prompt(self, config: LabelingConfig) -> str:
        """Build prompt for image classification"""
        prompt = "You are an expert image classifier. Analyze this image carefully and classify it."

        if config.target_labels:
            labels_str = ", ".join(config.target_labels)
            prompt += f"\n\nChoose ONLY from these categories: {labels_str}"
        else:
            prompt += "\n\nProvide a specific, accurate classification label for what you see in the image."

        prompt += "\n\nIMPORTANT: Respond ONLY with valid JSON in this exact format (no markdown, no code blocks):\n"
        prompt += '{"classification": "your_label_here", "confidence": 0.95, "description": "brief description of what you see"}'

        return prompt

    def _build_object_detection_prompt(self, config: LabelingConfig) -> str:
        """Build prompt for object detection"""
        prompt = "You are an expert object detector. Identify and list all distinct objects visible in this image."

        if config.target_labels:
            labels_str = ", ".join(config.target_labels)
            prompt += f"\n\nFocus primarily on detecting these objects: {labels_str}"
        else:
            prompt += "\n\nDetect all significant objects you can see."

        prompt += "\n\nIMPORTANT: Respond ONLY with valid JSON in this exact format (no markdown, no code blocks):\n"
        prompt += '{"objects": [{"label": "object_name", "confidence": 0.95}, {"label": "another_object", "confidence": 0.85}], "description": "overall scene description"}'

        return prompt

    def _build_text_classification_prompt(self, text: str, config: LabelingConfig) -> str:
        """Build prompt for text classification"""
        prompt = f"Classify the following text:\n\n{text}\n\n"

        if config.target_labels:
            labels_str = ", ".join(config.target_labels)
            prompt += f"Choose ONLY from these categories: {labels_str}\n\n"
        else:
            prompt += "Provide an appropriate category label for this text.\n\n"

        prompt += "IMPORTANT: Respond ONLY with valid JSON in this exact format (no markdown, no code blocks, no explanatory text):\n"
        prompt += '{"label": "category_name", "confidence": 0.95, "explanation": "brief reason for this classification"}'

        return prompt

    def _build_sentiment_analysis_prompt(self, text: str, config: LabelingConfig) -> str:
        """Build prompt for sentiment analysis"""
        prompt = f"Analyze the sentiment of this text:\n\n{text}\n\n"
        prompt += "IMPORTANT: Respond ONLY with valid JSON in this exact format (no markdown, no code blocks, no explanatory text):\n"
        prompt += '{"sentiment": "positive/negative/neutral", "label": "positive/negative/neutral", "confidence": 0.95, "explanation": "brief reason for this sentiment"}'

        return prompt

    def _build_entity_extraction_prompt(self, text: str, config: LabelingConfig) -> str:
        """Build prompt for entity extraction"""
        prompt = f"Extract all named entities from this text:\n\n{text}\n\n"
        prompt += "Identify entities such as: PERSON (people's names), ORG (organizations, companies), LOCATION (places, countries, cities), DATE (dates, times), MONEY (monetary amounts), PRODUCT (product names), etc.\n\n"
        prompt += "IMPORTANT: Respond ONLY with valid JSON in this exact format (no markdown, no code blocks, no explanatory text):\n"
        prompt += '{"entities": [{"text": "entity text", "type": "PERSON", "start_index": 0, "end_index": 10, "confidence": 0.95}], "summary": "brief summary of the text"}'

        return prompt

    def _build_refinement_prompt(
        self,
        labels: List[Any],
        feedback: str
    ) -> str:
        """Build prompt for label refinement"""
        labels_json = json.dumps([label.dict() if hasattr(label, 'dict') else label.model_dump() for label in labels], indent=2)
        prompt = f"Here are the current labels:\n\n{labels_json}\n\n"
        prompt += f"User feedback: {feedback}\n\n"
        prompt += "Please refine the labels based on this feedback and return the updated labels in the same JSON format."

        return prompt

    async def _call_gemini_with_retry(self, prompt: str) -> str:
        """Call Gemini API with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if not self.gemini_service.is_available():
                    raise RuntimeError("Gemini service is not available")

                response = await self.gemini_service.generate_response(
                    messages=[{"role": "user", "content": prompt}]
                )
                return response

            except Exception as e:
                error_msg = str(e).lower()
                if ("rate limit" in error_msg or "quota" in error_msg) and attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay_base ** (attempt + 1)
                    logger.warning(f"Rate limit hit, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    continue
                raise

    async def _call_gemini_with_image(self, prompt: str, image_bytes: bytes) -> str:
        """
        Call Gemini API with image using vision capabilities
        Uses inline image data approach
        """
        import google.generativeai as genai
        from PIL import Image
        from io import BytesIO

        for attempt in range(self.max_retries):
            try:
                if not self.gemini_service.is_available():
                    raise RuntimeError("Gemini service is not available")

                # Convert bytes to PIL Image
                image = Image.open(BytesIO(image_bytes))

                # Try different model names for vision (in order of preference)
                # Use the latest available Gemini models that support vision
                vision_model_names = [
                    'models/gemini-2.5-flash',  # Latest stable multimodal model
                    'models/gemini-flash-latest',  # Latest flash model
                    'models/gemini-2.0-flash',  # Gemini 2.0 Flash
                ]

                # Try each model until one works
                last_error = None
                for model_name in vision_model_names:
                    try:
                        logger.info(f"Trying vision model: {model_name}")
                        vision_model = genai.GenerativeModel(model_name)

                        # Generate content with image and prompt
                        response = await asyncio.to_thread(
                            vision_model.generate_content,
                            [prompt, image]
                        )

                        logger.info(f"Successfully used model: {model_name}")
                        return response.text

                    except Exception as model_error:
                        last_error = model_error
                        error_str = str(model_error)
                        if "404" in error_str or "not found" in error_str.lower():
                            logger.debug(f"Model {model_name} not available, trying next...")
                            continue
                        else:
                            # For non-404 errors, propagate immediately
                            logger.error(f"Error with model {model_name}: {str(model_error)}")
                            raise

                # If all models failed with 404, raise the last error
                if last_error:
                    logger.error(f"All vision models failed. Last error: {str(last_error)}")
                    raise last_error

            except Exception as e:
                error_msg = str(e).lower()
                if ("rate limit" in error_msg or "quota" in error_msg) and attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay_base ** (attempt + 1)
                    logger.warning(f"Rate limit hit, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    continue

                # Log the error for debugging
                logger.error(f"Vision API error: {str(e)}")
                raise


# Create singleton instance
labeling_service = LabelingService()

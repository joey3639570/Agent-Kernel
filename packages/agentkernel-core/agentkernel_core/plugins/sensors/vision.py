"""Vision sensor for processing images in multi-modal messages.

This module provides a VisionSensor that can process images using
either cloud-based VLMs (GPT-4o, Claude 3.5) or local models (LLaVA).
"""

from __future__ import annotations

import base64
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from agentkernel_core.types.schemas.message import Message, MessageContent

logger = logging.getLogger(__name__)


class VisionBackend(ABC):
    """Abstract base class for vision model backends."""

    @abstractmethod
    async def process_image(
        self,
        image: str,
        prompt: Optional[str] = None,
    ) -> str:
        """Process an image and return a description or response.

        Args:
            image: Base64 encoded image or URL.
            prompt: Optional prompt for the vision model.

        Returns:
            Text description or analysis of the image.
        """

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the backend is available."""


class OpenAIVisionBackend(VisionBackend):
    """OpenAI GPT-4 Vision backend.

    Uses the OpenAI API with vision capabilities.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        base_url: Optional[str] = None,
    ) -> None:
        """Initialize the OpenAI vision backend.

        Args:
            api_key: OpenAI API key (or uses OPENAI_API_KEY env var).
            model: Model name to use.
            base_url: Optional custom API base URL.
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._client: Optional[Any] = None

    async def _get_client(self) -> Any:
        """Get or create OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise ImportError("openai package required. Install with: pip install openai")

            kwargs = {}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.base_url:
                kwargs["base_url"] = self.base_url

            self._client = AsyncOpenAI(**kwargs)

        return self._client

    async def is_available(self) -> bool:
        """Check if OpenAI API is available."""
        try:
            client = await self._get_client()
            # Simple check - list models
            await client.models.list()
            return True
        except Exception as e:
            logger.warning("OpenAI vision not available: %s", e)
            return False

    async def process_image(
        self,
        image: str,
        prompt: Optional[str] = None,
    ) -> str:
        """Process image using GPT-4 Vision.

        Args:
            image: Base64 encoded image or URL.
            prompt: Optional prompt.

        Returns:
            Image description.
        """
        client = await self._get_client()

        # Prepare image content
        if image.startswith(("http://", "https://")):
            image_content = {"type": "image_url", "image_url": {"url": image}}
        else:
            # Assume base64
            image_content = {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image}"},
            }

        prompt_text = prompt or "Describe this image in detail."

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        image_content,
                    ],
                }
            ],
            max_tokens=1000,
        )

        return response.choices[0].message.content or ""


class LocalVisionBackend(VisionBackend):
    """Local vision model backend (e.g., LLaVA via Ollama or vLLM).

    This backend connects to a locally running vision model server.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llava",
    ) -> None:
        """Initialize local vision backend.

        Args:
            base_url: URL of the local model server.
            model: Model name to use.
        """
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def is_available(self) -> bool:
        """Check if local model server is available."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    return resp.status == 200
        except Exception as e:
            logger.warning("Local vision model not available: %s", e)
            return False

    async def process_image(
        self,
        image: str,
        prompt: Optional[str] = None,
    ) -> str:
        """Process image using local model.

        Args:
            image: Base64 encoded image or URL.
            prompt: Optional prompt.

        Returns:
            Image description.
        """
        import aiohttp

        # Convert URL to base64 if needed
        if image.startswith(("http://", "https://")):
            async with aiohttp.ClientSession() as session:
                async with session.get(image) as resp:
                    image_data = await resp.read()
                    image = base64.b64encode(image_data).decode()

        prompt_text = prompt or "Describe this image in detail."

        payload = {
            "model": self.model,
            "prompt": prompt_text,
            "images": [image],
            "stream": False,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Local model error: {await resp.text()}")
                result = await resp.json()
                return result.get("response", "")


class VisionSensor:
    """Vision sensor for processing images in messages.

    This sensor can be integrated into the perception pipeline to
    automatically process images in multi-modal messages.
    """

    def __init__(
        self,
        backend: Optional[VisionBackend] = None,
        default_prompt: str = "Describe what you see in this image.",
        auto_caption: bool = True,
    ) -> None:
        """Initialize the vision sensor.

        Args:
            backend: Vision model backend to use.
            default_prompt: Default prompt for image processing.
            auto_caption: Whether to auto-caption images in messages.
        """
        self._backend = backend
        self._default_prompt = default_prompt
        self._auto_caption = auto_caption

    async def _get_backend(self) -> VisionBackend:
        """Get or auto-detect available backend."""
        if self._backend:
            return self._backend

        # Try OpenAI first
        openai_backend = OpenAIVisionBackend()
        if await openai_backend.is_available():
            self._backend = openai_backend
            logger.info("Using OpenAI vision backend")
            return self._backend

        # Try local model
        local_backend = LocalVisionBackend()
        if await local_backend.is_available():
            self._backend = local_backend
            logger.info("Using local vision backend")
            return self._backend

        raise RuntimeError("No vision backend available")

    async def process_image(
        self,
        image: str,
        prompt: Optional[str] = None,
    ) -> str:
        """Process a single image.

        Args:
            image: Base64 encoded image or URL.
            prompt: Optional prompt for the vision model.

        Returns:
            Text description of the image.
        """
        backend = await self._get_backend()
        return await backend.process_image(image, prompt or self._default_prompt)

    async def process_message(
        self,
        message: Message,
        prompt: Optional[str] = None,
    ) -> Message:
        """Process images in a message and add captions.

        If the message contains images and auto_caption is enabled,
        this will process each image and add the descriptions to
        the message metadata.

        Args:
            message: The message to process.
            prompt: Optional prompt for image processing.

        Returns:
            The message with image captions added to metadata.
        """
        content = message.get_content_as_multimodal()

        if not content.has_images():
            return message

        if not self._auto_caption:
            return message

        # Process each image
        captions = []
        for image in content.images:
            try:
                caption = await self.process_image(image, prompt)
                captions.append(caption)
            except Exception as e:
                logger.warning("Failed to process image: %s", e)
                captions.append("[Image processing failed]")

        # Add captions to metadata
        if captions:
            if content.metadata is None:
                content.metadata = {}
            content.metadata["image_captions"] = captions

            # Update message content
            message.content = content

        return message

    async def describe_images(
        self,
        images: List[str],
        prompt: Optional[str] = None,
    ) -> List[str]:
        """Process multiple images and return descriptions.

        Args:
            images: List of base64 encoded images or URLs.
            prompt: Optional prompt for all images.

        Returns:
            List of descriptions.
        """
        descriptions = []
        for image in images:
            try:
                desc = await self.process_image(image, prompt)
                descriptions.append(desc)
            except Exception as e:
                logger.warning("Failed to process image: %s", e)
                descriptions.append(f"[Error: {e}]")
        return descriptions

    def is_multimodal_message(self, message: Message) -> bool:
        """Check if a message contains images or audio.

        Args:
            message: The message to check.

        Returns:
            True if the message is multi-modal.
        """
        return message.is_multimodal()


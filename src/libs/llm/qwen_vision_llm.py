"""Qwen Vision LLM implementation (Aliyun DashScope).

This module provides a Vision LLM implementation for Qwen-VL models
using the Aliyun DashScope OpenAI-compatible API endpoint.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from src.libs.llm.openai_vision_llm import OpenAIVisionLLM


class QwenVisionLLMError(RuntimeError):
    """Raised when Qwen Vision API call fails."""


class QwenVisionLLM(OpenAIVisionLLM):
    """Qwen Vision LLM provider implementation.
    
    This class extends OpenAIVisionLLM to support Qwen-VL models
    via the DashScope compatible-mode endpoint.
    
    Attributes:
        api_key: The DashScope API key.
        base_url: The DashScope compatible-mode URL.
        model: The Qwen-VL model identifier (e.g., qwen-vl-max-latest).
    """
    
    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    DEFAULT_MODEL = "qwen-vl-max-latest"
    
    def __init__(
        self,
        settings: Any,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_image_size: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Qwen Vision LLM provider.
        
        Args:
            settings: Application settings containing vision_llm configuration.
            api_key: Optional API key override.
            base_url: Optional base URL override.
            max_image_size: Maximum image dimension in pixels for auto-compression.
            **kwargs: Additional configuration overrides.
        
        Raises:
            ValueError: If required configuration is missing.
        """
        # Get vision settings section
        vision_settings = getattr(settings, "vision_llm", None)
        
        # Model name: prefer vision_llm.model, fallback to default
        vision_model = getattr(vision_settings, 'model', None) if vision_settings else None
        self.model = vision_model or self.DEFAULT_MODEL
        
        # Max image size
        vision_max_size = getattr(vision_settings, 'max_image_size', None) if vision_settings else None
        self.max_image_size = max_image_size or vision_max_size or 2048
        
        # Temperature / max_tokens
        self.default_temperature = getattr(settings.llm, 'temperature', 0.0)
        self.default_max_tokens = getattr(settings.llm, 'max_tokens', 4096)
        
        # API key resolution order: param > vision_settings > env vars
        self.api_key = api_key
        if not self.api_key and vision_settings:
            self.api_key = getattr(vision_settings, 'api_key', None)
        if not self.api_key:
            self.api_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("QWEN_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Qwen API key not provided. Set in settings.yaml (vision_llm.api_key), "
                "DASHSCOPE_API_KEY/QWEN_API_KEY environment variable, or pass api_key parameter."
            )
        
        # Base URL resolution
        self.base_url = base_url
        if not self.base_url and vision_settings:
            self.base_url = getattr(vision_settings, 'base_url', None)
        if not self.base_url:
            self.base_url = self.DEFAULT_BASE_URL
            
        # Azure auth is not used for Qwen
        self._use_azure_auth = False
        self.api_version = None
        self._extra_config = kwargs

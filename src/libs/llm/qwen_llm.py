"""Qwen LLM implementation.

This module provides the Qwen LLM implementation that works with
Qwen's API through DashScope's compatible-mode endpoint.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from src.libs.llm.base_llm import BaseLLM, ChatResponse, Message


class QwenLLMError(RuntimeError):
    """Raised when Qwen API call fails."""


class QwenLLM(BaseLLM):
    """Qwen LLM provider implementation.

    This class implements the BaseLLM interface for Qwen's chat API.
    Qwen uses a DashScope-compatible API format.

    Attributes:
        api_key: The API key for authentication.
        base_url: The base URL for the API.
        model: The model identifier to use.
        default_temperature: Default temperature for generation.
        default_max_tokens: Default max tokens for generation.

    Example:
        >>> from src.core.settings import load_settings
        >>> settings = load_settings('config/settings.yaml')
        >>> llm = QwenLLM(settings)
        >>> response = llm.chat([Message(role='user', content='Hello')])
    """

    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(
            self,
            settings: Any,
            api_key: Optional[str] = None,
            base_url: Optional[str] = None,
            llm_config: Optional[Any] = None,  # 新增参数
            **kwargs: Any,
    ) -> None:
        """Initialize the Qwen LLM provider.

        Args:
            settings: Application settings containing LLM configuration.
            api_key: Optional API key override (falls back to env var QWEN_API_KEY).
            base_url: Optional base URL override.
            llm_config: Optional specific LLM config (for additional_llms support).
            **kwargs: Additional configuration overrides.

        Raises:
            ValueError: If API key is not provided and not found in environment.
        """
        # 支持从 additional_llms 或主 llm 配置加载
        if llm_config is not None:
            # 使用传入的特定配置
            llm_settings = llm_config
        elif hasattr(settings, 'additional_llms') and settings.additional_llms and 'qwen' in settings.additional_llms:
            # 自动从 additional_llms 中获取 qwen 配置
            llm_settings = settings.additional_llms['qwen']
        else:
            # 回退到主 llm 配置
            llm_settings = settings.llm

        self.model = llm_settings.model
        self.default_temperature = llm_settings.temperature
        self.default_max_tokens = llm_settings.max_tokens

        # API key: explicit > env var > config
        self.api_key = api_key or os.getenv("QWEN_API_KEY") or settings.llm.api_key
        if not self.api_key:
            raise ValueError(
                "Qwen API key not provided. Set QWEN_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Base URL: explicit > config > default
        self.base_url = base_url or self.DEFAULT_BASE_URL

        # Store any additional kwargs for future use
        self._extra_config = kwargs

    def chat(
            self,
            messages: List[Message],
            trace: Optional[Any] = None,
            **kwargs: Any,
    ) -> ChatResponse:
        """Generate a chat completion using Qwen API.

        Args:
            messages: List of conversation messages.
            trace: Optional TraceContext for observability (reserved for Stage F).
            **kwargs: Override parameters (temperature, max_tokens, etc.).

        Returns:
            ChatResponse with generated content and metadata.

        Raises:
            ValueError: If messages are invalid.
            QwenLLMError: If API call fails.
        """
        # Validate input
        self.validate_messages(messages)

        # Prepare request parameters
        temperature = kwargs.get("temperature", self.default_temperature)
        max_tokens = kwargs.get("max_tokens", self.default_max_tokens)
        model = kwargs.get("model", self.model)

        # Convert messages to API format
        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        # Make API call
        try:
            response_data = self._call_api(
                messages=api_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Parse response
            content = response_data["choices"][0]["message"]["content"]
            usage = response_data.get("usage")

            return ChatResponse(
                content=content,
                model=response_data.get("model", model),
                usage=usage,
                raw_response=response_data,
            )
        except KeyError as e:
            raise QwenLLMError(
                f"[Qwen] Unexpected response format: missing key {e}"
            ) from e
        except Exception as e:
            if isinstance(e, QwenLLMError):
                raise
            raise QwenLLMError(
                f"[Qwen] API call failed: {type(e).__name__}: {e}"
            ) from e

    def _call_api(
            self,
            messages: List[Dict[str, str]],
            model: str,
            temperature: float,
            max_tokens: int,
    ) -> Dict[str, Any]:
        """Make the actual API call to Qwen.

        This method is separated to allow easy mocking in tests.

        Args:
            messages: Messages in API format.
            model: Model identifier.
            temperature: Generation temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Raw API response as dictionary.

        Raises:
            QwenLLMError: If the API call fails.
        """
        import httpx

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=payload, headers=headers)

                if response.status_code != 200:
                    error_detail = self._parse_error_response(response)
                    raise QwenLLMError(
                        f"[Qwen] API error (HTTP {response.status_code}): {error_detail}"
                    )

                return response.json()
        except httpx.TimeoutException as e:
            raise QwenLLMError(
                f"[Qwen] Request timed out after 60 seconds"
            ) from e
        except httpx.RequestError as e:
            raise QwenLLMError(
                f"[Qwen] Connection failed: {type(e).__name__}: {e}"
            ) from e

    def _parse_error_response(self, response: Any) -> str:
        """Parse error details from API response.

        Args:
            response: The HTTP response object.

        Returns:
            Human-readable error message.
        """
        try:
            error_data = response.json()
            if "error" in error_data:
                error = error_data["error"]
                if isinstance(error, dict):
                    return error.get("message", str(error))
                return str(error)
            return response.text
        except Exception:
            return response.text or "Unknown error"

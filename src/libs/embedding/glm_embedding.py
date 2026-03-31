"""Glm Embedding implementation.

This module provides the Glm Embedding implementation that works with
Alibaba Cloud DashScope's compatible-mode endpoint.
"""

from __future__ import annotations

import os
from typing import Any, List, Optional

from src.libs.embedding.base_embedding import BaseEmbedding


class GlmEmbeddingError(RuntimeError):
    """Raised when Glm Embeddings API call fails."""


class GlmEmbedding(BaseEmbedding):
    """Glm Embedding provider implementation.

    This class implements the BaseEmbedding interface for Glm's Embeddings API.
    It supports Alibaba Cloud DashScope's embedding models like text-embedding-v1,
    text-embedding-v2, and text-embedding-v3.

    Attributes:
        api_key: The API key for authentication.
        model: The model identifier to use.
        dimensions: Optional dimension reduction.
        base_url: The base URL for the API (default: DashScope's endpoint).

    Example:
        >>> from src.core.settings import load_settings
        >>> settings = load_settings('config/settings.yaml')
        >>> embedding = GlmEmbedding(settings)
        >>> vectors = embedding.embed(["hello world", "test"])
    """

    DEFAULT_BASE_URL = "https://maas-coding-api.cn-huabei-1.xf-yun.com/v2"

    def __init__(
            self,
            settings: Any,
            api_key: Optional[str] = None,
            base_url: Optional[str] = None,
            embedding_config: Optional[Any] = None,
            **kwargs: Any,
    ) -> None:
        """Initialize the Glm Embedding provider.

        Args:
            settings: Application settings containing Embedding configuration.
            api_key: Optional API key override (falls back to settings.embedding.api_key or env var).
            base_url: Optional base URL override.
            embedding_config: Optional specific embedding config (for additional_embeddings support).
            **kwargs: Additional configuration overrides.

        Raises:
            ValueError: If API key is not provided and not found in environment.
        """
        # 支持从 additional_embeddings 或主 embedding 配置加载
        if embedding_config is not None:
            emb_settings = embedding_config
        elif hasattr(settings, 'additional_embeddings') and settings.additional_embeddings and 'glm' in settings.additional_embeddings:
            # 自动从 additional_embeddings 中获取 glm 配置
            emb_settings = settings.additional_embeddings['glm']
        else:
            # 回退到主 embedding 配置
            emb_settings = settings.embedding

        self.model = emb_settings.model

        # Extract optional dimensions setting
        self.dimensions = getattr(emb_settings, 'dimensions', None)

        # API key: explicit > config > env var
        config_api_key = getattr(emb_settings, 'api_key', None)
        self.api_key = (
                api_key
                or config_api_key
                or os.environ.get("Glm_API_KEY")
        )
        if not self.api_key:
            raise ValueError(
                "Glm API key not provided. Set in settings.yaml (api_key), "
                "Glm_API_KEY environment variable, or pass api_key parameter."
            )

        # Base URL: explicit > config > default
        if base_url:
            self.base_url = base_url
        else:
            settings_base_url = getattr(emb_settings, 'base_url', None)
            self.base_url = settings_base_url if settings_base_url else self.DEFAULT_BASE_URL

        # Store any additional kwargs for future use
        self._extra_config = kwargs

    def embed(
            self,
            texts: List[str],
            trace: Optional[Any] = None,
            **kwargs: Any,
    ) -> List[List[float]]:
        """Generate embeddings for a batch of texts using Glm API.

        Args:
            texts: List of text strings to embed. Must not be empty.
            trace: Optional TraceContext for observability (reserved for Stage F).
            **kwargs: Override parameters (dimensions, etc.).

        Returns:
            List of embedding vectors, where each vector is a list of floats.
            The length of the outer list matches len(texts).

        Raises:
            ValueError: If texts list is empty or contains invalid entries.
            GlmEmbeddingError: If API call fails.
        """
        # Validate input
        self.validate_texts(texts)

        # Import httpx for API calls
        try:
            import httpx
        except ImportError as e:
            raise RuntimeError(
                "httpx package not installed. Install with: pip install httpx"
            ) from e

        # Prepare request parameters
        url = f"{self.base_url.rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "input": texts,
            "model": self.model,
        }

        # Add dimensions if specified
        dimensions = kwargs.get("dimensions", self.dimensions)
        if dimensions is not None:
            payload["dimensions"] = dimensions

        # Make API call
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=payload, headers=headers)

                if response.status_code != 200:
                    error_detail = self._parse_error_response(response)
                    raise GlmEmbeddingError(
                        f"[Glm] API error (HTTP {response.status_code}): {error_detail}"
                    )

                response_data = response.json()
        except httpx.TimeoutException as e:
            raise GlmEmbeddingError(
                f"[Glm] Request timed out after 60 seconds"
            ) from e
        except httpx.RequestError as e:
            raise GlmEmbeddingError(
                f"[Glm] Connection failed: {type(e).__name__}: {e}"
            ) from e

        # Extract embeddings from response
        # Response format: {"data": [{"embedding": [...], "index": 0}, ...], "usage": {...}}
        try:
            embeddings = [item["embedding"] for item in response_data.get("data", [])]
        except (KeyError, TypeError) as e:
            raise GlmEmbeddingError(
                f"[Glm] Failed to parse API response: {e}"
            ) from e

        # Verify output matches input length
        if len(embeddings) != len(texts):
            raise GlmEmbeddingError(
                f"[Glm] Output length mismatch: expected {len(texts)}, got {len(embeddings)}"
            )

        return embeddings

    def _parse_error_response(self, response: Any) -> str:
        """Parse error details from API response.

        Args:
            response: The HTTP response object.

        Returns:
            Error message string.
        """
        try:
            error_data = response.json()
            # Try common error formats
            if "error" in error_data:
                error = error_data["error"]
                if isinstance(error, dict):
                    return error.get("message", str(error))
                return str(error)
            return response.text
        except Exception:
            return response.text or f"HTTP {response.status_code}"

    def get_dimension(self) -> Optional[int]:
        """Get the embedding dimension for the configured model.

        Returns:
            The embedding dimension, or None if not deterministic.

        Note:
            For Glm embedding models:
            - text-embedding-v1: 1536
            - text-embedding-v2: 1536
            - text-embedding-v3: 1024
        """
        # If dimensions explicitly configured, return it
        if self.dimensions is not None:
            return self.dimensions

        # Model-specific defaults for Glm models
        model_dimensions = {
            "text-embedding-v1": 1536,
            "text-embedding-v2": 1536,
            "text-embedding-v3": 1024,
        }

        return model_dimensions.get(self.model)

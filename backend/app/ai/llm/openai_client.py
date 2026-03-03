"""OpenAI LLM client — production implementation using the OpenAI SDK."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import APIError, AsyncOpenAI, AuthenticationError, RateLimitError

from app.ai.llm.base import LLMClient, LLMResponse, ToolCallResult

logger = logging.getLogger(__name__)


class OpenAIClient(LLMClient):
    """Production OpenAI client using the Chat Completions API with tool calling."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
    ) -> LLMResponse:
        """Call OpenAI Chat Completions API with optional tool definitions."""
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }

        # Only include tools if we have any
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        logger.debug("OpenAI request: model=%s, messages=%d, tools=%d",
                      self._model, len(messages), len(tools))

        try:
            response = await self._client.chat.completions.create(**kwargs)
        except AuthenticationError:
            logger.error("OpenAI authentication failed — check LLM_API_KEY")
            return LLMResponse(
                message="I'm temporarily unavailable due to a configuration issue. Please try again later.",
                raw_response={"error": "authentication_failed"},
            )
        except RateLimitError as e:
            logger.error("OpenAI rate limit / quota exceeded: %s", e)
            return LLMResponse(
                message="I'm temporarily unavailable due to high demand. Please try again in a moment.",
                raw_response={"error": "rate_limit_exceeded", "detail": str(e)},
            )
        except APIError as e:
            logger.error("OpenAI API error: %s", e)
            return LLMResponse(
                message="I'm experiencing a temporary issue. Please try again shortly.",
                raw_response={"error": "api_error", "detail": str(e)},
            )

        choice = response.choices[0]
        message = choice.message

        # Extract tool call if present
        tool_call: ToolCallResult | None = None
        if message.tool_calls:
            tc = message.tool_calls[0]  # We process one tool call at a time
            try:
                arguments = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                logger.warning("Failed to parse tool call arguments: %s",
                               tc.function.arguments)
                arguments = {}

            tool_call = ToolCallResult(
                name=tc.function.name,
                arguments=arguments,
            )
            logger.info("LLM requested tool: %s(%s)", tc.function.name, arguments)

        assistant_message = message.content or ""

        return LLMResponse(
            message=assistant_message,
            tool_call=tool_call,
            raw_response={
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
                "finish_reason": choice.finish_reason,
            },
        )

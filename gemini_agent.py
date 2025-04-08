import os
from typing import AsyncGenerator, Sequence

from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage, TextMessage
from autogen_core import CancellationToken
from autogen_core.model_context import UnboundedChatCompletionContext
from autogen_core.models import AssistantMessage, RequestUsage
from dotenv import load_dotenv, find_dotenv
from google import genai
from google.genai import types


load_dotenv(find_dotenv())


class GeminiAssistantAgent(BaseChatAgent):
    def __init__(
        self,
        name: str = "GeminiAssistantAgent",
        description: str = "An agent that provides assistance with ability to use tools.",
        model: str = "gemini-2.0-flash",
        api_key: str = os.environ["GEMINI_API_KEY"],
        system_message: (
            str | None
        ) = "You are a helpful assistant that can respond to messages. Reply with TERMINATE when the task has been completed.",
    ):
        super().__init__(name=name, description=description)
        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
        )
        self._model_context = UnboundedChatCompletionContext()
        self._model_client = genai.Client(api_key=api_key)
        self._system_message = system_message
        self._model = model

    @property
    def produced_message_types(self) -> Sequence[type[BaseChatMessage]]:
        return (TextMessage,)

    async def on_messages(
        self, messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken
    ) -> Response:
        final_response = None
        async for message in self.on_messages_stream(messages, cancellation_token):
            if isinstance(message, Response):
                final_response = message

        if final_response is None:
            raise AssertionError("The stream should have returned the final result.")

        return final_response

    async def on_messages_stream(
        self, messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken
    ) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | Response, None]:
        # Add messages to the model context
        for msg in messages:
            await self._model_context.add_message(msg.to_model_message())

        # Get conversation history
        history = [
            (msg.source if hasattr(msg, "source") else "system")
            + ": "
            + (msg.content if isinstance(msg.content, str) else "")
            + "\n"
            for msg in await self._model_context.get_messages()
        ]
        # Generate response using Gemini
        response = self._model_client.models.generate_content(
            model=self._model,
            contents=f"History: {history}\nGiven the history, please provide a response",
            config=types.GenerateContentConfig(
                system_instruction=self._system_message,
                temperature=0.3,
            ),
        )

        # Create usage metadata
        usage = RequestUsage(
            prompt_tokens=response.usage_metadata.prompt_token_count,
            completion_tokens=response.usage_metadata.candidates_token_count,
        )

        # Add response to model context
        await self._model_context.add_message(
            AssistantMessage(content=response.text, source=self.name)
        )

        # Yield the final response
        yield Response(
            chat_message=TextMessage(
                content=response.text, source=self.name, models_usage=usage
            ),
            inner_messages=[],
        )

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        """Reset the assistant by clearing the model context."""
        await self._model_context.clear()

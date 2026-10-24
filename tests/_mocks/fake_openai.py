from types import SimpleNamespace

PROMPT_TOKENS = 120
COMPLETION_TOKENS = 45


def chat_response(model: str, text: str) -> SimpleNamespace:
    """A minimal chat.completions response shaped like the OpenAI SDK's."""
    return SimpleNamespace(
        model=model,
        choices=[SimpleNamespace(message=SimpleNamespace(role='assistant', content=text))],
        usage=SimpleNamespace(
            prompt_tokens=PROMPT_TOKENS,
            completion_tokens=COMPLETION_TOKENS,
            model_dump=lambda: {
                'prompt_tokens': PROMPT_TOKENS,
                'completion_tokens': COMPLETION_TOKENS,
            },
        ),
    )


class FakeChatCreate:
    """Offline double for client.chat.completions.create; records calls, returns canned text."""

    def __init__(self, text: str = '<answer>{"cart": {}, "total": 0}</answer>') -> None:
        self.text = text
        self.calls: list[dict[str, object]] = []

    async def __call__(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        reasoning_effort: object = None,
    ) -> object:
        self.calls.append(
            {
                'model': model,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'reasoning_effort': reasoning_effort,
            }
        )
        return chat_response(model, self.text)


class FakeScriptedChatCreate:
    """Offline double returning a scripted sequence of replies; records calls.

    Judge tests use it to script both-order verdicts; running out of replies is a
    broken test setup, so it fails loudly.
    """

    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.calls: list[dict[str, object]] = []

    async def __call__(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        reasoning_effort: object = None,
    ) -> object:
        self.calls.append(
            {
                'model': model,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'reasoning_effort': reasoning_effort,
            }
        )
        assert self.replies, 'FakeScriptedChatCreate ran out of scripted replies'
        return chat_response(model, self.replies.pop(0))

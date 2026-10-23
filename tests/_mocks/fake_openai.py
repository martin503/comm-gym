from types import SimpleNamespace


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
        return SimpleNamespace(
            model=model,
            choices=[
                SimpleNamespace(message=SimpleNamespace(role='assistant', content=self.text))
            ],
            usage=SimpleNamespace(
                prompt_tokens=120,
                completion_tokens=45,
                model_dump=lambda: {'prompt_tokens': 120, 'completion_tokens': 45},
            ),
        )

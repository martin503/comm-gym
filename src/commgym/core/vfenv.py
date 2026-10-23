def completion_text(completion: object) -> str:
    """verifiers passes chat completions as Messages (dicts or models) and plain strings."""
    if isinstance(completion, str):
        return completion
    assert isinstance(completion, list), f'unsupported completion type {type(completion)}'
    texts = []
    for message in completion:
        role = message.get('role') if isinstance(message, dict) else getattr(message, 'role', None)
        if role != 'assistant':
            continue
        content = (
            message['content'] if isinstance(message, dict) else getattr(message, 'content', '')
        )
        assert isinstance(content, str), f'non-text completion content: {type(content)}'
        texts.append(content)
    assert texts, 'completion carries no assistant message'
    return '\n'.join(texts)

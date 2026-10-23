import gzip
import json
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from http.client import HTTPException
from pathlib import Path
from urllib.request import Request, urlopen

from openai import AsyncOpenAI

BASE_URL = 'https://openrouter.ai/api/v1'
PRICES_URL = 'https://openrouter.ai/api/v1/models'

# the OpenAI client's overloaded create() defies a structural Protocol, so the injectable
# boundary stays permissive; the test double in tests/_mocks mirrors the keyword contract
type ChatCreate = Callable[..., Awaitable[object]]


@dataclass(frozen=True, slots=True)
class ChatResult:
    text: str
    prompt_tokens: int
    completion_tokens: int
    model: str
    latency_s: float
    usage: dict[str, object]  # raw usage; carries reasoning details / reported cost when present


def load_api_key(env: Mapping[str, str], env_path: Path) -> str:
    """OPENROUTER_API_KEY from the environment, falling back to a .env file."""
    if env.get('OPENROUTER_API_KEY'):
        return env['OPENROUTER_API_KEY']
    assert env_path.is_file(), (
        f'no OPENROUTER_API_KEY in the environment and no {env_path}; put the key in .env'
    )
    for line in env_path.read_text().splitlines():
        key, sep, value = line.partition('=')
        if sep and key.strip() == 'OPENROUTER_API_KEY':
            return value.strip().strip('"').strip("'")
    raise AssertionError(f'{env_path} has no OPENROUTER_API_KEY line')


class OpenRouterClient:
    """Thin async wrapper: one chat call, normalized with token usage and latency."""

    def __init__(self, api_key: str | None = None, *, acreate: ChatCreate | None = None) -> None:
        if acreate is None:
            assert api_key is not None, 'live calls need the OpenRouter API key'
            client = AsyncOpenAI(api_key=api_key, base_url=BASE_URL, timeout=90.0, max_retries=3)
            self._acreate: ChatCreate = client.chat.completions.create
        else:
            self._acreate = acreate

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 2048,
        reasoning_effort: str | None = None,
    ) -> ChatResult:
        params: dict[str, object] = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
        }
        if reasoning_effort is not None:
            params['reasoning_effort'] = reasoning_effort
        start = time.perf_counter()
        response = await self._acreate(**params)
        latency = time.perf_counter() - start
        return _normalize(response, model, latency)


def fetch_model_prices(timeout: float = 30.0, retries: int = 3) -> dict[str, dict[str, str]]:
    """Per-token USD prices keyed by model id, from OpenRouter's public models endpoint.

    Uses urllib (system CA bundle) rather than httpx: the project sandbox blocks reading
    certifi's bundled cacert.pem, which would break every https call from this module.
    Requests gzip and retries: proxies in front of this endpoint tend to truncate the
    ~800 KB uncompressed chunked body.
    """
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = Request(
                PRICES_URL, headers={'User-Agent': 'comm-gym', 'Accept-Encoding': 'gzip'}
            )
            with urlopen(request, timeout=timeout) as response:
                raw = response.read()
                encoding = response.headers.get('Content-Encoding', '')
            body = gzip.decompress(raw) if encoding == 'gzip' else raw
            payload = json.loads(body)
            break
        except (OSError, HTTPException, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(2.0 * (attempt + 1))
    else:
        raise AssertionError(f'model prices unavailable after {retries} tries: {last_error}')
    assert isinstance(payload, dict) and isinstance(payload.get('data'), list), (
        'unexpected /models payload shape'
    )
    prices: dict[str, dict[str, str]] = {}
    for entry in payload['data']:
        assert isinstance(entry, dict), 'unexpected /models entry'
        model_id = entry.get('id')
        pricing = entry.get('pricing')
        if isinstance(model_id, str) and isinstance(pricing, dict):
            prices[model_id] = {
                key: value for key, value in pricing.items() if isinstance(value, str)
            }
    return prices


def estimate_cost_usd(
    prices: dict[str, dict[str, str]], model: str, prompt_tokens: int, completion_tokens: int
) -> float:
    """Estimated spend for one call from OpenRouter's per-token USD prices.

    Unknown models return 0.0; the caller treats missing pricing as a hard error at startup.
    """
    entry = prices.get(model, {})
    prompt_price = float(entry.get('prompt', '0') or '0')
    completion_price = float(entry.get('completion', '0') or '0')
    return prompt_tokens * prompt_price + completion_tokens * completion_price


def _normalize(response: object, model: str, latency: float) -> ChatResult:
    choices = getattr(response, 'choices', None)
    usage = getattr(response, 'usage', None)
    assert choices, f'{model}: response carries no choices'
    content = getattr(choices[0].message, 'content', None)
    usage_dict = usage.model_dump() if hasattr(usage, 'model_dump') else dict(usage or {})
    return ChatResult(
        text=content if isinstance(content, str) else '',
        prompt_tokens=int(getattr(usage, 'prompt_tokens', 0) or 0),
        completion_tokens=int(getattr(usage, 'completion_tokens', 0) or 0),
        model=str(getattr(response, 'model', model)),
        latency_s=latency,
        usage=usage_dict,
    )

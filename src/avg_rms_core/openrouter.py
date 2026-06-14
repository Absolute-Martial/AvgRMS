import asyncio

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI


def build_openrouter_client(
    api_key: str,
    model: str = "google/gemma-2-9b-it",
    base_url: str = "https://openrouter.ai/api/v1",
    timeout: float = 20.0,
) -> ChatOpenAI:
    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=0,
        timeout=timeout,
    )


async def invoke_openrouter_with_retry(
    client: ChatOpenAI,
    prompt: str,
    *,
    timeout_seconds: float = 20.0,
    retries: int = 1,
) -> str:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = await asyncio.wait_for(
                client.ainvoke([HumanMessage(content=prompt)]),
                timeout=timeout_seconds,
            )
            return response.content if hasattr(response, "content") else str(response)
        except Exception as exc:  # pragma: no cover - exercised through planner tests
            last_error = exc
            if attempt >= retries:
                break
    assert last_error is not None
    raise last_error

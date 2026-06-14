from langchain_openai import ChatOpenAI


def build_openrouter_client(
    api_key: str,
    model: str = "google/gemma-2-9b-it",
    base_url: str = "https://openrouter.ai/api/v1",
) -> ChatOpenAI:
    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=0,
    )

"""
Abstracción del proveedor de LLM (sección 23). El motor RAG solo conoce
`generate(system_prompt, user_prompt) -> str`.
"""
from abc import ABC, abstractmethod
from functools import lru_cache

from backend.core.config import settings


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        ...


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        import anthropic
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=1500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(block.text for block in resp.content if block.type == "text")


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        from openai import OpenAI
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return resp.choices[0].message.content


class MockProvider(LLMProvider):
    """[DEMO] Proveedor simulado para pruebas sin claves API reales.
    NUNCA usar en producción. Refleja únicamente los fragmentos recibidos,
    sin generar redacción real, para dejar explícito que es un stub."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return (
            "[RESPUESTA DEMO - MockProvider, no hay LLM real configurado]\n"
            "Este es un marcador de posición. Configure LLM_PROVIDER y LLM_API_KEY "
            "en .env para obtener respuestas generadas realmente a partir de los "
            "fragmentos recuperados que se incluyeron en el prompt."
        )


@lru_cache
def get_llm_provider() -> LLMProvider:
    if settings.LLM_PROVIDER == "anthropic":
        return AnthropicProvider(settings.LLM_API_KEY, settings.LLM_MODEL)
    elif settings.LLM_PROVIDER == "openai":
        return OpenAIProvider(settings.LLM_API_KEY, settings.LLM_MODEL)
    elif settings.LLM_PROVIDER == "mock":
        return MockProvider()
    raise NotImplementedError(f"Proveedor LLM no implementado: {settings.LLM_PROVIDER}")

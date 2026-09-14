"""Proveedores de generación de respuesta, intercambiables vía configuración (LLM_PROVIDER).

Regla fundamental del sistema: la IA no debe inventar, completar ni especular información
normativa. Cada implementación recibe únicamente los fragmentos recuperados y, si no hay
fragmentos, debe devolver siempre el mensaje de "sin información suficiente" sin excepción.
"""

from abc import ABC, abstractmethod

SYSTEM_PROMPT = """Actúas como asistente institucional de consulta documental de la Secretaría de Educación.
Tu función es responder preguntas utilizando exclusivamente la información contenida en los documentos institucionales recuperados.
No debes utilizar conocimiento externo para completar una respuesta normativa.
No debes inventar información.
Cada afirmación normativa debe estar respaldada por una fuente recuperada.
Si los documentos proporcionados no contienen información suficiente, debes indicarlo expresamente.
Cuando respondas, cita las fuentes utilizadas e identifica el documento y el apartado correspondiente cuando esta información esté disponible.
Si existen documentos contradictorios, debes señalar la contradicción y no seleccionar arbitrariamente una disposición.
No reemplazas la asesoría jurídica, administrativa o técnica de la Secretaría de Educación."""

NO_INFO_MESSAGE = (
    "No encontré información suficiente en la documentación institucional disponible "
    "para responder esta consulta con seguridad. Te recomiendo verificar la normativa "
    "vigente o remitir la consulta al área competente."
)


class LLMProvider(ABC):
    name: str

    @abstractmethod
    def generate(self, question: str, context_chunks: list[dict]) -> str: ...


class ExtractiveProvider(LLMProvider):
    """Modo sin costo: no llama a ningún LLM externo. Ensambla la respuesta directamente
    a partir de los fragmentos recuperados. Es el valor por defecto y también la
    salvaguarda cuando no hay una API key de LLM configurada."""

    name = "extractive-v1"

    def generate(self, question: str, context_chunks: list[dict]) -> str:
        if not context_chunks:
            return NO_INFO_MESSAGE

        lines = ["Fragmentos relevantes encontrados en la documentación institucional:", ""]
        for chunk in context_chunks:
            lines.append(f"- {chunk['content'].strip()}")
        lines.append("")
        lines.append(
            "Nota: esta respuesta fue ensamblada directamente a partir de los fragmentos "
            "recuperados (modo extractivo, sin modelo generativo). Revisa las fuentes "
            "citadas abajo para el texto completo."
        )
        return "\n".join(lines)


class AnthropicProvider(LLMProvider):
    """Respuestas generativas vía la API de Anthropic. Requiere ANTHROPIC_API_KEY.
    El prompt de sistema prohíbe explícitamente usar conocimiento externo al contexto
    recuperado."""

    name = "anthropic"

    def __init__(self, model: str, api_key: str):
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def generate(self, question: str, context_chunks: list[dict]) -> str:
        if not context_chunks:
            return NO_INFO_MESSAGE

        context_text = "\n\n".join(
            f"[Fragmento {i + 1}] (Documento: {c['document_title']}, "
            f"p.{c.get('page') or '-'}, art.{c.get('article') or '-'})\n{c['content']}"
            for i, c in enumerate(context_chunks)
        )
        user_message = (
            f"Documentos recuperados:\n\n{context_text}\n\n"
            f"Pregunta del usuario: {question}\n\n"
            "Responde siguiendo la estructura: Respuesta, Procedimiento (si aplica), "
            "Consideraciones (si aplica). No incluyas la sección de Fuentes, esa se agrega aparte."
        )
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text


_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    global _provider
    if _provider is None:
        from app.config import get_settings

        settings = get_settings()
        if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
            _provider = AnthropicProvider(settings.anthropic_model, settings.anthropic_api_key)
        else:
            _provider = ExtractiveProvider()
    return _provider

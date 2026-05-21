import requests
from typing import Optional

from app.core.config import settings

# ── Constantes Ollama ────────────────────────────────────────────────────────
OLLAMA_URL           = "http://localhost:11434/api/generate"
OLLAMA_MODEL         = settings.faq_llm_model
OLLAMA_TIMEOUT       = 60
MAX_CLUSTER_MESSAGES = 10


# ── Conexión con Ollama ──────────────────────────────────────────────────────

def _generate_with_ollama(prompt: str) -> str:
    #Envía un prompt a Ollama y retorna el texto generado.
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=OLLAMA_TIMEOUT
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()

    except Exception as e:
        print(f"❌ Error Ollama: {e}")
        return ""


# ── Generación de pregunta FAQ ───────────────────────────────────────────────

def refine_question_to_faq(
    medoid_message: str,
    cluster_messages: list[str],
    workspace_context: Optional[dict] = None,
) -> str:

    #Usa el LLM para convertir el medoide y los mensajes del cluster en una pregunta FAQ profesional.
    
    workspace_name     = workspace_context.get("name", "la empresa") if workspace_context else "la empresa"
    workspace_category = workspace_context.get("category", "") if workspace_context else ""

    ejemplos = "\n".join(
        f"- {msg}"
        for msg in cluster_messages[:MAX_CLUSTER_MESSAGES]
    )

    prompt = f"""
Eres un experto en generación de preguntas FAQ.

Empresa: {workspace_name}
Categoría: {workspace_category}

Estos mensajes pertenecen al mismo tema:
{ejemplos}

Tu tarea:
- Generar UNA SOLA pregunta FAQ
- Clara y profesional
- Máximo 15 palabras
- Debe iniciar con ¿ y terminar con ?
- En español
- No debes escribir nombres propios, datos específicos (precios, horarios, links, correos o teléfonos) ni información que no esté presente en los mensajes del cluster.

Responde SOLO con la pregunta.
"""

    try:
        question = _generate_with_ollama(prompt).replace('"', '')

        if not question:
            raise Exception("Respuesta vacía")

        if not question.startswith("¿"):
            question = "¿" + question
        if not question.endswith("?"):
            question += "?"

        return question

    except Exception as e:
        print(f"❌ Error generando pregunta FAQ: {e}")
        return _format_fallback_question(medoid_message)


def _format_fallback_question(text: str) -> str:
    text = text.strip().capitalize()
    if not text.startswith("¿"):
        text = "¿" + text
    if not text.endswith("?"):
        text += "?"
    return text


# ── Generación de respuesta FAQ ──────────────────────────────────────────────

def generate_answer_with_llm(
    question: str,
    workspace_context: Optional[dict] = None,
) -> str:

    #Usa el LLM para generar una respuesta profesional a la pregunta FAQ.
    workspace_name = workspace_context.get("name", "la empresa") if workspace_context else "la empresa"

    prompt = f"""
Eres un asistente profesional de atención al cliente.

Empresa: {workspace_name}

Pregunta: {question}

Genera una respuesta:
- Clara y profesional
- Máximo 3 oraciones
- No inventes datos específicos (precios, horarios, links, correos o teléfonos)
- Si desconoces un dato específico, invita al cliente a consultar con un asesor
- Lista para sección FAQ

Responde SOLO con la respuesta.
"""

    try:
        answer = _generate_with_ollama(prompt)

        if not answer:
            raise Exception("Respuesta vacía")

        return answer.strip()

    except Exception as e:
        print(f"❌ Error generando respuesta FAQ: {e}")
        return "Nuestro equipo actualizará esta información próximamente."
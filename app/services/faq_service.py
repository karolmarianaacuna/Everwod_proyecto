import requests
from typing import Optional

from app.core.config import settings

#Conexión con Ollama 
def _generate_with_ollama(prompt: str) -> str:
    #Envía un prompt a Ollama y retorna el texto generado.
    try:
        response = requests.post(
            settings.ollama_url,
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            timeout=settings.ollama_timeout
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()

    except Exception as e:
        print(f"❌ Error Ollama: {e}")
        return ""



# Generación de pregunta FAQ
def refine_question_to_faq(
    medoid_message: str,
    cluster_messages: list[str],
    workspace_context: Optional[dict] = None,
    agent_texts: list[str] = [],    # ← agregar
) -> str:

    #Usa el LLM para convertir el medoide y los mensajes del cluster en una pregunta FAQ profesional.
    
    workspace_name     = workspace_context.get("name") if workspace_context else "la empresa"
    workspace_category = workspace_context.get("category") if workspace_context else ""

    ejemplos = "\n".join(
        f"- {msg}"
        for msg in cluster_messages[:settings.max_cluster_messages]
    )
    contexto_negocio = "\n".join(
        f"- {text}" for text in agent_texts[:5] if text
    )


    prompt = f"""Eres un experto en análisis de conversaciones y generación de preguntas FAQ para empresas de atención al cliente.

=== CONTEXTO DE LA EMPRESA ===
Nombre: {workspace_name}
Categoría: {workspace_category}

=== INFORMACIÓN REAL DEL NEGOCIO ===
{contexto_negocio if contexto_negocio else "No hay información adicional disponible."}

=== MENSAJE REPRESENTATIVO DEL TEMA ===
{medoid_message}

=== MENSAJES DEL CLUSTER ===
{ejemplos}

=== TU TAREA ===
Usando la información real del negocio como referencia, analiza si los mensajes representan una duda o necesidad real que un cliente tendría sobre los servicios de {workspace_name}.

=== CRITERIOS PARA MARCAR COMO INVALIDO ===
Responde exactamente INVALIDO si los mensajes cumplen CUALQUIERA de estas condiciones:
- Son saludos o despedidas (hola, buenos días, bye, gracias, etc.)
- Son respuestas de una sola palabra (sí, no, ok, claro, listo, dale, etc.)
- Son solo nombres, teléfonos, direcciones o datos de contacto
- No tienen relación con los servicios reales de {workspace_name} descritos arriba
- Son etiquetas del sistema: [PHONE], [EMAIL], [NAME], [URL], [CARD]
- No tienen contexto suficiente para entender la intención del cliente

=== CRITERIOS PARA GENERAR UNA PREGUNTA FAQ ===
Si los mensajes SÍ representan una duda real:
- Genera UNA SOLA pregunta FAQ, máximo 15 palabras
- Redactada desde la perspectiva del cliente
- Basada únicamente en los servicios reales descritos en la información del negocio
- Detecta el idioma predominante de los mensajes y responde en ese idioma
- Sin nombres propios, precios, horarios, links, correos ni teléfonos
- Usable directamente en una sección FAQ pública sin edición

=== FORMATO ===
Solo la pregunta con signos de interrogación, o la palabra INVALIDO. Sin explicaciones."""

    try:
        raw = _generate_with_ollama(prompt).strip().replace('"', '').replace("'", "")

        if not raw or "INVALIDO" in raw.upper():
            return ""

        question = raw.strip("?").strip("¿").strip()
        question = f"¿{question}?" if "¿" in raw else f"{question}?"

        return question

    except Exception as e:
        print(f"❌ Error generando pregunta FAQ: {e}")
        return ""



# Generación de respuesta FAQ 

def generate_answer_with_llm(
    question: str,
    workspace_context: dict,
    existing_answers: list[str],
    agent_texts: list[str],
) -> str:

    #Usa el LLM para generar una respuesta profesional a la pregunta FAQ.
    workspace_name = workspace_context.get("name", "la empresa")

    contexto_respuestas = "\n".join(
        f"- {answer}"
        for answer in existing_answers[:10]
        if answer
    )

    contexto_textos = "\n".join(
        f"- {text}"
        for text in agent_texts[:5]
        if text
    )

    prompt = f"""
Eres un asistente profesional de atención al cliente.

Empresa: {workspace_name}

Información del negocio:
{contexto_textos}

Respuestas que ya maneja la empresa:
{contexto_respuestas}

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
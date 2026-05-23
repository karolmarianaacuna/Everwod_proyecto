# test_faq.py

from app.services.faq_service import (
    refine_question_to_faq,
    generate_answer_with_llm,
)
from app.repositories.faq_repository import (
    get_existing_faqs_answers,
    get_agent_texts,
)

workspace_id = 126

workspace_context = {
    "name": "Everwod Technologies",
    "category": "Tecnología"
}

# Simulamos un cluster con mensajes reales de usuarios
cluster_messages = [
    "tengo 50.000 pesos en mi cuenta pero no puedo hacer transferencias",
    "cuanto valen",
    "precios porfavor",
    "quisiera saber el precio de los productos que ofrecen",
]

medoid = cluster_messages[0]

print("\n========== TEST FAQ SERVICE ==========\n")

print("💬 MENSAJES DEL CLUSTER:")
for i, msg in enumerate(cluster_messages, start=1):
    print(f"  {i}. {msg}")

# ── Cargar contexto de la BD ──────────────────────────────────────────────────
print("\n📦 Cargando contexto del workspace...")
existing_answers = [row["answer"] for row in get_existing_faqs_answers(workspace_id)]
agent_texts      = [row["text"] for row in get_agent_texts(workspace_id)]
print(f"  ✓ {len(existing_answers)} respuestas existentes")
print(f"  ✓ {len(agent_texts)} textos del agente")

# ── Generar pregunta ──────────────────────────────────────────────────────────
print("\n🤖 Generando pregunta FAQ con LLM...")

question = refine_question_to_faq(
    medoid_message=medoid,
    cluster_messages=cluster_messages,
    workspace_context=workspace_context,
)

print(f"\n❓ PREGUNTA GENERADA:")
print(question)

# ── Generar respuesta ─────────────────────────────────────────────────────────
print("\n🤖 Generando respuesta con LLM...")

answer = generate_answer_with_llm(
    question=question,
    workspace_context=workspace_context,
    existing_answers=existing_answers,
    agent_texts=agent_texts,
)

print(f"\n📝 RESPUESTA GENERADA:")
print(answer)

print("\n========== END TEST ==========\n")
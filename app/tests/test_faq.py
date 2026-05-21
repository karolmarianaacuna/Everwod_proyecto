# test_faq.py

from app.services.faq_service import (
    refine_question_to_faq,
    generate_answer_with_llm,
)

workspace_context = {
    "name": "Everwod Technologies",
    "category": "Tecnología"
}

# Simulamos un cluster con mensajes reales de usuarios
cluster_messages = [
    "no me deja iniciar sesión",
    "olvidé mi contraseña y no puedo entrar",
    "cómo recupero mi acceso a la plataforma",
    "me bloqueó la cuenta no sé qué hacer",
]

medoid = cluster_messages[0]

print("\n========== TEST FAQ SERVICE ==========\n")

print("💬 MENSAJES DEL CLUSTER:")
for i, msg in enumerate(cluster_messages, start=1):
    print(f"  {i}. {msg}")

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
)

print(f"\n📝 RESPUESTA GENERADA:")
print(answer)

print("\n========== END TEST ==========\n")
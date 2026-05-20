# app/tests/test_semantic_pipeline.py

from app.repositories.message_repository import (
    get_messages_by_workspace_id
)

from app.repositories.faq_repository import (
    get_existing_faqs
)

from app.utils.text_utils import (
    extract_message_text,
    extract_faq_text
)

from app.services.cleaning_service import (
    clean_text
)

from app.services.embedding_service import (
    generate_embedding,
    cosine_similarity,
    interpret_similarity
)


workspace_id = 126


def test_semantic_pipeline():

    # =========================================
    # TRAER MENSAJES
    # =========================================

    messages = get_messages_by_workspace_id(
        workspace_id=workspace_id
    )

    # =========================================
    # TRAER FAQS
    # =========================================

    faqs = get_existing_faqs(
        workspace_id=workspace_id
    )

    print("\n========== TEST SEMANTIC PIPELINE ==========\n")

    print(f"Mensajes encontrados: {len(messages)}")
    print(f"FAQs encontradas: {len(faqs)}")

    if not messages:
        print("\n⚠️ No hay mensajes")
        return

    if not faqs:
        print("\n⚠️ No hay FAQs")
        return

    # =========================================
    # PROBAR SOLO 5 MENSAJES
    # =========================================

    for index, row in enumerate(messages[:5], start=1):

        print("\n" + "=" * 70)

        print(f"\n📌 MENSAJE #{index}")

        message = row.get("message")

        if not message:
            print("\n⚠️ Mensaje vacío")
            continue

        # =========================================
        # EXTRAER TEXTO
        # =========================================

        original_text = extract_message_text(message)

        if not original_text:
            print("\n⚠️ No se pudo extraer texto")
            continue

        print("\n📝 ORIGINAL:")
        print(original_text)

        # =========================================
        # CLEANING
        # =========================================

        cleaned_text = clean_text(original_text)

        print("\n🧹 CLEAN TEXT:")
        print(cleaned_text)

        if not cleaned_text:
            print("\n⚠️ Texto vacío luego del cleaning")
            continue

        # =========================================
        # EMBEDDING QUERY
        # =========================================

        query_embedding = generate_embedding(
            cleaned_text
        )

        results = []

        # =========================================
        # COMPARAR VS FAQS
        # =========================================

        for faq in faqs:

            faq_text = extract_faq_text(faq)

            if not faq_text:
                continue

            faq_embedding = generate_embedding(
                faq_text
            )

            similarity = cosine_similarity(
                query_embedding,
                faq_embedding
            )

            similarity_type = interpret_similarity(
                similarity
            )

            results.append({

                "question": faq["question"],
                "answer": faq["answer"],

                "similarity": similarity,

                "similarity_type": similarity_type
            })

        # =========================================
        # ORDENAR
        # =========================================

        results.sort(
            key=lambda x: x["similarity"],
            reverse=True
        )

        # =========================================
        # TOP 3
        # =========================================

        print("\n🎯 TOP 3 FAQS MÁS PARECIDAS:\n")

        for top_index, result in enumerate(results[:3], start=1):

            print(f"\n#{top_index}")

            print("\n❓ QUESTION:")
            print(result["question"])

            print("\n📊 SIMILARITY:")
            print(round(result["similarity"], 4))

            print("\n🏷️ TYPE:")
            print(result["similarity_type"])

            print("\n" + "-" * 50)

    print("\n========== END TEST ==========\n")


if __name__ == "__main__":
    test_semantic_pipeline()
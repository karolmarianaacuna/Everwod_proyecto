import numpy as np

from app.services.embedding_service import (
    generate_embedding,
    cosine_similarity
)

from app.repositories.faq_repository import get_existing_faqs


def test_faq_similarity():

    workspace_id = 126

    faqs = get_existing_faqs(workspace_id)

    print(f"\nFAQs encontradas: {len(faqs)}\n")

    if len(faqs) < 2:
        print("Necesitas mínimo 2 FAQs")
        return

    faq1 = faqs[0]
    faq2 = faqs[1]

    text1 = f"""
    Pregunta: {faq1['question']}
    Respuesta: {faq1['answer']}
    """

    text2 = f"""
    Pregunta: {faq2['question']}
    Respuesta: {faq2['answer']}
    """

    emb1 = generate_embedding(text1)
    emb2 = generate_embedding(text2)

    similarity = cosine_similarity(
        emb1,
        emb2
    )

    print("=" * 50)

    print("\nFAQ 1:\n")
    print(text1)

    print("\nFAQ 2:\n")
    print(text2)

    print("\nSIMILITUD COSENO:")
    print(similarity)

    print("\nINTERPRETACIÓN:")

    if similarity >= 0.85:
        print("Muy similares")

    elif similarity >= 0.75:
        print("Relacionadas")

    elif similarity >= 0.60:
        print("Medianamente relacionadas")

    else:
        print("Diferentes")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    test_faq_similarity()
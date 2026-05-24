import logging
import numpy as np

from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.models.models import IngestRequest
from app.repositories.faq_repository import get_existing_faqs
from app.services.cleaning_service import clean_text



logger = logging.getLogger(__name__)

multilingual_model = settings.faq_embedding_model

faq_very_similar = settings.faq_similarity_very_similar
faq_related = settings.faq_similarity_related
faq_medium = settings.faq_similarity_medium


try:
    logger.info(f"Loading embedding model: {multilingual_model}")
    model = SentenceTransformer(multilingual_model)
    logger.info("Embedding model loaded successfully")

except Exception as error:
    logger.error(f"Error loading embedding model: {error}", exc_info=True)
    model = None


def generate_embedding(text: str, text_type: str = "passage") -> list | None:
    if not model:
        raise Exception("Embedding model not loaded")

    cleaned_text = clean_text(text)

    if not cleaned_text:
        return None

    formatted_text = f"{text_type}: {cleaned_text}"

    embedding = model.encode(
        formatted_text,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embedding.tolist()


def generate_faq_embeddings(request: IngestRequest) -> list:
    workspace_id = request.workspace_id

    logger.info(f"Getting FAQs from workspace {workspace_id}")

    faqs = get_existing_faqs(workspace_id)

    logger.info(f"FAQs found: {len(faqs)}")

    embeddings_data = []

    for faq in faqs:
        question = str(faq.get("question", "")).strip()

        if not question:
            continue

        embedding = generate_embedding(
            question,
            text_type="passage"
        )

        if embedding is None:
            continue

        embeddings_data.append({
            "workspace_id": faq.get("workspace_id"),
            "workspace_name": faq.get("workspace_name"),
            "question": question,
            "text": question,
            "embedding": embedding
        })

    logger.info(f"Generated embeddings: {len(embeddings_data)}")

    return embeddings_data


def cosine_similarity(vec1: list, vec2: list) -> float:
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    return float(np.dot(vec1, vec2))


def interpret_similarity(score: float) -> str:
    if score >= faq_very_similar:
        return "very_similar"

    if score >= faq_related:
        return "related"

    if score >= faq_medium:
        return "medium"

    return "low"


def find_similar_faqs(
    query: str,
    embeddings_data: list,
    top_k: int = 5
) -> list:
    query_embedding = generate_embedding(
        query,
        text_type="query"
    )

    if query_embedding is None:
        return []

    results = []

    for faq in embeddings_data:
        faq_embedding = faq.get("embedding")

        if not faq_embedding:
            continue

        similarity = cosine_similarity(
            query_embedding,
            faq_embedding
        )

        results.append({
            "question": faq.get("question"),
            "similarity": similarity,
            "similarity_type": interpret_similarity(similarity)
        })

    results.sort(
        key=lambda item: item["similarity"],
        reverse=True
    )

    return results[:top_k]
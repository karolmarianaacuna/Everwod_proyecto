import logging
import numpy as np

from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.models.models import IngestRequest, FAQResponse
from app.repositories.faq_repository import get_existing_faqs
from app.utils.text_utils import extract_faq_text



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
    logger.error(f"Error loading embedding model: {error}")
    model = None


#Se usa passage por que sae analizan conversaciones hosticas y el modelo fucniona o interpreta mejor con ets prefijo passage
def generate_embedding(
    text: str,
    text_type: str = "passage" 
):

    if not model:
        raise Exception("Embedding model not loaded")

    if not text.strip():
        return None

    # Prefijos requeridos por E5
    formatted_text = f"{text_type}: {text}"

    embedding = model.encode(
        formatted_text,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embedding.tolist()


def generate_faq_embeddings(request: IngestRequest):

    workspace_id = request.workspace_id

    logger.info(f"Getting FAQs from workspace {workspace_id}")

    faqs = get_existing_faqs(workspace_id)

    logger.info(f"FAQs found: {len(faqs)}")

    embeddings_data = []

    for faq in faqs:

        # convertir faq a texto
        text = extract_faq_text(faq)

        if not text:
            continue

        # embedding FAQ = passage
        embedding = generate_embedding(
            text,
            text_type="passage"
        )

        embeddings_data.append({

            "workspace_id": faq["workspace_id"],
            "workspace_name": faq["workspace_name"],

            "question": faq["question"],

            "text": text,

            "embedding": embedding
        })

    logger.info(f"Generated embeddings: {len(embeddings_data)}")

    return embeddings_data





#compara el embedding que crea y el que viene de la base de datos para no duplicar
def cosine_similarity(vec1, vec2):

    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    return float(np.dot(vec1, vec2))


def interpret_similarity(score: float):

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
):

    # embedding usuario = query
    query_embedding = generate_embedding(
        query,
        text_type="query"
    )

    results = []

    for faq in embeddings_data:

        similarity = cosine_similarity(
            query_embedding,
            faq["embedding"]
        )

        similarity_type = interpret_similarity(
            similarity
        )

        results.append({

            "question": faq["question"],

            "similarity": similarity,

            "similarity_type": similarity_type
        })

    # ordenar mayor a menor
    results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return results[:top_k]
import logging
import numpy as np
from sklearn.cluster import DBSCAN, HDBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

logger = logging.getLogger(__name__)

# ── Constantes ───────────────────────────────────────────────────────────────
SMALL_DATASET_THRESHOLD  = 20
MIN_CLUSTER_MESSAGES     = 2
DBSCAN_EPS               = 0.35
DBSCAN_MIN_SAMPLES       = 1
HDBSCAN_MIN_CLUSTER_SIZE = 2
HDBSCAN_MIN_SAMPLES      = 1
HDBSCAN_EPSILON          = 0.05
DUPLICATE_THRESHOLD      = 0.85


# ── Clustering ───────────────────────────────────────────────────────────────

def cluster_embeddings(
    embeddings: list[list[float]],
    min_cluster_size: int = HDBSCAN_MIN_CLUSTER_SIZE,
    min_samples: int = HDBSCAN_MIN_SAMPLES,
) -> list[int]:
    
    #Agrupa los embeddings usando HDBSCAN. Para datasets muy pequeños usa DBSCAN. En conjuntos moderados se omite UMAP para evitar distorsión.
    n = len(embeddings)

    if not embeddings or n < MIN_CLUSTER_MESSAGES:
        logger.warning(f"Dataset demasiado pequeño para clustering: {n} mensajes")
        return [-1] * n

    try:
        X = normalize(np.array(embeddings), norm="l2")

        if n < SMALL_DATASET_THRESHOLD:
            logger.info(f"Dataset pequeño ({n} msgs) → usando DBSCAN")
            clusterer = DBSCAN(eps=DBSCAN_EPS, min_samples=min_samples, metric="cosine")
        else:
            logger.info(f"Dataset moderado/grande ({n} msgs) → usando HDBSCAN")
            clusterer = HDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=min_samples,
                metric="cosine",
                cluster_selection_epsilon=HDBSCAN_EPSILON,
                cluster_selection_method="eom",
            )

        labels = clusterer.fit_predict(X).tolist()

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise    = labels.count(-1)
        logger.info(f"Resultado → {n_clusters} clusters, {n_noise} mensajes como ruido")

        return labels

    except Exception as e:
        logger.error(f"Error en clustering: {e}", exc_info=True)
        return [-1] * n


# ── Agrupación de mensajes ───────────────────────────────────────────────────

def group_messages_by_cluster(
    messages: list[str],
    embeddings: list[list[float]],
    labels: list[int],
) -> dict[int, dict]:

    #Organiza los mensajes y sus vectores por cada grupo encontrado. Los mensajes de ruido (label == -1) se descartan.
    clusters: dict[int, dict] = {}

    for i, label in enumerate(labels):
        if label == -1:
            continue
        if label not in clusters:
            clusters[label] = {"messages": [], "embeddings": []}
        clusters[label]["messages"].append(messages[i])
        clusters[label]["embeddings"].append(embeddings[i])

    logger.info(f"Grupos formados: {len(clusters)} clusters con mensajes válidos")
    return clusters


# ── Representante del cluster ────────────────────────────────────────────────

def get_representative_message(
    cluster_messages: list[str],
    cluster_embeddings: list[list[float]],
) -> str:

    #Encuentra el medoide: el mensaje más céntrico del grupo. A diferencia del centroide, el medoide es un texto real del dataset.
    if not cluster_messages:
        return ""

    if len(cluster_messages) == 1:
        return cluster_messages[0]

    try:
        sim_matrix = cosine_similarity(cluster_embeddings)
        medoid_idx = int(np.argmax(np.sum(sim_matrix, axis=0)))
        return cluster_messages[medoid_idx]

    except Exception as e:
        logger.error(f"Error calculando medoide: {e}", exc_info=True)
        return max(cluster_messages, key=len)


# ── Deduplicación ────────────────────────────────────────────────────────────

def is_duplicate_faq(
    new_question_emb: list[float],
    existing_faqs_embs: np.ndarray | None,
    threshold: float = DUPLICATE_THRESHOLD,
) -> bool:
    
    #Retorna True si la pregunta nueva es semánticamente duplicada de alguna FAQ existente en el workspace.
    if existing_faqs_embs is None or len(existing_faqs_embs) == 0:
        return False

    similarities = cosine_similarity([new_question_emb], existing_faqs_embs)
    return bool(np.max(similarities) >= threshold)
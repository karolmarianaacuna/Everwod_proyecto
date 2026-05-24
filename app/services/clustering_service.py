import logging
import numpy as np

from sklearn.cluster import DBSCAN
import hdbscan as hdbscan_lib

from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from sklearn.preprocessing import normalize

from app.core.config import settings

logger = logging.getLogger(__name__)


def cluster_embeddings(
    embeddings: list[list[float]],
    min_cluster_size: int | None = None,
    min_samples: int | None = None,
) -> list[int]:

    n = len(embeddings)

    if not embeddings or n < settings.clustering_min_cluster_messages:
        logger.warning(f"Dataset demasiado pequeño para clustering: {n} mensajes")
        return [-1] * n

    min_cluster_size = min_cluster_size or settings.clustering_hdbscan_min_cluster_size
    min_samples = min_samples or settings.clustering_hdbscan_min_samples

    try:
        X = normalize(np.array(embeddings, dtype=np.float64), norm="l2")

        if n < settings.clustering_small_dataset_threshold:
            logger.info(f"Dataset pequeño ({n} msgs) → usando DBSCAN")
            clusterer = DBSCAN(
                eps=settings.clustering_dbscan_eps,
                min_samples=settings.clustering_dbscan_min_samples,
                metric="cosine"
            )
            labels = clusterer.fit_predict(X).tolist()

        else:
            logger.info(f"Dataset moderado/grande ({n} msgs) → usando HDBSCAN")
            clusterer = hdbscan_lib.HDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=min_samples,
                metric="euclidean",
                cluster_selection_epsilon=settings.clustering_hdbscan_epsilon,
                cluster_selection_method="eom",
            )
            labels = clusterer.fit_predict(X).tolist()

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = labels.count(-1)
        logger.info(f"Resultado → {n_clusters} clusters, {n_noise} mensajes como ruido")
        return labels
        
    except Exception as e:
        logger.error(f"Error en clustering: {e}", exc_info=True)
        return [-1] * n


def group_messages_by_cluster(
    messages: list[str],
    embeddings: list[list[float]],
    labels: list[int],
) -> dict[int, dict]:

    clusters: dict[int, dict] = {}
    for i, label in enumerate(labels):
        if label == -1:
            continue

        if label not in clusters:
            clusters[label] = {
                "messages": [],
                "embeddings": []
            }

        clusters[label]["messages"].append(messages[i])
        clusters[label]["embeddings"].append(embeddings[i])
    
    logger.info(f"Grupos formados: {len(clusters)} clusters con mensajes válidos")

    return clusters


def get_representative_message(
    cluster_messages: list[str],
    cluster_embeddings: list[list[float]],
) -> str:

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


def is_duplicate_faq(
    new_question_emb: list[float],
    existing_faqs_embs: np.ndarray | None,
    threshold: float | None = None,
) -> bool:

    if threshold is None:
        threshold = settings.clustering_duplicate_threshold

    if existing_faqs_embs is None or len(existing_faqs_embs) == 0:
        return False
    
    similarities = cosine_similarity([new_question_emb], existing_faqs_embs)
    return bool(np.max(similarities) >= threshold)
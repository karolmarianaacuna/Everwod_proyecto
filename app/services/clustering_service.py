import logging
import numpy as np

from sklearn.cluster import DBSCAN, HDBSCAN
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from sklearn.preprocessing import normalize

from app.core.config import settings

logger = logging.getLogger(__name__)

<<<<<<< HEAD

=======
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
>>>>>>> 04c9ac6da5ce4c460b74aa80c4f13ec6b44338ce
def cluster_embeddings(
    embeddings: list[list[float]],
    min_cluster_size: int | None = None,
    min_samples: int | None = None,
) -> list[int]:
<<<<<<< HEAD

    n = len(embeddings)

    if not embeddings or n < settings.clustering_min_cluster_messages:
        logger.warning(f"Dataset demasiado pequeño para clustering: {n} mensajes")
        return [-1] * n

    min_cluster_size = min_cluster_size or settings.clustering_hdbscan_min_cluster_size
    min_samples = min_samples or settings.clustering_hdbscan_min_samples

    try:
        X = normalize(np.array(embeddings, dtype=np.float64), norm="l2")

        if n < settings.clustering_small_dataset_threshold:
=======
    """
    Agrupa los embeddings usando HDBSCAN. Para datasets muy pequeños usa DBSCAN. 
    En conjuntos moderados se omite UMAP para evitar distorsión.
    """
    n = len(embeddings)
    if not embeddings or n < MIN_CLUSTER_MESSAGES:
        logger.warning(f"Dataset demasiado pequeño para clustering: {n} mensajes")
        return [-1] * n
    
    try:
        X = normalize(np.array(embeddings), norm="l2")
        
        if n < SMALL_DATASET_THRESHOLD:
>>>>>>> 04c9ac6da5ce4c460b74aa80c4f13ec6b44338ce
            logger.info(f"Dataset pequeño ({n} msgs) → usando DBSCAN")
            clusterer = DBSCAN(
                eps=settings.clustering_dbscan_eps,
                min_samples=settings.clustering_dbscan_min_samples,
                metric="cosine"
            )
            labels = clusterer.fit_predict(X).tolist()

        else:
            logger.info(f"Dataset moderado/grande ({n} msgs) → usando HDBSCAN")
            # Precomputar matriz de distancias para evitar bug de sklearn HDBSCAN
            dist_matrix = euclidean_distances(X).astype(np.float64)
            clusterer = HDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=min_samples,
                metric="precomputed",
                cluster_selection_epsilon=settings.clustering_hdbscan_epsilon,
                cluster_selection_method="eom",
<<<<<<< HEAD
                copy=True,  # silencia el FutureWarning
            )
            labels = clusterer.fit_predict(dist_matrix).tolist()

=======
                copy=True,  # FIX: Soluciona el FutureWarning
            )
        
        # FIX: Convertir correctamente el array a lista para evitar TypeError
        labels_array = clusterer.fit_predict(X)
        labels = np.asarray(labels_array, dtype=int).tolist()
        
>>>>>>> 04c9ac6da5ce4c460b74aa80c4f13ec6b44338ce
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = labels.count(-1)
        logger.info(f"Resultado → {n_clusters} clusters, {n_noise} mensajes como ruido")
        return labels
        
    except Exception as e:
        logger.error(f"Error en clustering: {e}", exc_info=True)
        return [-1] * n


<<<<<<< HEAD
=======
# ── Agrupación de mensajes ───────────────────────────────────────────────────
>>>>>>> 04c9ac6da5ce4c460b74aa80c4f13ec6b44338ce
def group_messages_by_cluster(
    messages: list[str],
    embeddings: list[list[float]],
    labels: list[int],
) -> dict[int, dict]:
<<<<<<< HEAD

=======
    """
    Organiza los mensajes y sus vectores por cada grupo encontrado. 
    Los mensajes de ruido (label == -1) se descartan.
    """
>>>>>>> 04c9ac6da5ce4c460b74aa80c4f13ec6b44338ce
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


<<<<<<< HEAD
=======
# ── Representante del cluster ────────────────────────────────────────────────
>>>>>>> 04c9ac6da5ce4c460b74aa80c4f13ec6b44338ce
def get_representative_message(
    cluster_messages: list[str],
    cluster_embeddings: list[list[float]],
) -> str:
<<<<<<< HEAD

=======
    """
    Encuentra el medoide: el mensaje más céntrico del grupo. 
    A diferencia del centroide, el medoide es un texto real del dataset.
    """
>>>>>>> 04c9ac6da5ce4c460b74aa80c4f13ec6b44338ce
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


<<<<<<< HEAD
=======
# ── Deduplicación ────────────────────────────────────────────────────────────
>>>>>>> 04c9ac6da5ce4c460b74aa80c4f13ec6b44338ce
def is_duplicate_faq(
    new_question_emb: list[float],
    existing_faqs_embs: np.ndarray | None,
    threshold: float | None = None,
) -> bool:
<<<<<<< HEAD

    if threshold is None:
        threshold = settings.clustering_duplicate_threshold

=======
    """
    Retorna True si la pregunta nueva es semánticamente duplicada 
    de alguna FAQ existente en el workspace.
    """
>>>>>>> 04c9ac6da5ce4c460b74aa80c4f13ec6b44338ce
    if existing_faqs_embs is None or len(existing_faqs_embs) == 0:
        return False
    
    similarities = cosine_similarity([new_question_emb], existing_faqs_embs)
    return bool(np.max(similarities) >= threshold)
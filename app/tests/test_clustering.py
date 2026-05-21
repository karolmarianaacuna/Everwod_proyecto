# test_clustering.py

from app.repositories.message_repository import get_messages_by_workspace_id
from app.services.cleaning_service import clean_text
from app.services.embedding_service import generate_embedding
from app.services.clustering_service import (
    cluster_embeddings,
    group_messages_by_cluster,
    get_representative_message,
)

workspace_id = 126
MIN_WORDS    = 3


def extract_text(message: dict) -> str:
    """Extrae el texto de la estructura real del campo message en la BD."""
    try:
        return message["content"][0]["text"]["value"].strip()
    except (KeyError, IndexError, TypeError):
        return ""


print("\n========== TEST CLUSTERING ==========\n")

# ── Traer mensajes ────────────────────────────────────────────────────────────
rows = get_messages_by_workspace_id(workspace_id=workspace_id)
print(f"📩 Mensajes encontrados: {len(rows)}")

# ── Limpiar ───────────────────────────────────────────────────────────────────
cleaned_messages = []
raw_messages     = []

for row in rows:
    raw_text = extract_text(row.get("message", {}))
    cleaned  = clean_text(raw_text)

    if len(cleaned.split()) < MIN_WORDS:
        continue

    raw_messages.append(raw_text)
    cleaned_messages.append(cleaned)

print(f"🧹 Mensajes válidos tras limpieza: {len(cleaned_messages)}")

if not cleaned_messages:
    print("⚠️ No hay mensajes suficientes para clustering")
    exit()

# ── Embeddings ────────────────────────────────────────────────────────────────
print("\n🧠 Generando embeddings...")

embeddings    = []
valid_cleaned = []

for cleaned in cleaned_messages:
    emb = generate_embedding(cleaned, text_type="passage")
    if emb is None:
        continue
    embeddings.append(emb)
    valid_cleaned.append(cleaned)

print(f"✅ Embeddings generados: {len(embeddings)}")

# ── Clustering ────────────────────────────────────────────────────────────────
print("\n📊 Ejecutando clustering...")

labels   = cluster_embeddings(embeddings)
clusters = group_messages_by_cluster(valid_cleaned, embeddings, labels)

print(f"✅ Clusters encontrados: {len(clusters)}")

# ── Resultados por cluster ────────────────────────────────────────────────────
for cluster_id, cluster_data in clusters.items():

    messages           = cluster_data["messages"]
    cluster_embeddings = cluster_data["embeddings"]

    print("\n" + "=" * 50)
    print(f"🏷️  CLUSTER {cluster_id} — {len(messages)} mensajes")

    medoid = get_representative_message(messages, cluster_embeddings)

    print(f"\n📌 MEDOIDE:")
    print(medoid)

    print(f"\n💬 MUESTRA DE MENSAJES:")
    for i, msg in enumerate(messages[:3], start=1):
        print(f"  {i}. {msg}")

print("\n========== END TEST ==========\n")
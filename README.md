# 🤖 Everwod - Pipeline de Clustering Semántico para FAQs Automáticas

> **Arquitectura profesional de NLP/ML** para detectar automáticamente preguntas frecuentes desde conversaciones de usuarios utilizando embeddings semánticos y clustering DBSCAN.

## 🎯 Características

- ✅ **Carga automática** de mensajes desde PostgreSQL
- ✅ **Limpieza inteligente** de texto conversacional
- ✅ **Anonimización automática** de datos sensibles (PII)
- ✅ **Embeddings semánticos** con SentenceTransformers (384-dim)
- ✅ **Clustering automático** con DBSCAN (sin especificar K)
- ✅ **Detección inteligente** de FAQs con scoring
- ✅ **Validación de calidad** de clusters
- ✅ **API REST** con FastAPI
- ✅ **Logging profundo** y monitoreo

## 📊 Flujo de Datos

```
Mensajes (BD)
    ↓ [LOAD]
Mensajes Validados
    ↓ [CLEAN]
Texto Limpio + Anonimizado
    ↓ [DEDUP]
Mensajes Únicos
    ↓ [EMBED]
Vectores 384-dim
    ↓ [CLUSTER]
Grupos Semánticos
    ↓ [FAQ]
Preguntas Frecuentes
```

## 🚀 Quick Start

### Instalación

```bash
# Clonar proyecto
cd everwod_proyecto

# Activar entorno
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\Activate.ps1  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### Test Local

```bash
python test_pipeline.py
```

**Salida esperada:**
```
=== TEST DEL PIPELINE ===
✓ Pipeline inicializado
✓ Mensajes cargados: 19
✓ Clusters encontrados: 4
✓ FAQs detectadas: 3
✓ Tiempo: 8.32s
✅ TEST COMPLETADO EXITOSAMENTE
```

### Usar API

```bash
# Iniciar servidor
uvicorn app.main:app --reload --port 8000

# En otra terminal
curl -X POST http://localhost:8000/api/cluster/ingest \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": 1}'

# Ver docs interactivas
# http://localhost:8000/docs
```

## 📚 Documentación

| Archivo | Descripción |
|---------|------------|
| **[EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)** | Resumen ejecutivo (2 min lectura) |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Guía técnica completa (20 min lectura) |
| **[USAGE_GUIDE.md](USAGE_GUIDE.md)** | Ejemplos prácticos (15 min lectura) |
| **[test_pipeline.py](test_pipeline.py)** | Test ejecutable |

**Recomendación:** Empezar por [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)

## 🏗️ Arquitectura

### Componentes Principales

```
app/
├── core/
│   ├── config.py              # 🔧 Configuración centralizada
│   └── database.py            # 🗄️ Conexión PostgreSQL
├── models/
│   └── models.py              # 📋 Esquemas Pydantic
├── repositories/
│   ├── message_repository.py  # 📖 Queries BD
│   └── faq_repository.py      # 💾 Persistencia FAQs
├── services/
│   ├── cleaning_service.py    # 🧹 Limpieza + anonimización
│   ├── ingest_service.py      # 📥 Orquestador
│   ├── pipeline_service.py    # ⭐ Pipeline principal (600+ líneas)
│   ├── embedding_utils.py     # 🔬 Análisis embeddings
│   ├── debug_tools.py         # 🐛 Debugging
│   └── llm_service.py         # 🤖 LLM (futuro)
└── main.py                    # 🚀 FastAPI app
```

### Flujo del Pipeline

```python
from app.services.pipeline_service import SemanticClusteringPipeline

pipeline = SemanticClusteringPipeline()

clusters, faq_candidates, stats = pipeline.run_pipeline(
    messages=messages,
    workspace_id=1,
    skip_deduplication=False,
    quality_threshold=0.3,
)

print(f"Clusters encontrados: {len(clusters)}")
print(f"FAQs detectadas: {len(faq_candidates)}")
print(f"Tiempo: {stats.processing_time_seconds:.2f}s")
```

## 📊 Estadísticas Tipicas

Para **1000 mensajes de usuarios**:

```
Entrada:                 1000 crudos
├─ Limpieza:              850 válidos (-150 ruido)
├─ Deduplicación:         780 únicos (-70 duplicados)
└─ Filtrado calidad:      720 finales (-60 baja calidad)

Embeddings:              720 vectores (384-dim)

Clustering:              12 clusters + 8 outliers

FAQs Detectadas:         8-10 de alta confianza

Performance:             45-60 segundos
```

## ⚙️ Configuración

Todos los parámetros en `.env`:

```env
# Base de datos
DB_NAME=db_everwod
DB_USER=postgres
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432

# Embeddings
FAQ_EMBEDDING_MODEL=all-MiniLM-L6-v2
FAQ_DUPLICATE_THRESHOLD=0.78

# Clustering (DBSCAN)
FAQ_CLUSTER_EPS=0.34              # ← Ajustable
FAQ_MIN_CLUSTER_SIZE=3            # ← Ajustable

# Limpieza
MIN_TEXT_LENGTH=5
MIN_TOKENS_AFTER_CLEAN=2

# Performance
BATCH_SIZE=32
EMBEDDING_BATCH_SIZE=64
ENABLE_CACHE=true

# Debugging
LOG_LEVEL=INFO
VERBOSE=false
```

## 🔍 Casos de Uso

### 1. Generar FAQs Automáticamente
```python
clusters, faqs, stats = pipeline.run_pipeline(messages)

for faq in faqs[:5]:
    print(f"❓ {faq.question}")
    print(f"   Confianza: {faq.confidence_score:.0%}")
```

### 2. Monitorear Calidad
```python
metrics = pipeline.get_pipeline_metrics(clusters)
print(f"Avg cluster size: {metrics['avg_cluster_size']:.1f}")
print(f"Clusters saludables: {len(clusters)}")
```

### 3. Análisis Temporal
```python
# Ejecutar clustering por período
for month in ['2024-01', '2024-02', '2024-03']:
    messages = db.get_messages_by_period(month)
    _, faqs, stats = pipeline.run_pipeline(messages)
    print(f"{month}: {len(faqs)} FAQs en {stats.processing_time_seconds:.1f}s")
```

### 4. Búsqueda de Similares
```python
from app.services.embedding_utils import EmbeddingAnalyzer

query_text = "¿Cómo hago para pagar?"
query_embedding = pipeline.embedding_model.encode(query_text)

analyzer = EmbeddingAnalyzer()
similar = analyzer.find_similar_messages(
    query_embedding,
    candidate_embeddings,
    top_k=5,
    min_similarity=0.5
)
```

## 🛡️ Características de Robustez

### Anonimización Automática
```
Email:        usuario@ejemplo.com  → [EMAIL]
Teléfono:     +34 123 456 7890     → [PHONE]
Tarjeta:      1234-5678-9012-3456  → [CARD]
IP:           192.168.1.1          → [IP]
```

### Validación de Calidad
```python
✓ Score de calidad por mensaje (0-1)
✓ Detección de ruido (outliers)
✓ Validación de coherencia de clusters
✓ Métricas de separación entre clusters
```

### Manejo de Errores
```python
✓ Mensajes malformados
✓ Conexión BD caída
✓ OOM (reducción automática)
✓ Modelos no disponibles
✓ Edge cases (texto vacío, solo emojis, etc)
```

## 📈 Performance

| Escala | Mensajes | Tiempo | Memory |
|--------|----------|--------|--------|
| Pequeño | 1K | 30-60s | 2GB |
| Medio | 10K | 5-15min | 3GB |
| Grande | 100K | 1-2hrs | 4GB* |

*Con optimizaciones (paralelización, reducción dimensionalidad)

## 🧪 Testing

```bash
# Test local
python test_pipeline.py

# Test con datos reales (necesita BD)
python -c "from app.services.ingest_service import IngestService; ..."

# Test API
curl -X POST http://localhost:8000/api/cluster/ingest \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": 1}'
```

## 🔧 Ajuste de Parámetros

**Muchos clusters pequeños?** → Aumentar `eps` (0.40)  
**Pocos clusters grandes?** → Disminuir `eps` (0.28)  
**Mucho ruido?** → Aumentar `eps` + reducir `quality_threshold`  
**Baja calidad?** → Aumentar `min_cluster_size` + disminuir `eps`  

Ver [USAGE_GUIDE.md](USAGE_GUIDE.md) para guía completa de ajuste.

## 🚀 Deploying

### Docker (Futuro)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

### Kubernetes (Futuro)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: clustering-pipeline
spec:
  replicas: 2
  containers:
  - name: pipeline
    image: everwod:1.0.0
    ports:
    - containerPort: 8000
```

## 📋 Roadmap

**Versión 1.0** (Actual) ✅
- [x] Pipeline core de clustering
- [x] API REST básica
- [x] Documentación completa

**Versión 1.1** (Próximo)
- [ ] LLM para generar preguntas naturales
- [ ] Persistencia de FAQs en BD
- [ ] Búsqueda FAISS

**Versión 2.0**
- [ ] Fine-tuning de embeddings
- [ ] Análisis temporal
- [ ] Dashboard web

## 📞 Soporte

- **Documentación técnica:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Ejemplos prácticos:** [USAGE_GUIDE.md](USAGE_GUIDE.md)
- **Debugging:** `app/services/debug_tools.py`
- **Test suite:** `test_pipeline.py`

## 📄 Licencia

MIT License - Ver LICENSE.md

## 👥 Autor

Diseñado por: **ML/NLP Senior Architect**  
Especialización: Clustering Semántico y Sistemas de FAQs  
Versión: 1.0.0  
Fecha: Mayo 2026

---

## 🎓 Aprender Más

1. **Comenzar aquí:** [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)
2. **Entender técnica:** [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Usar en producción:** [USAGE_GUIDE.md](USAGE_GUIDE.md)
4. **Ver código:** Comentarios en `pipeline_service.py`

---

**¿Listo para detectar FAQs automáticamente?** 🚀

```bash
python test_pipeline.py
```

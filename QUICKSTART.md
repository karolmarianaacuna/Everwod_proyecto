# 🚀 Everwod - Generador Automático de FAQs

## ¿Qué hace?

**Everwod analiza los mensajes que envían tus clientes y sugiere automáticamente preguntas frecuentes (FAQs) basadas en ellos.**

### Flujo Simple
```
Mensajes de Clientes → Análisis IA → Clustering → Generación de FAQs
```

## 🏃 Cómo Usar

### 1️⃣ Iniciar la aplicación

```bash
cd /Users/julianag/EverwodIA/Everwod_proyecto
python run.py
```

O con uvicorn:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2️⃣ Ver documentación interactiva

Abre en tu navegador:
```
http://localhost:8000/docs
```

### 3️⃣ Ver los workspaces disponibles

```bash
curl http://localhost:8000/api/v1/workspaces
```

### 4️⃣ Analizar mensajes y sugerir FAQs

Para un workspace específico (ej: workspace_id = 1):

```bash
curl -X POST http://localhost:8000/api/v1/workspaces/1/analyze
```

### 5️⃣ Ver las FAQs sugeridas

```bash
curl http://localhost:8000/api/v1/workspaces/1/faqs
```

## 📚 Endpoints Principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/v1/workspaces` | Listar todos los workspaces |
| `POST` | `/api/v1/workspaces/{id}/analyze` | **Analizar mensajes y sugerir FAQs** |
| `GET` | `/api/v1/workspaces/{id}/faqs` | Ver FAQs sugeridas de un workspace |
| `GET` | `/api/v1/info` | Info de la aplicación |
| `GET` | `/health` | Estado de la app |
| `GET` | `/docs` | Documentación (Swagger) |

## ⚙️ Requisitos

- Python 3.13+
- PostgreSQL (db_everwod con las tablas)
- Ollama corriendo localmente (http://localhost:11434)
  - Modelo: qwen2.5:7b

## 📦 Instalación de Dependencias

```bash
pip install -r requirements.txt
```

## 🧪 Tests

```bash
# Todos los tests (47 tests)
python -m pytest app/tests/ -v

# Con coverage
python -m pytest app/tests/ --cov=app --cov-report=html
```

## 📊 Cómo Funciona el Análisis

1. **Obtiene** todos los mensajes del workspace
2. **Limpia** el texto (remove stopwords, normaliza)
3. **Genera embeddings** multilingual (intfloat/multilingual-e5-base)
4. **Agrupa** mensajes similares (clustering con sklearn)
5. **Genera** preguntas FAQ de cada grupo
6. **Genera** respuestas con IA (Ollama qwen2.5:7b)
7. **Guarda** las FAQs en la base de datos
8. **Retorna** las FAQs sugeridas

## 🔧 Configuración

Edita `.env` para cambiar:
- Host/puerto de PostgreSQL
- Modelo de embeddings
- Modelo LLM
- Thresholds de similitud

## 💡 Ejemplo Completo

```bash
# 1. Ver workspaces
curl http://localhost:8000/api/v1/workspaces | python -m json.tool

# 2. Analizar workspace 1
curl -X POST http://localhost:8000/api/v1/workspaces/1/analyze | python -m json.tool

# 3. Ver FAQs sugeridas
curl http://localhost:8000/api/v1/workspaces/1/faqs | python -m json.tool
```

## ✅ Status

- ✅ 47 tests pasando
- ✅ Tests de job_service: 19/19
- ✅ Tests de pipeline_service: 28/28
- ✅ API REST completa
- ✅ Documentación Swagger incluida

¡Listo para usar! 🎉

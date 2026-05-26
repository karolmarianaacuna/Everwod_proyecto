
# Microservicio de Análisis de Conversaciones con IA (RAG + NLP)
## Proyecto para la empresa Everwod Technologies 

Se desarrolló un pipeline automatizado que permite la mejora continua de agentes de IA mediante el análisis periódico de conversaciones reales, asi mismo se debe tener en cuenta que se va Generar FAQs segmentadas por workspace (cliente/empresa)

## Obejetivo de este poryecto 

Permitir a la empresa:

    - Detectar preguntas frecuentes reales de usuarios
    - Mejorar la atención al cliente
    - Identificar fallas en procesos (pagos, envíos, etc.)
    - Automatizar la generación de conocimiento


## Arquitectura de microservicios 

El sistema sigue una arquitectura de **microservicios**, separando responsabilidades:

    **API → Services → Repository → Base de Datos**

Además incluye:

 -Pipeline de procesamiento NLP
 -Scheduler automático
 -Interfaz de validación (Streamlit)

## Estructura del proyecto


EVERWOD_PROYECTO/
│
├── app/
│   ├── main.py
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   ├── repository/
│   ├── scheduler/
│   ├── utils/
│
├── streamlit_app/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env

---

## Entorno de Desarrollo

### 1. Crear entorno virtual

Se recomienda crear un entorno virtual para gestionar correctamente las dependencias del proyecto:


python -m venv venv

# Windows
venv/Scripts/activate

# Linux / Mac
source venv/bin/activate

pip install -r requirements.txt

# Ejecutar tests por archivo
pytest tests/test_cleaning.py
pytest tests/test_cleaning_embedding.py
pytest tests/test_embedding_utils.py
pytest tests/test_clustering.py
pytest tests/test_faq.py

## Ejecución local (FastAPI)

1. Desde la carpeta `everwod_proyecto` ejecutar:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

2. Endpoints útiles:

- `GET /api/v1/workspaces` — listar workspaces
- `GET /api/v1/workspaces/{id}/faqs` — obtener FAQs del workspace
- `GET /api/v1/workspaces/{id}/accepted-faqs` — FAQs aceptadas
- `GET /api/v1/workspaces/{id}/rejected-faqs` — FAQs rechazadas
- `POST /api/v1/workspaces/{id}/analyze` — ejecutar análisis (pipeline) para un workspace
- `POST /api/v1/faqs/review` — aceptar/rechazar una FAQ (payload JSON: `action`, `workspace_id`, `agent_id`, `question`, `answer`, `cluster_id`, `cluster_size`, `confidence`)

## Notas adicionales
- Asegúrate de configurar `.env` basado en `.env.example` con la conexión a la base de datos y modelos de embeddings/LLM.
- Para probar endpoints desde PowerShell usa `Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/workspaces" | ConvertTo-Json -Depth 5`.

## Cómo contribuir

Si vas a colaborar en el backend, sigue este flujo mínimo:

1. Crea una branch con nombre descriptivo: `git checkout -b feat/mi-cambio`.
2. Asegúrate de tener un entorno virtual limpio y variables en `.env`.
3. Ejecuta las pruebas relevantes antes de abrir PR:

```powershell
# ejecutar todos los tests
pytest -q

# ejecutar un archivo específico
pytest app/tests/test_pipeline_service.py::TestGenerateEmbeddings::test_generate_embeddings_success
```

4. Añade tests para cambios significativos y actualiza `requirements.txt` si agregas dependencias.
5. Abre un Pull Request describiendo el cambio y cómo probarlo localmente.

Checklist rápido antes de merge:
- [ ] Tests pasan localmente
- [ ] Linters (si aplican) limpios
- [ ] Documentación o README actualizados si cambian endpoints o comportamientos



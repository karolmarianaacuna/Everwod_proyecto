
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
python tests/test_clustering
python tests/test_faq


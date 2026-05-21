"""
main.py - Punto de entrada de la aplicación FastAPI de Everwod
Microservicio de Análisis de Conversaciones con IA (RAG + NLP)
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.config import settings
from app.services.pipeline_service import PipelineService
from app.services.job_service import FAQJobs, MaintenanceJobs
from app.repositories.faq_repository import get_existing_faqs, get_all_workspaces

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────
# MODELOS
# ──────────────────────────────────────────────────────────────────────────

class HealthCheckResponse(BaseModel):
    """Respuesta de chequeo de salud"""
    status: str
    timestamp: str
    version: str


class PipelineRequest(BaseModel):
    """Request para ejecutar el pipeline"""
    workspace_id: int


class PipelineResponse(BaseModel):
    """Response del pipeline"""
    workspace_id: int
    status: str
    faqs_generated: int
    clusters_found: int


class ReloadFAQsRequest(BaseModel):
    """Request para recargar FAQs"""
    workspace_id: int


class FAQItem(BaseModel):
    """Modelo para una FAQ"""
    workspace_id: int
    workspace_name: str
    question: str
    answer: str


class WorkspaceItem(BaseModel):
    """Modelo para un workspace"""
    id: int
    name: str
    description: str | None = None


# ──────────────────────────────────────────────────────────────────────────
# LIFESPAN
# ──────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación
    - Startup: inicializar servicios
    - Shutdown: limpiar recursos
    """
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 INICIANDO APLICACIÓN EVERWOD")
    logger.info("=" * 60)
    logger.info(f"⚙️ Base de datos: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    logger.info(f"📦 Modelo embedding: {settings.faq_embedding_model}")
    logger.info(f"🤖 Modelo LLM: {settings.faq_llm_model}")
    logger.info("=" * 60)
    logger.info("✅ Aplicación inicializada correctamente")
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("🛑 DETENIENDO APLICACIÓN EVERWOD")
    logger.info("=" * 60)


# ──────────────────────────────────────────────────────────────────────────
# APLICACIÓN
# ──────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Everwod - Generador Automático de FAQs",
    description="Microservicio que analiza mensajes de clientes y sugiere preguntas frecuentes (FAQs) automáticamente usando IA",
    version="1.0.0",
    lifespan=lifespan,
)

# Inicializar servicio
pipeline_service = PipelineService()


# ──────────────────────────────────────────────────────────────────────────
# RUTAS - HEALTH
# ──────────────────────────────────────────────────────────────────────────

@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Health"],
    summary="Verificar salud de la aplicación"
)
def health_check():
    """
    Endpoint para verificar que la aplicación está activa y funcionando.
    
    Returns:
        HealthCheckResponse con status y timestamp
    """
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@app.get(
    "/health/detailed",
    tags=["Health"],
    summary="Verificar salud detallada del sistema"
)
def detailed_health_check():
    """
    Endpoint para verificar la salud de todos los componentes del sistema.
    
    Verifica:
    - Conexión a base de datos
    - Disponibilidad del modelo de embeddings
    - Disponibilidad del LLM (Ollama)
    - Almacenamiento disponible
    """
    logger.info("🏥 Realizando chequeo de salud detallado...")
    MaintenanceJobs.check_system_health()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "Todos los sistemas funcionan correctamente"
    }


# ──────────────────────────────────────────────────────────────────────────
# RUTAS - FAQs POR WORKSPACE
# ──────────────────────────────────────────────────────────────────────────

@app.get(
    "/api/v1/workspaces",
    tags=["Workspaces"],
    summary="Listar todos los workspaces"
)
def list_workspaces():
    """
    Retorna la lista de todos los workspaces disponibles.
    
    Returns:
        Lista de workspaces
    """
    try:
        logger.info("📋 Obteniendo lista de workspaces...")
        
        workspaces = get_all_workspaces()
        
        logger.info(f"✅ Se encontraron {len(workspaces)} workspaces")
        return {
            "status": "success",
            "count": len(workspaces),
            "workspaces": workspaces,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo workspaces: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching workspaces: {str(e)}"
        )


@app.get(
    "/api/v1/workspaces/{workspace_id}/faqs",
    tags=["Workspaces"],
    summary="Obtener FAQs sugeridas de un workspace"
)
def get_workspace_faqs(workspace_id: int):
    """
    Retorna las FAQs generadas/sugeridas para un workspace específico.
    Estas FAQs se generan a partir del análisis de los mensajes de los clientes.
    
    Args:
        workspace_id: ID del workspace
        
    Returns:
        Lista de FAQs generadas para el workspace
    """
    try:
        logger.info(f"🔍 Obteniendo FAQs para workspace {workspace_id}...")
        
        faqs = get_existing_faqs(workspace_id)
        
        logger.info(f"✅ Se encontraron {len(faqs)} FAQs para workspace {workspace_id}")
        return {
            "status": "success",
            "workspace_id": workspace_id,
            "count": len(faqs),
            "faqs": faqs,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo FAQs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching FAQs: {str(e)}"
        )


# ──────────────────────────────────────────────────────────────────────────
# RUTAS - PIPELINE
# ──────────────────────────────────────────────────────────────────────────

@app.post(
    "/api/v1/workspaces/{workspace_id}/analyze",
    tags=["Workspaces"],
    summary="Analizar mensajes y sugerir FAQs"
)
def analyze_and_suggest_faqs(workspace_id: int):
    """
    Analiza los mensajes de los clientes de un workspace y sugiere FAQs automáticamente.
    
    Pasos:
    1. Obtener todos los mensajes del workspace
    2. Limpiar y procesar el texto
    3. Generar embeddings multilingual
    4. Agrupar mensajes similares (clustering)
    5. Generar preguntas FAQ a partir de los clusters
    6. Generar respuestas con IA (Ollama)
    7. Guardar FAQs sugeridas en la base de datos
    
    Args:
        workspace_id: ID del workspace a analizar
        
    Returns:
        FAQs sugeridas y estadísticas del análisis
        
    Raises:
        HTTPException: Si hay error en el análisis
    """
    try:
        logger.info(f"🔬 Analizando mensajes y sugiriendo FAQs para workspace {workspace_id}...")
        
        # Ejecutar pipeline de análisis
        result = pipeline_service.execute_pipeline(workspace_id)
        
        if result.get("status") != "success":
            logger.error(f"❌ Análisis falló: {result.get('error')}")
            raise HTTPException(
                status_code=400,
                detail=f"Analysis failed: {result.get('error')}"
            )
        
        stats = result.get("stats", {})
        suggested_faqs = result.get("faqs_generated", [])
        
        logger.info(f"✅ Análisis completado")
        logger.info(f"   • FAQs sugeridas: {stats.get('faqs_generated')}")
        logger.info(f"   • Grupos de mensajes similares: {stats.get('clusters')}")
        
        return {
            "status": "success",
            "workspace_id": workspace_id,
            "message": "Mensajes analizados y FAQs sugeridas exitosamente",
            "analysis_stats": {
                "faqs_generated": stats.get("faqs_generated", 0),
                "clusters_found": stats.get("clusters", 0),
                "messages_processed": stats.get("messages_processed", 0)
            },
            "suggested_faqs": suggested_faqs,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error analizando mensajes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@app.post(
    "/api/v1/pipeline/execute",
    response_model=PipelineResponse,
    tags=["Pipeline"],
    summary="Ejecutar pipeline de análisis (heredado)"
)
def execute_pipeline(request: PipelineRequest):
    """
    ⚠️ HEREDADO - Usar: POST /api/v1/workspaces/{workspace_id}/analyze
    
    Ejecuta el pipeline completo de análisis de conversaciones para un workspace.
    
    Args:
        request: PipelineRequest con workspace_id
        
    Returns:
        PipelineResponse con resultados del pipeline
        
    Raises:
        HTTPException: Si hay error en la ejecución
    """
    try:
        logger.info(f"▶️ Ejecutando pipeline para workspace: {request.workspace_id}")
        
        result = pipeline_service.execute_pipeline(request.workspace_id)
        
        if result.get("status") != "success":
            logger.error(f"❌ Pipeline falló: {result.get('error')}")
            raise HTTPException(
                status_code=400,
                detail=f"Pipeline failed: {result.get('error')}"
            )
        
        stats = result.get("stats", {})
        
        logger.info(f"✅ Pipeline completado exitosamente")
        logger.info(f"   • FAQs generadas: {stats.get('faqs_generated')}")
        logger.info(f"   • Clusters encontrados: {stats.get('clusters')}")
        
        return PipelineResponse(
            workspace_id=request.workspace_id,
            status="success",
            faqs_generated=stats.get("faqs_generated", 0),
            clusters_found=stats.get("clusters", 0),
        )
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando pipeline: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {str(e)}"
        )


@app.post(
    "/api/v1/pipeline/test",
    tags=["Pipeline"],
    summary="Probar pipeline con mensajes de ejemplo"
)
def test_pipeline():
    """
    Prueba rápida del pipeline usando mensajes de ejemplo.
    Útil para validar que todos los componentes funcionan correctamente.
    
    Returns:
        Resultado del test con estadísticas
    """
    try:
        logger.info("🧪 Ejecutando test del pipeline...")
        
        result = FAQJobs.test_pipeline_with_sample_messages()
        
        if result.get("status") != "success":
            raise HTTPException(
                status_code=400,
                detail="Pipeline test failed"
            )
        
        logger.info("✅ Test del pipeline completado")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error en test del pipeline: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline test failed: {str(e)}"
        )


# ──────────────────────────────────────────────────────────────────────────
# RUTAS - JOBS
# ──────────────────────────────────────────────────────────────────────────

@app.post(
    "/api/v1/jobs/reload-faqs",
    tags=["Jobs"],
    summary="Recargar FAQs para todos los workspaces"
)
def reload_faqs_job():
    """
    Ejecuta el job de recarga mensual de FAQs para todos los workspaces.
    
    Este endpoint típicamente se ejecutaría desde un scheduler (APScheduler, Celery, etc),
    pero se expone aquí para permitir ejecución manual.
    
    Returns:
        Resumen de la ejecución del job
    """
    try:
        logger.info("⚙️ Iniciando job de recarga de FAQs...")
        
        FAQJobs.reload_faqs()
        
        logger.info("✅ Job de recarga de FAQs completado")
        return {
            "status": "success",
            "message": "FAQs reload job completed",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en job de recarga de FAQs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"FAQ reload job failed: {str(e)}"
        )


@app.post(
    "/api/v1/jobs/verify-integrity",
    tags=["Jobs"],
    summary="Verificar integridad de FAQs"
)
def verify_faq_integrity_job():
    """
    Ejecuta el job de verificación de integridad de FAQs.
    Se ejecuta cada 30 minutos para detectar problemas temprano.
    
    Returns:
        Resultado de la verificación
    """
    try:
        logger.info("🧪 Iniciando verificación de integridad de FAQs...")
        
        FAQJobs.test_faq_integrity()
        
        logger.info("✅ Verificación de integridad completada")
        return {
            "status": "success",
            "message": "FAQ integrity check completed",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en verificación de integridad: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Integrity check failed: {str(e)}"
        )


# ──────────────────────────────────────────────────────────────────────────
# RUTAS - MANTENIMIENTO
# ──────────────────────────────────────────────────────────────────────────

@app.post(
    "/api/v1/maintenance/cleanup-logs",
    tags=["Maintenance"],
    summary="Limpiar logs antiguos"
)
def cleanup_logs_job():
    """
    Ejecuta el job de limpieza de logs antiguos (> 30 días).
    """
    try:
        logger.info("🧹 Iniciando limpieza de logs antiguos...")
        
        MaintenanceJobs.cleanup_old_logs()
        
        logger.info("✅ Limpieza de logs completada")
        return {
            "status": "success",
            "message": "Old logs cleanup completed",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error limpiando logs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )


# ──────────────────────────────────────────────────────────────────────────
# RUTAS - INFO
# ──────────────────────────────────────────────────────────────────────────

@app.get(
    "/api/v1/info",
    tags=["Info"],
    summary="Información de la aplicación"
)
def get_app_info():
    """
    Retorna información sobre la aplicación y cómo usarla.
    """
    return {
        "name": "Everwod - Generador Automático de FAQs",
        "version": "1.0.0",
        "description": "Analiza mensajes de clientes y sugiere preguntas frecuentes (FAQs) automáticamente",
        "purpose": "Extraer y sugerir FAQs a partir del análisis de conversaciones de clientes",
        "workflow": [
            "1. Los clientes envían mensajes a tu plataforma",
            "2. Estos mensajes se almacenan en la base de datos",
            "3. Ejecutas POST /api/v1/workspaces/{id}/analyze",
            "4. El sistema analiza todos los mensajes",
            "5. Agrupa mensajes similares (clustering)",
            "6. Genera preguntas FAQ automáticamente",
            "7. Genera respuestas con IA (Ollama)",
            "8. Las FAQs aparecen en GET /api/v1/workspaces/{id}/faqs"
        ],
        "endpoints": {
            "workspaces": "GET /api/v1/workspaces - Listar workspaces",
            "list_faqs": "GET /api/v1/workspaces/{id}/faqs - Ver FAQs sugeridas",
            "analyze": "POST /api/v1/workspaces/{id}/analyze - Analizar y sugerir FAQs",
            "docs": "GET /docs - Documentación interactiva"
        },
        "configuration": {
            "database": f"{settings.db_host}:{settings.db_port}/{settings.db_name}",
            "embedding_model": settings.faq_embedding_model,
            "llm_model": settings.faq_llm_model,
            "similarity_threshold": settings.similarity_threshold_very_similar,
        },
        "documentation": "/docs"
    }


# ──────────────────────────────────────────────────────────────────────────
# RUTAS - ROOT
# ──────────────────────────────────────────────────────────────────────────

@app.get(
    "/",
    tags=["Root"],
    summary="Raíz de la API"
)
def root():
    """Endpoint raíz de la API"""
    return {
        "message": "Bienvenido a Everwod - Análisis de Conversaciones con IA",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


# ──────────────────────────────────────────────────────────────────────────
# ERROR HANDLERS
# ──────────────────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handler general para excepciones no manejadas"""
    logger.error(f"❌ Error no manejado: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 60)
    logger.info("🚀 Iniciando servidor Everwod")
    logger.info("=" * 60)
    logger.info("📍 http://localhost:8000")
    logger.info("📚 Documentación: http://localhost:8000/docs")
    logger.info("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

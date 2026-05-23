from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# REQUESTS
# ─────────────────────────────────────────────────────────────

class PipelineRequest(BaseModel):
    """Request para ejecutar el pipeline"""
    workspace_id: int


class ReloadFAQsRequest(BaseModel):
    """Request para recargar FAQs"""
    workspace_id: int


# ─────────────────────────────────────────────────────────────
# RESPONSES
# ─────────────────────────────────────────────────────────────

class HealthCheckResponse(BaseModel):
    """Respuesta de chequeo de salud"""
    status: str
    timestamp: str
    version: str


class FAQResponse(BaseModel):
    """Una FAQ que generamos como resultado del pipeline"""
    workspace_id: int
    workspace_name: str
    question: str
    cluster_id: Optional[int] = None
    cluster_size: Optional[int] = None
    keywords: Optional[List[str]] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class PipelineResponse(BaseModel):
    """Response del pipeline con resultados del análisis"""
    workspace_id: int
    status: str
    faqs_generated: int
    clusters_found: int


class WorkspaceItem(BaseModel):
    """Modelo para un workspace"""
    id: int
    name: str


# Alias para mantener compatibilidad
IngestRequest = PipelineRequest

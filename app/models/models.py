from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

#Lo que nos manda el usuario para iniciar el pipeline.
class IngestRequest(BaseModel):
    
    workspace_id: int

# Una FAQ que generamos como resultado.
class FAQResponse(BaseModel):
   
    workspace_id: int
    workspace_name: str
    question: str
    cluster_id: Optional[int] = None
    cluster_size: Optional[int] = None
    keywords: Optional[List[str]] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

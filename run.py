#!/usr/bin/env python
"""
run.py - Script para ejecutar la aplicación Everwod
"""

import uvicorn
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 INICIANDO SERVIDOR EVERWOD")
    print("=" * 70)
    print("📍 http://localhost:8000")
    print("📚 Documentación: http://localhost:8000/docs")
    print("🧪 Health Check: http://localhost:8000/health")
    print("=" * 70 + "\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

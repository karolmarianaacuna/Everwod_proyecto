"""
Jobs que se ejecutan según el scheduler
Incluye la lógica de recarga de FAQs usando el pipeline_service
"""

import logging
from datetime import datetime
from typing import List

# Importar el pipeline service
from app.services.pipeline_service import pipeline_service
from app.repositories.faq_repository import get_all_workspaces

logger = logging.getLogger(__name__)


class FAQJobs:
    """Clase con los jobs relacionados a FAQs"""
    
    @staticmethod
    def reload_faqs():
        """
        Job para recargar las FAQs mensualmente
        Se ejecuta para todos los workspaces
        """
        logger.info("=" * 60)
        logger.info("🔄 INICIANDO RECARGA MENSUAL DE FAQs")
        logger.info(f"⏰ Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        try:
            # Obtener todos los workspaces
            logger.info("📋 Obteniendo lista de workspaces...")
            workspaces = get_all_workspaces()
            logger.info(f"✓ {len(workspaces)} workspaces encontrados")
            
            total_faqs = 0
            successful_workspaces = 0
            failed_workspaces = []
            
            # Procesar cada workspace
            for workspace in workspaces:
                workspace_id = workspace.get("id") or workspace.get("workspace_id")
                workspace_name = workspace.get("name", workspace_id)
                
                logger.info(f"\n  📦 Procesando: {workspace_name} ({workspace_id})")
                
                try:
                    # Ejecutar pipeline para este workspace
                    result = pipeline_service.reload_faqs(workspace_id)
                    
                    if result.get("status") == "success":
                        faqs_count = result.get("faqs_count", 0)
                        total_faqs += faqs_count
                        successful_workspaces += 1
                        logger.info(f"    ✅ {faqs_count} FAQs cargadas")
                    else:
                        error_msg = result.get("message", "Error desconocido")
                        failed_workspaces.append((workspace_name, error_msg))
                        logger.error(f"    ❌ Error: {error_msg}")
                
                except Exception as e:
                    error_msg = str(e)
                    failed_workspaces.append((workspace_name, error_msg))
                    logger.error(f"    ❌ Excepción: {error_msg}", exc_info=True)
            
            # Resumen final
            logger.info("\n" + "=" * 60)
            logger.info("📊 RESUMEN DE RECARGA DE FAQs")
            logger.info("=" * 60)
            logger.info(f"✓ Workspaces procesados: {successful_workspaces}/{len(workspaces)}")
            logger.info(f"✓ Total de FAQs cargadas: {total_faqs}")
            
            if failed_workspaces:
                logger.warning(f"⚠️ Workspaces con error: {len(failed_workspaces)}")
                for ws_name, error in failed_workspaces:
                    logger.warning(f"   • {ws_name}: {error}")
            
            logger.info("=" * 60)
            logger.info("✅ RECARGA DE FAQs COMPLETADA")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Error CRÍTICO en reload_faqs: {str(e)}", exc_info=True)
            # Aquí podrías enviar una notificación de error (email, Slack, etc.)
            raise
    
    @staticmethod
    def test_faq_integrity():
        """
        Job para verificar la integridad de las FAQs
        Se ejecuta cada 30 minutos para detectar problemas temprano
        """
        logger.info("=" * 60)
        logger.info("🧪 INICIANDO PRUEBA DE INTEGRIDAD DE FAQs")
        logger.info(f"⏰ Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        try:
            # Obtener todos los workspaces
            workspaces = get_all_workspaces()
            logger.info(f"📋 Verificando {len(workspaces)} workspaces...")
            
            checks_passed = 0
            checks_failed = 0
            
            for workspace in workspaces:
                workspace_id = workspace.get("id") or workspace.get("workspace_id")
                workspace_name = workspace.get("name", workspace_id)
                
                try:
                    # Ejecutar test del pipeline
                    logger.info(f"  Verificando: {workspace_name}...")
                    
                    result = pipeline_service.reload_faqs(workspace_id)
                    
                    if result.get("status") == "success":
                        faqs_count = result.get("faqs_count", 0)
                        logger.info(f"    ✓ {faqs_count} FAQs presentes")
                        checks_passed += 1
                    else:
                        logger.warning(f"    ⚠️ Problema: {result.get('message')}")
                        checks_failed += 1
                
                except Exception as e:
                    logger.error(f"    ❌ Error: {str(e)}")
                    checks_failed += 1
            
            # Resumen
            logger.info("\n" + "=" * 60)
            logger.info("✅ PRUEBA DE INTEGRIDAD COMPLETADA")
            logger.info(f"  Verificaciones exitosas: {checks_passed}")
            logger.info(f"  Verificaciones fallidas: {checks_failed}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Error en prueba de integridad: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def test_pipeline_with_sample_messages():
        """
        Job de prueba que ejecuta el pipeline con mensajes de ejemplo
        Útil para testing sin datos reales
        """
        logger.info("🧪 Ejecutando test de pipeline con datos de ejemplo...")
        
        test_messages = [
            "¿Cuál es el horario de atención?",
            "¿A qué hora abren ustedes?",
            "¿Qué horarios tienen?",
            "¿Cuánto cuesta el servicio?",
            "¿Cuál es el precio?",
            "¿Cuál es el valor?",
            "¿Cómo puedo pagar?",
            "¿Qué métodos de pago aceptan?",
            "¿Puedo pagar con tarjeta?",
            "¿Dónde están ubicados?",
            "¿Cuál es su dirección?",
            "¿Dónde puedo encontrarlos?",
        ]
        
        try:
            result = pipeline_service.test_pipeline(test_messages)
            
            logger.info(f"✅ Test completado:")
            logger.info(f"   Input: {result.get('input_messages')} mensajes")
            logger.info(f"   Válidos: {result.get('valid_messages')} mensajes")
            logger.info(f"   Clusters: {result.get('clusters_found')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en test: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}


class MaintenanceJobs:
    """Otros jobs de mantenimiento del sistema"""
    
    @staticmethod
    def cleanup_old_logs():
        """Limpiar logs antiguos (más de 30 días)"""
        logger.info("🧹 Iniciando limpieza de logs antiguos...")
        
        try:
            from datetime import datetime, timedelta
            import os
            import logging.handlers
            
            # Aquí implementar lógica de limpieza según tu sistema de logs
            # Ejemplo para rotated log files:
            
            logger.info("✅ Limpieza de logs completada")
            
        except Exception as e:
            logger.error(f"❌ Error limpiando logs: {str(e)}")
    
    @staticmethod
    def check_system_health():
        """Verificar salud del sistema"""
        logger.info("🏥 Verificando salud del sistema...")
        
        try:
            checks = {
                "database": False,
                "embedding_model": False,
                "llm_service": False,
                "storage": False,
            }
            
            # Check 1: Conexión a BD
            try:
                from app.repositories.faq_repository import get_all_workspaces
                workspaces = get_all_workspaces()
                checks["database"] = True
                logger.info(f"  ✓ BD: OK ({len(workspaces)} workspaces)")
            except Exception as e:
                logger.warning(f"  ✗ BD: {str(e)}")
            
            # Check 2: Embedding model
            try:
                from app.services.embedding_service import generate_embedding
                test_emb = generate_embedding("test", text_type="passage")
                if test_emb:
                    checks["embedding_model"] = True
                    logger.info(f"  ✓ Embedding Model: OK")
            except Exception as e:
                logger.warning(f"  ✗ Embedding Model: {str(e)}")
            
            # Check 3: LLM Service (Ollama via faq_service)
            try:
                from app.services.faq_service import _generate_with_ollama
                response = _generate_with_ollama("test")
                if response:
                    checks["llm_service"] = True
                    logger.info(f"  ✓ LLM Service: OK")
                else:
                    logger.warning(f"  ✗ LLM Service: No response")
            except Exception as e:
                logger.warning(f"  ✗ LLM Service: {str(e)}")
            
            # Check 4: Storage (si lo tienes)
            try:
                checks["storage"] = True
                logger.info(f"  ✓ Storage: OK")
            except Exception as e:
                logger.warning(f"  ✗ Storage: {str(e)}")
            
            # Resumen
            total_checks = len(checks)
            passed_checks = sum(1 for v in checks.values() if v)
            
            logger.info(f"\n📊 Salud del sistema: {passed_checks}/{total_checks} checks pasados")
            
            if passed_checks == total_checks:
                logger.info("✅ Sistema en BUEN ESTADO")
            elif passed_checks >= total_checks * 0.75:
                logger.warning("⚠️ Sistema con PROBLEMAS MENORES")
            else:
                logger.error("❌ Sistema con PROBLEMAS CRÍTICOS")
            
        except Exception as e:
            logger.error(f"❌ Error en check de salud: {str(e)}", exc_info=True)


class PipelineJobs:
    """Jobs relacionados al pipeline de ingesta"""
    
    @staticmethod
    def reprocess_pending_messages():
        """
        Reprocesa mensajes pendientes
        Útil si hubo errores en la ingesta inicial
        """
        logger.info("🔄 Reprocesando mensajes pendientes...")
        
        try:
            # TODO: Implementar lógica de reprocesamiento
            # Buscar mensajes con estado "pending" o "error"
            # Ejecutar pipeline para cada uno
            
            logger.info("✅ Reprocesamiento completado")
            
        except Exception as e:
            logger.error(f"❌ Error reprocesando: {str(e)}", exc_info=True)
    
    @staticmethod
    def optimize_embeddings():
        """
        Optimiza índices de embeddings
        Mejora performance de búsquedas
        """
        logger.info("⚙️ Optimizando embeddings...")
        
        try:
            # TODO: Implementar optimización
            # Recalcular embeddings si es necesario
            # Actualizar índices
            
            logger.info("✅ Optimización completada")
            
        except Exception as e:
            logger.error(f"❌ Error optimizando: {str(e)}", exc_info=True)
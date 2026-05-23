import logging
from typing import Optional, List, Dict
import numpy as np

from app.core.config import settings
from app.models.models import FAQResponse
from app.repositories.faq_repository import (
    save_faq,
    get_existing_faqs,
    get_messages_by_workspace_id,
    faq_exists,
    get_all_workspaces,
    get_workspace_context,
    get_first_agent_id,
)
from app.services.cleaning_service import clean_text, find_keywords
from app.services.embedding_service import (
    generate_embedding,
    cosine_similarity,
)
from app.services.clustering_service import (
    cluster_embeddings,
    group_messages_by_cluster,
    get_representative_message,
    is_duplicate_faq,
)
from app.services.faq_service import (
    refine_question_to_faq,
    generate_answer_with_llm,
)

logger = logging.getLogger(__name__)


class PipelineService:
    """
    Servicio principal que ejecuta el pipeline completo de ingesta de mensajes
    y generación de FAQs inteligentes desde PostgreSQL
    """
    
    def __init__(self):
        self.workspace_context = None
        self.existing_faqs_embeddings = None
        
    def execute_pipeline(
        self,
        workspace_id: int,
        limit: int = 1000,
    ) -> dict:
        """
        Ejecuta el pipeline completo:
        1. Obtener mensajes de BD
        2. Limpieza de texto
        3. Clustering de mensajes similares
        4. Generación de preguntas FAQ
        5. Deduplicación
        6. Generación de respuestas
        
        
        Args:
            workspace_id: ID del workspace a procesar
            limit: Máximo de mensajes a procesar
            
        Returns:
            Dict con FAQs generadas y estadísticas del proceso
        """
        logger.info(f"🚀 Iniciando pipeline para workspace: {workspace_id}")
        
        try:
            # Paso 0: Obtener contexto del workspace
            logger.info("📋 Paso 0: Obteniendo contexto del workspace...")
            self.workspace_context = get_workspace_context(workspace_id) or {}
            
            if not self.workspace_context:
                logger.warning(f"⚠️ Workspace {workspace_id} no encontrado")
                return self._error_response(workspace_id, "Workspace no encontrado")
            
            ws_name = self.workspace_context.get("name", "Unknown")
            logger.info(f"  Workspace: {ws_name}")
            
            # Paso 1: Obtener mensajes de BD
            logger.info("📥 Paso 1: Obteniendo mensajes de la BD...")
            messages_from_db = get_messages_by_workspace_id(workspace_id, limit=limit)
            
            if not messages_from_db:
                logger.warning(f"⚠️ No hay mensajes en la BD para workspace {workspace_id}")
                return {
                    "workspace_id": workspace_id,
                    "faqs_generated": [],
                    "stats": {
                        "total_input": 0,
                        "valid_messages": 0,
                        "clusters": 0,
                        "faqs_generated": 0,
                        "faqs_saved": 0,
                        "duplicates_found": 0,
                        "success_rate": 0,
                    },
                    "status": "no_valid_messages"
                }
            
            # Extraer solo el texto de los mensajes
            message_texts = [
                msg.get("message", "")
                for msg in messages_from_db
                if msg.get("message")
            ]
            logger.info(f"✓ {len(message_texts)} mensajes obtenidos de BD")
            
            # Paso 2: Limpieza de mensajes
            logger.info("📝 Paso 2: Limpiando mensajes...")
            cleaned_messages = self._clean_messages(message_texts)
            
            if not cleaned_messages:
                logger.warning("⚠️ No hay mensajes válidos después de limpiar")
                return {
                    "workspace_id": workspace_id,
                    "faqs_generated": [],
                    "stats": {
                        "total_input": len(message_texts),
                        "valid_messages": 0,
                        "clusters": 0,
                        "faqs_generated": 0,
                        "faqs_saved": 0,
                        "duplicates_found": 0,
                        "success_rate": 0,
                    },
                    "status": "no_valid_messages"
                }
            
            logger.info(f"✓ {len(cleaned_messages)} mensajes válidos después de limpiar")
            
            # Paso 3: Generar embeddings de los mensajes limpios
            logger.info("🧠 Paso 3: Generando embeddings...")
            embeddings = self._generate_embeddings(cleaned_messages)
            
            if not embeddings:
                logger.error("❌ No se pudieron generar embeddings")
                return self._error_response(workspace_id, "Error generando embeddings")
            
            # Paso 4: Clustering
            logger.info("🎯 Paso 4: Clustering de mensajes...")
            labels = cluster_embeddings(embeddings)
            
            # Paso 5: Agrupar mensajes por cluster
            logger.info("📦 Paso 5: Agrupando mensajes...")
            clusters = group_messages_by_cluster(cleaned_messages, embeddings, labels)
            logger.info(f"✓ {len(clusters)} clusters encontrados")
            
            # Paso 6: Cargar FAQs existentes para deduplicación
            logger.info("🔍 Paso 6: Cargando FAQs existentes...")
            self._load_existing_faqs(workspace_id)
            
            # Paso 7: Obtener agent_id para guardar FAQs
            logger.info("🔐 Paso 7: Obteniendo agent ID...")
            agent_id = get_first_agent_id(workspace_id)
            
            if not agent_id:
                logger.error(f"❌ No se encontró agent para workspace {workspace_id}")
                return self._error_response(workspace_id, "No se encontró agent")
            
            logger.info(f"✓ Agent ID: {agent_id}")
            
            # Paso 8: Procesar cada cluster
            logger.info("⚡ Paso 8: Procesando clusters...")
            faqs_generated = []
            duplicates_found = 0
            
            for cluster_id, cluster_data in clusters.items():
                logger.info(f"\n  📌 Procesando cluster {cluster_id} ({len(cluster_data['messages'])} msgs)")
                
                try:
                    # Obtener mensaje representativo
                    medoid = get_representative_message(
                        cluster_data["messages"],
                        cluster_data["embeddings"]
                    )
                    logger.info(f"  Medoide: {medoid[:80]}...")
                    
                    # Generar pregunta FAQ
                    logger.info("  Generando pregunta FAQ...")
                    faq_question = refine_question_to_faq(
                        medoid,
                        cluster_data["messages"],
                        self.workspace_context
                    )
                    logger.info(f"  ✓ Pregunta: {faq_question}")
                    
                    # Verificar duplicados (solo para información, no para filtrar)
                    logger.info("  Verificando duplicados...")
                    question_embedding = generate_embedding(faq_question, text_type="passage")
                    
                    is_duplicate = is_duplicate_faq(
                        question_embedding,
                        self.existing_faqs_embeddings,
                        threshold=settings.faq_similarity_very_similar
                    )
                    
                    if is_duplicate:
                        logger.warning(f"  ⚠️ FAQ similar a existentes: {faq_question}")
                        duplicates_found += 1
                    
                    # Generar respuesta
                    # Crear objeto FAQ (sin campo `answer`)
                    faq = FAQResponse(
                        workspace_id=workspace_id,
                        workspace_name=self.workspace_context.get("name", ""),
                        question=faq_question,
                        cluster_id=cluster_id,
                        cluster_size=len(cluster_data["messages"]),
                        keywords=find_keywords(medoid),
                        confidence=self._calculate_cluster_confidence(
                            cluster_data["embeddings"]
                        ),
                    )
                    
                    faqs_generated.append(faq)
                    logger.info(f"  ✅ FAQ generada exitosamente")
                    
                except Exception as e:
                    logger.error(f"  ❌ Error procesando cluster {cluster_id}: {str(e)}", exc_info=True)
                    continue
            
            # Paso 9: Retornar FAQs sugeridas (sin guardar en BD)
            logger.info("\n📋 Paso 9: Preparando FAQs sugeridas...")
            
            logger.info(f"\n✅ Pipeline completado exitosamente")
            logger.info(f"   • FAQs sugeridas: {len(faqs_generated)}")
            logger.info(f"   • Duplicados evitados: {duplicates_found}")
            
            return {
                "workspace_id": workspace_id,
                "faqs_generated": [faq.dict() for faq in faqs_generated],
                "stats": {
                    "total_input": len(message_texts),
                    "valid_messages": len(cleaned_messages),
                    "clusters": len(clusters),
                    "faqs_generated": len(faqs_generated),
                    "duplicates_found": duplicates_found,
                    "success_rate": (len(faqs_generated) / len(clusters) * 100) if clusters else 0,
                },
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"❌ Error en pipeline: {str(e)}", exc_info=True)
            return self._error_response(workspace_id, str(e))
    
    def reload_faqs(self, workspace_id: int) -> dict:
        """
        Job programado para recargar todas las FAQs del workspace
        Se ejecuta mensualmente
        """
        logger.info(f"🔄 Recargando FAQs para workspace: {workspace_id}")
        
        try:
            # Obtener todas las FAQs del workspace
            faqs = get_existing_faqs(workspace_id)
            logger.info(f"✅ FAQs cargadas: {len(faqs)}")
            
            return {
                "workspace_id": workspace_id,
                "faqs_count": len(faqs),
                "status": "success",
                "message": f"Se cargaron {len(faqs)} FAQs del workspace"
            }
            
        except Exception as e:
            logger.error(f"❌ Error recargando FAQs: {str(e)}", exc_info=True)
            return {
                "workspace_id": workspace_id,
                "status": "error",
                "message": f"Error: {str(e)}"
            }
    
    def test_pipeline(self, test_messages: List[str]) -> dict:
        """
        Prueba rápida del pipeline sin guardar en BD
        Útil para testing durante desarrollo
        """
        logger.info("🧪 Ejecutando test del pipeline...")
        
        try:
            # Ejecutar pipeline sin guardar
            cleaned = self._clean_messages(test_messages)
            embeddings = self._generate_embeddings(cleaned)
            labels = cluster_embeddings(embeddings)
            clusters = group_messages_by_cluster(cleaned, embeddings, labels)
            
            logger.info(f"✅ Test completado:")
            logger.info(f"   • Mensajes de entrada: {len(test_messages)}")
            logger.info(f"   • Mensajes válidos: {len(cleaned)}")
            logger.info(f"   • Clusters encontrados: {len(clusters)}")
            
            return {
                "status": "success",
                "input_messages": len(test_messages),
                "valid_messages": len(cleaned),
                "clusters_found": len(clusters),
                "clusters_detail": {
                    cluster_id: {
                        "size": len(data["messages"]),
                        "sample_messages": data["messages"][:3]
                    }
                    for cluster_id, data in clusters.items()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error en test: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }
    
    # ──── Métodos privados ────────────────────────────────────────────────
    
    def _clean_messages(self, messages: List[str]) -> List[str]:
        """Limpia y filtra mensajes"""
        cleaned = []
        for msg in messages:
            if isinstance(msg, str) and msg.strip():
                cleaned_msg = clean_text(msg)
                if len(cleaned_msg) >= settings.min_text_length:
                    cleaned.append(cleaned_msg)
        return cleaned
    
    def _generate_embeddings(self, messages: List[str]) -> List[List[float]]:
        """Genera embeddings para una lista de mensajes"""
        embeddings = []
        for msg in messages:
            try:
                emb = generate_embedding(msg, text_type="passage")
                embeddings.append(emb)
            except Exception as e:
                logger.error(f"Error generando embedding: {e}")
                continue
        return embeddings
    
    def _load_existing_faqs(self, workspace_id: int):
        """Carga los embeddings de FAQs existentes para deduplicación"""
        try:
            faqs_data = get_existing_faqs(workspace_id)
            
            if faqs_data:
                # Generar embeddings para cada FAQ existente
                embeddings_list = []
                for faq in faqs_data:
                    text = faq.get("question", "")
                    if text:
                        try:
                            emb = generate_embedding(text, text_type="passage")
                            embeddings_list.append(emb)
                        except Exception as e:
                            logger.warning(f"Error generando embedding para FAQ: {e}")
                            continue
                
                if embeddings_list:
                    self.existing_faqs_embeddings = np.array(embeddings_list)
                    logger.info(f"✅ Loaded {len(embeddings_list)} existing FAQ embeddings")
                else:
                    self.existing_faqs_embeddings = None
            else:
                self.existing_faqs_embeddings = None
                logger.info("ℹ️ No existing FAQs found")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not load existing FAQs: {e}")
            self.existing_faqs_embeddings = None
    
    def _save_faqs(self, workspace_id: int, agent_id: int, faqs: List[FAQResponse]) -> int:
        """Guarda las FAQs generadas en la BD"""
        saved_count = 0
        
        for faq in faqs:
            try:
                faq_id = save_faq(
                    workspace_id=workspace_id,
                    question=faq.question,
                    agent_id=agent_id,
                    metadata={
                        "cluster_id": faq.cluster_id,
                        "cluster_size": faq.cluster_size,
                        "keywords": faq.keywords,
                        "confidence": faq.confidence,
                    }
                )
                if faq_id:
                    saved_count += 1
            except Exception as e:
                logger.error(f"Error saving FAQ: {e}")
                continue
        
        return saved_count
    
    def _calculate_cluster_confidence(self, embeddings: List[List[float]]) -> float:
        """
        Calcula la confianza basada en la cohesión del cluster
        Mayor similitud intra-cluster = mayor confianza
        """
        if len(embeddings) < 2:
            return 1.0
        
        try:
            similarities = []
            
            # Calcular similitud promedio intra-cluster
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = cosine_similarity(
                        embeddings[i],
                        embeddings[j]
                    )
                    similarities.append(sim)
            
            # Retornar promedio de similitudes
            avg_similarity = np.mean(similarities) if similarities else 0.5
            return float(avg_similarity)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _error_response(self, workspace_id: int, error_message: str) -> dict:
        """Genera una respuesta de error estandarizada"""
        return {
            "workspace_id": workspace_id,
            "faqs_generated": [],
            "stats": {
                "total_input": 0,
                "valid_messages": 0,
                "clusters": 0,
                "faqs_generated": 0,
                "faqs_saved": 0,
                "duplicates_found": 0,
            },
            "status": "error",
            "error": error_message
        }


# Instancia global del servicio
pipeline_service = PipelineService()
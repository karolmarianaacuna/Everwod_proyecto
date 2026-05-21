"""
Tests para pipeline_service.py
Pruebas unitarias para el PipelineService principal
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock, call
from typing import List

from app.services.pipeline_service import PipelineService
from app.models.models import FAQResponse


class TestPipelineServiceInit:
    """Tests para la inicialización de PipelineService"""
    
    def test_pipeline_service_initialization(self):
        """Test que PipelineService se inicializa correctamente"""
        # Act
        service = PipelineService()
        
        # Assert
        assert service.workspace_context is None
        assert service.existing_faqs_embeddings is None


class TestExecutePipeline:
    """Tests para el método execute_pipeline"""
    
    @patch('app.services.pipeline_service.get_workspace_context')
    @patch('app.services.pipeline_service.get_messages_by_workspace_id')
    def test_execute_pipeline_no_messages(self, mock_get_messages, mock_get_context):
        """Test execute_pipeline cuando no hay mensajes"""
        # Arrange
        service = PipelineService()
        workspace_id = 1
        
        mock_get_context.return_value = {"id": 1, "name": "Test Workspace"}
        mock_get_messages.return_value = []
        
        # Act
        result = service.execute_pipeline(workspace_id)
        
        # Assert
        assert result["status"] == "no_valid_messages"
        assert result["workspace_id"] == workspace_id
        assert result["faqs_generated"] == []
    
    @patch('app.services.pipeline_service.get_workspace_context')
    def test_execute_pipeline_workspace_not_found(self, mock_get_context):
        """Test execute_pipeline cuando workspace no existe"""
        # Arrange
        service = PipelineService()
        workspace_id = 999
        
        mock_get_context.return_value = None
        
        # Act
        result = service.execute_pipeline(workspace_id)
        
        # Assert
        assert result["status"] == "error"
        assert result["workspace_id"] == workspace_id
    
    @patch('app.services.pipeline_service.get_workspace_context')
    @patch('app.services.pipeline_service.get_messages_by_workspace_id')
    @patch('app.services.pipeline_service.clean_text')
    def test_execute_pipeline_all_messages_invalid(self, mock_clean_text, mock_get_messages, mock_get_context):
        """Test execute_pipeline cuando todos los mensajes son inválidos"""
        # Arrange
        service = PipelineService()
        workspace_id = 1
        
        mock_get_context.return_value = {"id": 1, "name": "Test"}
        mock_get_messages.return_value = [
            {"message": "a"},
            {"message": "b"},
            {"message": "c"},
        ]
        # Simular mensajes demasiado cortos
        mock_clean_text.side_effect = ["a", "b", "c"]
        
        # Act
        result = service.execute_pipeline(workspace_id)
        
        # Assert
        assert result["status"] == "no_valid_messages"
        assert result["faqs_generated"] == []
    
    @patch('app.services.pipeline_service.get_workspace_context')
    @patch('app.services.pipeline_service.get_messages_by_workspace_id')
    @patch.object(PipelineService, '_clean_messages')
    @patch.object(PipelineService, '_generate_embeddings')
    @patch('app.services.pipeline_service.cluster_embeddings')
    @patch('app.services.pipeline_service.group_messages_by_cluster')
    def test_execute_pipeline_complete_flow(
        self,
        mock_group_clusters,
        mock_cluster_embeddings,
        mock_gen_embeddings,
        mock_clean_msgs,
        mock_get_messages,
        mock_get_context
    ):
        """Test execute_pipeline con flujo completo"""
        # Arrange
        service = PipelineService()
        workspace_id = 1
        
        mock_get_context.return_value = {"id": 1, "name": "Test Workspace"}
        mock_get_messages.return_value = [
            {"message": "¿Cuál es el horario?"},
            {"message": "¿A qué hora abren?"},
        ]
        
        cleaned_msgs = ["cuál es el horario", "a qué hora abren"]
        mock_clean_msgs.return_value = cleaned_msgs
        
        embeddings = [
            np.array([0.1, 0.2, 0.3]),
            np.array([0.11, 0.21, 0.31]),
        ]
        mock_gen_embeddings.return_value = embeddings
        mock_cluster_embeddings.return_value = np.array([0, 0])
        
        clusters = {
            0: {
                "messages": cleaned_msgs,
                "embeddings": embeddings,
            }
        }
        mock_group_clusters.return_value = clusters
        
        # Act
        with patch.object(service, '_load_existing_faqs'):
            with patch.object(service, '_save_faqs', return_value=0):
                with patch('app.services.pipeline_service.get_first_agent_id', return_value=1):
                    with patch.object(service, '_clean_messages', return_value=cleaned_msgs):
                        with patch.object(service, '_generate_embeddings', return_value=embeddings):
                            result = service.execute_pipeline(workspace_id)
        
        # Assert
        assert result["workspace_id"] == workspace_id
        assert "stats" in result


class TestCleanMessages:
    """Tests para el método _clean_messages"""
    
    def test_clean_messages_empty_list(self):
        """Test _clean_messages con lista vacía"""
        # Arrange
        service = PipelineService()
        messages = []
        
        # Act
        result = service._clean_messages(messages)
        
        # Assert
        assert result == []
    
    @patch('app.services.pipeline_service.clean_text')
    @patch('app.services.pipeline_service.settings')
    def test_clean_messages_filters_short_messages(self, mock_settings, mock_clean_text):
        """Test _clean_messages filtra mensajes demasiado cortos"""
        # Arrange
        service = PipelineService()
        mock_settings.min_text_length = 10
        
        messages = [
            "a",  # Muy corto
            "Este es un mensaje válido",
            "Otro mensaje",
        ]
        
        mock_clean_text.side_effect = [
            "a",
            "este es un mensaje válido",
            "otro mensaje",
        ]
        
        # Act
        result = service._clean_messages(messages)
        
        # Assert
        assert len(result) == 2
        assert "este es un mensaje válido" in result
        assert "otro mensaje" in result
    
    @patch('app.services.pipeline_service.clean_text')
    def test_clean_messages_handles_non_strings(self, mock_clean_text):
        """Test _clean_messages maneja entrada no-string"""
        # Arrange
        service = PipelineService()
        messages = [
            "mensaje válido",
            None,
            123,
            [],
            "otro mensaje",
        ]
        
        mock_clean_text.side_effect = ["mensaje válido", "otro mensaje"]
        
        # Act
        result = service._clean_messages(messages)
        
        # Assert
        assert len(result) == 2


class TestGenerateEmbeddings:
    """Tests para el método _generate_embeddings"""
    
    @patch('app.services.pipeline_service.generate_embedding')
    def test_generate_embeddings_success(self, mock_gen_emb):
        """Test _generate_embeddings genera embeddings correctamente"""
        # Arrange
        service = PipelineService()
        messages = ["mensaje 1", "mensaje 2", "mensaje 3"]
        
        mock_embeddings = [
            [0.1, 0.2, 0.3],
            [0.2, 0.3, 0.4],
            [0.3, 0.4, 0.5],
        ]
        mock_gen_emb.side_effect = mock_embeddings
        
        # Act
        result = service._generate_embeddings(messages)
        
        # Assert
        assert len(result) == 3
        assert mock_gen_emb.call_count == 3
    
    @patch('app.services.pipeline_service.generate_embedding')
    def test_generate_embeddings_handles_errors(self, mock_gen_emb):
        """Test _generate_embeddings maneja errores generando embeddings"""
        # Arrange
        service = PipelineService()
        messages = ["mensaje 1", "mensaje 2", "mensaje 3"]
        
        mock_gen_emb.side_effect = [
            [0.1, 0.2, 0.3],
            Exception("Embedding error"),
            [0.3, 0.4, 0.5],
        ]
        
        # Act
        result = service._generate_embeddings(messages)
        
        # Assert
        assert len(result) == 2  # Solo los éxitosos
        assert mock_gen_emb.call_count == 3
    
    @patch('app.services.pipeline_service.generate_embedding')
    def test_generate_embeddings_empty_list(self, mock_gen_emb):
        """Test _generate_embeddings con lista vacía"""
        # Arrange
        service = PipelineService()
        messages = []
        
        # Act
        result = service._generate_embeddings(messages)
        
        # Assert
        assert result == []
        mock_gen_emb.assert_not_called()


class TestLoadExistingFAQs:
    """Tests para el método _load_existing_faqs"""
    
    @patch('app.services.pipeline_service.get_existing_faqs')
    @patch('app.services.pipeline_service.generate_embedding')
    def test_load_existing_faqs_success(self, mock_gen_emb, mock_get_faqs):
        """Test _load_existing_faqs carga FAQs existentes"""
        # Arrange
        service = PipelineService()
        workspace_id = 1
        
        mock_faqs = [
            {"question": "¿Horario?"},
            {"question": "¿Precio?"},
        ]
        mock_get_faqs.return_value = mock_faqs
        
        mock_embeddings = [
            np.array([0.1, 0.2, 0.3]),
            np.array([0.2, 0.3, 0.4]),
        ]
        mock_gen_emb.side_effect = mock_embeddings
        
        # Act
        service._load_existing_faqs(workspace_id)
        
        # Assert
        assert service.existing_faqs_embeddings is not None
        assert len(service.existing_faqs_embeddings) == 2
    
    @patch('app.services.pipeline_service.get_existing_faqs')
    def test_load_existing_faqs_no_faqs(self, mock_get_faqs):
        """Test _load_existing_faqs cuando no hay FAQs existentes"""
        # Arrange
        service = PipelineService()
        workspace_id = 1
        
        mock_get_faqs.return_value = []
        
        # Act
        service._load_existing_faqs(workspace_id)
        
        # Assert
        assert service.existing_faqs_embeddings is None
    
    @patch('app.services.pipeline_service.get_existing_faqs')
    def test_load_existing_faqs_error(self, mock_get_faqs):
        """Test _load_existing_faqs maneja errores"""
        # Arrange
        service = PipelineService()
        workspace_id = 1
        
        mock_get_faqs.side_effect = Exception("DB error")
        
        # Act
        service._load_existing_faqs(workspace_id)
        
        # Assert
        assert service.existing_faqs_embeddings is None


class TestSaveFAQs:
    """Tests para el método _save_faqs"""
    
    @patch('app.services.pipeline_service.save_faq')
    def test_save_faqs_success(self, mock_save_faq):
        """Test _save_faqs guarda FAQs exitosamente"""
        # Arrange
        service = PipelineService()
        workspace_id = 1
        agent_id = 100
        
        faqs = [
            Mock(
                question="¿Horario?",
                answer="Abierto 9-5",
                cluster_id=0,
                cluster_size=5,
                keywords=["horario"],
                confidence=0.95
            ),
            Mock(
                question="¿Precio?",
                answer="$100",
                cluster_id=1,
                cluster_size=3,
                keywords=["precio"],
                confidence=0.88
            ),
        ]
        
        mock_save_faq.side_effect = [1, 2]
        
        # Act
        result = service._save_faqs(workspace_id, agent_id, faqs)
        
        # Assert
        assert result == 2
        assert mock_save_faq.call_count == 2
    
    @patch('app.services.pipeline_service.save_faq')
    def test_save_faqs_partial_failure(self, mock_save_faq):
        """Test _save_faqs maneja fallos parciales"""
        # Arrange
        service = PipelineService()
        workspace_id = 1
        agent_id = 100
        
        faqs = [
            Mock(question="¿Horario?", answer="Test", cluster_id=0, cluster_size=5, keywords=[], confidence=0.9),
            Mock(question="¿Precio?", answer="Test", cluster_id=1, cluster_size=3, keywords=[], confidence=0.8),
            Mock(question="¿Ubicación?", answer="Test", cluster_id=2, cluster_size=2, keywords=[], confidence=0.7),
        ]
        
        mock_save_faq.side_effect = [1, Exception("DB error"), 3]
        
        # Act
        result = service._save_faqs(workspace_id, agent_id, faqs)
        
        # Assert
        assert result == 2  # Solo las exitosas
    
    @patch('app.services.pipeline_service.save_faq')
    def test_save_faqs_empty_list(self, mock_save_faq):
        """Test _save_faqs con lista vacía"""
        # Arrange
        service = PipelineService()
        workspace_id = 1
        agent_id = 100
        faqs = []
        
        # Act
        result = service._save_faqs(workspace_id, agent_id, faqs)
        
        # Assert
        assert result == 0
        mock_save_faq.assert_not_called()


class TestCalculateClusterConfidence:
    """Tests para el método _calculate_cluster_confidence"""
    
    def test_calculate_cluster_confidence_single_embedding(self):
        """Test _calculate_cluster_confidence con un embedding"""
        # Arrange
        service = PipelineService()
        embeddings = [np.array([0.1, 0.2, 0.3])]
        
        # Act
        confidence = service._calculate_cluster_confidence(embeddings)
        
        # Assert
        assert confidence == 1.0
    
    def test_calculate_cluster_confidence_empty_list(self):
        """Test _calculate_cluster_confidence con lista vacía"""
        # Arrange
        service = PipelineService()
        embeddings = []
        
        # Act
        confidence = service._calculate_cluster_confidence(embeddings)
        
        # Assert
        assert confidence == 1.0
    
    @patch('app.services.pipeline_service.cosine_similarity')
    def test_calculate_cluster_confidence_multiple_embeddings(self, mock_cosine):
        """Test _calculate_cluster_confidence con múltiples embeddings"""
        # Arrange
        service = PipelineService()
        embeddings = [
            np.array([0.1, 0.2, 0.3]),
            np.array([0.11, 0.21, 0.31]),
            np.array([0.12, 0.22, 0.32]),
        ]
        
        mock_cosine.side_effect = [0.95, 0.92, 0.93]
        
        # Act
        confidence = service._calculate_cluster_confidence(embeddings)
        
        # Assert
        assert 0.92 <= confidence <= 0.95
    
    @patch('app.services.pipeline_service.cosine_similarity')
    def test_calculate_cluster_confidence_error_handling(self, mock_cosine):
        """Test _calculate_cluster_confidence maneja errores"""
        # Arrange
        service = PipelineService()
        embeddings = [
            np.array([0.1, 0.2, 0.3]),
            np.array([0.11, 0.21, 0.31]),
        ]
        
        mock_cosine.side_effect = Exception("Calculation error")
        
        # Act
        confidence = service._calculate_cluster_confidence(embeddings)
        
        # Assert
        assert confidence == 0.5  # Valor por defecto en caso de error


class TestReloadFAQs:
    """Tests para el método reload_faqs"""
    
    @patch('app.services.pipeline_service.get_existing_faqs')
    def test_reload_faqs_success(self, mock_get_faqs):
        """Test reload_faqs carga FAQs exitosamente"""
        # Arrange
        service = PipelineService()
        workspace_id = 1
        
        mock_get_faqs.return_value = [
            {"question": "¿Horario?", "answer": "9-5"},
            {"question": "¿Precio?", "answer": "$100"},
        ]
        
        # Act
        result = service.reload_faqs(workspace_id)
        
        # Assert
        assert result["status"] == "success"
        assert result["faqs_count"] == 2
        assert result["workspace_id"] == workspace_id
    
    @patch('app.services.pipeline_service.get_existing_faqs')
    def test_reload_faqs_no_faqs(self, mock_get_faqs):
        """Test reload_faqs cuando no hay FAQs"""
        # Arrange
        service = PipelineService()
        workspace_id = 1
        
        mock_get_faqs.return_value = []
        
        # Act
        result = service.reload_faqs(workspace_id)
        
        # Assert
        assert result["status"] == "success"
        assert result["faqs_count"] == 0
    
    @patch('app.services.pipeline_service.get_existing_faqs')
    def test_reload_faqs_error(self, mock_get_faqs):
        """Test reload_faqs maneja errores"""
        # Arrange
        service = PipelineService()
        workspace_id = 1
        
        mock_get_faqs.side_effect = Exception("DB connection error")
        
        # Act
        result = service.reload_faqs(workspace_id)
        
        # Assert
        assert result["status"] == "error"
        assert "DB connection error" in result["message"]


class TestTestPipeline:
    """Tests para el método test_pipeline"""
    
    @patch.object(PipelineService, '_clean_messages')
    @patch.object(PipelineService, '_generate_embeddings')
    @patch('app.services.pipeline_service.cluster_embeddings')
    @patch('app.services.pipeline_service.group_messages_by_cluster')
    def test_test_pipeline_success(
        self,
        mock_group_clusters,
        mock_cluster_embeddings,
        mock_gen_embeddings,
        mock_clean_msgs
    ):
        """Test test_pipeline ejecuta correctamente"""
        # Arrange
        service = PipelineService()
        test_messages = ["mensaje 1", "mensaje 2"]
        
        cleaned = ["mensaje 1", "mensaje 2"]
        embeddings = [np.array([0.1, 0.2]), np.array([0.2, 0.3])]
        labels = np.array([0, 0])
        clusters = {0: {"messages": cleaned, "embeddings": embeddings}}
        
        mock_clean_msgs.return_value = cleaned
        mock_gen_embeddings.return_value = embeddings
        mock_cluster_embeddings.return_value = labels
        mock_group_clusters.return_value = clusters
        
        # Act
        result = service.test_pipeline(test_messages)
        
        # Assert
        assert result["status"] == "success"
        assert result["input_messages"] == 2
        assert result["valid_messages"] == 2
        assert result["clusters_found"] == 1
    
    @patch.object(PipelineService, '_clean_messages')
    def test_test_pipeline_error(self, mock_clean_msgs):
        """Test test_pipeline maneja errores"""
        # Arrange
        service = PipelineService()
        test_messages = ["mensaje"]
        
        mock_clean_msgs.side_effect = Exception("Cleaning error")
        
        # Act
        result = service.test_pipeline(test_messages)
        
        # Assert
        assert result["status"] == "error"
        assert "Cleaning error" in result["message"]


class TestErrorResponse:
    """Tests para el método _error_response"""
    
    def test_error_response_format(self):
        """Test _error_response genera respuesta de error estandarizada"""
        # Arrange
        service = PipelineService()
        workspace_id = 1
        error_msg = "Test error message"
        
        # Act
        result = service._error_response(workspace_id, error_msg)
        
        # Assert
        assert result["workspace_id"] == workspace_id
        assert result["status"] == "error"
        assert result["error"] == error_msg
        assert "stats" in result
        assert result["faqs_generated"] == []


class TestPipelineIntegration:
    """Tests de integración para PipelineService"""
    
    @patch('app.services.pipeline_service.get_workspace_context')
    @patch('app.services.pipeline_service.get_messages_by_workspace_id')
    @patch('app.services.pipeline_service.get_first_agent_id')
    @patch.object(PipelineService, '_clean_messages')
    @patch.object(PipelineService, '_generate_embeddings')
    @patch.object(PipelineService, '_load_existing_faqs')
    @patch.object(PipelineService, '_save_faqs')
    @patch('app.services.pipeline_service.cluster_embeddings')
    @patch('app.services.pipeline_service.group_messages_by_cluster')
    def test_complete_pipeline_workflow(
        self,
        mock_group_clusters,
        mock_cluster_embeddings,
        mock_save_faqs,
        mock_load_existing,
        mock_gen_embeddings,
        mock_clean_msgs,
        mock_get_agent,
        mock_get_messages,
        mock_get_context
    ):
        """Test flujo completo del pipeline"""
        # Arrange
        service = PipelineService()
        workspace_id = 1
        
        mock_get_context.return_value = {"id": 1, "name": "Test Workspace"}
        mock_get_messages.return_value = [
            {"message": "mensaje 1"},
            {"message": "mensaje 2"},
        ]
        mock_get_agent.return_value = 100
        mock_clean_msgs.return_value = ["mensaje 1", "mensaje 2"]
        mock_gen_embeddings.return_value = [
            np.array([0.1, 0.2]),
            np.array([0.2, 0.3])
        ]
        mock_cluster_embeddings.return_value = np.array([0, 0])
        mock_group_clusters.return_value = {
            0: {
                "messages": ["mensaje 1", "mensaje 2"],
                "embeddings": [np.array([0.1, 0.2]), np.array([0.2, 0.3])]
            }
        }
        mock_save_faqs.return_value = 0
        
        # Act
        result = service.execute_pipeline(workspace_id)
        
        # Assert
        assert result["workspace_id"] == workspace_id
        mock_get_context.assert_called_once_with(workspace_id)
        mock_get_messages.assert_called_once()
        mock_load_existing.assert_called_once_with(workspace_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

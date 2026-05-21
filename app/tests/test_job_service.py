"""
Tests para job_service.py
Pruebas unitarias para los jobs de recarga de FAQs y mantenimiento
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

from app.services.job_service import FAQJobs, MaintenanceJobs, PipelineJobs


class TestFAQJobs:
    """Tests para la clase FAQJobs"""
    
    @patch('app.services.job_service.get_all_workspaces')
    @patch('app.services.job_service.pipeline_service')
    def test_reload_faqs_success(self, mock_pipeline_service, mock_get_workspaces):
        """Test que reload_faqs se ejecuta exitosamente con múltiples workspaces"""
        # Arrange
        mock_workspaces = [
            {"id": 1, "name": "Workspace 1"},
            {"id": 2, "name": "Workspace 2"},
            {"id": 3, "name": "Workspace 3"},
        ]
        mock_get_workspaces.return_value = mock_workspaces
        
        mock_pipeline_service.reload_faqs.side_effect = [
            {"status": "success", "faqs_count": 5},
            {"status": "success", "faqs_count": 8},
            {"status": "success", "faqs_count": 3},
        ]
        
        # Act
        FAQJobs.reload_faqs()
        
        # Assert
        mock_get_workspaces.assert_called_once()
        assert mock_pipeline_service.reload_faqs.call_count == 3
        mock_pipeline_service.reload_faqs.assert_any_call(1)
        mock_pipeline_service.reload_faqs.assert_any_call(2)
        mock_pipeline_service.reload_faqs.assert_any_call(3)
    
    @patch('app.services.job_service.get_all_workspaces')
    @patch('app.services.job_service.pipeline_service')
    def test_reload_faqs_with_partial_failures(self, mock_pipeline_service, mock_get_workspaces):
        """Test que reload_faqs maneja errores en algunos workspaces"""
        # Arrange
        mock_workspaces = [
            {"id": 1, "name": "Workspace 1"},
            {"id": 2, "name": "Workspace 2"},
            {"id": 3, "name": "Workspace 3"},
        ]
        mock_get_workspaces.return_value = mock_workspaces
        
        mock_pipeline_service.reload_faqs.side_effect = [
            {"status": "success", "faqs_count": 5},
            {"status": "error", "message": "Error al procesar"},
            {"status": "success", "faqs_count": 2},
        ]
        
        # Act - El job debe continuar procesando a pesar de los errores
        FAQJobs.reload_faqs()
        
        # Assert - Se procesaron todos los workspaces
        assert mock_pipeline_service.reload_faqs.call_count == 3
    
    @patch('app.services.job_service.get_all_workspaces')
    @patch('app.services.job_service.pipeline_service')
    def test_reload_faqs_empty_workspaces(self, mock_pipeline_service, mock_get_workspaces):
        """Test que reload_faqs maneja caso sin workspaces"""
        # Arrange
        mock_get_workspaces.return_value = []
        
        # Act
        FAQJobs.reload_faqs()
        
        # Assert
        mock_get_workspaces.assert_called_once()
        mock_pipeline_service.reload_faqs.assert_not_called()
    
    @patch('app.services.job_service.get_all_workspaces')
    @patch('app.services.job_service.pipeline_service')
    def test_test_faq_integrity_all_passed(self, mock_pipeline_service, mock_get_workspaces):
        """Test que test_faq_integrity verifica integridad correctamente"""
        # Arrange
        mock_workspaces = [
            {"id": 1, "name": "Workspace 1"},
            {"id": 2, "name": "Workspace 2"},
        ]
        mock_get_workspaces.return_value = mock_workspaces
        
        mock_pipeline_service.reload_faqs.side_effect = [
            {"status": "success", "faqs_count": 5},
            {"status": "success", "faqs_count": 3},
        ]
        
        # Act
        FAQJobs.test_faq_integrity()
        
        # Assert
        mock_get_workspaces.assert_called_once()
        assert mock_pipeline_service.reload_faqs.call_count == 2
    
    @patch('app.services.job_service.get_all_workspaces')
    @patch('app.services.job_service.pipeline_service')
    def test_test_faq_integrity_with_failures(self, mock_pipeline_service, mock_get_workspaces):
        """Test que test_faq_integrity maneja fallos en verificaciones"""
        # Arrange
        mock_workspaces = [
            {"id": 1, "name": "Workspace 1"},
            {"id": 2, "name": "Workspace 2"},
        ]
        mock_get_workspaces.return_value = mock_workspaces
        
        mock_pipeline_service.reload_faqs.side_effect = [
            {"status": "success", "faqs_count": 5},
            {"status": "error", "message": "Error"},
        ]
        
        # Act & Assert - No debe lanzar excepción
        FAQJobs.test_faq_integrity()
        
        assert mock_pipeline_service.reload_faqs.call_count == 2
    
    @patch('app.services.job_service.pipeline_service')
    def test_test_pipeline_with_sample_messages(self, mock_pipeline_service):
        """Test que test_pipeline_with_sample_messages ejecuta correctamente"""
        # Arrange
        mock_result = {
            "status": "success",
            "input_messages": 12,
            "valid_messages": 12,
            "clusters_found": 4,
        }
        mock_pipeline_service.test_pipeline.return_value = mock_result
        
        # Act
        result = FAQJobs.test_pipeline_with_sample_messages()
        
        # Assert
        assert result["status"] == "success"
        mock_pipeline_service.test_pipeline.assert_called_once()
        # Verificar que se pasaron 12 mensajes de prueba
        call_args = mock_pipeline_service.test_pipeline.call_args
        assert len(call_args[0][0]) == 12
    
    @patch('app.services.job_service.pipeline_service')
    def test_test_pipeline_with_sample_messages_error(self, mock_pipeline_service):
        """Test que test_pipeline_with_sample_messages maneja errores"""
        # Arrange
        mock_pipeline_service.test_pipeline.side_effect = Exception("Pipeline error")
        
        # Act
        result = FAQJobs.test_pipeline_with_sample_messages()
        
        # Assert
        assert result["status"] == "error"
        assert "Pipeline error" in result["message"]


class TestMaintenanceJobs:
    """Tests para la clase MaintenanceJobs"""
    
    def test_cleanup_old_logs_success(self):
        """Test que cleanup_old_logs se ejecuta sin errores"""
        # Act & Assert - No debe lanzar excepción
        MaintenanceJobs.cleanup_old_logs()
    
    @patch('app.services.job_service.get_all_workspaces')
    def test_check_system_health_all_ok(self, mock_get_workspaces):
        """Test que check_system_health reporta sistema en buen estado"""
        # Arrange
        mock_get_workspaces.return_value = [
            {"id": 1, "name": "Workspace 1"},
            {"id": 2, "name": "Workspace 2"},
        ]
        
        # Act & Assert - No debe lanzar excepción
        MaintenanceJobs.check_system_health()
    
    @patch('app.services.job_service.get_all_workspaces')
    def test_check_system_health_with_db_error(self, mock_get_workspaces):
        """Test que check_system_health maneja errores de BD"""
        # Arrange
        mock_get_workspaces.side_effect = Exception("Connection failed")
        
        # Act & Assert - No debe lanzar excepción, solo reportar
        MaintenanceJobs.check_system_health()


class TestPipelineJobs:
    """Tests para la clase PipelineJobs"""
    
    def test_reprocess_pending_messages_success(self):
        """Test que reprocess_pending_messages se ejecuta sin errores"""
        # Act & Assert - No debe lanzar excepción
        PipelineJobs.reprocess_pending_messages()
    
    def test_optimize_embeddings_success(self):
        """Test que optimize_embeddings se ejecuta sin errores"""
        # Act & Assert - No debe lanzar excepción
        PipelineJobs.optimize_embeddings()


class TestJobsIntegration:
    """Tests de integración para verificar flujos completos"""
    
    @patch('app.services.job_service.get_all_workspaces')
    @patch('app.services.job_service.pipeline_service')
    def test_reload_faqs_workflow(self, mock_pipeline_service, mock_get_workspaces):
        """Test del flujo completo de recarga de FAQs"""
        # Arrange
        mock_workspaces = [
            {"id": 1, "name": "Test Workspace", "workspace_id": 1},
        ]
        mock_get_workspaces.return_value = mock_workspaces
        mock_pipeline_service.reload_faqs.return_value = {
            "status": "success",
            "faqs_count": 10,
            "workspace_id": 1,
            "message": "Se cargaron 10 FAQs"
        }
        
        # Act
        FAQJobs.reload_faqs()
        
        # Assert
        mock_get_workspaces.assert_called_once()
        mock_pipeline_service.reload_faqs.assert_called_with(1)
    
    @patch('app.services.job_service.get_all_workspaces')
    @patch('app.services.job_service.pipeline_service')
    def test_multiple_workspace_processing(self, mock_pipeline_service, mock_get_workspaces):
        """Test procesamiento de múltiples workspaces en secuencia"""
        # Arrange
        workspaces_data = [
            {"id": i, "name": f"Workspace {i}", "workspace_id": i}
            for i in range(1, 6)
        ]
        mock_get_workspaces.return_value = workspaces_data
        
        mock_pipeline_service.reload_faqs.side_effect = [
            {"status": "success", "faqs_count": i * 2}
            for i in range(1, 6)
        ]
        
        # Act
        FAQJobs.reload_faqs()
        
        # Assert
        assert mock_pipeline_service.reload_faqs.call_count == 5
        for i in range(1, 6):
            mock_pipeline_service.reload_faqs.assert_any_call(i)


class TestJobsErrorHandling:
    """Tests para manejo de errores en jobs"""
    
    @patch('app.services.job_service.get_all_workspaces')
    @patch('app.services.job_service.pipeline_service')
    def test_reload_faqs_critical_error(self, mock_pipeline_service, mock_get_workspaces):
        """Test que errores críticos se propaguen correctamente"""
        # Arrange
        mock_get_workspaces.side_effect = Exception("Critical DB failure")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            FAQJobs.reload_faqs()
        
        assert "Critical DB failure" in str(exc_info.value)
    
    @patch('app.services.job_service.get_all_workspaces')
    @patch('app.services.job_service.pipeline_service')
    def test_test_faq_integrity_critical_error(self, mock_pipeline_service, mock_get_workspaces):
        """Test que errores en integridad se propaguen"""
        # Arrange
        mock_get_workspaces.side_effect = Exception("System error")
        
        # Act & Assert
        with pytest.raises(Exception):
            FAQJobs.test_faq_integrity()


class TestJobsLogging:
    """Tests para verificar que se registran eventos correctamente"""
    
    @patch('app.services.job_service.logger')
    @patch('app.services.job_service.get_all_workspaces')
    @patch('app.services.job_service.pipeline_service')
    def test_reload_faqs_logging(self, mock_pipeline_service, mock_get_workspaces, mock_logger):
        """Test que se registran eventos importantes en reload_faqs"""
        # Arrange
        mock_workspaces = [{"id": 1, "name": "Test"}]
        mock_get_workspaces.return_value = mock_workspaces
        mock_pipeline_service.reload_faqs.return_value = {
            "status": "success",
            "faqs_count": 5
        }
        
        # Act
        FAQJobs.reload_faqs()
        
        # Assert - Verificar que se llamó a logger.info
        assert mock_logger.info.called
        assert mock_logger.error.call_count == 0


class TestJobsEdgeCases:
    """Tests para casos especiales y edge cases"""
    
    @patch('app.services.job_service.get_all_workspaces')
    @patch('app.services.job_service.pipeline_service')
    def test_reload_faqs_with_missing_workspace_id(self, mock_pipeline_service, mock_get_workspaces):
        """Test que reload_faqs maneja workspaces sin ID"""
        # Arrange
        mock_workspaces = [
            {"name": "Workspace without ID"},
        ]
        mock_get_workspaces.return_value = mock_workspaces
        mock_pipeline_service.reload_faqs.return_value = {
            "status": "success",
            "faqs_count": 0
        }
        
        # Act & Assert
        # Debería manejar None como workspace_id
        FAQJobs.reload_faqs()
    
    @patch('app.services.job_service.get_all_workspaces')
    @patch('app.services.job_service.pipeline_service')
    def test_reload_faqs_with_zero_faqs(self, mock_pipeline_service, mock_get_workspaces):
        """Test que reload_faqs maneja workspaces sin FAQs"""
        # Arrange
        mock_workspaces = [{"id": 1, "name": "Empty Workspace"}]
        mock_get_workspaces.return_value = mock_workspaces
        mock_pipeline_service.reload_faqs.return_value = {
            "status": "success",
            "faqs_count": 0
        }
        
        # Act
        FAQJobs.reload_faqs()
        
        # Assert
        mock_pipeline_service.reload_faqs.assert_called_once_with(1)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

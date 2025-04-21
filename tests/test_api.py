import unittest
from unittest.mock import patch, MagicMock
import json
from fastapi.testclient import TestClient

from app.main import app
from app.models.ner_model import GLiNERModel


class TestAPI(unittest.TestCase):
    """
    Test cases for the API endpoints
    """
    
    def setUp(self):
        """
        Set up test client and mock dependencies
        """
        self.client = TestClient(app)
        
        # Mock the model to avoid actual loading during tests
        self.model_patcher = patch('app.api.endpoints.prediction.get_model')
        self.mock_get_model = self.model_patcher.start()
        
        # Create a mock model instance
        self.mock_model = MagicMock(spec=GLiNERModel)
        self.mock_model.model_name = "urchade/gliner_medium-v2.1"
        self.mock_model.device = "cpu"
        self.mock_model.is_loaded = True
        
        # Configure the mock to return our mock model instance
        self.mock_get_model.return_value = self.mock_model
        
        # Set up example prediction response
        self.example_entities = [
            {
                "text": "Microsoft",
                "start": 10,
                "end": 19,
                "entity_type": "ORGANIZATION",
                "score": 0.95
            },
            {
                "text": "Seattle",
                "start": 33,
                "end": 40,
                "entity_type": "LOCATION",
                "score": 0.92
            }
        ]
        
        # Configure the mock model to return our example entities
        self.mock_model.predict.return_value = self.example_entities
    
    def tearDown(self):
        """
        Clean up after tests
        """
        self.model_patcher.stop()
    
    def test_health_endpoint(self):
        """
        Test the health endpoint
        """
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})
    
    def test_model_health_endpoint(self):
        """
        Test the model health endpoint
        """
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "status": "healthy",
            "model_name": "urchade/gliner_medium-v2.1",
            "device": "cpu",
            "is_loaded": True
        })
    
    def test_predict_endpoint_success(self):
        """
        Test successful prediction
        """
        # Test request data
        request_data = {
            "text": "I work at Microsoft based in Seattle, Washington.",
            "entity_type": "ORGANIZATION"
        }
        
        # Send request to the endpoint
        response = self.client.post(
            "/api/v1/predict",
            json=request_data
        )
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Verify entities in response
        self.assertIn("entities", response_data)
        self.assertIn("processing_time", response_data)
        self.assertEqual(len(response_data["entities"]), 2)
        
        # Verify the model was called with the correct parameters
        self.mock_model.predict.assert_called_once_with(
            text=request_data["text"],
            entity_type=request_data["entity_type"]
        )
    
    def test_predict_endpoint_validation_error(self):
        """
        Test validation error for invalid request
        """
        # Missing required field
        request_data = {
            "text": "I work at Microsoft."
            # Missing entity_type
        }
        
        # Send request to the endpoint
        response = self.client.post(
            "/api/v1/predict",
            json=request_data
        )
        
        # Verify the response shows a validation error
        self.assertEqual(response.status_code, 422)
        self.assertIn("detail", response.json())
    
    def test_predict_endpoint_empty_text(self):
        """
        Test validation error for empty text
        """
        # Empty text field
        request_data = {
            "text": "",
            "entity_type": "ORGANIZATION"
        }
        
        # Send request to the endpoint
        response = self.client.post(
            "/api/v1/predict",
            json=request_data
        )
        
        # Verify the response shows a validation error
        self.assertEqual(response.status_code, 422)
        self.assertIn("detail", response.json())
    
    def test_predict_endpoint_model_error(self):
        """
        Test handling of model errors
        """
        # Configure mock to raise an exception
        self.mock_model.predict.side_effect = RuntimeError("Model prediction failed")
        
        # Test request data
        request_data = {
            "text": "I work at Microsoft based in Seattle, Washington.",
            "entity_type": "ORGANIZATION"
        }
        
        # Send request to the endpoint
        response = self.client.post(
            "/api/v1/predict",
            json=request_data
        )
        
        # Verify the response shows a server error
        self.assertEqual(response.status_code, 500)
        self.assertIn("detail", response.json())
        self.assertIn("Error during prediction", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
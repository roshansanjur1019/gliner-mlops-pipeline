import unittest
from unittest.mock import patch, MagicMock
import torch

from app.models.ner_model import GLiNERModel


class TestNERModel(unittest.TestCase):
    """
    Test cases for the GLiNERModel class
    """
    
    def setUp(self):
        """
        Set up test fixtures
        """
        # Patch the AutoTokenizer and AutoModelForTokenClassification for testing
        self.tokenizer_patcher = patch('app.models.ner_model.AutoTokenizer')
        self.model_patcher = patch('app.models.ner_model.AutoModelForTokenClassification')
        
        # Get the mocks
        self.mock_tokenizer_class = self.tokenizer_patcher.start()
        self.mock_model_class = self.model_patcher.start()
        
        # Create mock instances
        self.mock_tokenizer = MagicMock()
        self.mock_model = MagicMock()
        
        # Configure the mocks
        self.mock_tokenizer_class.from_pretrained.return_value = self.mock_tokenizer
        self.mock_model_class.from_pretrained.return_value = self.mock_model
        
        # Configure the model mock
        self.mock_model.eval = MagicMock(return_value=None)
        self.mock_model.to = MagicMock(return_value=self.mock_model)
        
        # Mock model outputs
        self.mock_outputs = MagicMock()
        self.mock_outputs.logits = torch.randn(1, 10, 2)  # Batch size 1, sequence length 10, 2 classes
        self.mock_model.return_value = self.mock_outputs
        
        # Create the model instance
        self.model_name = "urchade/gliner_medium-v2.1"
        self.ner_model = GLiNERModel(self.model_name)
    
    def tearDown(self):
        """
        Clean up after tests
        """
        self.tokenizer_patcher.stop()
        self.model_patcher.stop()
    
    def test_model_initialization(self):
        """
        Test model initialization
        """
        self.assertEqual(self.ner_model.model_name, self.model_name)
        self.assertIn(self.ner_model.device, ["cuda", "cpu"])
        self.assertFalse(self.ner_model.is_loaded)
        self.assertIsNone(self.ner_model.tokenizer)
        self.assertIsNone(self.ner_model.model)
    
    def test_load_model(self):
        """
        Test model loading
        """
        # Load the model
        self.ner_model.load_model()
        
        # Verify the model was loaded correctly
        self.mock_tokenizer_class.from_pretrained.assert_called_once_with(self.model_name)
        self.mock_model_class.from_pretrained.assert_called_once_with(self.model_name)
        
        # Verify model was moved to the correct device
        self.mock_model.to.assert_called_once_with(self.ner_model.device)
        
        # Verify model was set to eval mode
        self.mock_model.eval.assert_called_once()
        
        # Verify model state
        self.assertTrue(self.ner_model.is_loaded)
        self.assertEqual(self.ner_model.tokenizer, self.mock_tokenizer)
        self.assertEqual(self.ner_model.model, self.mock_model)
    
    def test_ensure_model_loaded(self):
        """
        Test ensure_model_loaded method
        """
        # Model not loaded initially
        self.assertFalse(self.ner_model.is_loaded)
        
        # Call ensure_model_loaded
        self.ner_model.ensure_model_loaded()
        
        # Verify model is now loaded
        self.assertTrue(self.ner_model.is_loaded)
        self.assertEqual(self.ner_model.tokenizer, self.mock_tokenizer)
        self.assertEqual(self.ner_model.model, self.mock_model)
        
        # Call ensure_model_loaded again
        # This should not attempt to load the model again since it's already loaded
        # Reset the mocks to verify they're not called again
        self.mock_tokenizer_class.from_pretrained.reset_mock()
        self.mock_model_class.from_pretrained.reset_mock()
        
        # Call ensure_model_loaded again
        self.ner_model.ensure_model_loaded()
        
        # Verify the load methods were not called again
        self.mock_tokenizer_class.from_pretrained.assert_not_called()
        self.mock_model_class.from_pretrained.assert_not_called()
    
    def test_predict(self):
        """
        Test prediction method
        """
        # Mock tokenizer return value
        mock_inputs = {
            "input_ids": torch.tensor([[101, 2054, 2003, 1996, 2307, 102]]),
            "attention_mask": torch.tensor([[1, 1, 1, 1, 1, 1]])
        }
        self.mock_tokenizer.return_value = mock_inputs
        
        # Configure the model to return to the correct device
        for key, value in mock_inputs.items():
            mock_inputs[key].to = MagicMock(return_value=value)
        
        # Run prediction
        text = "Test sentence"
        entity_type = "PERSON"
        
        # Make prediction
        entities = self.ner_model.predict(text, entity_type)
        
        # Verify model called with correct input
        self.mock_tokenizer.assert_called_once()
        self.mock_model.assert_called_once()
        
        # Verify result is a list of entities
        self.assertIsInstance(entities, list)
        # Note: The actual entity extraction logic would depend on the model's implementation
        # and would require more detailed testing of the _process_outputs method


if __name__ == "__main__":
    unittest.main()
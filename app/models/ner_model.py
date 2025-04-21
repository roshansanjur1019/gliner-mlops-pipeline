import os
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification

from app.core.config import settings
from prometheus_client import Histogram

# Setup logging
logger = logging.getLogger(__name__)

# Metrics for model performance
model_loading_time = Histogram('model_loading_seconds', 'Time to load model')
model_inference_time = Histogram('model_inference_seconds', 'Time for model inference')

class GLiNERModel:
    """
    Wrapper for the GLiNER NER model to handle loading and inference
    """
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the model wrapper
        
        Args:
            model_name: HuggingFace model name or path, defaults to config value
        """
        self.model_name = model_name or settings.MODEL_NAME
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        
        # Cache flag to track if model is loaded
        self.is_loaded = False
        
    def load_model(self) -> None:
        """
        Load the model and tokenizer
        """
        with model_loading_time.time():
            try:
                start_time = time.time()
                logger.info(f"Loading GLiNER model: {self.model_name}")
                
                # Load tokenizer and model
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForTokenClassification.from_pretrained(self.model_name)
                
                # Move model to appropriate device
                self.model.to(self.device)
                
                # Set model to evaluation mode
                self.model.eval()
                
                self.is_loaded = True
                
                load_time = time.time() - start_time
                logger.info(f"Model loaded successfully in {load_time:.2f} seconds (using {self.device})")
                
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise RuntimeError(f"Failed to load GLiNER model: {str(e)}")
    
    def ensure_model_loaded(self) -> None:
        """
        Ensure the model is loaded before inference
        """
        if not self.is_loaded:
            self.load_model()
    
    def predict(self, text: str, entity_type: str) -> List[Dict[str, Any]]:
        """
        Run inference on input text for the specified entity type
        
        Args:
            text: Input text for NER
            entity_type: The type of entity to extract
            
        Returns:
            List of extracted entities with positions and scores
        """
        self.ensure_model_loaded()
        
        with model_inference_time.time():
            try:
                # Prepare inputs for GLiNER model
                inputs = self.tokenizer(
                    f"Find {entity_type} in: {text}",
                    return_tensors="pt"
                ).to(self.device)
                
                # Run inference with no gradient calculation
                with torch.no_grad():
                    outputs = self.model(**inputs)
                
                # Process outputs and extract entities
                # Note: This is a simplified implementation
                # The actual processing would depend on GLiNER's output format
                entities = self._process_outputs(outputs, inputs, text, entity_type)
                
                return entities
                
            except Exception as e:
                logger.error(f"Prediction error: {e}")
                raise RuntimeError(f"Failed to run prediction: {str(e)}")
    
    def _process_outputs(self, outputs, inputs, text: str, entity_type: str) -> List[Dict[str, Any]]:
        """
        Process model outputs to extract entities
        
        Note: This is a simplified implementation and would need to be adapted
        based on GLiNER's specific output format and processing requirements
        """
        # Get the token classification logits
        logits = outputs.logits
        
        # Apply softmax to get probabilities
        probs = torch.nn.functional.softmax(logits, dim=-1)
        
        # Get predictions (simplified approach)
        predictions = torch.argmax(probs, dim=-1)[0].cpu().numpy()
        
        # Convert token predictions to entities
        # This is a placeholder - actual implementation would depend on GLiNER's specific output format
        entities = []
        
        # Example entity extraction (simplified)
        # In a real implementation, this would use the model's specific tokenization and output processing
        
        # For demo purposes - returning a placeholder result
        # This should be replaced with actual GLiNER output processing
        entities = [
            {
                "text": "Entity 1",  # This would be extracted from the text using token positions
                "start": 10,  # Character position in original text
                "end": 18,    # Character position in original text
                "entity_type": entity_type,
                "score": 0.95 # Confidence score
            }
        ]
        
        return entities

# Create a global model instance
model = GLiNERModel(settings.MODEL_NAME)

# Function to get the model instance
def get_model():
    """
    Get the global model instance, ensuring it's loaded
    """
    model.ensure_model_loaded()
    return model
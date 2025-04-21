import time
import logging
from typing import Dict, List, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.models.ner_model import get_model
from prometheus_client import Counter, Histogram

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Define prediction metrics
prediction_counter = Counter('api_ner_predictions_total', 'Total NER API Predictions')
prediction_error_counter = Counter('api_ner_errors_total', 'Total NER API Errors')
entity_counter = Counter('api_entities_found_total', 'Total Entities Found', ['entity_type'])
request_size_histogram = Histogram('api_request_text_length', 'Distribution of request text lengths')

# Define request and response models
class NERRequest(BaseModel):
    text: str = Field(..., description="Text to analyze for named entities", min_length=1)
    entity_type: str = Field(..., description="The type of entity to extract", min_length=1)

class Entity(BaseModel):
    text: str = Field(..., description="The extracted entity text")
    start: int = Field(..., description="Start position in the original text")
    end: int = Field(..., description="End position in the original text")
    entity_type: str = Field(..., description="Type of the entity extracted")
    score: float = Field(..., description="Confidence score", ge=0.0, le=1.0)

class NERResponse(BaseModel):
    entities: List[Entity] = Field(default_factory=list, description="List of extracted entities")
    processing_time: float = Field(..., description="Processing time in seconds")

@router.post("/predict", response_model=NERResponse, tags=["prediction"])
async def predict_entities(
    request: NERRequest,
    model = Depends(get_model)
) -> NERResponse:
    """
    Extract named entities from text
    """
    start_time = time.time()
    
    try:
        # Record request metrics
        prediction_counter.inc()
        request_size_histogram.observe(len(request.text))
        
        logger.info(f"Processing NER request for entity type: {request.entity_type}")
        
        # Run prediction
        entities = model.predict(
            text=request.text,
            entity_type=request.entity_type
        )
        
        # Record entity metrics
        entity_counter.labels(entity_type=request.entity_type).inc(len(entities))
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        logger.info(f"Found {len(entities)} entities in {processing_time:.2f} seconds")
        
        # Prepare response
        return NERResponse(
            entities=entities,
            processing_time=processing_time
        )
        
    except Exception as e:
        # Record error metrics
        prediction_error_counter.inc()
        
        # Log the error
        logger.error(f"Prediction error: {str(e)}")
        
        # Return error response
        raise HTTPException(
            status_code=500,
            detail=f"Error during prediction: {str(e)}"
        )

@router.get("/health", tags=["health"])
async def model_health_check(
    model = Depends(get_model)
) -> Dict[str, Any]:
    """
    Check if the model is loaded and ready for inference
    """
    return {
        "status": "healthy",
        "model_name": model.model_name,
        "device": model.device,
        "is_loaded": model.is_loaded
    }
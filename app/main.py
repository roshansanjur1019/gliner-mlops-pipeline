import time
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader

from app.api.endpoints import prediction
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.security import verify_api_key

# Setup logging
logger = setup_logging()

# Setup metrics
request_counter = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'status'])
request_latency = Histogram('http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint'])
prediction_counter = Counter('model_predictions_total', 'Total Model Predictions')
prediction_latency = Histogram('model_prediction_duration_seconds', 'Model Prediction Latency')

# Initialize OpenTelemetry metrics
reader = PrometheusMetricReader()
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter("gliner.metrics")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for GLiNER Named Entity Recognition model",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for request timing and metrics
@app.middleware("http")
async def add_metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    try:
        response = await call_next(request)
        status_code = response.status_code
        
    except Exception as e:
        logger.exception(f"Request handling error: {e}")
        status_code = 500
        response = JSONResponse(
            status_code=status_code,
            content={"detail": "Internal server error"}
        )
    
    # Record request metrics
    duration = time.time() - start_time
    request_counter.labels(
        method=request.method, 
        endpoint=request.url.path,
        status=status_code
    ).inc()
    request_latency.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

# Include routers
app.include_router(
    prediction.router,
    prefix="/api/v1",
    dependencies=[Depends(verify_api_key)] if settings.API_KEY_ENABLED else None
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.PROJECT_NAME} API server")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.PROJECT_NAME} API server")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=settings.DEBUG)  
# GLiNER NER Model MLOps Pipeline

A production-ready MLOps pipeline for deploying and serving the GLiNER Named Entity Recognition model.

## Overview

This project implements a complete MLOps pipeline for the GLiNER medium NER model (`urchade/gliner_medium-v2.1`), capable of identifying any entity type using a bidirectional transformer encoder (BERT-like). It provides a flexible, scalable, and robust solution for serving NER predictions through an API.

## Features

- **Model Loading and Inference Pipeline**
  - Fast, efficient model loading and caching
  - Optimized inference for production use
  - Support for arbitrary entity types in a zero-shot manner

- **API Service**
  - RESTful API for model prediction with FastAPI
  - Input validation and error handling
  - Comprehensive documentation with Swagger UI
  - Authentication and rate limiting

- **Infrastructure**
  - Containerization with Docker
  - Kubernetes deployment manifests
  - Multi-cloud support (AWS, GCP, Azure)
  - Horizontal autoscaling

- **Monitoring & Observability**
  - Prometheus metrics integration
  - Grafana dashboards
  - Detailed logging
  - Alerting for critical issues

- **Security**
  - API key authentication
  - Secure container configuration
  - HTTPS/TLS support
  - Secret management

- **CI/CD**
  - Automated testing
  - Continuous integration with Jenkins
  - Deployment pipelines for dev, staging, and production
  - Blue/green deployment support

## Architecture

The system architecture follows modern microservices and cloud-native best practices:

```
┌───────────────┐    ┌──────────────────┐    ┌───────────────┐
│ Load Balancer │───►│ API Service Pods │───►│  NER Model    │
└───────────────┘    └──────────────────┘    └───────────────┘
                              │
                              ▼
┌───────────────┐    ┌──────────────────┐    ┌───────────────┐
│  Prometheus   │◄───│ Metrics & Logs   │───►│  Grafana      │
└───────────────┘    └──────────────────┘    └───────────────┘
        │                                            │
        └────────────────┐               ┌───────────┘
                         ▼               ▼
                    ┌───────────────────────┐
                    │     AlertManager      │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Notification Channels │
                    └───────────────────────┘
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Kubernetes cluster (for production deployment)
- Python 3.10+

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/gliner-mlops-pipeline.git
   cd gliner-mlops-pipeline
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file (use `.env.example` as a template):
   ```bash
   cp .env.example .env
   ```

4. Run the application in development mode:
   ```bash
   uvicorn app.main:app --reload
   ```

5. Or use Docker Compose for local development:
   ```bash
   docker-compose up -d
   ```

6. Access the API documentation:
   - Swagger UI: http://localhost:8000/api/docs
   - ReDoc: http://localhost:8000/api/redoc

### Production Deployment

#### Using Kubernetes (Recommended)

1. Configure your Kubernetes environment:
   ```bash
   # Update the Kubernetes namespace if needed
   kubectl create namespace mlops
   ```

2. Deploy the application:
   ```bash
   kubectl apply -f k8s/
   ```

3. For cloud-specific deployments, see the appropriate documentation sections.

## API Documentation

### Authentication

API requests require an API key to be included in the header:

```
X-API-Key: your-api-key
```

### Entity Recognition Endpoint

**Endpoint**: `/api/v1/predict`

**Method**: POST

**Request Body**:
```json
{
  "text": "I work at Microsoft based in Seattle, Washington.",
  "entity_type": "ORGANIZATION"
}
```

**Response**:
```json
{
  "entities": [
    {
      "text": "Microsoft",
      "start": 10,
      "end": 19,
      "entity_type": "ORGANIZATION",
      "score": 0.95
    }
  ],
  "processing_time": 0.0234
}
```

## Monitoring & Alerting

The pipeline includes a comprehensive monitoring setup with Prometheus and Grafana:

- **Metrics Dashboard**: Access at http://localhost:3000 when running locally
- **Alert Rules**: Configured in `monitoring/prometheus/rules/`
- **Notification Channels**: Configured in `monitoring/alertmanager/alertmanager.yml`

Key metrics monitored:
- API request latency and throughput
- Model inference time
- Error rates
- Resource utilization (CPU, memory)

## CI/CD Pipeline

The CI/CD pipeline is implemented using Jenkins with the following stages:

1. **Build**: Compile and package the application
2. **Test**: Run unit and integration tests
3. **Security Scan**: Check for vulnerabilities
4. **Package**: Build Docker container
5. **Deploy**: Deploy to target environment

The pipeline supports multiple environments:
- **Development**: Automatic deployment from the develop branch
- **Staging**: Automatic deployment from the staging branch
- **Production**: Manual approval required for deployment from the main branch

## Security Considerations

- All containers run as non-root users
- API authentication required for all endpoints
- Secrets managed securely using Kubernetes secrets or cloud provider solutions
- Regular security scanning integrated into the CI/CD pipeline
- Network policies implemented to restrict traffic

## Troubleshooting

### Common Issues

1. **Model Loading Errors**:
   - Ensure sufficient memory is available
   - Check connectivity to model repository
   - Verify cache directory permissions

2. **API Authentication Issues**:
   - Verify API key is correctly set in environment variables
   - Check request headers format

3. **Kubernetes Deployment Issues**:
   - Ensure resource requests and limits are appropriate
   - Check pod logs for detailed error information
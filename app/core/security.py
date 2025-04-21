import logging
from typing import Optional

from fastapi import Depends, HTTPException, status, Security
from fastapi.security.api_key import APIKeyHeader, APIKeyCookie, APIKeyQuery
from starlette.status import HTTP_403_FORBIDDEN

from app.core.config import settings

# Setup logging
logger = logging.getLogger(__name__)

# Define API key authentication schemes
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_cookie = APIKeyCookie(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(
    api_key_header: Optional[str] = Security(api_key_header),
    api_key_query: Optional[str] = Security(api_key_query),
    api_key_cookie: Optional[str] = Security(api_key_cookie),
) -> bool:
    """
    Verify the API key from header, query param, or cookie
    
    Returns:
        bool: True if API key is valid
        
    Raises:
        HTTPException: If API key is invalid
    """
    if not settings.API_KEY_ENABLED:
        return True
        
    # Try to get API key from different sources
    api_key = api_key_header or api_key_query or api_key_cookie
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing",
            headers={"WWW-Authenticate": f"APIKey {API_KEY_NAME}"},
        )
    
    # Validate API key
    if api_key != settings.API_KEY:
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
            headers={"WWW-Authenticate": f"APIKey {API_KEY_NAME}"},
        )
        
    return True
from typing import Optional
from .base_client import BaseAPIClient
from .etherscan_client import EtherscanClient
from ..models.enums import APIProvider
from ..utils.rate_limiter import RateLimiter
from ..exceptions.custom_exceptions import ConfigurationError

class ClientFactory:
    """Factory for creating API clients"""
    
    @staticmethod
    def create_client(provider: APIProvider, api_key: str, 
                     rate_limiter: Optional[RateLimiter] = None) -> BaseAPIClient:
        """Create API client based on provider"""
        
        if not rate_limiter:
            rate_limiter = RateLimiter(calls_per_second=5)
        
        if provider == APIProvider.ETHERSCAN:
            if not api_key:
                raise ConfigurationError("Etherscan API key is required")
            return EtherscanClient(api_key, rate_limiter)
        
        # Add other providers here
        # elif provider == APIProvider.ALCHEMY:
        #     return AlchemyClient(api_key, rate_limiter)
        
        else:
            raise ConfigurationError(f"Unsupported provider: {provider}")
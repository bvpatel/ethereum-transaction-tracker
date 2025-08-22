from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import aiohttp
import logging
from ..models.transaction import Transaction, TokenTransfer, InternalTransaction
from ..exceptions.custom_exceptions import APIError, RateLimitError
from ..utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class BaseAPIClient(ABC):
    """Abstract base class for API clients"""
    
    def __init__(self, api_key: str, base_url: str, rate_limiter: RateLimiter):
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limiter = rate_limiter
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'EthereumTransactionTracker/1.0'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request with rate limiting and error handling"""
        await self.rate_limiter.wait()
        
        if not self.session:
            raise APIError("Session not initialized")
        
        try:
            async with self.session.get(f"{self.base_url}{endpoint}", params=params) as response:
                if response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                
                if response.status != 200:
                    raise APIError(f"HTTP {response.status}: {await response.text()}")
                
                data = await response.json()
                
                if not self._is_successful_response(data):
                    raise APIError(f"API Error: {self._get_error_message(data)}")
                
                return data
                
        except aiohttp.ClientError as e:
            raise APIError(f"Network error: {str(e)}")

    @abstractmethod
    def _is_successful_response(self, data: Dict[str, Any]) -> bool:
        """Check if API response indicates success"""
        pass

    @abstractmethod
    def _get_error_message(self, data: Dict[str, Any]) -> str:
        """Extract error message from API response"""
        pass

    @abstractmethod
    async def get_normal_transactions(self, address: str, start_block: int = 0, 
                                    end_block: int = 99999999, page: int = 1, 
                                    offset: int = 1000) -> List[Transaction]:
        """Get normal transactions for an address"""
        pass

    @abstractmethod
    async def get_internal_transactions(self, address: str, start_block: int = 0,
                                      end_block: int = 99999999, page: int = 1,
                                      offset: int = 1000) -> List[InternalTransaction]:
        """Get internal transactions for an address"""
        pass

    @abstractmethod
    async def get_token_transfers(self, address: str, contract_address: str = None,
                                start_block: int = 0, end_block: int = 99999999,
                                page: int = 1, offset: int = 1000) -> List[TokenTransfer]:
        """Get token transfers for an address"""
        pass
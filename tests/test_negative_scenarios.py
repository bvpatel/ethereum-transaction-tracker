import pytest
from unittest.mock import AsyncMock, patch
from src.main import EthereumTransactionTracker
from src.exceptions.custom_exceptions import APIError, ConfigurationError, ValidationError

class TestNegativeScenarios:
    """Test negative scenarios and error handling"""
    
    @pytest.mark.asyncio
    async def test_missing_api_key(self):
        """Test initialization with missing API key"""
        with patch.dict('os.environ', {'ETHERSCAN_API_KEY': ''}):
            tracker = EthereumTransactionTracker()
            
            with pytest.raises(ConfigurationError):
                await tracker.initialize("etherscan")

    @pytest.mark.asyncio
    async def test_network_timeout(self, rate_limiter):
        """Test network timeout handling"""
        from src.api.etherscan_client import EtherscanClient
        
        client = EtherscanClient("test_key", rate_limiter)
        
        with patch.object(client, '_make_request', side_effect=APIError("Network timeout")):
            with pytest.raises(APIError):
                await client.get_normal_transactions("0xa39b189482f984388a34460636fea9eb181ad1a6")

    @pytest.mark.asyncio
    async def test_invalid_api_response(self, rate_limiter):
        """Test handling of invalid API responses"""
        from src.api.etherscan_client import EtherscanClient
        
        client = EtherscanClient("test_key", rate_limiter)
        
        # Mock invalid response
        invalid_response = {"status": "0", "message": "Invalid API Key"}
        
        with patch.object(client, '_make_request', return_value=invalid_response):
            with pytest.raises(APIError):
                await client.get_normal_transactions("0xa39b189482f984388a34460636fea9eb181ad1a6")

    def test_malformed_transaction_data(self):
        """Test handling of malformed transaction data"""
        from src.api.etherscan_client import EtherscanClient
        from src.utils.rate_limiter import RateLimiter
        
        client = EtherscanClient("test_key", RateLimiter())
        
        # Malformed transaction data
        malformed_data = {
            "hash": "invalid_hash",
            "blockNumber": "not_a_number",
            "timeStamp": "invalid_timestamp"
        }
        
        # Should return None for malformed data
        transaction = client._parse_normal_transaction(malformed_data)
        assert transaction is None

    @pytest.mark.asyncio
    async def test_empty_transaction_list(self, mock_api_client):
        """Test processing empty transaction list"""
        from src.processors.transaction_processor import TransactionProcessor
        
        mock_api_client.get_normal_transactions = AsyncMock(return_value=[])
        mock_api_client.get_internal_transactions = AsyncMock(return_value=[])
        mock_api_client.get_token_transfers = AsyncMock(return_value=[])
        
        processor = TransactionProcessor(mock_api_client)
        
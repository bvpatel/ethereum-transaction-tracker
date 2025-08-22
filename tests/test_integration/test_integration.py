import pytest
import tempfile
import os
from unittest.mock import patch, AsyncMock
from src.main import EthereumTransactionTracker
from src.models.enums import APIProvider

class TestEndToEnd:
    """End-to-end integration tests"""
    
    @pytest.fixture
    def temp_config(self):
        """Create temporary configuration"""
        with patch.dict(os.environ, {
            'ETHERSCAN_API_KEY': 'test_key',
            'OUTPUT_DIRECTORY': tempfile.mkdtemp(),
            'MAX_TRANSACTIONS': '100'
        }):
            yield

    @pytest.mark.asyncio
    async def test_full_workflow_success(self, temp_config, sample_transaction):
        """Test complete workflow from address to CSV"""
        tracker = EthereumTransactionTracker()
        
        # Mock the API client
        with patch('src.api.client_factory.ClientFactory.create_client') as mock_factory:
            mock_client = AsyncMock()
            mock_client.get_normal_transactions = AsyncMock(return_value=[sample_transaction])
            mock_client.get_internal_transactions = AsyncMock(return_value=[])
            mock_client.get_token_transfers = AsyncMock(return_value=[])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            mock_factory.return_value = mock_client
            
            await tracker.initialize("etherscan")
            
            result = await tracker.process_address(
                "0xa39b189482f984388a34460636fea9eb181ad1a6",
                max_transactions=100
            )
            
            assert result['transaction_count'] == 1
            assert result['csv_file'] is not None
            assert os.path.exists(result['csv_file'])

    @pytest.mark.asyncio
    async def test_invalid_address_handling(self, temp_config):
        """Test handling of invalid addresses"""
        from src.exceptions.custom_exceptions import ValidationError
        
        tracker = EthereumTransactionTracker()
        await tracker.initialize("etherscan")
        
        with pytest.raises(ValidationError):
            await tracker.process_address("invalid_address")

    @pytest.mark.asyncio
    async def test_batch_processing(self, temp_config, sample_transaction):
        """Test batch processing of multiple addresses"""
        tracker = EthereumTransactionTracker()
        
        with patch('src.api.client_factory.ClientFactory.create_client') as mock_factory:
            mock_client = AsyncMock()
            mock_client.get_normal_transactions = AsyncMock(return_value=[sample_transaction])
            mock_client.get_internal_transactions = AsyncMock(return_value=[])
            mock_client.get_token_transfers = AsyncMock(return_value=[])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            mock_factory.return_value = mock_client
            
            await tracker.initialize("etherscan")
            
            addresses = [
                "0xa39b189482f984388a34460636fea9eb181ad1a6",
                "0xd620aaadabaa20d2af700853c4504028cba7c3333"
            ]
            
            results = await tracker.batch_process_addresses(addresses, max_transactions=50)
            
            assert len(results) == 2
            for address in addresses:
                assert address in results
                assert 'transaction_count' in results[address]
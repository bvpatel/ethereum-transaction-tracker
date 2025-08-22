import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from src.processors.transaction_processor import TransactionProcessor
from src.processors.data_categorizer import DataCategorizer

class TestTransactionProcessor:
    """Test transaction processor functionality"""
    
    @pytest.fixture
    def processor(self, mock_api_client):
        """Create processor with mock client"""
        return TransactionProcessor(mock_api_client)

    @pytest.mark.asyncio
    async def test_process_wallet_transactions_success(self, processor, sample_transaction):
        """Test successful wallet transaction processing"""
        # Mock client responses
        processor.client.get_normal_transactions = AsyncMock(return_value=[sample_transaction])
        processor.client.get_internal_transactions = AsyncMock(return_value=[])
        processor.client.get_token_transfers = AsyncMock(return_value=[])
        
        address = "0xa39b189482f984388a34460636fea9eb181ad1a6"
        
        with patch.object(processor.client, '__aenter__', return_value=processor.client):
            with patch.object(processor.client, '__aexit__', return_value=None):
                transactions = await processor.process_wallet_transactions(address)
        
        assert len(transactions) == 1
        assert transactions[0].hash == sample_transaction.hash

    @pytest.mark.asyncio
    async def test_process_wallet_transactions_with_pagination(self, processor):
        """Test pagination handling"""
        # Mock large dataset requiring pagination
        batch1 = [Mock() for _ in range(1000)]
        batch2 = [Mock() for _ in range(500)]
        
        processor.client.get_normal_transactions = AsyncMock(side_effect=[batch1, batch2, []])
        processor.client.get_internal_transactions = AsyncMock(return_value=[])
        processor.client.get_token_transfers = AsyncMock(return_value=[])
        
        address = "0xa39b189482f984388a34460636fea9eb181ad1a6"
        
        with patch.object(processor.client, '__aenter__', return_value=processor.client):
            with patch.object(processor.client, '__aexit__', return_value=None):
                transactions = await processor.process_wallet_transactions(
                    address, max_transactions=2000
                )
        
        # Should have called get_normal_transactions multiple times
        assert processor.client.get_normal_transactions.call_count >= 2

    @pytest.mark.asyncio
    async def test_process_wallet_transactions_api_error(self, processor):
        """Test handling of API errors"""
        from src.exceptions.custom_exceptions import APIError
        
        processor.client.get_normal_transactions = AsyncMock(side_effect=APIError("API Error"))
        processor.client.get_internal_transactions = AsyncMock(return_value=[])
        processor.client.get_token_transfers = AsyncMock(return_value=[])
        
        address = "0xa39b189482f984388a34460636fea9eb181ad1a6"
        
        with patch.object(processor.client, '__aenter__', return_value=processor.client):
            with patch.object(processor.client, '__aexit__', return_value=None):
                with pytest.raises(Exception):  # Should propagate the error
                    await processor.process_wallet_transactions(address)
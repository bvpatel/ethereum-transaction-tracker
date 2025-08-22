import pytest
import gc
import psutil
import os
from unittest.mock import AsyncMock, patch
from src.processors.transaction_processor import TransactionProcessor

class TestMemoryManagement:
    """Memory usage and leak tests"""
    
    @pytest.mark.asyncio
    async def test_memory_usage_large_dataset(self, mock_api_client, sample_transaction):
        """Test memory usage with large transaction datasets"""
        # Create large dataset
        large_dataset = [sample_transaction] * 10000
        
        mock_api_client.get_normal_transactions = AsyncMock(return_value=large_dataset)
        mock_api_client.get_internal_transactions = AsyncMock(return_value=[])
        mock_api_client.get_token_transfers = AsyncMock(return_value=[])
        
        processor = TransactionProcessor(mock_api_client)
        
        # Measure memory before processing
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss
        
        with patch.object(mock_api_client, '__aenter__', return_value=mock_api_client):
            with patch.object(mock_api_client, '__aexit__', return_value=None):
                transactions = await processor.process_wallet_transactions(
                    "0xa39b189482f984388a34460636fea9eb181ad1a6",
                    max_transactions=10000
                )
        
        # Measure memory after processing
        memory_after = process.memory_info().rss
        memory_increase = memory_after - memory_before
        
        # Memory increase should be reasonable (less than 100MB for 10k transactions)
        assert memory_increase < 100 * 1024 * 1024
        assert len(transactions) <= 10000

    def test_garbage_collection_effectiveness(self, sample_transaction):
        """Test that objects are properly garbage collected"""
        import weakref
        
        # Create a large list of transactions
        transactions = [sample_transaction] * 1000
        
        # Create weak references to track garbage collection
        weak_refs = [weakref.ref(tx) for tx in transactions]
        
        # Delete the transactions
        del transactions
        gc.collect()
        
        # Most weak references should be dead
        alive_refs = sum(1 for ref in weak_refs if ref() is not None)
        assert alive_refs <= 1  # Only sample_transaction fixture should remain

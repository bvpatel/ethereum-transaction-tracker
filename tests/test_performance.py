import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from src.processors.transaction_processor import TransactionProcessor

class TestPerformance:
    """Performance and stress tests"""
    
    @pytest.mark.asyncio
    async def test_large_dataset_processing(self, mock_api_client, sample_transaction):
        """Test processing large number of transactions"""
        # Create large dataset
        large_dataset = [sample_transaction] * 1000
        
        mock_api_client.get_normal_transactions = AsyncMock(return_value=large_dataset)
        mock_api_client.get_internal_transactions = AsyncMock(return_value=[])
        mock_api_client.get_token_transfers = AsyncMock(return_value=[])
        
        processor = TransactionProcessor(mock_api_client)
        
        with patch.object(mock_api_client, '__aenter__', return_value=mock_api_client):
            with patch.object(mock_api_client, '__aexit__', return_value=None):
                transactions = await processor.process_wallet_transactions(
                    "0xa39b189482f984388a34460636fea9eb181ad1a6"
                )
        
        assert len(transactions) == 10000

    def test_csv_export_file_permission_error(self, sample_transaction):
        """Test CSV export with file permission errors"""
        from src.exporters.csv_exporter import CSVExporter
        
        # Try to export to a directory that doesn't exist and can't be created
        exporter = CSVExporter(output_directory="/invalid/path/that/cannot/be/created")
        
        with pytest.raises(Exception):  # Should raise an OS error
            exporter.export_transactions(
                [sample_transaction], 
                "0xa39b189482f984388a34460636fea9eb181ad1a6"
            )
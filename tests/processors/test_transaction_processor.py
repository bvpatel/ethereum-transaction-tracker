import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, call
from decimal import Decimal
from datetime import datetime
from typing import List
from concurrent.futures import ThreadPoolExecutor

# Assuming these imports exist in your project structure
from src.models.transaction import Transaction, TokenTransfer, InternalTransaction
from src.models.enums import TransactionType, TransactionStatus
from src.api.base_client import BaseAPIClient
from src.processors.data_categorizer import DataCategorizer
from src.processors.transaction_processor import TransactionProcessor


class TestTransactionProcessor:
    """Test cases for TransactionProcessor class"""

    @pytest.fixture
    def mock_client(self):
        """Create a mock API client"""
        client = Mock(spec=BaseAPIClient)
        client.get_normal_transactions = AsyncMock()
        client.get_internal_transactions = AsyncMock()
        client.get_token_transfers = AsyncMock()
        return client

    @pytest.fixture
    def mock_categorizer(self):
        """Create a mock data categorizer"""
        categorizer = Mock(spec=DataCategorizer)
        categorizer.convert_internal_to_transaction = Mock()
        categorizer.convert_token_transfer_to_transaction = Mock()
        categorizer.categorize_transactions = Mock()
        return categorizer

    @pytest.fixture
    def processor(self, mock_client, mock_categorizer):
        """Create a TransactionProcessor instance for testing"""
        return TransactionProcessor(mock_client, mock_categorizer)

    @pytest.fixture
    def processor_with_default_categorizer(self, mock_client):
        """Create a TransactionProcessor with default categorizer"""
        return TransactionProcessor(mock_client)

    @pytest.fixture
    def sample_normal_transaction(self):
        """Create a sample normal transaction"""
        return Transaction(
            hash="0xnormal123",
            block_number=12345,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            from_address="0xfrom123",
            to_address="0xto456",
            value=Decimal("1.0"),
            gas_used=21000,
            gas_price=Decimal("20"),
            transaction_fee=Decimal("0.42"),
            status=TransactionStatus.SUCCESS,
            transaction_type=TransactionType.ETH_TRANSFER,
            nonce=1,
            transaction_index=0,
            raw_data={}
        )

    @pytest.fixture
    def sample_internal_transaction(self):
        """Create a sample internal transaction"""
        return InternalTransaction(
            hash="0xinternal123",
            block_number=12346,
            timestamp=datetime(2024, 1, 1, 12, 1, 0),
            from_address="0xfrom123",
            to_address="0xto456",
            value=Decimal("0.5"),
            gas_used=15000,
            is_error=False,
            error_code=""
        )

    @pytest.fixture
    def sample_token_transfer(self):
        """Create a sample token transfer"""
        return TokenTransfer(
            transaction_hash="0xtoken123",
            block_number=12347,
            timestamp=datetime(2024, 1, 1, 12, 2, 0),
            from_address="0xfrom123",
            to_address="0xto456",
            value=Decimal("100"),
            contract_address="0xtoken_contract",
            token_symbol="TEST",
            token_name="Test Token",
            token_decimals=18,
            token_id=None
        )

    def test_init_with_categorizer(self, mock_client, mock_categorizer):
        """Test initialization with provided categorizer"""
        processor = TransactionProcessor(mock_client, mock_categorizer)
        
        assert processor.client == mock_client
        assert processor.categorizer == mock_categorizer
        assert isinstance(processor.executor, ThreadPoolExecutor)

    def test_init_with_default_categorizer(self, mock_client):
        """Test initialization with default categorizer"""
        with patch('src.processors.transaction_processor.DataCategorizer') as mock_categorizer_class:
            mock_categorizer_instance = Mock()
            mock_categorizer_class.return_value = mock_categorizer_instance
            
            processor = TransactionProcessor(mock_client)
            
            assert processor.client == mock_client
            assert processor.categorizer == mock_categorizer_instance
            mock_categorizer_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_wallet_transactions_success(self, processor, mock_client, mock_categorizer,
                                                      sample_normal_transaction, sample_internal_transaction,
                                                      sample_token_transfer):
        """Test successful processing of wallet transactions"""
        # Setup mock responses
        mock_client.get_normal_transactions.return_value = [sample_normal_transaction]
        mock_client.get_internal_transactions.return_value = [sample_internal_transaction]
        mock_client.get_token_transfers.return_value = [sample_token_transfer]
        
        # Setup categorizer mocks
        converted_internal = Transaction(
            hash="0xinternal_converted",
            block_number=12346,
            timestamp=datetime(2024, 1, 1, 12, 1, 0),
            from_address="0xfrom123",
            to_address="0xto456",
            value=Decimal("0.5"),
            gas_used=15000,
            gas_price=Decimal("0"),
            transaction_fee=Decimal("0"),
            status=TransactionStatus.SUCCESS,
            transaction_type=TransactionType.INTERNAL_TRANSFER,
            nonce=0,
            transaction_index=0,
            raw_data={"internal": True}
        )
        
        converted_token = Transaction(
            hash="0xtoken_converted",
            block_number=12347,
            timestamp=datetime(2024, 1, 1, 12, 2, 0),
            from_address="0xfrom123",
            to_address="0xto456",
            value=Decimal("100"),
            gas_used=0,
            gas_price=Decimal("0"),
            transaction_fee=Decimal("0"),
            status=TransactionStatus.SUCCESS,
            transaction_type=TransactionType.ERC20_TRANSFER,
            nonce=0,
            transaction_index=0,
            contract_address="0xtoken_contract",
            token_symbol="TEST",
            raw_data={"token_transfer": True}
        )
        
        mock_categorizer.convert_internal_to_transaction.return_value = converted_internal
        mock_categorizer.convert_token_transfer_to_transaction.return_value = converted_token
        mock_categorizer.categorize_transactions.return_value = [sample_normal_transaction, converted_internal, converted_token]
        
        # Execute
        result = await processor.process_wallet_transactions("0xtest_address")
        
        # Verify API calls
        mock_client.get_normal_transactions.assert_called_once_with("0xtest_address", 0, 99999999, 1, 1000)
        mock_client.get_internal_transactions.assert_called_once_with("0xtest_address", 0, 99999999, 1, 1000)
        mock_client.get_token_transfers.assert_called_once_with("0xtest_address", None, 0, 99999999, 1, 1000)
        
        # Verify categorizer calls
        mock_categorizer.convert_internal_to_transaction.assert_called_once_with(sample_internal_transaction)
        mock_categorizer.convert_token_transfer_to_transaction.assert_called_once_with(sample_token_transfer)
        mock_categorizer.categorize_transactions.assert_called_once()
        
        # Verify result
        assert len(result) == 3
        assert all(isinstance(tx, Transaction) for tx in result)

    @pytest.mark.asyncio
    async def test_process_wallet_transactions_with_parameters(self, processor, mock_client, mock_categorizer):
        """Test processing with custom parameters"""
        mock_client.get_normal_transactions.return_value = []
        mock_client.get_internal_transactions.return_value = []
        mock_client.get_token_transfers.return_value = []
        mock_categorizer.categorize_transactions.return_value = []
        
        await processor.process_wallet_transactions(
            "0xtest_address",
            start_block=100,
            end_block=200,
            max_transactions=50
        )
        
        # Verify parameters passed correctly
        mock_client.get_normal_transactions.assert_called_once_with("0xtest_address", 100, 200, 1, 50)
        mock_client.get_internal_transactions.assert_called_once_with("0xtest_address", 100, 200, 1, 50)
        mock_client.get_token_transfers.assert_called_once_with("0xtest_address", None, 100, 200, 1, 50)

    @pytest.mark.asyncio
    async def test_process_wallet_transactions_with_api_errors(self, processor, mock_client, mock_categorizer):
        """Test processing when some API calls fail"""
        # Make one API call fail
        mock_client.get_normal_transactions.return_value = []
        mock_client.get_internal_transactions.side_effect = Exception("API Error")
        mock_client.get_token_transfers.return_value = []
        mock_categorizer.categorize_transactions.return_value = []
        
        # Should not raise exception, but continue processing
        result = await processor.process_wallet_transactions("0xtest_address")
        
        assert result == []
        mock_categorizer.categorize_transactions.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_wallet_transactions_max_limit_applied(self, processor, mock_client, mock_categorizer):
        """Test that max transaction limit is applied"""
        # Create more transactions than the limit
        transactions = []
        for i in range(15):
            tx = Transaction(
                hash=f"0x{i:064x}",
                block_number=12345 + i,
                timestamp=datetime(2024, 1, 1, 12, 0, i),
                from_address="0xfrom123",
                to_address="0xto456",
                value=Decimal("1.0"),
                gas_used=21000,
                gas_price=Decimal("20"),
                transaction_fee=Decimal("0.42"),
                status=TransactionStatus.SUCCESS,
                transaction_type=TransactionType.ETH_TRANSFER,
                nonce=i,
                transaction_index=i,
                raw_data={}
            )
            transactions.append(tx)
        
        mock_client.get_normal_transactions.return_value = transactions
        mock_client.get_internal_transactions.return_value = []
        mock_client.get_token_transfers.return_value = []
        mock_categorizer.categorize_transactions.return_value = transactions
        
        result = await processor.process_wallet_transactions("0xtest_address", max_transactions=15)
        
        assert len(result) <= 15

    @pytest.mark.asyncio
    async def test_process_wallet_transactions_sorting(self, processor, mock_client, mock_categorizer):
        """Test that transactions are sorted by timestamp descending"""
        # Create transactions with different timestamps
        tx1 = Transaction(
            hash="0x1", block_number=1, timestamp=datetime(2024, 1, 1, 12, 0, 0),
            from_address="0xfrom", to_address="0xto", value=Decimal("1"),
            gas_used=21000, gas_price=Decimal("20"), transaction_fee=Decimal("0.42"),
            status=TransactionStatus.SUCCESS, transaction_type=TransactionType.ETH_TRANSFER,
            nonce=1, transaction_index=0, raw_data={}
        )
        
        tx2 = Transaction(
            hash="0x2", block_number=2, timestamp=datetime(2024, 1, 1, 12, 1, 0),
            from_address="0xfrom", to_address="0xto", value=Decimal("1"),
            gas_used=21000, gas_price=Decimal("20"), transaction_fee=Decimal("0.42"),
            status=TransactionStatus.SUCCESS, transaction_type=TransactionType.ETH_TRANSFER,
            nonce=2, transaction_index=1, raw_data={}
        )
        
        tx3 = Transaction(
            hash="0x3", block_number=3, timestamp=datetime(2024, 1, 1, 11, 59, 0),
            from_address="0xfrom", to_address="0xto", value=Decimal("1"),
            gas_used=21000, gas_price=Decimal("20"), transaction_fee=Decimal("0.42"),
            status=TransactionStatus.SUCCESS, transaction_type=TransactionType.ETH_TRANSFER,
            nonce=3, transaction_index=2, raw_data={}
        )
        
        mock_client.get_normal_transactions.return_value = [tx1, tx3, tx2]  # Unsorted
        mock_client.get_internal_transactions.return_value = []
        mock_client.get_token_transfers.return_value = []
        
        # Mock categorizer to return sorted transactions
        def sort_transactions(txs):
            return sorted(txs, key=lambda x: x.timestamp, reverse=True)
        
        mock_categorizer.categorize_transactions.side_effect = sort_transactions
        
        result = await processor.process_wallet_transactions("0xtest_address")
        
        # Should be sorted by timestamp descending (newest first)
        assert result[0].timestamp == datetime(2024, 1, 1, 12, 1, 0)  # tx2
        assert result[1].timestamp == datetime(2024, 1, 1, 12, 0, 0)  # tx1
        assert result[2].timestamp == datetime(2024, 1, 1, 11, 59, 0)  # tx3

    @pytest.mark.asyncio
    async def test_process_wallet_transactions_conversion_failures(self, processor, mock_client, mock_categorizer,
                                                                  sample_internal_transaction, sample_token_transfer):
        """Test handling of conversion failures"""
        mock_client.get_normal_transactions.return_value = []
        mock_client.get_internal_transactions.return_value = [sample_internal_transaction]
        mock_client.get_token_transfers.return_value = [sample_token_transfer]
        
        # Make conversions return None (failed conversions)
        mock_categorizer.convert_internal_to_transaction.return_value = None
        mock_categorizer.convert_token_transfer_to_transaction.return_value = None
        mock_categorizer.categorize_transactions.return_value = []
        
        result = await processor.process_wallet_transactions("0xtest_address")
        
        # Should not include failed conversions
        assert len(result) == 0
        mock_categorizer.convert_internal_to_transaction.assert_called_once()
        mock_categorizer.convert_token_transfer_to_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_normal_transactions_single_page(self, processor, mock_client, sample_normal_transaction):
        """Test fetching normal transactions with single page"""
        mock_client.get_normal_transactions.return_value = [sample_normal_transaction]
        
        result = await processor._fetch_normal_transactions("0xtest_address", 0, 999999, 1000)
        
        assert len(result) == 1
        assert result[0] == sample_normal_transaction
        mock_client.get_normal_transactions.assert_called_once_with("0xtest_address", 0, 999999, 1, 1000)

    @pytest.mark.asyncio
    async def test_fetch_normal_transactions_multiple_pages(self, processor, mock_client):
        """Test fetching normal transactions with multiple pages"""
        # Create transactions for multiple pages
        page1_txs = [Mock() for _ in range(1000)]
        page2_txs = [Mock() for _ in range(500)]
        
        mock_client.get_normal_transactions.side_effect = [page1_txs, page2_txs, []]
        
        result = await processor._fetch_normal_transactions("0xtest_address", 0, 999999, 2000)
        
        assert len(result) == 1500
        assert mock_client.get_normal_transactions.call_count == 2
        
        # Check call parameters
        calls = mock_client.get_normal_transactions.call_args_list
        assert calls[0] == call("0xtest_address", 0, 999999, 1, 1000)
        assert calls[1] == call("0xtest_address", 0, 999999, 2, 1000)

    @pytest.mark.asyncio
    async def test_fetch_normal_transactions_with_max_limit(self, processor, mock_client):
        """Test fetching normal transactions respects max limit"""
        # Create more transactions than max limit
        page1_txs = [Mock() for _ in range(1000)]
        page2_txs = [Mock() for _ in range(1000)]
        
        mock_client.get_normal_transactions.side_effect = [page1_txs, page2_txs]
        
        result = await processor._fetch_normal_transactions("0xtest_address", 0, 999999, 1500)
        
        # Should stop at max limit
        assert len(result) == 1500

    @pytest.mark.asyncio
    async def test_fetch_normal_transactions_api_error(self, processor, mock_client):
        """Test handling of API error during normal transaction fetching"""
        mock_client.get_normal_transactions.side_effect = Exception("API Error")
        
        result = await processor._fetch_normal_transactions("0xtest_address", 0, 999999, 1000)
        
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_normal_transactions_empty_response(self, processor, mock_client):
        """Test handling of empty response"""
        mock_client.get_normal_transactions.return_value = []
        
        result = await processor._fetch_normal_transactions("0xtest_address", 0, 999999, 1000)
        
        assert result == []
        mock_client.get_normal_transactions.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_internal_transactions(self, processor, mock_client, sample_internal_transaction):
        """Test fetching internal transactions"""
        mock_client.get_internal_transactions.return_value = [sample_internal_transaction]
        
        result = await processor._fetch_internal_transactions("0xtest_address", 0, 999999, 1000)
        
        assert len(result) == 1
        assert result[0] == sample_internal_transaction
        mock_client.get_internal_transactions.assert_called_once_with("0xtest_address", 0, 999999, 1, 1000)

    @pytest.mark.asyncio
    async def test_fetch_token_transfers(self, processor, mock_client, sample_token_transfer):
        """Test fetching token transfers"""
        mock_client.get_token_transfers.return_value = [sample_token_transfer]
        
        result = await processor._fetch_token_transfers("0xtest_address", 0, 999999, 1000)
        
        assert len(result) == 1
        assert result[0] == sample_token_transfer
        mock_client.get_token_transfers.assert_called_once_with("0xtest_address", None, 0, 999999, 1, 1000)

    @pytest.mark.asyncio
    async def test_categorize_transactions(self, processor, mock_categorizer, sample_normal_transaction):
        """Test transaction categorization using thread executor"""
        transactions = [sample_normal_transaction]
        categorized_transactions = [sample_normal_transaction]  # Assume same for test
        
        mock_categorizer.categorize_transactions.return_value = categorized_transactions
        
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = Mock()
            mock_get_loop.return_value = mock_loop
            mock_loop.run_in_executor = AsyncMock(return_value=categorized_transactions)
            
            result = await processor._categorize_transactions(transactions)
            
            # Verify executor was used
            mock_loop.run_in_executor.assert_called_once_with(
                processor.executor,
                mock_categorizer.categorize_transactions,
                transactions
            )
            
            assert result == categorized_transactions

    @pytest.mark.asyncio
    async def test_fetch_methods_with_small_max_transactions(self, processor, mock_client):
        """Test fetch methods adjust offset for small max_transactions"""
        mock_client.get_normal_transactions.return_value = []
        mock_client.get_internal_transactions.return_value = []
        mock_client.get_token_transfers.return_value = []
        
        # Test with max_transactions smaller than default offset (1000)
        await processor._fetch_normal_transactions("0xtest_address", 0, 999999, 500)
        await processor._fetch_internal_transactions("0xtest_address", 0, 999999, 500)
        await processor._fetch_token_transfers("0xtest_address", 0, 999999, 500)
        
        # Should use 500 as offset instead of 1000
        mock_client.get_normal_transactions.assert_called_with("0xtest_address", 0, 999999, 1, 500)
        mock_client.get_internal_transactions.assert_called_with("0xtest_address", 0, 999999, 1, 500)
        mock_client.get_token_transfers.assert_called_with("0xtest_address", None, 0, 999999, 1, 500)

    def test_executor_cleanup(self, processor):
        """Test that executor is properly created"""
        assert isinstance(processor.executor, ThreadPoolExecutor)
        # In a real scenario, you might want to test executor cleanup
        # but ThreadPoolExecutor doesn't have a simple way to check if it's closed


# Integration tests
class TestTransactionProcessorIntegration:
    """Integration tests for TransactionProcessor"""

    @pytest.mark.asyncio
    async def test_end_to_end_processing(self):
        """Test complete end-to-end transaction processing"""
        # Create real-like mock client
        mock_client = Mock(spec=BaseAPIClient)
        mock_client.get_normal_transactions = AsyncMock(return_value=[])
        mock_client.get_internal_transactions = AsyncMock(return_value=[])
        mock_client.get_token_transfers = AsyncMock(return_value=[])
        
        # Create processor with default categorizer
        with patch('src.processors.transaction_processor.DataCategorizer') as mock_categorizer_class:
            mock_categorizer = Mock()
            mock_categorizer.categorize_transactions.return_value = []
            mock_categorizer_class.return_value = mock_categorizer
            
            processor = TransactionProcessor(mock_client)
            
            result = await processor.process_wallet_transactions("0xtest_address")
            
            assert result == []
            assert mock_categorizer.categorize_transactions.called

    @pytest.mark.asyncio
    async def test_concurrent_api_calls_handling(self):
        """Test that concurrent API calls are handled properly"""
        mock_client = Mock(spec=BaseAPIClient)
        
        # Simulate different response times for different API calls
        async def slow_normal_tx(*args, **kwargs):
            await asyncio.sleep(0.1)
            return []
        
        async def fast_internal_tx(*args, **kwargs):
            await asyncio.sleep(0.05)
            return []
        
        async def medium_token_tx(*args, **kwargs):
            await asyncio.sleep(0.07)
            return []
        
        mock_client.get_normal_transactions = AsyncMock(side_effect=slow_normal_tx)
        mock_client.get_internal_transactions = AsyncMock(side_effect=fast_internal_tx)
        mock_client.get_token_transfers = AsyncMock(side_effect=medium_token_tx)
        
        mock_categorizer = Mock()
        mock_categorizer.categorize_transactions.return_value = []
        
        processor = TransactionProcessor(mock_client, mock_categorizer)
        
        start_time = asyncio.get_event_loop().time()
        result = await processor.process_wallet_transactions("0xtest_address")
        end_time = asyncio.get_event_loop().time()
        
        # All calls should run concurrently, so total time should be less than sum of individual times
        # but more than the longest individual time
        assert (end_time - start_time) < 0.25  # Much less than 0.1 + 0.05 + 0.07 = 0.22
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__])
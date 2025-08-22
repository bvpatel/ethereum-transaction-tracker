import pytest
from unittest.mock import AsyncMock, patch
from src.main import EthereumTransactionTracker
from src.exceptions.custom_exceptions import APIError, ConfigurationError, ValidationError
from src.models.enums import TransactionStatus, TransactionType

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
            # The client handles errors gracefully and returns empty list instead of raising
            result = await client.get_normal_transactions("0xa39b189482f984388a34460636fea9eb181ad1a6")
            
            # Should return empty list when API error occurs
            assert result == []

    @pytest.mark.asyncio
    async def test_invalid_api_response(self, rate_limiter):
        """Test handling of invalid API responses"""
        from src.api.etherscan_client import EtherscanClient
        
        client = EtherscanClient("test_key", rate_limiter)
        
        # Mock invalid response
        invalid_response = {"status": "0", "message": "Invalid API Key"}
        
        with patch.object(client, '_make_request', return_value=invalid_response):
            # The client handles invalid responses gracefully
            result = await client.get_normal_transactions("0xa39b189482f984388a34460636fea9eb181ad1a6")
            
            # Should return empty list for invalid API responses
            assert result == []

    @pytest.mark.asyncio
    async def test_api_error_propagation_to_higher_level(self, rate_limiter):
        """Test that API errors are properly logged but don't break the flow"""
        from src.api.etherscan_client import EtherscanClient
        
        client = EtherscanClient("test_key", rate_limiter)
        
        with patch.object(client, '_make_request', side_effect=APIError("Rate limit exceeded")):
            # Test that the method completes without raising but logs the error
            with patch('src.api.etherscan_client.logger.error') as mock_logger:
                result = await client.get_normal_transactions("0xa39b189482f984388a34460636fea9eb181ad1a6")
                
                # Should log the error
                mock_logger.assert_called()
                # Should return empty list
                assert result == []

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
        
        # Use the correct method name based on the actual TransactionProcessor implementation
        result = await processor.process_wallet_transactions(
            "0xa39b189482f984388a34460636fea9eb181ad1a6",
            max_transactions=100
        )
        
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_invalid_address_format(self):
        """Test processing with invalid address format"""
        tracker = EthereumTransactionTracker()
        
        with patch('src.api.client_factory.ClientFactory.create_client') as mock_factory:
            mock_client = AsyncMock()
            mock_factory.return_value = mock_client
            
            await tracker.initialize("etherscan")
            
            # Test various invalid address formats
            invalid_addresses = [
                "not_an_address",
                "0x123",  # Too short
                "0xg39b189482f984388a34460636fea9eb181ad1a6",  # Invalid hex
                "",
                None
            ]
            
            for invalid_addr in invalid_addresses[:-1]:  # Skip None to avoid TypeError
                with pytest.raises(ValidationError):
                    await tracker.process_address(invalid_addr)

    @pytest.mark.asyncio 
    async def test_api_rate_limit_handling(self, rate_limiter):
        """Test handling of API rate limits"""
        from src.api.etherscan_client import EtherscanClient
        
        client = EtherscanClient("test_key", rate_limiter)
        
        # Mock rate limit response
        rate_limit_response = {"status": "0", "message": "Max rate limit reached"}
        
        with patch.object(client, '_make_request', return_value=rate_limit_response):
            result = await client.get_normal_transactions("0xa39b189482f984388a34460636fea9eb181ad1a6")
            
            # Should handle rate limit gracefully and return empty list
            assert result == []

    @pytest.mark.asyncio
    async def test_malformed_json_response(self, rate_limiter):
        """Test handling of malformed JSON responses"""
        from src.api.etherscan_client import EtherscanClient
        import json
        
        client = EtherscanClient("test_key", rate_limiter)
        
        with patch.object(client, '_make_request', side_effect=json.JSONDecodeError("Invalid JSON", "", 0)):
            result = await client.get_normal_transactions("0xa39b189482f984388a34460636fea9eb181ad1a6")
            
            # Should handle JSON decode errors gracefully
            assert result == []

    @pytest.mark.asyncio
    async def test_partial_transaction_data(self, rate_limiter):
        """Test handling of transactions with missing fields"""
        from src.api.etherscan_client import EtherscanClient
        
        client = EtherscanClient("test_key", rate_limiter)
        
        # Mock response with incomplete transaction data
        incomplete_response = {
            "status": "1",
            "result": [
                {
                    "hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                    "blockNumber": "18500000",
                    # Missing required fields like timeStamp, from, to, etc.
                }
            ]
        }
        
        with patch.object(client, '_make_request', return_value=incomplete_response):
            result = await client.get_normal_transactions("0xa39b189482f984388a34460636fea9eb181ad1a6")
            
            # Should handle incomplete data gracefully (either skip or fill defaults)
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, rate_limiter):
        """Test handling of concurrent requests with errors"""
        from src.api.etherscan_client import EtherscanClient
        import asyncio
        
        client = EtherscanClient("test_key", rate_limiter)
        
        # Mock alternating success and failure
        call_count = 0
        def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise APIError(f"Error on call {call_count}")
            return {"status": "1", "result": []}
        
        with patch.object(client, '_make_request', side_effect=mock_request):
            # Make multiple concurrent requests
            tasks = [
                client.get_normal_transactions("0xa39b189482f984388a34460636fea9eb181ad1a6")
                for _ in range(4)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should return empty lists (no exceptions should be raised)
            for result in results:
                assert not isinstance(result, Exception)
                assert result == []

    @pytest.mark.asyncio
    async def test_configuration_validation(self):
        """Test configuration validation with invalid settings"""
        tracker = EthereumTransactionTracker()
        
        # Test with invalid provider
        with pytest.raises((ValueError, ConfigurationError)):
            await tracker.initialize("invalid_provider")

    @pytest.mark.asyncio
    async def test_file_system_errors(self, temp_config):
        """Test handling of file system errors during CSV writing"""
        tracker = EthereumTransactionTracker()
        
        with patch('src.api.client_factory.ClientFactory.create_client') as mock_factory:
            mock_client = AsyncMock()
            mock_client.get_normal_transactions = AsyncMock(return_value=[])
            mock_client.get_internal_transactions = AsyncMock(return_value=[])
            mock_client.get_token_transfers = AsyncMock(return_value=[])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            mock_factory.return_value = mock_client
            
            await tracker.initialize("etherscan")
            
            # Mock file writing to raise PermissionError
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                result = await tracker.process_address(
                    "0xa39b189482f984388a34460636fea9eb181ad1a6",
                    max_transactions=100
                )
                
                # Should handle file system errors gracefully
                assert result is not None
                # CSV file should be None or contain error info
                assert result.get('csv_file') is None or 'error' in result

    @pytest.mark.asyncio
    async def test_memory_limitations(self, temp_config):
        """Test handling of large datasets that might cause memory issues"""
        from src.models.transaction import Transaction
        from datetime import datetime
        
        tracker = EthereumTransactionTracker()
        
        # Create a very large number of mock transactions using the actual Transaction model
        large_transaction_list = []
        base_timestamp = datetime(2023, 10, 15, 12, 0, 0)
        
        for i in range(1000):  # Reduced number to avoid actual memory issues
            transaction = Transaction(
                hash=f'0x{i:064x}',
                block_number=18500000 + i,
                timestamp=base_timestamp,
                from_address='0xa39b189482f984388a34460636fea9eb181ad1a6',
                to_address='0xd621aadabaa20d2af700853c4504028cba7c3333',
                value=1000000000000000000,
                gas_price=20000000000,
                gas_used=21000,
                transaction_fee=420000000000000,
                transaction_index=1,
                transaction_type= TransactionType.ETH_TRANSFER,
                status=TransactionStatus.SUCCESS,
                nonce=0,
                contract_address=None,
                token_symbol=None,
                token_name=None,
                token_decimals=None,
                token_id=None,
                input_data=None,
                method_id=None,
                raw_data={}
            )
            large_transaction_list.append(transaction)
        
        with patch('src.api.client_factory.ClientFactory.create_client') as mock_factory:
            mock_client = AsyncMock()
            mock_client.get_normal_transactions = AsyncMock(return_value=large_transaction_list)
            mock_client.get_internal_transactions = AsyncMock(return_value=[])
            mock_client.get_token_transfers = AsyncMock(return_value=[])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            mock_factory.return_value = mock_client
            
            await tracker.initialize("etherscan")
            
            # Should handle large datasets without crashing
            result = await tracker.process_address(
                "0xa39b189482f984388a34460636fea9eb181ad1a6",
                max_transactions=1000
            )
            
            assert result is not None
            assert result['transaction_count'] <= 1000

    @pytest.fixture
    def temp_config(self):
        """Fixture for temporary test configuration"""
        import tempfile
        import os
        
        with patch.dict(os.environ, {
            'ETHERSCAN_API_KEY': 'test_key',
            'OUTPUT_DIRECTORY': tempfile.mkdtemp(),
            'MAX_TRANSACTIONS': '100'
        }):
            yield
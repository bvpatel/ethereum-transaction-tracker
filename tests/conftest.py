import pytest
import asyncio
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, AsyncMock

from src.models.transaction import Transaction, TokenTransfer, InternalTransaction
from src.models.enums import TransactionType, TransactionStatus
from src.utils.rate_limiter import RateLimiter

@pytest.fixture
def sample_transaction():
    """Sample transaction for testing"""
    return Transaction(
        hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        block_number=18500000,
        timestamp=datetime(2023, 10, 15, 12, 0, 0),
        from_address="0xa39b189482f984388a34460636fea9eb181ad1a6",
        to_address="0xd620aaadabaa20d2af700853c4504028cba7c3333",
        value=Decimal("1.5"),
        gas_used=21000,
        gas_price=Decimal("20000000000"),
        transaction_fee=Decimal("420000000000000"),
        status=TransactionStatus.SUCCESS,
        transaction_type=TransactionType.ETH_TRANSFER,
        nonce=42,
        transaction_index=1
    )

@pytest.fixture
def sample_token_transfer():
    """Sample token transfer for testing"""
    return TokenTransfer(
        contract_address="0xa0b73e1ff0b80914ab6fe0444e65848c4c34450b",
        from_address="0xa39b189482f984388a34460636fea9eb181ad1a6",
        to_address="0xd620aaadabaa20d2af700853c4504028cba7c3333",
        value=Decimal("100.0"),
        token_name="Cronos",
        token_symbol="CRO",
        token_decimals=8,
        transaction_hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        block_number=18500000,
        timestamp=datetime(2023, 10, 15, 12, 0, 0)
    )

@pytest.fixture
def sample_internal_transaction():
    """Sample internal transaction for testing"""
    return InternalTransaction(
        hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        from_address="0xa39b189482f984388a34460636fea9eb181ad1a6",
        to_address="0xd620aaadabaa20d2af700853c4504028cba7c3333",
        value=Decimal("0.5"),
        gas_used=21000,
        block_number=18500000,
        timestamp=datetime(2023, 10, 15, 12, 0, 0),
        is_error=False
    )

@pytest.fixture
def mock_api_client():
    """Mock API client for testing"""
    client = AsyncMock()
    client.get_normal_transactions = AsyncMock(return_value=[])
    client.get_internal_transactions = AsyncMock(return_value=[])
    client.get_token_transfers = AsyncMock(return_value=[])
    return client

@pytest.fixture
def rate_limiter():
    """Rate limiter for testing"""
    return RateLimiter(calls_per_second=100)  # Fast for tests

# tests/test_models/test_transaction.py
import pytest
from datetime import datetime
from decimal import Decimal

from src.models.transaction import Transaction
from src.models.enums import TransactionType, TransactionStatus

class TestTransaction:
    """Test Transaction model"""
    
    def test_transaction_creation(self, sample_transaction):
        """Test basic transaction creation"""
        assert sample_transaction.hash.startswith("0x")
        assert len(sample_transaction.hash) == 66
        assert sample_transaction.block_number > 0
        assert isinstance(sample_transaction.timestamp, datetime)
        assert sample_transaction.value > 0
        
    def test_transaction_checksum_addresses(self):
        """Test address checksumming"""
        tx = Transaction(
            hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            block_number=18500000,
            timestamp=datetime(2023, 10, 15, 12, 0, 0),
            from_address="0xA39B189482F984388A34460636FEA9EB181AD1A6",  # Mixed case
            to_address="0xD620AAADABAA20D2AF700853C4504028CBA7C3333",  # Upper case
            value=Decimal("1.0"),
            gas_used=21000,
            gas_price=Decimal("20000000000"),
            transaction_fee=Decimal("420000000000000"),
            status=TransactionStatus.SUCCESS,
            transaction_type=TransactionType.ETH_TRANSFER,
            nonce=1,
            transaction_index=0
        )
        
        # Addresses should be normalized to lowercase
        assert tx.from_address == "0xa39b189482f984388a34460636fea9eb181ad1a6"
        assert tx.to_address == "0xd620aaadabaa20d2af700853c4504028cba7c3333"

    def test_transaction_properties(self, sample_transaction):
        """Test transaction calculated properties"""
        assert sample_transaction.date_str == "2023-10-15 12:00:00"
        assert sample_transaction.value_str == "1.500000"
        assert sample_transaction.fee_in_eth == Decimal("0.00042")

    def test_transaction_to_dict(self, sample_transaction):
        """Test transaction dictionary conversion"""
        tx_dict = sample_transaction.to_dict()
        
        required_fields = [
            'transaction_hash', 'date_time', 'from_address', 'to_address',
            'transaction_type', 'asset_contract_address', 'asset_symbol_name',
            'token_id', 'value_amount', 'gas_fee_eth', 'block_number',
            'status', 'nonce', 'transaction_index'
        ]
        
        for field in required_fields:
            assert field in tx_dict

    def test_failed_transaction(self):
        """Test failed transaction handling"""
        tx = Transaction(
            hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            block_number=18500000,
            timestamp=datetime(2023, 10, 15, 12, 0, 0),
            from_address="0xa39b189482f984388a34460636fea9eb181ad1a6",
            to_address="0xd620aaadabaa20d2af700853c4504028cba7c3333",
            value=Decimal("0"),
            gas_used=21000,
            gas_price=Decimal("20000000000"),
            transaction_fee=Decimal("420000000000000"),
            status=TransactionStatus.FAILED,
            transaction_type=TransactionType.ETH_TRANSFER,
            nonce=1,
            transaction_index=0
        )
        
        assert tx.status == TransactionStatus.FAILED
        assert tx.value == 0
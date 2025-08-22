import pytest
from decimal import Decimal
from datetime import datetime
from src.models.transaction import Transaction
from src.models.enums import TransactionType, TransactionStatus
from src.processors.data_categorizer import DataCategorizer

class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_zero_value_transaction(self):
        """Test transaction with zero value"""
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
            status=TransactionStatus.SUCCESS,
            transaction_type=TransactionType.CONTRACT_INTERACTION,
            nonce=1,
            transaction_index=0
        )
        
        assert tx.value == 0
        assert tx.value_str == "0"

    def test_very_large_value_transaction(self):
        """Test transaction with very large value"""
        large_value = Decimal("1000000.123456789")
        
        tx = Transaction(
            hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            block_number=18500000,
            timestamp=datetime(2023, 10, 15, 12, 0, 0),
            from_address="0xa39b189482f984388a34460636fea9eb181ad1a6",
            to_address="0xd620aaadabaa20d2af700853c4504028cba7c3333",
            value=large_value,
            gas_used=21000,
            gas_price=Decimal("20000000000"),
            transaction_fee=Decimal("420000000000000"),
            status=TransactionStatus.SUCCESS,
            transaction_type=TransactionType.ETH_TRANSFER,
            nonce=1,
            transaction_index=0
        )
        
        assert tx.value == large_value
        assert "1000000.123457" in tx.value_str

    def test_empty_to_address(self):
        """Test transaction with empty to address (contract creation)"""
        tx = Transaction(
            hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            block_number=18500000,
            timestamp=datetime(2023, 10, 15, 12, 0, 0),
            from_address="0xa39b189482f984388a34460636fea9eb181ad1a6",
            to_address="",  # Empty for contract creation
            value=Decimal("0"),
            gas_used=21000,
            gas_price=Decimal("20000000000"),
            transaction_fee=Decimal("420000000000000"),
            status=TransactionStatus.SUCCESS,
            transaction_type=TransactionType.CONTRACT_INTERACTION,
            nonce=1,
            transaction_index=0
        )
        
        assert tx.to_address == ""

    def test_nft_with_very_long_token_id(self):
        """Test NFT transaction with very long token ID"""
        tx = Transaction(
            hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            block_number=18500000,
            timestamp=datetime(2023, 10, 15, 12, 0, 0),
            from_address="0xa39b189482f984388a34460636fea9eb181ad1a6",
            to_address="0xd620aaadabaa20d2af700853c4504028cba7c3333",
            value=Decimal("1"),
            gas_used=21000,
            gas_price=Decimal("20000000000"),
            transaction_fee=Decimal("420000000000000"),
            status=TransactionStatus.SUCCESS,
            transaction_type=TransactionType.ERC721_TRANSFER,
            nonce=1,
            transaction_index=0,
            token_id="123456789012345678901234567890123456789012345678901234567890"
        )
        
        assert len(tx.token_id) == 60
        
    def test_categorizer_with_unknown_method(self):
        """Test categorizer with unknown method signature"""
        categorizer = DataCategorizer()
        
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
            status=TransactionStatus.SUCCESS,
            transaction_type=TransactionType.ETH_TRANSFER,
            nonce=1,
            transaction_index=0,
            input_data="0x12345678"  # Unknown method
        )
        
        categorized = categorizer._categorize_single_transaction(tx)
        # Should not crash and should preserve original type
        assert categorized.transaction_type == TransactionType.ETH_TRANSFER

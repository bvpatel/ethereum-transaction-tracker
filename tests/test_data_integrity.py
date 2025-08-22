import pytest
from decimal import Decimal
from datetime import datetime
from src.models.transaction import Transaction
from src.models.enums import TransactionType, TransactionStatus
from src.processors.data_categorizer import DataCategorizer

class TestDataIntegrity:
    """Test data integrity and consistency"""
    
    def test_decimal_precision_preservation(self):
        """Test that decimal precision is preserved"""
        precise_value = Decimal("123.123456789012345678")
        
        tx = Transaction(
            hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            block_number=18500000,
            timestamp=datetime(2023, 10, 15, 12, 0, 0),
            from_address="0xa39b189482f984388a34460636fea9eb181ad1a6",
            to_address="0xd620aaadabaa20d2af700853c4504028cba7c3333",
            value=precise_value,
            gas_used=21000,
            gas_price=Decimal("20000000000"),
            transaction_fee=Decimal("420000000000000"),
            status=TransactionStatus.SUCCESS,
            transaction_type=TransactionType.ETH_TRANSFER,
            nonce=1,
            transaction_index=0
        )
        
        # Precision should be maintained
        assert tx.value == precise_value
        assert str(tx.value) == "123.123456789012345678"

    def test_transaction_sorting_consistency(self, sample_transaction):
        """Test that transaction sorting is consistent"""
        # Create transactions with different timestamps
        base_time = datetime(2023, 10, 15, 12, 0, 0)
        
        transactions = []
        for i in range(5):
            tx = Transaction(
                hash=f"0x{i:064x}",
                block_number=18500000 + i,
                timestamp=datetime(2023, 10, 15, 12, i, 0),
                from_address="0xa39b189482f984388a34460636fea9eb181ad1a6",
                to_address="0xd620aaadabaa20d2af700853c4504028cba7c3333",
                value=Decimal("1.0"),
                gas_used=21000,
                gas_price=Decimal("20000000000"),
                transaction_fee=Decimal("420000000000000"),
                status=TransactionStatus.SUCCESS,
                transaction_type=TransactionType.ETH_TRANSFER,
                nonce=i,
                transaction_index=0
            )
            transactions.append(tx)
        
        # Sort by timestamp descending
        sorted_txs = sorted(transactions, key=lambda x: x.timestamp, reverse=True)
        
        # Should be in descending order
        for i in range(len(sorted_txs) - 1):
            assert sorted_txs[i].timestamp >= sorted_txs[i + 1].timestamp

    def test_data_consistency_across_formats(self, sample_transaction):
        """Test data consistency between different formats"""
        # Convert to dictionary
        tx_dict = sample_transaction.to_dict()
        
        # Key fields should match
        assert tx_dict['transaction_hash'] == sample_transaction.hash
        assert tx_dict['from_address'] == sample_transaction.from_address
        assert tx_dict['to_address'] == sample_transaction.to_address
        assert tx_dict['transaction_type'] == sample_transaction.transaction_type.value

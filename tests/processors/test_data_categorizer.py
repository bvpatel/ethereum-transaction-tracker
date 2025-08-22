import pytest
from unittest.mock import Mock, patch, PropertyMock
from decimal import Decimal
from datetime import datetime
from typing import List

# Assuming these imports exist in your project structure
from src.models.transaction import Transaction, TokenTransfer, InternalTransaction
from src.models.enums import TransactionType, TransactionStatus
from src.processors.data_categorizer import DataCategorizer


class TestDataCategorizer:
    """Test cases for DataCategorizer class"""

    @pytest.fixture
    def categorizer(self):
        """Create a DataCategorizer instance for testing"""
        return DataCategorizer()

    @pytest.fixture
    def sample_transaction(self):
        """Create a sample transaction for testing"""
        return Transaction(
            hash="0x123456789abcdef",
            block_number=12345,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            from_address="0xfrom123",
            to_address="0xto456",
            value=Decimal("1.5"),
            gas_used=21000,
            gas_price=Decimal("20"),
            transaction_fee=Decimal("0.42"),
            status=TransactionStatus.SUCCESS,
            transaction_type=TransactionType.ETH_TRANSFER,
            nonce=1,
            transaction_index=0,
            input_data="0xa9059cbb000000000000000000000000recipient123000000000000000000000000000000000000000000000000000000000000000000000001",
            raw_data={}
        )

    @pytest.fixture
    def sample_internal_transaction(self):
        """Create a sample internal transaction for testing"""
        return InternalTransaction(
            hash="0xinternal123",
            block_number=12345,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            from_address="0xfrom123",
            to_address="0xto456",
            value=Decimal("0.5"),
            gas_used=15000,
            is_error=False,
            error_code=""
        )

    @pytest.fixture
    def sample_token_transfer(self):
        """Create a sample token transfer for testing"""
        return TokenTransfer(
            transaction_hash="0xtoken123",
            block_number=12345,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            from_address="0xfrom123",
            to_address="0xto456",
            value=Decimal("100"),
            contract_address="0xtoken_contract",
            token_symbol="TEST",
            token_name="Test Token",
            token_decimals=18,
            token_id=None
        )

    def test_init_loads_known_contracts_and_signatures(self, categorizer):
        """Test that initialization loads known contracts and method signatures"""
        assert isinstance(categorizer.known_contracts, dict)
        assert isinstance(categorizer.method_signatures, dict)
        
        # Check that some expected contracts are loaded
        assert "0xa0b86a33e6ba8c7fb7436fea2b7b3d8a7a3d3e1e" in categorizer.known_contracts
        assert "0x7a250d5630b4cf539739df2c5dacb4c659f2488d" in categorizer.known_contracts
        
        # Check that some expected method signatures are loaded
        assert "0xa9059cbb" in categorizer.method_signatures
        assert "0x23b872dd" in categorizer.method_signatures
        assert "0x095ea7b3" in categorizer.method_signatures

    def test_load_known_contracts(self, categorizer):
        """Test _load_known_contracts method"""
        contracts = categorizer._load_known_contracts()
        
        assert isinstance(contracts, dict)
        # Check structure of contract data
        for address, info in contracts.items():
            assert "name" in info
            assert "type" in info
            assert isinstance(address, str)
            assert address.startswith("0x")

    def test_load_method_signatures(self, categorizer):
        """Test _load_method_signatures method"""
        signatures = categorizer._load_method_signatures()
        
        assert isinstance(signatures, dict)
        # Check that transfer method is correctly mapped
        assert signatures["0xa9059cbb"] == "transfer(address,uint256)"
        assert signatures["0x23b872dd"] == "transferFrom(address,address,uint256)"
        assert signatures["0x095ea7b3"] == "approve(address,uint256)"

    def test_categorize_transactions_empty_list(self, categorizer):
        """Test categorizing an empty list of transactions"""
        result = categorizer.categorize_transactions([])
        assert result == []
        assert isinstance(result, list)

    def test_categorize_transactions_with_valid_list(self, categorizer, sample_transaction):
        """Test categorizing a list with valid transactions"""
        transactions = [sample_transaction]
        result = categorizer.categorize_transactions(transactions)
        
        assert len(result) == 1
        assert isinstance(result[0], Transaction)
        assert result[0].hash == sample_transaction.hash

    def test_categorize_single_transaction_with_transfer_method(self, categorizer, sample_transaction):
        """Test categorizing transaction with transfer method signature"""
        # Set input data with transfer method ID
        sample_transaction.input_data = "0xa9059cbb000000000000000000000000recipient123"
        
        result = categorizer._categorize_single_transaction(sample_transaction)
        
        assert result.method_id == "0xa9059cbb"
        assert result.transaction_type == TransactionType.ERC20_TRANSFER

    def test_categorize_single_transaction_with_transferfrom_method(self, categorizer, sample_transaction):
        """Test categorizing transaction with transferFrom method signature"""
        sample_transaction.input_data = "0x23b872dd000000000000000000000000sender123"
        
        result = categorizer._categorize_single_transaction(sample_transaction)
        
        assert result.method_id == "0x23b872dd"
        assert result.transaction_type == TransactionType.ERC20_TRANSFER

    def test_categorize_single_transaction_with_approve_method(self, categorizer, sample_transaction):
        """Test categorizing transaction with approve method signature"""
        sample_transaction.input_data = "0x095ea7b3000000000000000000000000spender123"
        
        result = categorizer._categorize_single_transaction(sample_transaction)
        
        assert result.method_id == "0x095ea7b3"
        assert result.transaction_type == TransactionType.CONTRACT_INTERACTION

    def test_categorize_single_transaction_with_unknown_method(self, categorizer, sample_transaction):
        """Test categorizing transaction with unknown method signature"""
        sample_transaction.input_data = "0x12345678unknown_method_data"
        
        result = categorizer._categorize_single_transaction(sample_transaction)
        
        # Should not set method_id for unknown methods
        assert not hasattr(result, 'method_id') or result.method_id != "0x12345678"

    def test_categorize_single_transaction_failed_status(self, categorizer, sample_transaction):
        """Test categorizing failed transaction"""
        sample_transaction.status = TransactionStatus.FAILED
        
        result = categorizer._categorize_single_transaction(sample_transaction)
        
        assert result.transaction_type == TransactionType.FAILED_TRANSACTION

    def test_categorize_single_transaction_with_known_contract(self, categorizer, sample_transaction):
        """Test categorizing transaction to known contract address"""
        # Use a known contract address from the categorizer
        sample_transaction.to_address = "0xa0b86a33e6ba8c7fb7436fea2b7b3d8a7a3d3e1e"
        
        result = categorizer._categorize_single_transaction(sample_transaction)
        
        assert result.raw_data["contract_name"] == "Uniswap V2 Router"
        assert result.raw_data["contract_type"] == "DEX"

    def test_categorize_single_transaction_with_empty_input_data(self, categorizer, sample_transaction):
        """Test categorizing transaction with empty input data"""
        sample_transaction.input_data = ""
        
        result = categorizer._categorize_single_transaction(sample_transaction)
        
        # Should not crash and should return the transaction
        assert isinstance(result, Transaction)
        assert result.hash == sample_transaction.hash

    def test_categorize_single_transaction_with_none_input_data(self, categorizer, sample_transaction):
        """Test categorizing transaction with None input data"""
        sample_transaction.input_data = None
        
        result = categorizer._categorize_single_transaction(sample_transaction)
        
        # Should not crash and should return the transaction
        assert isinstance(result, Transaction)
        assert result.hash == sample_transaction.hash

    def test_categorize_single_transaction_with_short_input_data(self, categorizer, sample_transaction):
        """Test categorizing transaction with input data shorter than method signature"""
        sample_transaction.input_data = "0x123"  # Too short for method ID
        
        result = categorizer._categorize_single_transaction(sample_transaction)
        
        # Should not crash and should return the transaction
        assert isinstance(result, Transaction)
        assert result.hash == sample_transaction.hash

    def test_convert_internal_to_transaction_success(self, categorizer, sample_internal_transaction):
        """Test converting internal transaction to Transaction object"""
        result = categorizer.convert_internal_to_transaction(sample_internal_transaction)
        
        assert isinstance(result, Transaction)
        assert result.hash == sample_internal_transaction.hash
        assert result.block_number == sample_internal_transaction.block_number
        assert result.from_address == sample_internal_transaction.from_address
        assert result.to_address == sample_internal_transaction.to_address
        assert result.value == sample_internal_transaction.value
        assert result.gas_used == sample_internal_transaction.gas_used
        assert result.gas_price == Decimal('0')
        assert result.transaction_fee == Decimal('0')
        assert result.status == TransactionStatus.SUCCESS
        assert result.transaction_type == TransactionType.INTERNAL_TRANSFER
        assert result.nonce == 0
        assert result.transaction_index == 0
        assert result.raw_data["internal"] == True

    def test_convert_internal_to_transaction_with_error(self, categorizer, sample_internal_transaction):
        """Test converting failed internal transaction"""
        sample_internal_transaction.is_error = True
        sample_internal_transaction.error_code = "OutOfGas"
        
        result = categorizer.convert_internal_to_transaction(sample_internal_transaction)
        
        assert result.status == TransactionStatus.FAILED
        assert result.raw_data["error_code"] == "OutOfGas"

    def test_convert_internal_to_transaction_exception_handling(self, categorizer):
        """Test exception handling in convert_internal_to_transaction"""
        # Patch the Transaction constructor to raise an exception
        with patch('src.processors.data_categorizer.Transaction', side_effect=Exception("Constructor failed")):
            # Create a valid internal transaction - the exception will come from Transaction constructor
            internal_tx = Mock()
            internal_tx.hash = "0x123"
            internal_tx.block_number = 12345
            internal_tx.timestamp = datetime.now()
            internal_tx.from_address = "0xfrom"
            internal_tx.to_address = "0xto"
            internal_tx.value = Decimal("1.0")
            internal_tx.gas_used = 21000
            internal_tx.is_error = False
            internal_tx.error_code = ""
            
            result = categorizer.convert_internal_to_transaction(internal_tx)
            
            assert result is None

    def test_convert_token_transfer_to_transaction_erc20(self, categorizer, sample_token_transfer):
        """Test converting ERC20 token transfer to Transaction object"""
        result = categorizer.convert_token_transfer_to_transaction(sample_token_transfer)
        
        assert isinstance(result, Transaction)
        assert result.hash == sample_token_transfer.transaction_hash
        assert result.block_number == sample_token_transfer.block_number
        assert result.from_address == sample_token_transfer.from_address
        assert result.to_address == sample_token_transfer.to_address
        assert result.value == sample_token_transfer.value
        assert result.gas_used == 0
        assert result.gas_price == Decimal('0')
        assert result.transaction_fee == Decimal('0')
        assert result.status == TransactionStatus.SUCCESS
        assert result.transaction_type == TransactionType.ERC20_TRANSFER
        assert result.contract_address == sample_token_transfer.contract_address
        assert result.token_symbol == sample_token_transfer.token_symbol
        assert result.token_name == sample_token_transfer.token_name
        assert result.token_decimals == sample_token_transfer.token_decimals
        assert result.raw_data["token_transfer"] == True

    def test_convert_token_transfer_to_transaction_erc721(self, categorizer, sample_token_transfer):
        """Test converting ERC721 token transfer to Transaction object"""
        sample_token_transfer.token_id = "123"  # Making it an NFT
        
        result = categorizer.convert_token_transfer_to_transaction(sample_token_transfer)
        
        assert result.transaction_type == TransactionType.ERC721_TRANSFER
        assert result.token_id == "123"

    def test_convert_token_transfer_to_transaction_with_none_timestamp(self, categorizer, sample_token_transfer):
        """Test converting token transfer with None timestamp"""
        sample_token_transfer.timestamp = None
        
        with patch('src.processors.data_categorizer.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 1, 15, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            result = categorizer.convert_token_transfer_to_transaction(sample_token_transfer)
            
            assert result.timestamp == mock_now

    def test_convert_token_transfer_to_transaction_exception_handling(self, categorizer):
        """Test exception handling in convert_token_transfer_to_transaction"""
        # Patch the Transaction constructor to raise an exception
        with patch('src.processors.data_categorizer.Transaction', side_effect=Exception("Constructor failed")):
            # Create a valid token transfer - the exception will come from Transaction constructor
            token_transfer = Mock()
            token_transfer.transaction_hash = "0x123"
            token_transfer.block_number = 12345
            token_transfer.timestamp = datetime.now()
            token_transfer.from_address = "0xfrom"
            token_transfer.to_address = "0xto"
            token_transfer.value = Decimal("100.0")
            token_transfer.contract_address = "0xcontract"
            token_transfer.token_symbol = "TEST"
            token_transfer.token_name = "Test Token"
            token_transfer.token_decimals = 18
            token_transfer.token_id = None
            
            result = categorizer.convert_token_transfer_to_transaction(token_transfer)
            
            assert result is None

    def test_categorize_transactions_preserves_order(self, categorizer):
        """Test that categorize_transactions preserves the order of transactions"""
        transactions = []
        for i in range(5):
            tx = Transaction(
                hash=f"0x{i:064x}",
                block_number=12345 + i,
                timestamp=datetime(2024, 1, 1, 12, i, 0),
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
        
        result = categorizer.categorize_transactions(transactions)
        
        # Check that order is preserved
        for i, tx in enumerate(result):
            assert tx.nonce == i
            assert tx.block_number == 12345 + i

    @pytest.mark.parametrize("method_id,expected_type", [
        ("0xa9059cbb", TransactionType.ERC20_TRANSFER),
        ("0x23b872dd", TransactionType.ERC20_TRANSFER),
        ("0x095ea7b3", TransactionType.CONTRACT_INTERACTION),
        ("0x18160ddd", None),  # totalSupply - should not change type
        ("0x70a08231", None),  # balanceOf - should not change type
    ])
    def test_method_signature_categorization(self, categorizer, sample_transaction, method_id, expected_type):
        """Test categorization based on different method signatures"""
        sample_transaction.input_data = f"{method_id}{'0' * 64}"
        original_type = sample_transaction.transaction_type
        
        result = categorizer._categorize_single_transaction(sample_transaction)
        
        if expected_type:
            assert result.transaction_type == expected_type
        else:
            assert result.transaction_type == original_type
        
        if method_id in categorizer.method_signatures:
            assert result.method_id == method_id

    def test_multiple_conditions_priority(self, categorizer, sample_transaction):
        """Test that failed status takes priority over method-based categorization"""
        sample_transaction.input_data = "0xa9059cbb" + "0" * 64
        sample_transaction.status = TransactionStatus.FAILED
        
        result = categorizer._categorize_single_transaction(sample_transaction)
        
        # Failed status should override method-based categorization
        assert result.transaction_type == TransactionType.FAILED_TRANSACTION
        # But method_id should still be set
        assert result.method_id == "0xa9059cbb"


# Integration test class for testing multiple components together
class TestDataCategorizerIntegration:
    """Integration tests for DataCategorizer"""

    def test_full_workflow_with_mixed_transactions(self):
        """Test complete workflow with different types of transactions"""
        categorizer = DataCategorizer()
        
        # Create mixed transaction types
        transactions = [
            Transaction(
                hash="0x1", block_number=1, timestamp=datetime.now(),
                from_address="0xfrom", to_address="0xa0b86a33e6ba8c7fb7436fea2b7b3d8a7a3d3e1e",
                value=Decimal("1"), gas_used=21000, gas_price=Decimal("20"),
                transaction_fee=Decimal("0.42"), status=TransactionStatus.SUCCESS,
                transaction_type=TransactionType.ETH_TRANSFER, nonce=1,
                transaction_index=0, input_data="0xa9059cbb" + "0" * 64, raw_data={}
            ),
            Transaction(
                hash="0x2", block_number=2, timestamp=datetime.now(),
                from_address="0xfrom", to_address="0xto", value=Decimal("1"),
                gas_used=21000, gas_price=Decimal("20"), transaction_fee=Decimal("0.42"),
                status=TransactionStatus.FAILED, transaction_type=TransactionType.ETH_TRANSFER,
                nonce=2, transaction_index=1, raw_data={}
            ),
        ]
        
        result = categorizer.categorize_transactions(transactions)
        
        # First transaction: ERC20 transfer to known contract
        assert result[0].transaction_type == TransactionType.ERC20_TRANSFER
        assert result[0].method_id == "0xa9059cbb"
        assert result[0].raw_data["contract_name"] == "Uniswap V2 Router"
        
        # Second transaction: Failed transaction
        assert result[1].transaction_type == TransactionType.FAILED_TRANSACTION


if __name__ == "__main__":
    pytest.main([__file__])
import pytest
from src.processors.data_categorizer import DataCategorizer
from src.models.enums import TransactionType

class TestDataCategorizer:
    """Test data categorization functionality"""
    
    @pytest.fixture
    def categorizer(self):
        """Create categorizer instance"""
        return DataCategorizer()

    def test_categorize_erc20_transfer(self, categorizer, sample_transaction):
        """Test ERC-20 transfer categorization"""
        # Set input data for ERC-20 transfer
        sample_transaction.input_data = "0xa9059cbb000000000000000000000000d620aaadabaa20d2af700853c4504028cba7c3333"
        
        categorized = categorizer._categorize_single_transaction(sample_transaction)
        
        assert categorized.transaction_type == TransactionType.ERC20_TRANSFER
        assert categorized.method_id == "0xa9059cbb"

    def test_categorize_failed_transaction(self, categorizer, sample_transaction):
        """Test failed transaction categorization"""
        sample_transaction.status = TransactionStatus.FAILED
        
        categorized = categorizer._categorize_single_transaction(sample_transaction)
        
        assert categorized.transaction_type == TransactionType.FAILED_TRANSACTION

    def test_convert_token_transfer_to_transaction(self, categorizer, sample_token_transfer):
        """Test token transfer conversion"""
        transaction = categorizer.convert_token_transfer_to_transaction(sample_token_transfer)
        
        assert transaction is not None
        assert transaction.transaction_type == TransactionType.ERC20_TRANSFER
        assert transaction.token_symbol == "CRO"
        assert transaction.contract_address == sample_token_transfer.contract_address

    def test_convert_internal_to_transaction(self, categorizer, sample_internal_transaction):
        """Test internal transaction conversion"""
        transaction = categorizer.convert_internal_to_transaction(sample_internal_transaction)
        
        assert transaction is not None
        assert transaction.transaction_type == TransactionType.INTERNAL_TRANSFER
        assert transaction.gas_price == Decimal('0')
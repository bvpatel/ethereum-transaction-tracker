import pytest
from src.utils.validators import AddressValidator, TransactionValidator

class TestAddressValidator:
    """Test address validation functionality"""
    
    @pytest.mark.parametrize("address,expected", [
        ("0xa39b189482f984388a34460636fea9eb181ad1a6", True),
        ("0xd620AADaBaA20d2af700853C4504028cba7C3333", True),
        ("0x1234567890123456789012345678901234567890", True),
        ("", False),
        ("0x", False),
        ("0x123", False),
        ("0xg39b189482f984388a34460636fea9eb181ad1a6", False),  # Invalid hex
        ("a39b189482f984388a34460636fea9eb181ad1a6", False),    # No 0x prefix
        ("0xa39b189482f984388a34460636fea9eb181ad1a", False),   # Too short
        ("0xa39b189482f984388a34460636fea9eb181ad1a66", False), # Too long
    ])
    def test_is_valid_ethereum_address(self, address, expected):
        """Test Ethereum address validation"""
        assert AddressValidator.is_valid_ethereum_address(address) == expected

    def test_normalize_address(self):
        """Test address normalization"""
        mixed_case = "0xA39B189482F984388A34460636FEA9EB181AD1A6"
        normalized = AddressValidator.normalize_address(mixed_case)
        assert normalized == "0xa39b189482f984388a34460636fea9eb181ad1a6"
        
        # Invalid address should return None
        invalid_normalized = AddressValidator.normalize_address("invalid")
        assert invalid_normalized is None

class TestTransactionValidator:
    """Test transaction validation functionality"""
    
    @pytest.mark.parametrize("tx_hash,expected", [
        ("0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef", True),
        ("0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890", True),
        ("", False),
        ("0x", False),
        ("0x123", False),
        ("1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef", False),  # No 0x
        ("0xg234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef", False), # Invalid hex
    ])
    def test_is_valid_transaction_hash(self, tx_hash, expected):
        """Test transaction hash validation"""
        assert TransactionValidator.is_valid_transaction_hash(tx_hash) == expected

    @pytest.mark.parametrize("block_number,expected", [
        (0, True),
        (18500000, True),
        (99999999, True),
        (-1, False),
        ("invalid", False),
    ])
    def test_is_valid_block_number(self, block_number, expected):
        """Test block number validation"""
        if isinstance(block_number, str):
            with pytest.raises(TypeError):
                TransactionValidator.is_valid_block_number(block_number)
        else:
            assert TransactionValidator.is_valid_block_number(block_number) == expected

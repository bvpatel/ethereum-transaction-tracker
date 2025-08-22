import re
from typing import Optional

class AddressValidator:
    """Ethereum address validation utilities"""
    
    @staticmethod
    def is_valid_ethereum_address(address: str) -> bool:
        """Validate Ethereum address format"""
        if not address:
            return False
        
        # Check if it's a valid hex string with 0x prefix and 40 characters
        pattern = r'^0x[a-fA-F0-9]{40}$'
        return bool(re.match(pattern, address))

    @staticmethod
    def normalize_address(address: str) -> Optional[str]:
        """Normalize Ethereum address to lowercase"""
        if not AddressValidator.is_valid_ethereum_address(address):
            return None
        return address.lower()

class TransactionValidator:
    """Transaction validation utilities"""
    
    @staticmethod
    def is_valid_transaction_hash(tx_hash: str) -> bool:
        """Validate transaction hash format"""
        if not tx_hash:
            return False
        
        pattern = r'^0x[a-fA-F0-9]{64}$'
        return bool(re.match(pattern, tx_hash))

    @staticmethod
    def is_valid_block_number(block_number: int) -> bool:
        """Validate block number"""
        return isinstance(block_number, int) and block_number >= 0

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal
from .enums import TransactionType, TransactionStatus

@dataclass
class Transaction:
    """Base transaction model"""
    hash: str
    block_number: int
    timestamp: datetime
    from_address: str
    to_address: str
    value: Decimal
    gas_used: int
    gas_price: Decimal
    transaction_fee: Decimal
    status: TransactionStatus
    transaction_type: TransactionType
    nonce: int
    transaction_index: int
    
    # Optional fields for tokens/NFTs
    contract_address: Optional[str] = None
    token_symbol: Optional[str] = None
    token_name: Optional[str] = None
    token_decimals: Optional[int] = None
    token_id: Optional[str] = None
    
    # Additional metadata
    input_data: Optional[str] = None
    method_id: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization processing"""
        # Ensure addresses are checksummed
        self.from_address = self._checksum_address(self.from_address)
        self.to_address = self._checksum_address(self.to_address)
        
        if self.contract_address:
            self.contract_address = self._checksum_address(self.contract_address)

    @staticmethod
    def _checksum_address(address: str) -> str:
        """Simple checksum address implementation"""
        if not address or address == "0x":
            return address
        return address.lower()  # Simplified for this example

    @property
    def date_str(self) -> str:
        """Formatted date string"""
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def value_str(self) -> str:
        """Formatted value string"""
        if self.transaction_type == TransactionType.ETH_TRANSFER:
            return f"{self.value:.6f}"
        return str(self.value)

    @property
    def fee_in_eth(self) -> Decimal:
        """Transaction fee in ETH"""
        return self.transaction_fee / (Decimal(10) ** 18)

    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary"""
        return {
            'transaction_hash': self.hash,
            'date_time': self.date_str,
            'from_address': self.from_address,
            'to_address': self.to_address,
            'transaction_type': self.transaction_type.value,
            'asset_contract_address': self.contract_address or '',
            'asset_symbol_name': self.token_symbol or 'ETH',
            'token_id': self.token_id or '',
            'value_amount': self.value_str,
            'gas_fee_eth': f"{self.fee_in_eth:.8f}",
            'block_number': self.block_number,
            'status': self.status.value,
            'nonce': self.nonce,
            'transaction_index': self.transaction_index
        }

@dataclass
class TokenTransfer:
    """Token transfer specific data"""
    contract_address: str
    from_address: str
    to_address: str
    value: Decimal
    token_name: Optional[str] = None
    token_symbol: Optional[str] = None
    token_decimals: Optional[int] = None
    token_id: Optional[str] = None
    transaction_hash: str = ""
    block_number: int = 0
    timestamp: Optional[datetime] = None

@dataclass
class InternalTransaction:
    """Internal transaction data"""
    hash: str
    from_address: str
    to_address: str
    value: Decimal
    gas_used: int
    block_number: int
    timestamp: datetime
    transaction_type: str = "call"
    is_error: bool = False
    error_code: Optional[str] = None
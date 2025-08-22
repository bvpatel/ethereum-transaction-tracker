import re
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from ..models.transaction import Transaction, TokenTransfer, InternalTransaction
from ..models.enums import TransactionType, TransactionStatus

class DataCategorizer:
    """Categorizes and enriches transaction data"""
    
    def __init__(self):
        self.known_contracts = self._load_known_contracts()
        self.method_signatures = self._load_method_signatures()

    def _load_known_contracts(self) -> Dict[str, Dict[str, Any]]:
        """Load known contract addresses and their metadata"""
        return {
            "0xa0b86a33e6ba8c7fb7436fea2b7b3d8a7a3d3e1e": {
                "name": "Uniswap V2 Router",
                "type": "DEX"
            },
            "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": {
                "name": "Uniswap V2 Router 02",
                "type": "DEX"
            }
            # Add more known contracts
        }

    def _load_method_signatures(self) -> Dict[str, str]:
        """Load common method signatures"""
        return {
            "0xa9059cbb": "transfer(address,uint256)",
            "0x23b872dd": "transferFrom(address,address,uint256)",
            "0x095ea7b3": "approve(address,uint256)",
            "0x18160ddd": "totalSupply()",
            "0x70a08231": "balanceOf(address)"
        }

    def categorize_transactions(self, transactions: List[Transaction]) -> List[Transaction]:
        """Categorize a list of transactions"""
        categorized = []
        
        for transaction in transactions:
            categorized_tx = self._categorize_single_transaction(transaction)
            categorized.append(categorized_tx)
        
        return categorized

    def _categorize_single_transaction(self, transaction: Transaction) -> Transaction:
        """Categorize a single transaction"""
        # Analyze input data to determine transaction type
        if transaction.input_data and len(transaction.input_data) > 2:
            method_id = transaction.input_data[:10]
            
            if method_id in self.method_signatures:
                transaction.method_id = method_id
                
                # Update transaction type based on method
                if method_id in ["0xa9059cbb", "0x23b872dd"]:
                    transaction.transaction_type = TransactionType.ERC20_TRANSFER
                elif method_id == "0x095ea7b3":
                    transaction.transaction_type = TransactionType.CONTRACT_INTERACTION
        
        # Check if transaction failed
        if transaction.status == TransactionStatus.FAILED:
            transaction.transaction_type = TransactionType.FAILED_TRANSACTION
        
        # Add contract information if available
        if transaction.to_address in self.known_contracts:
            contract_info = self.known_contracts[transaction.to_address]
            transaction.raw_data["contract_name"] = contract_info["name"]
            transaction.raw_data["contract_type"] = contract_info["type"]
        
        return transaction

    def convert_internal_to_transaction(self, internal_tx: InternalTransaction) -> Optional[Transaction]:
        """Convert internal transaction to Transaction object"""
        try:
            return Transaction(
                hash=internal_tx.hash,
                block_number=internal_tx.block_number,
                timestamp=internal_tx.timestamp,
                from_address=internal_tx.from_address,
                to_address=internal_tx.to_address,
                value=internal_tx.value,
                gas_used=internal_tx.gas_used,
                gas_price=Decimal('0'),  # Internal txs don't have gas price
                transaction_fee=Decimal('0'),
                status=TransactionStatus.FAILED if internal_tx.is_error else TransactionStatus.SUCCESS,
                transaction_type=TransactionType.INTERNAL_TRANSFER,
                nonce=0,  # Internal txs don't have nonce
                transaction_index=0,
                raw_data={"internal": True, "error_code": internal_tx.error_code}
            )
        except Exception:
            return None

    def convert_token_transfer_to_transaction(self, token_transfer: TokenTransfer) -> Optional[Transaction]:
        """Convert token transfer to Transaction object"""
        try:
            # Determine transaction type based on token properties
            tx_type = TransactionType.ERC20_TRANSFER
            
            if token_transfer.token_id:
                tx_type = TransactionType.ERC721_TRANSFER
            
            return Transaction(
                hash=token_transfer.transaction_hash,
                block_number=token_transfer.block_number,
                timestamp=token_transfer.timestamp or datetime.now(),
                from_address=token_transfer.from_address,
                to_address=token_transfer.to_address,
                value=token_transfer.value,
                gas_used=0,  # Token transfers don't have separate gas
                gas_price=Decimal('0'),
                transaction_fee=Decimal('0'),
                status=TransactionStatus.SUCCESS,
                transaction_type=tx_type,
                nonce=0,
                transaction_index=0,
                contract_address=token_transfer.contract_address,
                token_symbol=token_transfer.token_symbol,
                token_name=token_transfer.token_name,
                token_decimals=token_transfer.token_decimals,
                token_id=token_transfer.token_id,
                raw_data={"token_transfer": True}
            )
        except Exception:
            return None
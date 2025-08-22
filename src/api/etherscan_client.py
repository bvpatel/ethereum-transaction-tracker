import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal, InvalidOperation
from .base_client import BaseAPIClient
from ..models.transaction import Transaction, TokenTransfer, InternalTransaction
from ..models.enums import TransactionType, TransactionStatus
from ..utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class EtherscanClient(BaseAPIClient):
    """Etherscan API client implementation"""
    
    def __init__(self, api_key: str, rate_limiter: RateLimiter):
        super().__init__(api_key, "https://api.etherscan.io/api", rate_limiter)

    def _is_successful_response(self, data: Dict[str, Any]) -> bool:
        """Check if Etherscan response indicates success"""
        return data.get('status') == '1'

    def _get_error_message(self, data: Dict[str, Any]) -> str:
        """Extract error message from Etherscan response"""
        return data.get('message', 'Unknown error')

    async def get_normal_transactions(self, address: str, start_block: int = 0,
                                    end_block: int = 99999999, page: int = 1,
                                    offset: int = 1000) -> List[Transaction]:
        """Get normal transactions from Etherscan"""
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': start_block,
            'endblock': end_block,
            'page': page,
            'offset': offset,
            'sort': 'desc',
            'apikey': self.api_key
        }
        
        try:
            data = await self._make_request('', params)
            transactions = []
            
            for tx_data in data.get('result', []):
                transaction = self._parse_normal_transaction(tx_data)
                if transaction:
                    transactions.append(transaction)
            
            logger.info(f"Retrieved {len(transactions)} normal transactions for {address}")
            return transactions
            
        except Exception as e:
            logger.error(f"Error fetching normal transactions: {e}")
            return []

    async def get_internal_transactions(self, address: str, start_block: int = 0,
                                      end_block: int = 99999999, page: int = 1,
                                      offset: int = 1000) -> List[InternalTransaction]:
        """Get internal transactions from Etherscan"""
        params = {
            'module': 'account',
            'action': 'txlistinternal',
            'address': address,
            'startblock': start_block,
            'endblock': end_block,
            'page': page,
            'offset': offset,
            'sort': 'desc',
            'apikey': self.api_key
        }
        
        try:
            data = await self._make_request('', params)
            transactions = []
            for tx_data in data.get('result', []):
                transaction = self._parse_internal_transaction(tx_data)
                if transaction:
                    transactions.append(transaction)
            
            logger.info(f"Retrieved {len(transactions)} internal transactions for {address}")
            return transactions
            
        except Exception as e:
            logger.warning(f"Error fetching internal transactions: {e}")
            return []

    async def get_token_transfers(self, address: str, contract_address: str = None,
                                start_block: int = 0, end_block: int = 99999999,
                                page: int = 1, offset: int = 1000) -> List[TokenTransfer]:
        """Get token transfers from Etherscan"""
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'startblock': start_block,
            'endblock': end_block,
            'page': page,
            'offset': offset,
            'sort': 'desc',
            'apikey': self.api_key
        }
        
        if contract_address:
            params['contractaddress'] = contract_address
        
        try:
            data = await self._make_request('', params)
            transfers = []
            
            for transfer_data in data.get('result', []):
                transfer = self._parse_token_transfer(transfer_data)
                if transfer:
                    transfers.append(transfer)
            
            logger.info(f"Retrieved {len(transfers)} token transfers for {address}")
            return transfers
            
        except Exception as e:
            logger.error(f"Error fetching token transfers: {e}")
            raise

    def _parse_normal_transaction(self, tx_data: Dict[str, Any]) -> Optional[Transaction]:
        """Parse normal transaction data from Etherscan"""
        try:
            return Transaction(
                hash=tx_data['hash'],
                block_number=int(tx_data['blockNumber']),
                timestamp=datetime.fromtimestamp(int(tx_data['timeStamp'])),
                from_address=tx_data['from'],
                to_address=tx_data['to'] or '',
                value = Decimal(tx_data.get("value", "0") or "0") / Decimal(10) ** 18,
                gas_used=int(tx_data['gasUsed']),
                gas_price=Decimal(tx_data['gasPrice']),
                transaction_fee=Decimal(tx_data['gasUsed']) * Decimal(tx_data['gasPrice']),
                status=TransactionStatus(tx_data.get("txreceipt_status") or "unknown"),
                transaction_type=TransactionType.ETH_TRANSFER,
                nonce=int(tx_data['nonce']),
                transaction_index=int(tx_data['transactionIndex']),
                input_data=tx_data.get('input', ''),
                raw_data=tx_data
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse normal transaction: {e}")
            return None

    def _parse_internal_transaction(self, tx_data: Dict[str, Any]) -> Optional[InternalTransaction]:
        """Parse internal transaction data from Etherscan"""
        try:
            return InternalTransaction(
                hash=tx_data['hash'],
                from_address=tx_data['from'],
                to_address=tx_data['to'],
                value=Decimal(tx_data['value']) / Decimal(10) ** 18,
                gas_used=int(tx_data.get('gas', 0)),
                block_number=int(tx_data['blockNumber']),
                timestamp=datetime.fromtimestamp(int(tx_data['timeStamp'])),
                transaction_type=tx_data.get('type', 'call'),
                is_error=tx_data.get('isError', '0') == '1',
                error_code=tx_data.get('errCode')
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse internal transaction: {e}")
            return None

    def _parse_token_transfer(self, transfer_data: Dict[str, Any]) -> Optional[TokenTransfer]:
        """Parse token transfer data from Etherscan"""
        try:
            decimals = int(transfer_data.get('tokenDecimal', 0))
            
            # Parse value with error handling
            try:
                value = Decimal(str(transfer_data['value']))
            except (ValueError, TypeError, InvalidOperation):
                logger.warning(f"Invalid value in token transfer: {transfer_data.get('value')}")
                return None
            
            # Apply decimal adjustment if needed
            if decimals > 0:
                divisor = Decimal(10) ** decimals
                value = value / divisor
            
            return TokenTransfer(
                contract_address=transfer_data['contractAddress'],
                from_address=transfer_data['from'],
                to_address=transfer_data['to'],
                value=value,
                token_name=transfer_data.get('tokenName'),
                token_symbol=transfer_data.get('tokenSymbol'),
                token_decimals=decimals,
                token_id=transfer_data.get('tokenID'),  # For NFTs
                transaction_hash=transfer_data['hash'],
                block_number=int(transfer_data['blockNumber']),
                timestamp=datetime.fromtimestamp(int(transfer_data['timeStamp']))
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse token transfer: {e}")
            return None
import logging
from typing import List, Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
from ..models.transaction import Transaction, TokenTransfer, InternalTransaction
from ..models.enums import TransactionType
from ..api.base_client import BaseAPIClient
from .data_categorizer import DataCategorizer

logger = logging.getLogger(__name__)

class TransactionProcessor:
    """Main transaction processing class"""
    
    def __init__(self, client: BaseAPIClient, categorizer: Optional[DataCategorizer] = None):
        self.client = client
        self.categorizer = categorizer or DataCategorizer()
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def process_wallet_transactions(self, address: str, 
                                        start_block: int = 0,
                                        end_block: int = 99999999,
                                        max_transactions: int = 10000) -> List[Transaction]:
        """Process all transactions for a wallet address"""
        logger.info(f"Starting transaction processing for address: {address}")
        
        try:
            # Fetch all transaction types concurrently
            tasks = [
                self._fetch_normal_transactions(address, start_block, end_block, max_transactions),
                self._fetch_internal_transactions(address, start_block, end_block, max_transactions),
                self._fetch_token_transfers(address, start_block, end_block, max_transactions)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            normal_txs, internal_txs, token_transfers = [], [], []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error in task {i}: {result}")
                    continue
                
                if i == 0:  # Normal transactions
                    normal_txs = result
                elif i == 1:  # Internal transactions
                    internal_txs = result
                else:  # Token transfers
                    token_transfers = result
            
            # Convert all data to unified Transaction objects
            all_transactions = []
            
            # Add normal transactions
            all_transactions.extend(normal_txs)
            
            # Convert internal transactions
            for internal_tx in internal_txs:
                transaction = self.categorizer.convert_internal_to_transaction(internal_tx)
                if transaction:
                    all_transactions.append(transaction)
            
            # Convert token transfers
            for token_transfer in token_transfers:
                transaction = self.categorizer.convert_token_transfer_to_transaction(token_transfer)
                if transaction:
                    all_transactions.append(transaction)
            
            # Sort by timestamp (descending)
            all_transactions.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply max transaction limit
            if len(all_transactions) > max_transactions:
                logger.info(f"Limiting results to {max_transactions} transactions")
                all_transactions = all_transactions[:max_transactions]
            
            logger.info(f"Processed {len(all_transactions)} total transactions")
            
            # Categorize and enrich transactions
            return await self._categorize_transactions(all_transactions)
            
        except Exception as e:
            logger.error(f"Error processing wallet transactions: {e}")
            raise

    async def _fetch_normal_transactions(self, address: str, start_block: int,
                                       end_block: int, max_transactions: int) -> List[Transaction]:
        """Fetch normal transactions with pagination"""
        all_transactions = []
        page = 1
        offset = min(1000, max_transactions)
        
        while len(all_transactions) < max_transactions:
            try:
                transactions = await self.client.get_normal_transactions(
                    address, start_block, end_block, page, offset
                )
                
                if not transactions:
                    break
                
                all_transactions.extend(transactions)
                
                if len(transactions) < offset:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching normal transactions page {page}: {e}")
                break
        
        return all_transactions[:max_transactions]

    async def _fetch_internal_transactions(self, address: str, start_block: int,
                                         end_block: int, max_transactions: int) -> List[InternalTransaction]:
        """Fetch internal transactions with pagination"""
        all_transactions = []
        page = 1
        offset = min(1000, max_transactions)
        
        while len(all_transactions) < max_transactions:
            try:
                transactions = await self.client.get_internal_transactions(
                    address, start_block, end_block, page, offset
                )
                
                if not transactions:
                    break
                
                all_transactions.extend(transactions)
                
                if len(transactions) < offset:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching internal transactions page {page}: {e}")
                break
        
        return all_transactions[:max_transactions]

    async def _fetch_token_transfers(self, address: str, start_block: int,
                                   end_block: int, max_transactions: int) -> List[TokenTransfer]:
        """Fetch token transfers with pagination"""
        all_transfers = []
        page = 1
        offset = min(1000, max_transactions)
        
        while len(all_transfers) < max_transactions:
            try:
                transfers = await self.client.get_token_transfers(
                    address, None, start_block, end_block, page, offset
                )
                
                if not transfers:
                    break
                
                all_transfers.extend(transfers)
                
                if len(transfers) < offset:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching token transfers page {page}: {e}")
                break
        
        return all_transfers[:max_transactions]

    async def _categorize_transactions(self, transactions: List[Transaction]) -> List[Transaction]:
        """Categorize and enrich transactions"""
        loop = asyncio.get_event_loop()
        
        # Use thread pool for CPU-intensive categorization
        categorized_transactions = await loop.run_in_executor(
            self.executor,
            self.categorizer.categorize_transactions,
            transactions
        )
        
        return categorized_transactions
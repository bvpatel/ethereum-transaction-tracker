import csv
import os
from typing import List, Dict, Any
from datetime import datetime
import logging
from ..models.transaction import Transaction
from ..utils.helpers import ensure_directory_exists, format_timestamp

logger = logging.getLogger(__name__)

class CSVExporter:
    """CSV export functionality for transactions"""
    
    def __init__(self, output_directory: str = "./output", 
                 filename_format: str = "{address}_{timestamp}.csv",
                 delimiter: str = ","):
        self.output_directory = output_directory
        self.filename_format = filename_format
        self.delimiter = delimiter
        
        # CSV column headers
        self.headers = [
            "transaction_hash",
            "date_time",
            "from_address",
            "to_address", 
            "transaction_type",
            "asset_contract_address",
            "asset_symbol_name",
            "token_id",
            "value_amount",
            "gas_fee_eth",
            "block_number",
            "status",
            "nonce",
            "transaction_index"
        ]

    def export_transactions(self, transactions: List[Transaction], 
                          address: str, include_timestamp: bool = True) -> str:
        """Export transactions to CSV file"""
        try:
            # Ensure output directory exists
            ensure_directory_exists(self.output_directory)
            
            # Generate filename
            filename = self._generate_filename(address, include_timestamp)
            filepath = os.path.join(self.output_directory, filename)
            
            # Write CSV file
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.headers, 
                                      delimiter=self.delimiter)
                
                # Write header
                writer.writeheader()
                
                # Write transaction data
                for transaction in transactions:
                    row_data = self._prepare_row_data(transaction)
                    writer.writerow(row_data)
            
            logger.info(f"Exported {len(transactions)} transactions to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting transactions: {e}")
            raise

    def _generate_filename(self, address: str, include_timestamp: bool) -> str:
        """Generate filename based on format"""
        if include_timestamp:
            timestamp = format_timestamp(datetime.now())
            return self.filename_format.format(
                address=address.lower()[:10],  # Short address
                timestamp=timestamp
            )
        else:
            return self.filename_format.format(
                address=address.lower()[:10],
                timestamp=""
            ).replace("_.", ".")

    def _prepare_row_data(self, transaction: Transaction) -> Dict[str, Any]:
        """Prepare transaction data for CSV row"""
        return {
            "transaction_hash": transaction.hash,
            "date_time": transaction.date_str,
            "from_address": transaction.from_address,
            "to_address": transaction.to_address,
            "transaction_type": transaction.transaction_type.value,
            "asset_contract_address": transaction.contract_address or "",
            "asset_symbol_name": transaction.token_symbol or "ETH",
            "token_id": transaction.token_id or "",
            "value_amount": transaction.value_str,
            "gas_fee_eth": f"{transaction.fee_in_eth:.8f}",
            "block_number": transaction.block_number,
            "status": transaction.status.value,
            "nonce": transaction.nonce,
            "transaction_index": transaction.transaction_index
        }

    def export_summary(self, transactions: List[Transaction], 
                      address: str) -> Dict[str, Any]:
        """Generate transaction summary statistics"""
        if not transactions:
            return {"error": "No transactions to summarize"}
        
        summary = {
            "address": address,
            "total_transactions": len(transactions),
            "date_range": {
                "earliest": min(tx.timestamp for tx in transactions).strftime("%Y-%m-%d"),
                "latest": max(tx.timestamp for tx in transactions).strftime("%Y-%m-%d")
            },
            "transaction_types": {},
            "total_gas_fees_eth": 0,
            "unique_tokens": set(),
            "unique_contracts": set()
        }
        
        for transaction in transactions:
            # Count transaction types
            tx_type = transaction.transaction_type.value
            summary["transaction_types"][tx_type] = summary["transaction_types"].get(tx_type, 0) + 1
            
            # Sum gas fees
            summary["total_gas_fees_eth"] += float(transaction.fee_in_eth)
            
            # Collect unique tokens and contracts
            if transaction.token_symbol:
                summary["unique_tokens"].add(transaction.token_symbol)
            if transaction.contract_address:
                summary["unique_contracts"].add(transaction.contract_address)
        
        # Convert sets to lists for JSON serialization
        summary["unique_tokens"] = list(summary["unique_tokens"])
        summary["unique_contracts"] = list(summary["unique_contracts"])
        summary["unique_token_count"] = len(summary["unique_tokens"])
        summary["unique_contract_count"] = len(summary["unique_contracts"])
        
        return summary
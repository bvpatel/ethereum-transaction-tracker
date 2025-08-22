import asyncio
import argparse
import logging
import sys
import traceback
from typing import Optional
from datetime import datetime

from .config.config import Config
from .models.enums import APIProvider
from .api.client_factory import ClientFactory
from .processors.transaction_processor import TransactionProcessor
from .exporters.csv_exporter import CSVExporter
from .utils.validators import AddressValidator
from .utils.rate_limiter import RateLimiter
from .exceptions.custom_exceptions import (
    ValidationError, 
    ConfigurationError, 
    EthereumTrackerError
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ethereum_tracker.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class EthereumTransactionTracker:
    """Main application class"""
    
    def __init__(self):
        self.config = Config()
        self.rate_limiter = RateLimiter(calls_per_second=1/self.config.api.rate_limit_delay)
        self.client = None
        self.processor = None
        self.exporter = CSVExporter(
            output_directory=self.config.output.output_directory,
            filename_format=self.config.output.filename_format,
            delimiter=self.config.output.csv_delimiter
        )

    async def initialize(self, provider_name: str = None) -> None:
        """Initialize the tracker with API client"""
        try:
            # Validate configuration
            config_errors = self.config.validate()
            if config_errors:
                raise ConfigurationError(f"Configuration errors: {config_errors}")
            
            # Determine provider
            provider_name = provider_name or self.config.api.default_provider
            
            try:
                provider = APIProvider(provider_name)
            except ValueError:
                raise ConfigurationError(f"Invalid provider: {provider_name}")
            
            # Get API key for provider
            if provider == APIProvider.ETHERSCAN:
                api_key = self.config.api.etherscan_api_key
            elif provider == APIProvider.ALCHEMY:
                api_key = self.config.api.alchemy_api_key
            else:
                raise ConfigurationError(f"Unsupported provider: {provider}")
            
            # Create client
            self.client = ClientFactory.create_client(provider, api_key, self.rate_limiter)
            self.processor = TransactionProcessor(self.client)
            
            logger.info(f"Initialized with provider: {provider.value}")
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise

    async def process_address(self, address: str, 
                            start_block: int = 0,
                            end_block: int = 99999999,
                            max_transactions: int = None,
                            export_csv: bool = True) -> dict:
        """Process transactions for a given address"""
        try:
            # Validate address
            if not AddressValidator.is_valid_ethereum_address(address):
                raise ValidationError(f"Invalid Ethereum address: {address}")
            
            # Normalize address
            normalized_address = AddressValidator.normalize_address(address)
            
            # Set max transactions from config if not provided
            if max_transactions is None:
                max_transactions = self.config.data.max_transactions
            
            logger.info(f"Processing transactions for address: {normalized_address}")
            logger.info(f"Parameters: start_block={start_block}, end_block={end_block}, max_transactions={max_transactions}")
            
            # Process transactions
            async with self.client:
                transactions = await self.processor.process_wallet_transactions(
                    normalized_address,
                    start_block=start_block,
                    end_block=end_block,
                    max_transactions=max_transactions
                )
            
            result = {
                "address": normalized_address,
                "transaction_count": len(transactions),
                "processing_timestamp": datetime.now().isoformat(),
                "csv_file": None,
                "summary": self.exporter.export_summary(transactions, normalized_address)
            }
            
            # Export to CSV if requested
            if export_csv and transactions:
                csv_file = self.exporter.export_transactions(
                    transactions, 
                    normalized_address,
                    include_timestamp=self.config.output.include_timestamp
                )
                result["csv_file"] = csv_file
                logger.info(f"Exported to CSV: {csv_file}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing address {address}: {e}")
            traceback.print_exc()
            raise

    async def batch_process_addresses(self, addresses: list, **kwargs) -> dict:
        """Process multiple addresses"""
        results = {}
        
        for address in addresses:
            try:
                logger.info(f"Processing address {address} ({addresses.index(address) + 1}/{len(addresses)})")
                result = await self.process_address(address, **kwargs)
                results[address] = result
                
                # Small delay between addresses to be respectful
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to process address {address}: {e}")
                results[address] = {"error": str(e)}
        
        return results

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Ethereum Transaction Tracker")
    parser.add_argument("address", help="Ethereum wallet address")
    parser.add_argument("--provider", choices=["etherscan", "alchemy"], 
                       help="API provider to use")
    parser.add_argument("--start-block", type=int, default=0,
                       help="Starting block number")
    parser.add_argument("--end-block", type=int, default=99999999,
                       help="Ending block number")
    parser.add_argument("--max-transactions", type=int,
                       help="Maximum number of transactions to process")
    parser.add_argument("--no-export", action="store_true",
                       help="Skip CSV export")
    parser.add_argument("--batch-file", 
                       help="File containing addresses to process (one per line)")
    
    args = parser.parse_args()
    
    try:
        # Initialize tracker
        tracker = EthereumTransactionTracker()
        await tracker.initialize(args.provider)
        
        # Process addresses
        if args.batch_file:
            # Batch processing
            with open(args.batch_file, 'r') as f:
                addresses = [line.strip() for line in f if line.strip()]
            
            results = await tracker.batch_process_addresses(
                addresses,
                start_block=args.start_block,
                end_block=args.end_block,
                max_transactions=args.max_transactions,
                export_csv=not args.no_export
            )
            
            print(f"Processed {len(addresses)} addresses")
            for addr, result in results.items():
                if "error" in result:
                    print(f"❌ {addr}: {result['error']}")
                else:
                    print(f"✅ {addr}: {result['transaction_count']} transactions")
        
        else:
            # Single address processing
            result = await tracker.process_address(
                args.address,
                start_block=args.start_block,
                end_block=args.end_block,
                max_transactions=args.max_transactions,
                export_csv=not args.no_export
            )
            
            print(f"✅ Processed {result['transaction_count']} transactions for {args.address}")
            if result['csv_file']:
                print(f"📄 CSV exported to: {result['csv_file']}")
            
            # Print summary
            summary = result['summary']
            print(f"\n📊 Summary:")
            print(f"  Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")
            print(f"  Total gas fees: {summary['total_gas_fees_eth']:.6f} ETH")
            print(f"  Unique tokens: {summary['unique_token_count']}")
            print(f"  Transaction types: {summary['transaction_types']}")
        
    except EthereumTrackerError as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
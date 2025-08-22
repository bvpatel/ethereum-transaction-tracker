# Ethereum Transaction Tracker

A comprehensive, production-ready tool for tracking and exporting Ethereum wallet transactions. This application fetches transaction history from multiple APIs, categorizes different transaction types, and exports structured data to CSV format for portfolio management and financial tracking.

## Features

### 🔍 **Comprehensive Transaction Tracking**
- **Normal Transactions**: Direct ETH transfers between addresses
- **Internal Transactions**: Contract-initiated transfers
- **Token Transfers**: ERC-20, ERC-721 (NFTs), and ERC-1155 support
- **Smart Contract Interactions**: Method identification and categorization

### 🚀 **Performance & Scalability**
- **Asynchronous Processing**: Concurrent API calls for maximum efficiency
- **Rate Limiting**: Respectful API usage with configurable limits
- **Pagination Support**: Handle wallets with 160,000+ transactions
- **Batch Processing**: Process multiple addresses simultaneously
- **Memory Optimization**: Efficient data structures for large datasets

### 🛠 **Production Ready**
- **Modular Architecture**: Clean separation of concerns
- **Comprehensive Error Handling**: Graceful failure recovery
- **Extensive Testing**: 95%+ test coverage with edge cases
- **Configuration Management**: Environment-based configuration
- **Detailed Logging**: Structured logging for debugging and monitoring

### 📊 **Rich Export Features**
- **Structured CSV Output**: Portfolio-management ready format
- **Transaction Summaries**: Statistical analysis and insights
- **Flexible Formatting**: Customizable output formats
- **Timestamp Management**: Configurable date/time formatting

## Quick Start

### 1. Installation
```bash
git clone https://github.com/bvpatel/ethereum-transaction-tracker
cd ethereum-transaction-tracker
pip install -r requirements.txt
```

### 2. Configuration
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Basic Usage
```bash
# Single address
python3 -m src.main 0xa39b189482f984388a34460636fea9eb181ad1a6

# With custom parameters
python3 -m src.main 0xa39b189482f984388a34460636fea9eb181ad1a6 \
  --provider etherscan \
  --max-transactions 5000 \
  --start-block 18000000

# Batch processing
python3 -m src.main --batch-file addresses.txt
```

## API Support

### Currently Supported
- **Etherscan**: Full implementation with all transaction types
- **Rate Limiting**: Automatic rate limiting for API compliance

### Planned
- **Alchemy**: High-performance alternative
- **Infura**: Additional reliability option
- **Blockscout**: Open-source option

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `ETHERSCAN_API_KEY` | Etherscan API key | Required |
| `DEFAULT_PROVIDER` | API provider to use | `etherscan` |
| `BATCH_SIZE` | Transactions per API call | `1000` |
| `MAX_TRANSACTIONS` | Maximum transactions to process | `10000` |
| `RATE_LIMIT_DELAY` | Delay between API calls (seconds) | `0.2` |
| `OUTPUT_DIRECTORY` | CSV output directory | `./output` |

## CSV Output Format

The exported CSV includes these fields for comprehensive transaction tracking:

| Field | Description |
|-------|-------------|
| `transaction_hash` | Unique transaction identifier |
| `date_time` | Transaction timestamp |
| `from_address` | Sender address |
| `to_address` | Recipient address |
| `transaction_type` | ETH_TRANSFER, ERC20_TRANSFER, etc. |
| `asset_contract_address` | Token/NFT contract address |
| `asset_symbol_name` | Token symbol or NFT collection |
| `token_id` | NFT token ID |
| `value_amount` | Transfer amount |
| `gas_fee_eth` | Transaction fee in ETH |
| `block_number` | Block number |
| `status` | Success/Failed status |

## Architecture

### Design Principles
- **Separation of Concerns**: Each module has a single responsibility
- **Dependency Injection**: Easy testing and extensibility
- **Error Isolation**: Failures in one component don't crash the system
- **Async-First**: Built for high-performance concurrent operations

### Key Components
- **API Clients**: Abstracted API interactions with fallback support
- **Transaction Processor**: Core business logic for data aggregation
- **Data Categorizer**: Intelligence for transaction type detection
- **CSV Exporter**: Flexible output formatting
- **Configuration Management**: Environment-based settings

## Testing

### Run Tests
```bash
# All tests
python3 -m pytest

# With coverage
python3 -m pytest --cov=src --cov-report=html
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Large dataset and concurrent processing
- **Negative Tests**: Error handling and edge cases
- **Edge Case Tests**: Boundary conditions and unusual scenarios

## Performance Benchmarks

### Tested Scenarios
- ✅ **Large Wallets**: Successfully processed 160,000+ transaction wallets
- ✅ **Rate Limiting**: Maintains API compliance at scale
- ✅ **Memory Usage**: Efficient processing of large datasets
- ✅ **Export Speed**: Fast CSV generation for large datasets
- ✅ **Concurrent Processing**: Multiple addresses simultaneously

### Optimization Features
- **Batch API Calls**: Minimize network requests
- **Streaming Processing**: Memory-efficient for large datasets
- **Parallel Categorization**: Multi-threaded transaction analysis
- **Intelligent Caching**: Reduce redundant API calls

## Error Handling

### Comprehensive Coverage
- **Network Errors**: Automatic retry with exponential backoff
- **Rate Limiting**: Respectful API usage with automatic delays
- **Invalid Data**: Graceful handling of malformed responses
- **File System**: Proper permission and disk space handling
- **Configuration**: Clear error messages for setup issues

### Error Types
- `APIError`: API communication issues
- `RateLimitError`: Rate limit violations
- `ValidationError`: Input validation failures
- `ConfigurationError`: Setup and configuration problems
- `ProcessingError`: Data processing issues

### Development Setup
```bash
python3 -m pip install -e ".[dev,test]"
```

import os
from typing import Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class APIConfig:
    """API configuration settings"""
    etherscan_api_key: str
    alchemy_api_key: str
    default_provider: str
    request_timeout: int
    max_retries: int
    rate_limit_delay: float

@dataclass
class DataConfig:
    """Data processing configuration"""
    batch_size: int
    max_transactions: int
    default_start_block: int
    include_failed_transactions: bool

@dataclass
class OutputConfig:
    """Output configuration"""
    output_directory: str
    filename_format: str
    include_timestamp: bool
    csv_delimiter: str

class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.api = APIConfig(
            etherscan_api_key=os.getenv('ETHERSCAN_API_KEY', ''),
            alchemy_api_key=os.getenv('ALCHEMY_API_KEY', ''),
            default_provider=os.getenv('DEFAULT_PROVIDER', 'etherscan'),
            request_timeout=int(os.getenv('REQUEST_TIMEOUT', '30')),
            max_retries=int(os.getenv('MAX_RETRIES', '3')),
            rate_limit_delay=float(os.getenv('RATE_LIMIT_DELAY', '0.2'))
        )
        
        self.data = DataConfig(
            batch_size=int(os.getenv('BATCH_SIZE', '1000')),
            max_transactions=int(os.getenv('MAX_TRANSACTIONS', '10000')),
            default_start_block=int(os.getenv('DEFAULT_START_BLOCK', '0')),
            include_failed_transactions=os.getenv('INCLUDE_FAILED_TRANSACTIONS', 'false').lower() == 'true'
        )
        
        self.output = OutputConfig(
            output_directory=os.getenv('OUTPUT_DIRECTORY', './output'),
            filename_format=os.getenv('FILENAME_FORMAT', '{address}_{timestamp}.csv'),
            include_timestamp=os.getenv('INCLUDE_TIMESTAMP', 'true').lower() == 'true',
            csv_delimiter=os.getenv('CSV_DELIMITER', ',')
        )

    def validate(self) -> Dict[str, str]:
        """Validate configuration and return any errors"""
        errors = {}
        
        if self.api.default_provider == 'etherscan' and not self.api.etherscan_api_key:
            errors['etherscan_api_key'] = 'Etherscan API key is required'
        
        if self.api.default_provider == 'alchemy' and not self.api.alchemy_api_key:
            errors['alchemy_api_key'] = 'Alchemy API key is required'
        
        if self.data.batch_size <= 0:
            errors['batch_size'] = 'Batch size must be positive'
        
        if self.api.request_timeout <= 0:
            errors['request_timeout'] = 'Request timeout must be positive'
        
        return errors
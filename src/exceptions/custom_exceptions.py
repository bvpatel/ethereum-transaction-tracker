class EthereumTrackerError(Exception):
    """Base exception for Ethereum Tracker"""
    pass

class APIError(EthereumTrackerError):
    """API related errors"""
    pass

class RateLimitError(APIError):
    """Rate limit exceeded error"""
    pass

class ConfigurationError(EthereumTrackerError):
    """Configuration related errors"""
    pass

class ValidationError(EthereumTrackerError):
    """Validation related errors"""
    pass

class ProcessingError(EthereumTrackerError):
    """Data processing related errors"""
    pass
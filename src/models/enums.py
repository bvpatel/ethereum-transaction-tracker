from enum import Enum, auto

class TransactionType(Enum):
    """Transaction type enumeration"""
    ETH_TRANSFER = "ETH_TRANSFER"
    ERC20_TRANSFER = "ERC20_TRANSFER"
    ERC721_TRANSFER = "ERC721_TRANSFER"
    ERC1155_TRANSFER = "ERC1155_TRANSFER"
    INTERNAL_TRANSFER = "INTERNAL_TRANSFER"
    CONTRACT_INTERACTION = "CONTRACT_INTERACTION"
    FAILED_TRANSACTION = "FAILED_TRANSACTION"

class TransactionStatus(Enum):
    """Transaction status enumeration"""
    SUCCESS = "1"
    FAILED = "0"
    PENDING = "pending"
    UNKNOWN = "unknown"

class APIProvider(Enum):
    """API provider enumeration"""
    ETHERSCAN = "etherscan"
    ALCHEMY = "alchemy"
    BLOCKSCOUT = "blockscout"
    INFURA = "infura"
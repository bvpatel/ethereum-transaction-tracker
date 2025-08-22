import pytest
from unittest.mock import AsyncMock
from decimal import Decimal
import logging

from src.api.etherscan_client import EtherscanClient
from src.models.transaction import Transaction, TokenTransfer, InternalTransaction
from src.models.enums import TransactionStatus, TransactionType
from src.utils.rate_limiter import RateLimiter


@pytest.fixture
def client():
    return EtherscanClient("fake_api_key", rate_limiter=RateLimiter(1))


# ---------- NORMAL TRANSACTIONS ----------

@pytest.mark.asyncio
async def test_get_normal_transactions_success(client):
    mock_data = {
        "status": "1",
        "result": [
            {
                "hash": "0x123",
                "blockNumber": "100",
                "timeStamp": "1700000000",
                "from": "0xabc",
                "to": "0xdef",
                "value": "1000000000000000000",  # 1 ETH
                "gasUsed": "21000",
                "gasPrice": "1000000000",
                "txreceipt_status": "1",
                "nonce": "5",
                "transactionIndex": "2",
                "input": "0x"
            }
        ]
    }
    client._make_request = AsyncMock(return_value=mock_data)

    txs = await client.get_normal_transactions("0xabc")
    assert txs and len(txs) == 1
    tx = txs[0]
    assert isinstance(tx, Transaction)
    assert tx.hash == "0x123"
    assert tx.value == Decimal("1")
    assert tx.status == TransactionStatus.SUCCESS
    assert tx.transaction_type == TransactionType.ETH_TRANSFER


@pytest.mark.asyncio
async def test_get_normal_transactions_empty_result(client):
    client._make_request = AsyncMock(return_value={"status": "1", "result": []})
    txs = await client.get_normal_transactions("0xabc")
    assert txs == []


@pytest.mark.asyncio
async def test_get_normal_transactions_error_status(client):
    client._make_request = AsyncMock(return_value={"status": "0", "message": "NOTOK"})
    txs = await client.get_normal_transactions("0xabc")
    # Client returns empty list, not None
    assert txs == []


@pytest.mark.asyncio
async def test_get_normal_transactions_handles_exception(client, caplog):
    client._make_request = AsyncMock(side_effect=Exception("network error"))
    caplog.set_level(logging.ERROR)
    result = await client.get_normal_transactions("0xabc")
    assert result == []
    assert "Error fetching normal transactions" in caplog.text


# ---------- INTERNAL TRANSACTIONS ----------

@pytest.mark.asyncio
async def test_get_internal_transactions_success(client):
    mock_data = {
        "status": "1",
        "result": [
            {
                "hash": "0x456",
                "from": "0xaaa",
                "to": "0xbbb",
                "value": "2000000000000000000",  # 2 ETH
                "gas": "50000",
                "blockNumber": "200",
                "timeStamp": "1700000500",
                "type": "call",
                "isError": "0",
            }
        ]
    }
    client._make_request = AsyncMock(return_value=mock_data)

    txs = await client.get_internal_transactions("0xaaa")
    assert txs and len(txs) == 1
    tx = txs[0]
    assert isinstance(tx, InternalTransaction)
    assert tx.hash == "0x456"
    assert tx.value == Decimal("2")
    assert tx.is_error is False


@pytest.mark.asyncio
async def test_get_internal_transactions_empty_result(client):
    client._make_request = AsyncMock(return_value={"status": "1", "result": []})
    txs = await client.get_internal_transactions("0xaaa")
    assert txs == []


@pytest.mark.asyncio
async def test_get_internal_transactions_parse_failure(client):
    bad_data = {
        "status": "1",
        "result": [{"hash": "0x999"}]  # missing fields
    }
    client._make_request = AsyncMock(return_value=bad_data)
    txs = await client.get_internal_transactions("0xaaa")
    assert txs == []


@pytest.mark.asyncio
async def test_get_internal_transactions_handles_exception(client, caplog):
    client._make_request = AsyncMock(side_effect=Exception("timeout"))
    caplog.set_level(logging.WARNING)
    result = await client.get_internal_transactions("0xaaa")
    assert result == []
    assert "Error fetching internal transactions" in caplog.text


# ---------- TOKEN TRANSFERS ----------

@pytest.mark.asyncio
async def test_get_token_transfers_success(client):
    mock_data = {
        "status": "1",
        "result": [
            {
                "hash": "0x789",
                "contractAddress": "0xtoken",
                "from": "0x111",
                "to": "0x222",
                "value": "1000",
                "tokenName": "TestToken",
                "tokenSymbol": "TT",
                "tokenDecimal": "2",
                "blockNumber": "300",
                "timeStamp": "1700001000"
            }
        ]
    }
    client._make_request = AsyncMock(return_value=mock_data)

    transfers = await client.get_token_transfers("0x111")
    assert transfers and len(transfers) == 1
    transfer = transfers[0]
    assert isinstance(transfer, TokenTransfer)
    assert transfer.transaction_hash == "0x789"
    assert transfer.value == Decimal("10")  # 1000 / 10^2


@pytest.mark.asyncio
async def test_get_token_transfers_zero_decimals(client):
    mock_data = {
        "status": "1",
        "result": [
            {
                "hash": "0x999",
                "contractAddress": "0xtoken",
                "from": "0x111",
                "to": "0x222",
                "value": "500",
                "tokenName": "TestToken",
                "tokenSymbol": "TT",
                "tokenDecimal": "0",
                "blockNumber": "400",
                "timeStamp": "1700002000"
            }
        ]
    }
    client._make_request = AsyncMock(return_value=mock_data)

    transfers = await client.get_token_transfers("0x111")
    assert transfers and transfers[0].value == Decimal("500")


@pytest.mark.asyncio
async def test_get_token_transfers_invalid_value(client):
    mock_data = {
        "status": "1",
        "result": [
            {
                "hash": "0x999",
                "contractAddress": "0xtoken",
                "from": "0x111",
                "to": "0x222",
                "value": "invalid",  # not a number
                "tokenDecimal": "2",
                "blockNumber": "500",
                "timeStamp": "1700002500"
            }
        ]
    }
    client._make_request = AsyncMock(return_value=mock_data)

    transfers = await client.get_token_transfers("0x111")
    assert transfers == []


@pytest.mark.asyncio
async def test_get_token_transfers_handles_exception(client, caplog):
    client._make_request = AsyncMock(side_effect=Exception("boom"))
    caplog.set_level(logging.ERROR)
    with pytest.raises(Exception):
        await client.get_token_transfers("0x111")


# ---------- PARSE HELPERS ----------

def test_parse_normal_transaction_invalid_data(client, caplog):
    bad_data = {"hash": "0x123"}  # missing required fields
    caplog.set_level(logging.WARNING)
    tx = client._parse_normal_transaction(bad_data)
    assert tx is None
    assert "Failed to parse normal transaction" in caplog.text


def test_parse_internal_transaction_invalid_data(client, caplog):
    bad_data = {"hash": "0x456"}  # missing required fields
    caplog.set_level(logging.WARNING)
    tx = client._parse_internal_transaction(bad_data)
    assert tx is None
    assert "Failed to parse internal transaction" in caplog.text


def test_parse_token_transfer_invalid_data(client, caplog):
    bad_data = {"hash": "0x789"}  # missing required fields
    caplog.set_level(logging.WARNING)
    tx = client._parse_token_transfer(bad_data)
    assert tx is None
    assert "Failed to parse token transfer" in caplog.text

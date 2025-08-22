import pytest
import csv
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, mock_open, MagicMock
from datetime import datetime
from decimal import Decimal
import logging

from src.exporters.csv_exporter import CSVExporter
from src.models.transaction import Transaction
from src.models.enums import TransactionType, TransactionStatus


class TestCSVExporter:
    """Test cases for CSVExporter class"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def csv_exporter(self, temp_dir):
        """Create CSVExporter instance with temporary directory"""
        return CSVExporter(
            output_directory=temp_dir,
            filename_format="{address}_{timestamp}.csv",
            delimiter=","
        )

    @pytest.fixture
    def sample_transaction(self):
        """Create a sample transaction for testing"""
        return Transaction(
            hash="0x123abc",
            block_number=1000,
            timestamp=datetime(2023, 1, 15, 12, 30, 45),
            from_address="0xfrom123",
            to_address="0xto456",
            value=Decimal("1.5"),
            gas_used=21000,
            gas_price=Decimal("20000000000"),
            transaction_fee=Decimal("0.00042"),  # Added required parameter
            status=TransactionStatus.SUCCESS,
            nonce=42,
            transaction_index=5,
            transaction_type=TransactionType.ETH_TRANSFER,
            contract_address=None,
            token_symbol=None,
            token_id=None
        )

    @pytest.fixture
    def sample_token_transaction(self):
        """Create a sample token transaction for testing"""
        return Transaction(
            hash="0x456def",
            block_number=2000,
            timestamp=datetime(2023, 2, 20, 15, 45, 30),
            from_address="0xfrom789",
            to_address="0xto012",
            value=Decimal("100"),
            gas_used=50000,
            gas_price=Decimal("25000000000"),
            transaction_fee=Decimal("0.00125"),  # Added required parameter
            status=TransactionStatus.SUCCESS,
            nonce=43,
            transaction_index=8,
            transaction_type=TransactionType.ERC20_TRANSFER,  # Fixed enum value
            contract_address="0xtoken123",
            token_symbol="USDT",
            token_id="123"
        )

    def test_init_default_values(self):
        """Test CSVExporter initialization with default values"""
        exporter = CSVExporter()
        
        assert exporter.output_directory == "./output"
        assert exporter.filename_format == "{address}_{timestamp}.csv"
        assert exporter.delimiter == ","
        assert isinstance(exporter.headers, list)
        assert len(exporter.headers) == 14

    def test_init_custom_values(self):
        """Test CSVExporter initialization with custom values"""
        exporter = CSVExporter(
            output_directory="./custom_output",
            filename_format="{address}_custom.csv",
            delimiter=";"
        )
        
        assert exporter.output_directory == "./custom_output"
        assert exporter.filename_format == "{address}_custom.csv"
        assert exporter.delimiter == ";"

    def test_headers_completeness(self, csv_exporter):
        """Test that all required headers are present"""
        expected_headers = [
            "transaction_hash", "date_time", "from_address", "to_address",
            "transaction_type", "asset_contract_address", "asset_symbol_name",
            "token_id", "value_amount", "gas_fee_eth", "block_number",
            "status", "nonce", "transaction_index"
        ]
        
        assert csv_exporter.headers == expected_headers

    @patch('src.exporters.csv_exporter.ensure_directory_exists')
    @patch('src.exporters.csv_exporter.format_timestamp')
    def test_export_transactions_success(self, mock_format_timestamp, mock_ensure_dir, 
                                       csv_exporter, sample_transaction, temp_dir):
        """Test successful export of transactions to CSV"""
        mock_format_timestamp.return_value = "20230115_123045"
        transactions = [sample_transaction]
        address = "0xtest123"
        
        filepath = csv_exporter.export_transactions(transactions, address, True)
        
        # Verify directory creation was called
        mock_ensure_dir.assert_called_once_with(temp_dir)
        
        # Verify file was created
        expected_filename = "0xtest123_20230115_123045.csv"
        expected_filepath = os.path.join(temp_dir, expected_filename)
        assert filepath == expected_filepath
        assert os.path.exists(filepath)
        
        # Verify CSV content
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 1
            row = rows[0]
            assert row['transaction_hash'] == "0x123abc"
            assert row['from_address'] == "0xfrom123"
            assert row['to_address'] == "0xto456"
            assert row['transaction_type'] == TransactionType.ETH_TRANSFER.value

    @patch('src.exporters.csv_exporter.ensure_directory_exists')
    def test_export_transactions_multiple(self, mock_ensure_dir, csv_exporter, 
                                        sample_transaction, sample_token_transaction, temp_dir):
        """Test export of multiple transactions"""
        transactions = [sample_transaction, sample_token_transaction]
        address = "0xtest456"
        
        filepath = csv_exporter.export_transactions(transactions, address, False)
        
        # Verify file content
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 2
            assert rows[0]['transaction_hash'] == "0x123abc"
            assert rows[1]['transaction_hash'] == "0x456def"
            assert rows[1]['asset_symbol_name'] == "USDT"
            assert rows[1]['asset_contract_address'] == "0xtoken123"

    @patch('src.exporters.csv_exporter.ensure_directory_exists')
    def test_export_transactions_empty_list(self, mock_ensure_dir, csv_exporter, temp_dir):
        """Test export with empty transaction list"""
        transactions = []
        address = "0xempty"
        
        filepath = csv_exporter.export_transactions(transactions, address, True)
        
        # Verify file was created with only headers
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0
            assert reader.fieldnames == csv_exporter.headers

    @patch('src.exporters.csv_exporter.ensure_directory_exists')
    def test_export_transactions_custom_delimiter(self, mock_ensure_dir, temp_dir, sample_transaction):
        """Test export with custom delimiter"""
        exporter = CSVExporter(output_directory=temp_dir, delimiter=";")
        transactions = [sample_transaction]
        address = "0xtest789"
        
        filepath = exporter.export_transactions(transactions, address, False)
        
        # Verify delimiter in file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            assert ";" in content
            # Verify it's properly delimited
            lines = content.strip().split('\n')
            header_parts = lines[0].split(';')
            assert len(header_parts) == len(exporter.headers)

    @patch('src.exporters.csv_exporter.ensure_directory_exists', side_effect=Exception("Directory error"))
    def test_export_transactions_directory_error(self, mock_ensure_dir, csv_exporter, sample_transaction):
        """Test export when directory creation fails"""
        transactions = [sample_transaction]
        address = "0xtest"
        
        with pytest.raises(Exception, match="Directory error"):
            csv_exporter.export_transactions(transactions, address, True)

    @patch('src.exporters.csv_exporter.ensure_directory_exists')
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_export_transactions_file_permission_error(self, mock_open, mock_ensure_dir, 
                                                      csv_exporter, sample_transaction):
        """Test export when file cannot be written due to permissions"""
        transactions = [sample_transaction]
        address = "0xtest"
        
        with pytest.raises(PermissionError):
            csv_exporter.export_transactions(transactions, address, True)

    @patch('src.exporters.csv_exporter.format_timestamp')
    def test_generate_filename_with_timestamp(self, mock_format_timestamp, csv_exporter):
        """Test filename generation with timestamp"""
        mock_format_timestamp.return_value = "20230115_123045"
        address = "0x1234567890abcdef"
        
        filename = csv_exporter._generate_filename(address, True)
        
        assert filename == "0x12345678_20230115_123045.csv"
        mock_format_timestamp.assert_called_once()

    def test_generate_filename_without_timestamp(self, csv_exporter):
        """Test filename generation without timestamp"""
        address = "0x1234567890abcdef"
        
        filename = csv_exporter._generate_filename(address, False)
        
        # The actual implementation removes "_." and replaces with "."
        assert filename == "0x12345678.csv"

    def test_generate_filename_custom_format(self, temp_dir):
        """Test filename generation with custom format"""
        exporter = CSVExporter(
            output_directory=temp_dir,
            filename_format="export_{address}.csv"
        )
        address = "0x1234567890abcdef"
        
        filename = exporter._generate_filename(address, False)
        
        assert filename == "export_0x12345678.csv"

    def test_generate_filename_address_truncation(self, csv_exporter):
        """Test that long addresses are properly truncated"""
        long_address = "0x1234567890abcdef1234567890abcdef12345678"
        
        filename = csv_exporter._generate_filename(long_address, False)
        
        # The actual implementation removes "_." and replaces with "."  
        assert filename == "0x12345678.csv"
        assert len("0x12345678") == 10  # Verify truncation to 10 chars

    def test_prepare_row_data_eth_transaction(self, csv_exporter, sample_transaction):
        """Test row data preparation for ETH transaction"""
        row_data = csv_exporter._prepare_row_data(sample_transaction)
        
        assert row_data['transaction_hash'] == "0x123abc"
        assert row_data['from_address'] == "0xfrom123"
        assert row_data['to_address'] == "0xto456"
        assert row_data['transaction_type'] == TransactionType.ETH_TRANSFER.value
        assert row_data['asset_contract_address'] == ""
        assert row_data['asset_symbol_name'] == "ETH"
        assert row_data['token_id'] == ""
        assert row_data['value_amount'] == "1.500000"
        assert row_data['block_number'] == 1000
        assert row_data['status'] == TransactionStatus.SUCCESS.value
        assert row_data['nonce'] == 42
        assert row_data['transaction_index'] == 5

    def test_prepare_row_data_token_transaction(self, csv_exporter, sample_token_transaction):
        """Test row data preparation for token transaction"""
        row_data = csv_exporter._prepare_row_data(sample_token_transaction)
        
        assert row_data['transaction_hash'] == "0x456def"
        assert row_data['asset_contract_address'] == "0xtoken123"
        assert row_data['asset_symbol_name'] == "USDT"
        assert row_data['token_id'] == "123"
        assert row_data['transaction_type'] == TransactionType.ERC20_TRANSFER.value

    def test_prepare_row_data_gas_fee_formatting(self, csv_exporter, sample_transaction):
        """Test gas fee formatting in row data"""
        row_data = csv_exporter._prepare_row_data(sample_transaction)
        
        # Verify gas fee is formatted to 8 decimal places
        gas_fee = row_data['gas_fee_eth']
        assert isinstance(gas_fee, str)
        decimal_places = len(gas_fee.split('.')[1]) if '.' in gas_fee else 0
        assert decimal_places == 8

    def test_export_summary_empty_transactions(self, csv_exporter):
        """Test summary export with empty transaction list"""
        summary = csv_exporter.export_summary([], "0xtest")
        
        assert summary == {"error": "No transactions to summarize"}

    def test_export_summary_single_transaction(self, csv_exporter, sample_transaction):
        """Test summary export with single transaction"""
        address = "0xtest123"
        summary = csv_exporter.export_summary([sample_transaction], address)
        
        assert summary['address'] == address
        assert summary['total_transactions'] == 1
        assert summary['date_range']['earliest'] == "2023-01-15"
        assert summary['date_range']['latest'] == "2023-01-15"
        assert summary['transaction_types'][TransactionType.ETH_TRANSFER.value] == 1
        assert summary['total_gas_fees_eth'] > 0
        assert summary['unique_tokens'] == []
        assert summary['unique_contracts'] == []
        assert summary['unique_token_count'] == 0
        assert summary['unique_contract_count'] == 0

    def test_export_summary_multiple_transactions(self, csv_exporter, sample_transaction, sample_token_transaction):
        """Test summary export with multiple transactions"""
        transactions = [sample_transaction, sample_token_transaction]
        address = "0xtest456"
        
        summary = csv_exporter.export_summary(transactions, address)
        
        assert summary['total_transactions'] == 2
        assert summary['date_range']['earliest'] == "2023-01-15"
        assert summary['date_range']['latest'] == "2023-02-20"
        assert summary['transaction_types'][TransactionType.ETH_TRANSFER.value] == 1
        assert summary['transaction_types'][TransactionType.ERC20_TRANSFER.value] == 1
        assert "USDT" in summary['unique_tokens']
        assert "0xtoken123" in summary['unique_contracts']
        assert summary['unique_token_count'] == 1
        assert summary['unique_contract_count'] == 1

    def test_export_summary_gas_fee_calculation(self, csv_exporter):
        """Test gas fee calculation in summary"""
        # Create transactions with known gas fees
        tx1 = Transaction(
            hash="0x1", block_number=1, timestamp=datetime(2023, 1, 1),
            from_address="0xa", to_address="0xb", value=Decimal("1"),
            gas_used=21000, gas_price=Decimal("20000000000"),
            transaction_fee=Decimal("0.00042"),  # Added required parameter
            status=TransactionStatus.SUCCESS, nonce=1, transaction_index=1,
            transaction_type=TransactionType.ETH_TRANSFER
        )
        tx2 = Transaction(
            hash="0x2", block_number=2, timestamp=datetime(2023, 1, 2),
            from_address="0xc", to_address="0xd", value=Decimal("2"),
            gas_used=50000, gas_price=Decimal("30000000000"),
            transaction_fee=Decimal("0.0015"),  # Added required parameter
            status=TransactionStatus.SUCCESS, nonce=2, transaction_index=2,
            transaction_type=TransactionType.ETH_TRANSFER
        )
        
        summary = csv_exporter.export_summary([tx1, tx2], "0xtest")
        
        expected_total_gas = float(tx1.fee_in_eth) + float(tx2.fee_in_eth)
        assert abs(summary['total_gas_fees_eth'] - expected_total_gas) < 1e-10

    def test_export_summary_unique_collections(self, csv_exporter):
        """Test unique token and contract collection"""
        # Create transactions with duplicate and unique tokens/contracts
        tx1 = Transaction(
            hash="0x1", block_number=1, timestamp=datetime(2023, 1, 1),
            from_address="0xa", to_address="0xb", value=Decimal("1"),
            gas_used=21000, gas_price=Decimal("20000000000"),
            transaction_fee=Decimal("0.00042"),
            status=TransactionStatus.SUCCESS, nonce=1, transaction_index=1,
            transaction_type=TransactionType.ERC20_TRANSFER,
            contract_address="0xcontract1", token_symbol="USDT"
        )
        tx2 = Transaction(
            hash="0x2", block_number=2, timestamp=datetime(2023, 1, 2),
            from_address="0xc", to_address="0xd", value=Decimal("2"),
            gas_used=50000, gas_price=Decimal("30000000000"),
            transaction_fee=Decimal("0.0015"),
            status=TransactionStatus.SUCCESS, nonce=2, transaction_index=2,
            transaction_type=TransactionType.ERC20_TRANSFER,
            contract_address="0xcontract1", token_symbol="USDT"  # Duplicate
        )
        tx3 = Transaction(
            hash="0x3", block_number=3, timestamp=datetime(2023, 1, 3),
            from_address="0xe", to_address="0xf", value=Decimal("3"),
            gas_used=30000, gas_price=Decimal("25000000000"),
            transaction_fee=Decimal("0.00075"),
            status=TransactionStatus.SUCCESS, nonce=3, transaction_index=3,
            transaction_type=TransactionType.ERC20_TRANSFER,
            contract_address="0xcontract2", token_symbol="USDC"  # Different
        )
        
        summary = csv_exporter.export_summary([tx1, tx2, tx3], "0xtest")
        
        assert set(summary['unique_tokens']) == {"USDT", "USDC"}
        assert set(summary['unique_contracts']) == {"0xcontract1", "0xcontract2"}
        assert summary['unique_token_count'] == 2
        assert summary['unique_contract_count'] == 2

    @patch('src.exporters.csv_exporter.ensure_directory_exists')
    def test_logging_on_successful_export(self, mock_ensure_dir, csv_exporter, 
                                        sample_transaction, temp_dir, caplog):
        """Test that successful export logs appropriate message"""
        transactions = [sample_transaction]
        address = "0xtest"
        
        with caplog.at_level(logging.INFO):
            filepath = csv_exporter.export_transactions(transactions, address, False)
        
        assert "Exported 1 transactions to" in caplog.text
        assert filepath in caplog.text

    @patch('src.exporters.csv_exporter.ensure_directory_exists', side_effect=Exception("Test error"))
    def test_logging_on_export_error(self, mock_ensure_dir, csv_exporter, 
                                   sample_transaction, caplog):
        """Test that export errors are logged"""
        transactions = [sample_transaction]
        address = "0xtest"
        
        with caplog.at_level(logging.ERROR):
            with pytest.raises(Exception):
                csv_exporter.export_transactions(transactions, address, False)
        
        assert "Error exporting transactions: Test error" in caplog.text


class TestCSVExporterIntegration:
    """Integration tests for CSVExporter"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_full_export_workflow(self, temp_dir):
        """Test complete export workflow"""
        # Setup
        exporter = CSVExporter(output_directory=temp_dir)
        
        # Create test transactions
        transactions = [
            Transaction(
                hash="0xabc123", block_number=1000, 
                timestamp=datetime(2023, 1, 15, 12, 0, 0),
                from_address="0xfrom", to_address="0xto", value=Decimal("1.5"),
                gas_used=21000, gas_price=Decimal("20000000000"),
                transaction_fee=Decimal("0.00042"),
                status=TransactionStatus.SUCCESS, nonce=1, transaction_index=0,
                transaction_type=TransactionType.ETH_TRANSFER
            ),
            Transaction(
                hash="0xdef456", block_number=2000,
                timestamp=datetime(2023, 2, 20, 15, 30, 0),
                from_address="0xfrom2", to_address="0xto2", value=Decimal("100"),
                gas_used=50000, gas_price=Decimal("25000000000"),
                transaction_fee=Decimal("0.00125"),
                status=TransactionStatus.SUCCESS, nonce=2, transaction_index=1,
                transaction_type=TransactionType.ERC20_TRANSFER,
                contract_address="0xtoken", token_symbol="USDT"
            )
        ]
        
        address = "0x1234567890"
        
        # Export transactions
        with patch('src.exporters.csv_exporter.format_timestamp', return_value="20230315_120000"):
            filepath = exporter.export_transactions(transactions, address, True)
        
        # Verify file exists and has correct content
        assert os.path.exists(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['transaction_hash'] == "0xabc123"
        assert rows[1]['transaction_hash'] == "0xdef456"
        assert rows[1]['asset_symbol_name'] == "USDT"
        
        # Generate summary
        summary = exporter.export_summary(transactions, address)
        assert summary['total_transactions'] == 2
        assert summary['unique_token_count'] == 1
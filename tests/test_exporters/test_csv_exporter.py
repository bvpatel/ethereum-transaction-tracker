import pytest
import os
import tempfile
import csv
from unittest.mock import patch
from src.exporters.csv_exporter import CSVExporter

class TestCSVExporter:
    """Test CSV export functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def exporter(self, temp_dir):
        """Create CSV exporter with temp directory"""
        return CSVExporter(output_directory=temp_dir)

    def test_export_transactions_success(self, exporter, sample_transaction, temp_dir):
        """Test successful transaction export"""
        transactions = [sample_transaction]
        address = "0xa39b189482f984388a34460636fea9eb181ad1a6"
        
        filepath = exporter.export_transactions(transactions, address, include_timestamp=False)
        
        # Check file was created
        assert os.path.exists(filepath)
        
        # Check file contents
        with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            
            assert len(rows) == 1
            assert rows[0]['transaction_hash'] == sample_transaction.hash
            assert rows[0]['transaction_type'] == sample_transaction.transaction_type.value

    def test_export_empty_transactions(self, exporter):
        """Test export with empty transaction list"""
        transactions = []
        address = "0xa39b189482f984388a34460636fea9eb181ad1a6"
        
        filepath = exporter.export_transactions(transactions, address)
        
        # File should still be created with headers only
        assert os.path.exists(filepath)
        
        with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            assert len(rows) == 0

    def test_export_summary(self, exporter, sample_transaction):
        """Test transaction summary generation"""
        transactions = [sample_transaction]
        address = "0xa39b189482f984388a34460636fea9eb181ad1a6"
        
        summary = exporter.export_summary(transactions, address)
        
        assert summary['address'] == address
        assert summary['total_transactions'] == 1
        assert 'date_range' in summary
        assert 'transaction_types' in summary
        assert summary['transaction_types'][TransactionType.ETH_TRANSFER.value] == 1

    def test_filename_generation(self, exporter):
        """Test filename generation"""
        address = "0xa39b189482f984388a34460636fea9eb181ad1a6"
        
        # Without timestamp
        filename = exporter._generate_filename(address, include_timestamp=False)
        assert filename.startswith("0xa39b1894")
        assert filename.endswith(".csv")
        
        # With timestamp
        filename_with_ts = exporter._generate_filename(address, include_timestamp=True)
        assert "_" in filename_with_ts
        assert filename_with_ts.endswith(".csv")
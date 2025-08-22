"""
Tests for vendor_parser module.
"""

import pandas as pd
from src.vendor_parser import VendorQueryBuilder


class TestVendorQueryBuilder:
    """Test cases for VendorQueryBuilder class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.builder = VendorQueryBuilder()

    def test_init(self):
        """Test VendorQueryBuilder initialization."""
        assert isinstance(self.builder.vendor_patterns, dict)
        assert "cisco" in self.builder.vendor_patterns
        assert "palo_alto" in self.builder.vendor_patterns

    def test_add_vendor_pattern(self):
        """Test adding custom vendor patterns."""
        self.builder.add_vendor_pattern("test_vendor", ["test_pattern"])
        assert "test_vendor" in self.builder.vendor_patterns
        assert self.builder.vendor_patterns["test_vendor"] == ["test_pattern"]

    def test_build_basic_vendor_query(self):
        """Test basic vendor query generation."""
        indices = ["main", "security"]
        query = self.builder.build_basic_vendor_query(indices)

        assert "index=main OR index=security" in query
        assert "eval vendor_product = case(" in query
        assert "stats count by vendor_product" in query

    def test_extract_vendor_products_empty(self):
        """Test extracting vendor products from empty DataFrame."""
        empty_df = pd.DataFrame()
        result = self.builder.extract_vendor_products(empty_df)
        assert result.empty

    def test_extract_vendor_products_valid(self):
        """Test extracting vendor products from valid DataFrame."""
        test_data = pd.DataFrame(
            {"vendor_product": ["Cisco", "Palo Alto"], "count": [100, 50]}
        )

        result = self.builder.extract_vendor_products(test_data)

        assert not result.empty
        assert "percentage" in result.columns
        assert "category" in result.columns
        assert result.iloc[0]["vendor_product"] == "Cisco"

    def test_identify_coverage_gaps_empty(self):
        """Test gap analysis with empty data."""
        empty_df = pd.DataFrame()
        expected_vendors = ["Cisco", "Palo Alto"]

        result = self.builder.identify_coverage_gaps(empty_df, expected_vendors)

        assert not result.empty
        assert len(result) == 2
        assert all(result["status"] == "Missing")

    def test_classify_vendor_category(self):
        """Test vendor category classification."""
        assert self.builder._classify_vendor_category("Cisco") == "Network Security"
        assert self.builder._classify_vendor_category("Microsoft") == "Microsoft"
        assert self.builder._classify_vendor_category("Unknown Vendor") == "Other"

    def test_generate_summary_stats_empty(self):
        """Test summary statistics with empty data."""
        empty_df = pd.DataFrame()
        stats = self.builder.generate_summary_stats(empty_df)

        assert stats["total_vendors"] == 0
        assert stats["total_events"] == 0
        assert stats["top_vendor"] == "None"

    def test_generate_summary_stats_valid(self):
        """Test summary statistics with valid data."""
        test_data = pd.DataFrame(
            {"vendor_product": ["Cisco", "Palo Alto"], "count": [100, 50]}
        )

        # Process data through extract_vendor_products to get required columns
        processed_data = self.builder.extract_vendor_products(test_data)
        stats = self.builder.generate_summary_stats(processed_data)

        assert stats["total_vendors"] == 2
        assert stats["total_events"] == 150
        assert stats["top_vendor"] == "Cisco"

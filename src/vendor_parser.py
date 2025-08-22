"""
Vendor Query Parser for custom SPL query generation and vendor product identification.
"""

import pandas as pd
from typing import List, Dict, Any, Optional


class VendorQueryBuilder:
    """Builder for custom SPL queries to identify vendor products."""

    def __init__(self):
        """Initialize the query builder with common vendor patterns."""
        self.vendor_patterns = {
            "cisco": [
                r"cisco",
                r"asa-",
                r"%asa-",
                r"catalyst",
                r"nexus",
                r"ios",
                r"nxos",
            ],
            "palo_alto": [r"palo.*alto", r"panos", r"pa-\d+", r"globalprotect"],
            "fortinet": [r"fortinet", r"fortigate", r"fortios", r"fortianalyzer"],
            "checkpoint": [r"check.*point", r"checkpoint", r"gaia", r"splat"],
            "juniper": [r"juniper", r"junos", r"srx", r"mx\d+", r"ex\d+"],
            "f5": [r"\bf5\b", r"big-?ip", r"ltm", r"asm", r"apm"],
            "microsoft": [
                r"microsoft",
                r"windows",
                r"azure",
                r"office365",
                r"exchange",
            ],
            "vmware": [r"vmware", r"vsphere", r"vcenter", r"esxi"],
            "splunk": [r"splunk", r"splunkd", r"universal.*forwarder"],
            "aws": [r"amazon.*web.*services", r"\baws\b", r"ec2", r"cloudtrail"],
        }

    def add_vendor_pattern(self, vendor_name: str, patterns: List[str]):
        """
        Add custom vendor patterns.

        Args:
            vendor_name: Name of the vendor
            patterns: List of regex patterns to identify the vendor
        """
        self.vendor_patterns[vendor_name] = patterns

    def build_basic_vendor_query(
        self, indices: List[str], time_range: str = "-24h@h"
    ) -> str:
        """
        Build a basic vendor identification query.

        Args:
            indices: List of Splunk indices to search
            time_range: Time range for the search

        Returns:
            SPL query string
        """
        index_clause = " OR ".join([f"index={idx}" for idx in indices])

        vendor_cases = []
        for vendor, patterns in self.vendor_patterns.items():
            pattern_conditions = " OR ".join(
                [f'match(_raw, "(?i){pattern}")' for pattern in patterns]
            )
            vendor_cases.append(
                f'({pattern_conditions}), "{vendor.replace("_", " ").title()}"'
            )

        vendor_case_clause = ",\n    ".join(vendor_cases)

        query = f"""search {index_clause} earliest={time_range}
| eval vendor_product = case(
    {vendor_case_clause},
    1==1, "Unknown"
)
| where vendor_product != "Unknown"
| stats count by vendor_product, sourcetype, index
| sort -count"""

        return query

    def build_custom_query(
        self,
        indices: List[str],
        custom_patterns: Dict[str, List[str]],
        time_range: str = "-24h@h",
        additional_filters: Optional[str] = None,
    ) -> str:
        """
        Build a custom SPL query with user-defined patterns.

        Args:
            indices: List of Splunk indices to search
            custom_patterns: Custom vendor patterns dict
            time_range: Time range for the search
            additional_filters: Additional SPL filters

        Returns:
            SPL query string
        """
        index_clause = " OR ".join([f"index={idx}" for idx in indices])

        # Merge default and custom patterns
        all_patterns = {**self.vendor_patterns, **custom_patterns}

        vendor_cases = []
        for vendor, patterns in all_patterns.items():
            pattern_conditions = " OR ".join(
                [f'match(_raw, "(?i){pattern}")' for pattern in patterns]
            )
            vendor_cases.append(
                f'({pattern_conditions}), "{vendor.replace("_", " ").title()}"'
            )

        vendor_case_clause = ",\n    ".join(vendor_cases)

        query = f"""search {index_clause} earliest={time_range}"""

        if additional_filters:
            query += f" {additional_filters}"

        query += f"""
| eval vendor_product = case(
    {vendor_case_clause},
    1==1, "Unknown"
)
| where vendor_product != "Unknown"
| eval host_clean = if(isnull(host), "unknown_host", host)
| stats count by vendor_product, sourcetype, index, host_clean
| sort vendor_product, -count"""

        return query

    def build_gap_analysis_query(
        self, indices: List[str], expected_vendors: List[str], time_range: str = "-7d@d"
    ) -> str:
        """
        Build a query specifically for gap analysis.

        Args:
            indices: List of Splunk indices to search
            expected_vendors: List of vendors expected to be present
            time_range: Time range for analysis

        Returns:
            SPL query for gap analysis
        """
        index_clause = " OR ".join([f"index={idx}" for idx in indices])

        # Filter patterns to only expected vendors
        filtered_patterns = {
            k: v
            for k, v in self.vendor_patterns.items()
            if k.replace("_", " ").title() in expected_vendors
        }

        vendor_cases = []
        for vendor, patterns in filtered_patterns.items():
            pattern_conditions = " OR ".join(
                [f'match(_raw, "(?i){pattern}")' for pattern in patterns]
            )
            vendor_cases.append(
                f'({pattern_conditions}), "{vendor.replace("_", " ").title()}"'
            )

        vendor_case_clause = ",\n    ".join(vendor_cases)

        query = f"""search {index_clause} earliest={time_range} latest=now
| eval vendor_product = case(
    {vendor_case_clause},
    1==1, "Unknown"
)
| stats count by vendor_product, index
| eval present = if(vendor_product="Unknown", 0, 1)
| stats sum(count) as event_count, max(present) as is_present by vendor_product, index
| where vendor_product != "Unknown"
| sort vendor_product, index"""

        return query

    def extract_vendor_products(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Extract and normalize vendor product data from raw Splunk results.

        Args:
            raw_data: Raw DataFrame from Splunk query

        Returns:
            Processed DataFrame with vendor information
        """
        if raw_data.empty:
            return pd.DataFrame()

        # Normalize column names
        df = raw_data.copy()

        # Ensure required columns exist
        required_cols = ["vendor_product", "count"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = "Unknown" if col == "vendor_product" else 0

        # Convert count to numeric
        df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0)

        # Add percentage calculation
        total_events = df["count"].sum()
        df["percentage"] = (
            (df["count"] / total_events * 100).round(2) if total_events > 0 else 0
        )

        # Add category classification
        df["category"] = df["vendor_product"].apply(self._classify_vendor_category)

        return df.sort_values("count", ascending=False)

    def identify_coverage_gaps(
        self, vendor_data: pd.DataFrame, expected_vendors: List[str]
    ) -> pd.DataFrame:
        """
        Identify coverage gaps based on expected vendors.

        Args:
            vendor_data: DataFrame with vendor product data
            expected_vendors: List of expected vendor names

        Returns:
            DataFrame with gap analysis
        """
        if vendor_data.empty:
            # All vendors are missing
            gap_data = []
            for vendor in expected_vendors:
                gap_data.append(
                    {
                        "vendor_product": vendor,
                        "status": "Missing",
                        "event_count": 0,
                        "percentage": 0.0,
                        "gap_severity": "High",
                    }
                )
            return pd.DataFrame(gap_data)

        # Normalize vendor names for comparison
        present_vendors = set(vendor_data["vendor_product"].str.lower())

        gap_analysis = []

        for expected_vendor in expected_vendors:
            vendor_lower = expected_vendor.lower()

            if vendor_lower in present_vendors:
                # Vendor is present
                vendor_row = vendor_data[
                    vendor_data["vendor_product"].str.lower() == vendor_lower
                ].iloc[0]
                gap_analysis.append(
                    {
                        "vendor_product": expected_vendor,
                        "status": "Present",
                        "event_count": int(vendor_row["count"]),
                        "percentage": float(vendor_row.get("percentage", 0)),
                        "gap_severity": self._assess_gap_severity(
                            vendor_row["count"], vendor_data["count"].sum()
                        ),
                    }
                )
            else:
                # Vendor is missing
                gap_analysis.append(
                    {
                        "vendor_product": expected_vendor,
                        "status": "Missing",
                        "event_count": 0,
                        "percentage": 0.0,
                        "gap_severity": "High",
                    }
                )

        return pd.DataFrame(gap_analysis)

    def _classify_vendor_category(self, vendor_name: str) -> str:
        """Classify vendor into categories."""
        vendor_lower = vendor_name.lower()

        if any(
            term in vendor_lower
            for term in ["cisco", "juniper", "palo alto", "fortinet", "checkpoint"]
        ):
            return "Network Security"
        elif any(term in vendor_lower for term in ["f5", "nginx", "haproxy"]):
            return "Load Balancer"
        elif any(term in vendor_lower for term in ["microsoft", "windows", "azure"]):
            return "Microsoft"
        elif any(term in vendor_lower for term in ["vmware", "vsphere"]):
            return "Virtualization"
        elif any(term in vendor_lower for term in ["aws", "amazon"]):
            return "Cloud - AWS"
        elif any(term in vendor_lower for term in ["splunk"]):
            return "SIEM/Logging"
        else:
            return "Other"

    def _assess_gap_severity(self, vendor_count: int, total_count: int) -> str:
        """Assess gap severity based on event volume."""
        if vendor_count == 0:
            return "High"

        percentage = (vendor_count / total_count) * 100

        if percentage < 1:
            return "Medium"
        elif percentage < 5:
            return "Low"
        else:
            return "None"

    def generate_summary_stats(self, vendor_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics for vendor data.

        Args:
            vendor_data: DataFrame with vendor information

        Returns:
            Dictionary with summary statistics
        """
        if vendor_data.empty:
            return {
                "total_vendors": 0,
                "total_events": 0,
                "top_vendor": "None",
                "categories": {},
                "missing_data_percentage": 100.0,
            }

        total_events = vendor_data["count"].sum()
        category_stats = vendor_data.groupby("category")["count"].sum().to_dict()

        return {
            "total_vendors": len(vendor_data),
            "total_events": int(total_events),
            "top_vendor": (
                vendor_data.iloc[0]["vendor_product"]
                if not vendor_data.empty
                else "None"
            ),
            "top_vendor_count": (
                int(vendor_data.iloc[0]["count"]) if not vendor_data.empty else 0
            ),
            "categories": category_stats,
            "unknown_percentage": vendor_data[
                vendor_data["vendor_product"] == "Unknown"
            ]["percentage"].sum(),
        }

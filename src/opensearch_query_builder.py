"""
OpenSearch Query Builder for vendor product identification and analysis.
Translates Splunk SPL logic to OpenSearch Query DSL.
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class OpenSearchQueryBuilder:
    """Builder for OpenSearch queries to identify vendor products."""

    def __init__(self):
        """Initialize the query builder with vendor patterns from Splunk implementation."""
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

        # Field mappings for different log formats
        self.field_mappings = {
            "message_fields": ["message", "log", "event.original", "_raw"],
            "timestamp_field": "@timestamp",
            "host_field": "host",
            "index_field": "_index"
        }

    def add_vendor_pattern(self, vendor_name: str, patterns: List[str]):
        """
        Add custom vendor patterns.

        Args:
            vendor_name: Name of the vendor
            patterns: List of regex patterns to identify the vendor
        """
        self.vendor_patterns[vendor_name] = patterns

    def _get_time_range_query(self, time_range: str) -> Dict[str, Any]:
        """
        Convert Splunk time range to OpenSearch time query.

        Args:
            time_range: Time range (e.g., '-24h@h', '-7d@d')

        Returns:
            OpenSearch time range query
        """
        now = datetime.utcnow()
        
        # Parse Splunk-style time ranges
        if time_range.startswith('-'):
            time_part = time_range[1:]  # Remove leading dash
            
            if '@' in time_part:
                duration, snap = time_part.split('@', 1)
            else:
                duration = time_part
                snap = None
            
            # Parse duration
            if duration.endswith('h'):
                hours = int(duration[:-1])
                start_time = now - timedelta(hours=hours)
            elif duration.endswith('d'):
                days = int(duration[:-1])
                start_time = now - timedelta(days=days)
            elif duration.endswith('m'):
                minutes = int(duration[:-1])
                start_time = now - timedelta(minutes=minutes)
            elif duration.endswith('s'):
                seconds = int(duration[:-1])
                start_time = now - timedelta(seconds=seconds)
            else:
                # Default to hours
                start_time = now - timedelta(hours=24)
            
            # Apply snap-to if specified
            if snap == 'h':
                start_time = start_time.replace(minute=0, second=0, microsecond=0)
            elif snap == 'd':
                start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            
            return {
                "range": {
                    self.field_mappings["timestamp_field"]: {
                        "gte": start_time.isoformat() + "Z",
                        "lte": now.isoformat() + "Z"
                    }
                }
            }
        
        # Default to last 24 hours
        start_time = now - timedelta(hours=24)
        return {
            "range": {
                self.field_mappings["timestamp_field"]: {
                    "gte": start_time.isoformat() + "Z",
                    "lte": now.isoformat() + "Z"
                }
            }
        }

    def _create_vendor_detection_script(self) -> str:
        """
        Create Painless script for vendor detection.

        Returns:
            Painless script as string
        """
        script_lines = []
        script_lines.append("String message = '';")
        
        # Try different message fields
        for field in self.field_mappings["message_fields"]:
            script_lines.append(f"if (doc['{field}.keyword'].size() > 0) {{")
            script_lines.append(f"    message = doc['{field}.keyword'].value.toLowerCase();")
            script_lines.append("} else if (doc['message'].size() > 0) {")
            script_lines.append("    message = doc['message'].value.toLowerCase();")
            script_lines.append("}")
        
        # Add vendor detection logic
        for vendor, patterns in self.vendor_patterns.items():
            vendor_name = vendor.replace("_", " ").title()
            
            conditions = []
            for pattern in patterns:
                # Convert regex to simple contains check for better performance
                simple_pattern = pattern.replace(r"\b", "").replace(r"\d+", "").replace(".*", "").replace(r"\\", "")
                if simple_pattern and len(simple_pattern) > 2:
                    conditions.append(f"message.contains('{simple_pattern.lower()}')")
            
            if conditions:
                condition_str = " || ".join(conditions)
                script_lines.append(f"if ({condition_str}) return '{vendor_name}';")
        
        script_lines.append("return 'Unknown';")
        
        return " ".join(script_lines)

    def build_basic_vendor_query(
        self, index_patterns: List[str], time_range: str = "-24h@h"
    ) -> Dict[str, Any]:
        """
        Build a basic vendor identification query.

        Args:
            index_patterns: List of OpenSearch index patterns to search
            time_range: Time range for the search

        Returns:
            OpenSearch query dictionary
        """
        index_pattern = ",".join(index_patterns)
        
        query = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        self._get_time_range_query(time_range)
                    ]
                }
            },
            "aggs": {
                "vendor_products": {
                    "terms": {
                        "script": {
                            "source": self._create_vendor_detection_script()
                        },
                        "size": 50
                    },
                    "aggs": {
                        "by_index": {
                            "terms": {
                                "field": "_index",
                                "size": 10
                            }
                        },
                        "sample_logs": {
                            "top_hits": {
                                "size": 3,
                                "_source": {
                                    "includes": ["message", "@timestamp", "host"]
                                }
                            }
                        }
                    }
                }
            }
        }
        
        return query

    def build_term_based_vendor_query(
        self, index_patterns: List[str], time_range: str = "-24h@h"
    ) -> Dict[str, Any]:
        """
        Build a term-based vendor query for better performance.
        Uses pre-indexed vendor field if available.

        Args:
            index_patterns: List of OpenSearch index patterns
            time_range: Time range for the search

        Returns:
            OpenSearch query dictionary
        """
        query = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        self._get_time_range_query(time_range)
                    ]
                }
            },
            "aggs": {
                "vendor_products": {
                    "terms": {
                        "field": "vendor",
                        "size": 50,
                        "missing": "Unknown"
                    },
                    "aggs": {
                        "by_index": {
                            "terms": {
                                "field": "_index",
                                "size": 10
                            }
                        },
                        "by_host": {
                            "terms": {
                                "field": "host",
                                "size": 20
                            }
                        }
                    }
                }
            }
        }
        
        return query

    def build_gap_analysis_query(
        self, index_patterns: List[str], expected_vendors: List[str], 
        time_range: str = "-7d@d"
    ) -> Dict[str, Any]:
        """
        Build a query specifically for gap analysis.

        Args:
            index_patterns: List of OpenSearch index patterns
            expected_vendors: List of vendors expected to be present
            time_range: Time range for analysis

        Returns:
            OpenSearch query for gap analysis
        """
        # Filter patterns to only expected vendors
        expected_patterns = {}
        for vendor, patterns in self.vendor_patterns.items():
            vendor_display = vendor.replace("_", " ").title()
            if vendor_display in expected_vendors:
                expected_patterns[vendor] = patterns

        # Create script that only detects expected vendors
        script_lines = []
        script_lines.append("String message = '';")
        script_lines.append("if (doc['message.keyword'].size() > 0) {")
        script_lines.append("    message = doc['message.keyword'].value.toLowerCase();")
        script_lines.append("}")
        
        for vendor, patterns in expected_patterns.items():
            vendor_name = vendor.replace("_", " ").title()
            conditions = []
            for pattern in patterns:
                simple_pattern = pattern.replace(r"\b", "").replace(r"\d+", "").replace(".*", "").replace(r"\\", "")
                if simple_pattern and len(simple_pattern) > 2:
                    conditions.append(f"message.contains('{simple_pattern.lower()}')")
            
            if conditions:
                condition_str = " || ".join(conditions)
                script_lines.append(f"if ({condition_str}) return '{vendor_name}';")
        
        script_lines.append("return 'Unknown';")
        gap_script = " ".join(script_lines)

        query = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        self._get_time_range_query(time_range)
                    ]
                }
            },
            "aggs": {
                "vendor_presence": {
                    "terms": {
                        "script": {
                            "source": gap_script
                        },
                        "size": len(expected_vendors) + 5
                    },
                    "aggs": {
                        "by_index": {
                            "terms": {
                                "field": "_index",
                                "size": 10
                            }
                        }
                    }
                },
                "total_events": {
                    "value_count": {
                        "field": "@timestamp"
                    }
                }
            }
        }
        
        return query

    def build_custom_query(
        self,
        query_body: str,
        index_patterns: List[str],
        time_range: str = "-24h@h"
    ) -> Dict[str, Any]:
        """
        Build a custom OpenSearch query from user input.

        Args:
            query_body: Custom query string or JSON
            index_patterns: List of index patterns
            time_range: Time range for the search

        Returns:
            OpenSearch query dictionary
        """
        try:
            # Try to parse as JSON first
            if query_body.strip().startswith('{'):
                import json
                custom_query = json.loads(query_body)
                
                # Add time range if not present
                if "query" not in custom_query:
                    custom_query["query"] = {"match_all": {}}
                
                if "bool" not in custom_query["query"]:
                    original_query = custom_query["query"]
                    custom_query["query"] = {
                        "bool": {
                            "must": [
                                original_query,
                                self._get_time_range_query(time_range)
                            ]
                        }
                    }
                else:
                    if "must" not in custom_query["query"]["bool"]:
                        custom_query["query"]["bool"]["must"] = []
                    custom_query["query"]["bool"]["must"].append(self._get_time_range_query(time_range))
                
                return custom_query
            
            else:
                # Simple string query
                return {
                    "size": 100,
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "simple_query_string": {
                                        "query": query_body,
                                        "fields": self.field_mappings["message_fields"],
                                        "default_operator": "and"
                                    }
                                },
                                self._get_time_range_query(time_range)
                            ]
                        }
                    },
                    "sort": [
                        {"@timestamp": {"order": "desc"}}
                    ]
                }
                
        except Exception as e:
            # Fallback to simple query
            return {
                "size": 100,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "message": query_body
                                }
                            },
                            self._get_time_range_query(time_range)
                        ]
                    }
                },
                "sort": [
                    {"@timestamp": {"order": "desc"}}
                ]
            }

    def extract_vendor_products(self, aggregation_response: Dict[str, Any]) -> pd.DataFrame:
        """
        Extract vendor product data from OpenSearch aggregation response.

        Args:
            aggregation_response: Response from aggregation query

        Returns:
            Processed DataFrame with vendor information
        """
        if not aggregation_response or "aggregations" not in aggregation_response:
            return pd.DataFrame()

        aggs = aggregation_response["aggregations"]
        vendor_agg = aggs.get("vendor_products", {})
        
        if "buckets" not in vendor_agg:
            return pd.DataFrame()

        records = []
        total_events = sum(bucket["doc_count"] for bucket in vendor_agg["buckets"])

        for bucket in vendor_agg["buckets"]:
            vendor_product = bucket["key"]
            count = bucket["doc_count"]
            percentage = (count / total_events * 100) if total_events > 0 else 0

            # Extract index breakdown
            indices = []
            if "by_index" in bucket:
                indices = [idx_bucket["key"] for idx_bucket in bucket["by_index"]["buckets"]]

            # Extract sample sourcetypes (use index as proxy)
            sourcetypes = indices[:3] if indices else ["unknown"]

            record = {
                "vendor_product": vendor_product,
                "count": count,
                "percentage": round(percentage, 2),
                "category": self._classify_vendor_category(vendor_product),
                "sourcetype": sourcetypes[0] if sourcetypes else "unknown",
                "index": ",".join(indices[:3]) if indices else "unknown"
            }
            records.append(record)

        df = pd.DataFrame(records)
        return df.sort_values("count", ascending=False) if not df.empty else df

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
                gap_data.append({
                    "vendor_product": vendor,
                    "status": "Missing",
                    "event_count": 0,
                    "percentage": 0.0,
                    "gap_severity": "High",
                })
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
                gap_analysis.append({
                    "vendor_product": expected_vendor,
                    "status": "Present",
                    "event_count": int(vendor_row["count"]),
                    "percentage": float(vendor_row.get("percentage", 0)),
                    "gap_severity": self._assess_gap_severity(
                        vendor_row["count"], vendor_data["count"].sum()
                    ),
                })
            else:
                # Vendor is missing
                gap_analysis.append({
                    "vendor_product": expected_vendor,
                    "status": "Missing",
                    "event_count": 0,
                    "percentage": 0.0,
                    "gap_severity": "High",
                })

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
                "top_vendor_count": 0,
                "categories": {},
                "unknown_percentage": 100.0,
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
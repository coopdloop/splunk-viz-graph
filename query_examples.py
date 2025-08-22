#!/usr/bin/env python3
"""
Generate raw OpenSearch queries for Dev Tools usage.
Run this to get query JSON that you can copy/paste into OpenSearch Dashboards Dev Tools.
"""

import json
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))
from opensearch_query_builder import OpenSearchQueryBuilder

def print_query(title, query_dict):
    """Print a formatted query for Dev Tools."""
    print(f"\n# {title}")
    print("# Copy the JSON below and paste into OpenSearch Dev Tools")
    print("# URL: http://localhost:5601/app/dev_tools#/console")
    print("-" * 60)
    print(f"GET /logs-*/_search")
    print(json.dumps(query_dict, indent=2))
    print("-" * 60)

def main():
    """Generate example queries."""
    builder = OpenSearchQueryBuilder()
    
    print("🔍 OpenSearch Query Generator")
    print("=" * 60)
    print("Use these queries in OpenSearch Dashboards Dev Tools")
    print("Access Dev Tools at: http://localhost:5601/app/dev_tools#/console")
    
    # 1. Basic vendor detection (term-based)
    basic_query = builder.build_term_based_vendor_query(["logs-*"], "-24h@h")
    print_query("Basic Vendor Detection (Fast)", basic_query)
    
    # 2. Script-based vendor detection  
    script_query = builder.build_basic_vendor_query(["logs-*"], "-24h@h")
    print_query("Script-based Vendor Detection (Flexible)", script_query)
    
    # 3. Gap analysis query
    expected_vendors = ["Cisco", "Palo Alto", "Fortinet", "Checkpoint", "Juniper", "F5", "Microsoft", "Vmware", "Aws"]
    gap_query = builder.build_gap_analysis_query(["logs-*"], expected_vendors, "-7d@d")
    print_query("Gap Analysis Query", gap_query)
    
    # 4. Simple aggregation query
    simple_agg = {
        "size": 0,
        "query": {
            "range": {
                "@timestamp": {
                    "gte": "now-24h"
                }
            }
        },
        "aggs": {
            "vendors": {
                "terms": {
                    "field": "vendor",
                    "size": 20
                }
            },
            "top_messages": {
                "top_hits": {
                    "size": 5,
                    "_source": ["vendor", "message", "@timestamp"]
                }
            }
        }
    }
    print_query("Simple Vendor Aggregation", simple_agg)
    
    # 5. Custom time range example
    custom_time = {
        "size": 10,
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": "2025-08-22T00:00:00Z",
                                "lte": "2025-08-22T23:59:59Z"
                            }
                        }
                    },
                    {
                        "term": {
                            "vendor": "Cisco"
                        }
                    }
                ]
            }
        },
        "sort": [
            {"@timestamp": {"order": "desc"}}
        ]
    }
    print_query("Custom Time Range - Cisco Only", custom_time)
    
    print(f"\n🎯 Quick Usage Tips:")
    print("1. Copy any query JSON from above")
    print("2. Open http://localhost:5601/app/dev_tools#/console")
    print("3. Paste the query (starting with GET)")
    print("4. Click the ▶️ button or press Ctrl+Enter")
    print("5. View results in the right panel")

if __name__ == "__main__":
    main()
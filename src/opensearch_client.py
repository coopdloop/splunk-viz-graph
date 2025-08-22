"""
OpenSearch Client for authentication and query execution.
"""

import json
import pandas as pd
from typing import Dict, Optional, Any, List
import time
from opensearchpy import OpenSearch
from opensearchpy.exceptions import ConnectionError, RequestError, NotFoundError
import boto3
from opensearchpy import AWSV4SignerAuth, RequestsHttpConnection


class OpenSearchClient:
    """Client for connecting to OpenSearch with various authentication methods."""

    def __init__(
        self,
        base_url: str,
        auth_type: str = "basic",
        username: str = None,
        password: str = None,
        api_key: str = None,
        client_cert: str = None,
        client_key: str = None,
        ca_certs: str = None,
        aws_region: str = None,
        verify_ssl: bool = True,
    ):
        """
        Initialize OpenSearch client.

        Args:
            base_url: OpenSearch cluster endpoint URL
            auth_type: Authentication type ('basic', 'api_key', 'client_cert', 'aws_iam')
            username: Username for basic auth
            password: Password for basic auth
            api_key: API key for API key auth
            client_cert: Path to client certificate file
            client_key: Path to client private key file
            ca_certs: Path to CA certificates file
            aws_region: AWS region for IAM auth
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip("/")
        self.auth_type = auth_type
        self.verify_ssl = verify_ssl
        
        # Parse host and port from URL
        if "://" in base_url:
            protocol, host_port = base_url.split("://", 1)
            self.use_ssl = protocol == "https"
        else:
            host_port = base_url
            self.use_ssl = verify_ssl
            
        if ":" in host_port:
            self.host, port_str = host_port.split(":", 1)
            self.port = int(port_str.split("/")[0])  # Remove any path
        else:
            self.host = host_port
            self.port = 443 if self.use_ssl else 9200

        # Initialize client based on auth type
        self.client = self._create_client(
            username, password, api_key, client_cert, client_key, 
            ca_certs, aws_region
        )

    def _create_client(
        self, username: str, password: str, api_key: str, 
        client_cert: str, client_key: str, ca_certs: str, aws_region: str
    ) -> OpenSearch:
        """Create OpenSearch client with appropriate authentication."""
        
        host_config = {"host": self.host, "port": self.port}
        
        if self.auth_type == "basic":
            if not username or not password:
                raise ValueError("Username and password required for basic auth")
                
            return OpenSearch(
                hosts=[host_config],
                http_auth=(username, password),
                use_ssl=self.use_ssl,
                verify_certs=self.verify_ssl,
                ssl_assert_hostname=False,
                ssl_show_warn=False,
            )
            
        elif self.auth_type == "api_key":
            if not api_key:
                raise ValueError("API key required for API key auth")
                
            return OpenSearch(
                hosts=[host_config],
                headers={"Authorization": f"ApiKey {api_key}"},
                use_ssl=self.use_ssl,
                verify_certs=self.verify_ssl,
                ssl_assert_hostname=False,
                ssl_show_warn=False,
            )
            
        elif self.auth_type == "client_cert":
            if not client_cert or not client_key:
                raise ValueError("Client cert and key required for client cert auth")
                
            return OpenSearch(
                hosts=[host_config],
                client_cert=client_cert,
                client_key=client_key,
                ca_certs=ca_certs,
                use_ssl=True,
                verify_certs=self.verify_ssl,
                ssl_assert_hostname=False,
                ssl_show_warn=False,
            )
            
        elif self.auth_type == "aws_iam":
            if not aws_region:
                raise ValueError("AWS region required for IAM auth")
                
            credentials = boto3.Session().get_credentials()
            auth = AWSV4SignerAuth(credentials, aws_region, "es")
            
            return OpenSearch(
                hosts=[host_config],
                http_auth=auth,
                use_ssl=True,
                verify_certs=self.verify_ssl,
                connection_class=RequestsHttpConnection,
                ssl_assert_hostname=False,
                ssl_show_warn=False,
            )
            
        else:
            # No authentication
            return OpenSearch(
                hosts=[host_config],
                use_ssl=self.use_ssl,
                verify_certs=self.verify_ssl,
                ssl_assert_hostname=False,
                ssl_show_warn=False,
            )

    def validate_connection(self) -> Dict[str, Any]:
        """
        Validate the OpenSearch connection.

        Returns:
            Dictionary with validation results
        """
        try:
            health = self.client.cluster.health()
            
            return {
                "valid": True,
                "status": health["status"],
                "cluster_name": health["cluster_name"],
                "number_of_nodes": health["number_of_nodes"],
                "message": f"Connected to {health['cluster_name']} ({health['status']})"
            }
            
        except ConnectionError as e:
            return {
                "valid": False,
                "message": f"Connection failed: {str(e)}",
                "error_type": "connection"
            }
        except Exception as e:
            return {
                "valid": False,
                "message": f"Validation failed: {str(e)}",
                "error_type": "unknown"
            }

    def execute_query(self, query: Dict[str, Any], index: str = "_all") -> pd.DataFrame:
        """
        Execute a query and return results as DataFrame.

        Args:
            query: OpenSearch query dictionary
            index: Index pattern to search

        Returns:
            DataFrame with query results
        """
        try:
            response = self.client.search(
                body=query,
                index=index,
                timeout=120
            )
            
            # Extract hits
            hits = response.get("hits", {}).get("hits", [])
            
            if not hits:
                return pd.DataFrame()
            
            # Convert to DataFrame
            records = []
            for hit in hits:
                record = hit["_source"]
                record["_index"] = hit["_index"]
                record["_score"] = hit["_score"]
                records.append(record)
            
            return pd.DataFrame(records)
            
        except RequestError as e:
            raise Exception(f"Query execution failed: {e.error}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")

    def execute_aggregation_query(self, query: Dict[str, Any], index: str = "_all") -> pd.DataFrame:
        """
        Execute an aggregation query and return results as DataFrame.

        Args:
            query: OpenSearch aggregation query
            index: Index pattern to search

        Returns:
            DataFrame with aggregation results
        """
        try:
            response = self.client.search(
                body=query,
                index=index,
                timeout=120
            )
            
            # Extract aggregations
            aggregations = response.get("aggregations", {})
            
            if not aggregations:
                return pd.DataFrame()
            
            # Process aggregation results
            records = []
            
            # Handle different aggregation types
            for agg_name, agg_data in aggregations.items():
                if "buckets" in agg_data:
                    # Terms aggregation
                    for bucket in agg_data["buckets"]:
                        record = {
                            agg_name: bucket["key"],
                            "count": bucket["doc_count"]
                        }
                        # Add nested aggregations
                        for nested_name, nested_data in bucket.items():
                            if nested_name not in ["key", "doc_count"] and isinstance(nested_data, dict):
                                if "value" in nested_data:
                                    record[nested_name] = nested_data["value"]
                                elif "buckets" in nested_data:
                                    # Handle nested terms
                                    record[nested_name] = nested_data["buckets"]
                        records.append(record)
                        
                elif "value" in agg_data:
                    # Metric aggregation
                    records.append({
                        agg_name: agg_data["value"]
                    })
            
            return pd.DataFrame(records) if records else pd.DataFrame()
            
        except RequestError as e:
            raise Exception(f"Aggregation query failed: {e.error}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")

    def scroll_search(self, query: Dict[str, Any], index: str = "_all", 
                     scroll_size: int = 1000, max_results: int = 10000) -> pd.DataFrame:
        """
        Execute a scrolling search for large result sets.

        Args:
            query: OpenSearch query dictionary
            index: Index pattern to search
            scroll_size: Number of results per scroll
            max_results: Maximum number of results to return

        Returns:
            DataFrame with all results
        """
        try:
            # Initialize scroll
            query["size"] = scroll_size
            
            response = self.client.search(
                body=query,
                index=index,
                scroll="120s",
                timeout=120
            )
            
            scroll_id = response["_scroll_id"]
            hits = response["hits"]["hits"]
            
            all_records = []
            
            # Process initial batch
            for hit in hits:
                record = hit["_source"]
                record["_index"] = hit["_index"]
                record["_score"] = hit["_score"]
                all_records.append(record)
            
            # Continue scrolling
            while len(hits) > 0 and len(all_records) < max_results:
                try:
                    response = self.client.scroll(
                        scroll_id=scroll_id,
                        scroll="120s"
                    )
                    
                    scroll_id = response["_scroll_id"]
                    hits = response["hits"]["hits"]
                    
                    for hit in hits:
                        if len(all_records) >= max_results:
                            break
                        record = hit["_source"]
                        record["_index"] = hit["_index"]
                        record["_score"] = hit["_score"]
                        all_records.append(record)
                        
                except Exception as e:
                    print(f"Scroll error: {e}")
                    break
            
            # Clear scroll
            try:
                self.client.clear_scroll(scroll_id=scroll_id)
            except:
                pass
            
            return pd.DataFrame(all_records) if all_records else pd.DataFrame()
            
        except RequestError as e:
            raise Exception(f"Scroll search failed: {e.error}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")

    def get_indices(self, pattern: str = "*") -> List[str]:
        """
        Get list of available indices.

        Args:
            pattern: Index pattern to match

        Returns:
            List of index names
        """
        try:
            response = self.client.cat.indices(index=pattern, format="json")
            return [idx["index"] for idx in response]
        except Exception as e:
            print(f"Failed to get indices: {e}")
            return []

    def get_field_mapping(self, index: str) -> Dict[str, Any]:
        """
        Get field mapping for an index.

        Args:
            index: Index name or pattern

        Returns:
            Field mapping dictionary
        """
        try:
            response = self.client.indices.get_mapping(index=index)
            
            mappings = {}
            for idx_name, idx_data in response.items():
                idx_mappings = idx_data.get("mappings", {}).get("properties", {})
                mappings[idx_name] = idx_mappings
                
            return mappings
            
        except NotFoundError:
            return {}
        except Exception as e:
            print(f"Failed to get field mapping: {e}")
            return {}

    def paginate_results(self, query: Dict[str, Any], index: str = "_all",
                        page_size: int = 1000, max_results: int = 10000) -> pd.DataFrame:
        """
        Paginate through query results using search_after.

        Args:
            query: OpenSearch query dictionary
            index: Index pattern to search
            page_size: Results per page
            max_results: Maximum results to return

        Returns:
            Combined DataFrame with all results
        """
        try:
            # Ensure sort is specified for pagination
            if "sort" not in query:
                query["sort"] = [{"@timestamp": {"order": "desc"}}]
            
            query["size"] = min(page_size, max_results)
            
            all_records = []
            search_after = None
            
            while len(all_records) < max_results:
                if search_after:
                    query["search_after"] = search_after
                
                response = self.client.search(
                    body=query,
                    index=index,
                    timeout=120
                )
                
                hits = response.get("hits", {}).get("hits", [])
                
                if not hits:
                    break
                
                # Process hits
                for hit in hits:
                    if len(all_records) >= max_results:
                        break
                        
                    record = hit["_source"]
                    record["_index"] = hit["_index"]
                    record["_score"] = hit["_score"]
                    all_records.append(record)
                
                # Get search_after value for next page
                if hits:
                    search_after = hits[-1]["sort"]
                else:
                    break
            
            return pd.DataFrame(all_records) if all_records else pd.DataFrame()
            
        except RequestError as e:
            raise Exception(f"Paginated search failed: {e.error}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")
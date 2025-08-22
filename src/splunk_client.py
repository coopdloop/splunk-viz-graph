"""
Splunk HEC Client for authentication and query execution.
"""
import requests
import pandas as pd
from typing import Dict, List, Optional, Any
import json
import time
from urllib.parse import urljoin


class SplunkHECClient:
    """Client for connecting to Splunk via HTTP Event Collector (HEC)."""
    
    def __init__(self, base_url: str, token: str = None, username: str = None, password: str = None, verify_ssl: bool = True):
        """
        Initialize Splunk client.
        
        Args:
            base_url: Splunk REST API endpoint URL
            token: HEC authentication token (optional)
            username: Splunk username (optional, alternative to token)
            password: Splunk password (optional, alternative to token)
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        
        # Set up authentication
        if username and password:
            # Use basic authentication
            self.session.auth = (username, password)
        elif token:
            # Use HEC token authentication
            self.session.headers.update({
                'Authorization': f'Splunk {self.token}'
            })
        
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def validate_connection(self) -> Dict[str, Any]:
        """
        Validate Splunk connection and authentication.
        
        Returns:
            Dict with validation results
        """
        try:
            # Use server info endpoint to test connection
            url = self.base_url.replace('/services/search/jobs', '/services/server/info')
            
            response = self.session.get(
                url,
                verify=self.verify_ssl,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'valid': True,
                    'status_code': response.status_code,
                    'message': 'Connection successful'
                }
            else:
                return {
                    'valid': False,
                    'status_code': response.status_code,
                    'message': f'Connection failed: {response.text}'
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'valid': False,
                'status_code': None,
                'message': f'Connection error: {str(e)}'
            }
    
    def execute_search(self, search_query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a search query via Splunk REST API.
        
        Args:
            search_query: SPL search query
            **kwargs: Additional search parameters
            
        Returns:
            Dict with search job information
        """
        url = urljoin(self.base_url, '/services/search/jobs')
        
        search_params = {
            'search': search_query,
            'output_mode': 'json',
            'earliest_time': kwargs.get('earliest_time', '-24h@h'),
            'latest_time': kwargs.get('latest_time', 'now'),
            'max_count': kwargs.get('max_count', 10000)
        }
        
        try:
            response = self.session.post(
                url,
                data=search_params,
                verify=self.verify_ssl,
                timeout=60
            )
            response.raise_for_status()
            
            # Extract search job ID from JSON response
            if response.headers.get('content-type', '').startswith('application/json'):
                job_data = response.json()
                job_id = job_data.get('sid', response.text.strip())
            else:
                job_id = response.text.strip()
                
            return {
                'success': True,
                'job_id': job_id,
                'status_code': response.status_code
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None)
            }
    
    def get_search_results(self, job_id: str, offset: int = 0, count: int = 1000) -> Dict[str, Any]:
        """
        Retrieve results from a search job.
        
        Args:
            job_id: Search job ID
            offset: Result offset for pagination
            count: Number of results to retrieve
            
        Returns:
            Dict with search results
        """
        url = urljoin(self.base_url, f'/services/search/jobs/{job_id}/results')
        
        params = {
            'output_mode': 'json',
            'offset': offset,
            'count': count
        }
        
        try:
            response = self.session.get(
                url,
                params=params,
                verify=self.verify_ssl,
                timeout=60
            )
            response.raise_for_status()
            
            return {
                'success': True,
                'data': response.json(),
                'status_code': response.status_code
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None)
            }
    
    def wait_for_job_completion(self, job_id: str, max_wait_time: int = 300) -> Dict[str, Any]:
        """
        Wait for search job to complete.
        
        Args:
            job_id: Search job ID
            max_wait_time: Maximum wait time in seconds
            
        Returns:
            Dict with job status
        """
        url = urljoin(self.base_url, f'/services/search/jobs/{job_id}')
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = self.session.get(
                    url,
                    params={'output_mode': 'json'},
                    verify=self.verify_ssl,
                    timeout=30
                )
                response.raise_for_status()
                
                job_data = response.json()
                dispatch_state = job_data['entry'][0]['content']['dispatchState']
                
                if dispatch_state == 'DONE':
                    return {
                        'success': True,
                        'completed': True,
                        'job_data': job_data
                    }
                elif dispatch_state == 'FAILED':
                    return {
                        'success': False,
                        'completed': True,
                        'error': 'Search job failed'
                    }
                
                time.sleep(2)  # Wait 2 seconds before checking again
                
            except requests.exceptions.RequestException as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        return {
            'success': False,
            'error': 'Job did not complete within timeout period'
        }
    
    def execute_query(self, query: str, **kwargs) -> pd.DataFrame:
        """
        Execute query and return results as DataFrame.
        
        Args:
            query: SPL query string
            **kwargs: Additional query parameters
            
        Returns:
            Pandas DataFrame with results
        """
        # Start search job
        job_result = self.execute_search(query, **kwargs)
        
        if not job_result['success']:
            raise Exception(f"Failed to start search job: {job_result.get('error')}")
        
        job_id = job_result['job_id']
        
        # Wait for completion
        completion_result = self.wait_for_job_completion(job_id)
        
        if not completion_result['success']:
            raise Exception(f"Search job failed: {completion_result.get('error')}")
        
        # Get results
        results = self.get_search_results(job_id)
        
        if not results['success']:
            raise Exception(f"Failed to retrieve results: {results.get('error')}")
        
        # Convert to DataFrame
        if 'results' in results['data']:
            return pd.DataFrame(results['data']['results'])
        else:
            return pd.DataFrame()
    
    def paginate_results(self, query: str, page_size: int = 1000, max_results: Optional[int] = None) -> pd.DataFrame:
        """
        Execute query with pagination support.
        
        Args:
            query: SPL query string
            page_size: Number of results per page
            max_results: Maximum total results to retrieve
            
        Returns:
            Pandas DataFrame with all paginated results
        """
        all_results = []
        offset = 0
        
        # Start search job
        job_result = self.execute_search(query)
        
        if not job_result['success']:
            raise Exception(f"Failed to start search job: {job_result.get('error')}")
        
        job_id = job_result['job_id']
        
        # Wait for completion
        completion_result = self.wait_for_job_completion(job_id)
        
        if not completion_result['success']:
            raise Exception(f"Search job failed: {completion_result.get('error')}")
        
        # Paginate through results
        while True:
            results = self.get_search_results(job_id, offset=offset, count=page_size)
            
            if not results['success']:
                raise Exception(f"Failed to retrieve results: {results.get('error')}")
            
            page_results = results['data'].get('results', [])
            
            if not page_results:
                break
            
            all_results.extend(page_results)
            offset += len(page_results)
            
            # Check if we've reached max results
            if max_results and len(all_results) >= max_results:
                all_results = all_results[:max_results]
                break
            
            # If we got fewer results than page_size, we're done
            if len(page_results) < page_size:
                break
        
        return pd.DataFrame(all_results)
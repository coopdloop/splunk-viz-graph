"""
Tests for splunk_client module.
"""

from unittest.mock import Mock, patch
from src.splunk_client import SplunkHECClient


class TestSplunkHECClient:
    """Test cases for SplunkHECClient class."""

    def test_init_with_token(self):
        """Test initialization with HEC token."""
        client = SplunkHECClient(
            base_url="https://test.splunk.com:8089/services/search/jobs",
            token="test-token",
        )

        assert client.base_url == "https://test.splunk.com:8089/services/search/jobs"
        assert client.token == "test-token"
        assert client.verify_ssl is True

    def test_init_with_username_password(self):
        """Test initialization with username/password."""
        client = SplunkHECClient(
            base_url="https://test.splunk.com:8089/services/search/jobs",
            username="admin",
            password="password",
        )

        assert client.username == "admin"
        assert client.password == "password"
        assert client.session.auth == ("admin", "password")

    def test_base_url_stripping(self):
        """Test that base URL trailing slash is stripped."""
        client = SplunkHECClient(
            base_url="https://test.splunk.com:8089/services/search/jobs/",
            token="test-token",
        )

        assert client.base_url == "https://test.splunk.com:8089/services/search/jobs"

    @patch("src.splunk_client.requests.Session.get")
    def test_validate_connection_success(self, mock_get):
        """Test successful connection validation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = SplunkHECClient(
            base_url="https://test.splunk.com:8089/services/search/jobs",
            token="test-token",
        )

        result = client.validate_connection()

        assert result["valid"] is True
        assert result["status_code"] == 200

    @patch("src.splunk_client.requests.Session.get")
    def test_validate_connection_failure(self, mock_get):
        """Test failed connection validation."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response

        client = SplunkHECClient(
            base_url="https://test.splunk.com:8089/services/search/jobs",
            token="invalid-token",
        )

        result = client.validate_connection()

        assert result["valid"] is False
        assert result["status_code"] == 401

    @patch("src.splunk_client.requests.Session.post")
    def test_execute_search_success(self, mock_post):
        """Test successful search execution."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"sid": "test-job-id"}
        mock_response.headers = {"content-type": "application/json"}
        mock_post.return_value = mock_response

        client = SplunkHECClient(
            base_url="https://test.splunk.com:8089/services/search/jobs",
            token="test-token",
        )

        result = client.execute_search("search index=main")

        assert result["success"] is True
        assert result["job_id"] == "test-job-id"

    def test_no_authentication_provided(self):
        """Test initialization without authentication."""
        client = SplunkHECClient(
            base_url="https://test.splunk.com:8089/services/search/jobs"
        )

        assert client.token is None
        assert client.username is None
        assert client.password is None

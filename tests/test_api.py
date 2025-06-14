"""Tests for the Loggamera API client."""
import unittest
from unittest.mock import MagicMock, patch

from custom_components.loggamera.api import LoggameraAPI, LoggameraAPIError


class TestLoggameraAPI(unittest.TestCase):
    """Test the Loggamera API client."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = LoggameraAPI("test_api_key")

    def test_api_initialization(self):
        """Test API client initialization."""
        self.assertEqual(self.api.api_key, "test_api_key")
        self.assertIsNone(self.api.organization_id)
        self.assertIsNone(self.api.user_id)

    @patch("requests.post")
    def test_get_organizations(self, mock_post):
        """Test getting organizations."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Data": {"Organizations": [{"Id": 1, "Name": "Test Org", "ParentId": 0}]},
            "Error": None,
        }
        mock_post.return_value = mock_response

        # Call the method
        result = self.api.get_organizations()

        # Check results
        self.assertEqual(result["Data"]["Organizations"][0]["Name"], "Test Org")
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_api_error_handling(self, mock_post):
        """Test API error handling."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        # Call the method and check for error
        with self.assertRaises(LoggameraAPIError):
            self.api.get_organizations()


if __name__ == "__main__":
    unittest.main()

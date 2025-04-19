"""Tests for vector search functionality."""

import unittest
from unittest.mock import MagicMock, patch

from app.services.vector_search import search_endpoints_by_text


class TestVectorSearch(unittest.TestCase):
    """Test suite for the vector search functionality."""

    @patch("app.services.vector_search.get_session_context")
    def test_search_single_text_no_results(self, mock_session_context):
        """Test the search_single_text function when no results are found."""
        # Mock database session and empty result
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.execute.return_value.fetchall.return_value = []

        # Create a partial mock that only patches the embedding part
        with patch("app.services.vector_search.get_embedder") as mock_get_embedder:
            mock_embedder = MagicMock()
            mock_embedder.embed_text.return_value = [0.1, 0.2, 0.3]
            mock_get_embedder.return_value = mock_embedder

            # Call the function
            result = search_endpoints_by_text(query_text="nonexistent query", k=10)

            # Verify the result is an empty list
            assert result == []


if __name__ == "__main__":
    unittest.main()

"""Tests for the API specification parser."""

import unittest
from pathlib import Path

import pytest

from app.services.parser import APISpecParser, OpenAPIParser


class TestAPISpecParser(unittest.TestCase):
    """Test the APISpecParser class functionality."""

    def setUp(self):
        """Set up test environment."""
        self.parser = APISpecParser()
        self.fail_fast_parser = APISpecParser(fail_fast=True)
        # Get the path to the test OpenAPI files
        self.base_dir = Path(__file__).parent.parent
        self.openapis_dir = self.base_dir / "openapis"
        self.getplanet_yaml_path = self.openapis_dir / "getplanet-api.yaml"

    def test_parser_instance(self):
        """Test parser instantiation."""
        assert isinstance(self.parser, APISpecParser)
        assert not self.parser.fail_fast
        assert self.fail_fast_parser.fail_fast

    def test_openapi_compatibility(self):
        """Test that the OpenAPIParser class is compatible with APISpecParser."""
        legacy_parser = OpenAPIParser()
        assert isinstance(legacy_parser, APISpecParser)
        assert not legacy_parser.fail_fast

    def test_parse_slack_yaml(self):
        """Test parsing Slack AsyncAPI YAML file."""
        # Read the Slack YAML file
        with Path(self.getplanet_yaml_path).open("rb") as f:
            content = f.read()

        # Parse the content
        parsed = self.parser.parse(content)

        # Basic assertions to verify parsing worked
        assert parsed is not None
        assert isinstance(parsed, dict)
        assert "openapi" in parsed
        assert "info" in parsed
        assert "title" in parsed["info"]
        assert parsed["info"]["title"] == "Planet Earth API"

    def test_extract_endpoints_from_planet_yaml(self):
        """Test extracting endpoints from Planet OpenAPI YAML file."""
        # Read and parse the Planet YAML file
        with Path(self.getplanet_yaml_path).open("rb") as f:
            content = f.read()
        parsed = self.parser.parse(content)

        # Extract endpoints
        endpoints = self.parser.extract_endpoints(parsed)

        # Verify we got endpoints
        assert endpoints is not None
        assert isinstance(endpoints, list)
        assert len(endpoints) > 0

        # Check some properties of the endpoints
        for endpoint in endpoints:
            assert "hash" in endpoint
            assert "path" in endpoint
            assert "method" in endpoint

        # Verify we have endpoints for specific Planet API API paths
        paths = [endpoint["path"] for endpoint in endpoints]
        methods = [endpoint["method"] for endpoint in endpoints]

        # Check for some common Planet API API endpoints
        assert "/v1/schemas" in paths
        assert "GET" in methods
        assert "POST" in methods

    def test_parse_with_bytes_content(self):
        """Test parsing with bytes content."""
        # Read the Slack YAML file as bytes
        with Path(self.getplanet_yaml_path).open("rb") as f:
            content = f.read()

        # Parse the content
        parsed = self.parser.parse(content)
        assert parsed is not None
        assert isinstance(parsed, dict)

    def test_parse_with_string_content(self):
        """Test parsing with string content."""
        # Read the Slack YAML file as string
        with Path(self.getplanet_yaml_path).open("r", encoding="utf-8") as f:
            content = f.read()

        # Parse the content
        parsed = self.parser.parse(content)
        assert parsed is not None
        assert isinstance(parsed, dict)

    def test_extract_schema_metadata(self):
        """Test extracting schema metadata."""
        # Read and parse the Slack YAML file
        with Path(self.getplanet_yaml_path).open("rb") as f:
            content = f.read()
        parsed = self.parser.parse(content)

        # Extract metadata
        title, version = self.parser.extract_schema_metadata(parsed)

        # Verify metadata
        assert title == "Planet Earth API"

if __name__ == "__main__":
    pytest.main()

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
        self.slack_yaml_path = self.openapis_dir / "slack.yaml"
        self.github_yaml_path = self.openapis_dir / "github.yaml"

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
        with Path(self.slack_yaml_path).open("rb") as f:
            content = f.read()

        # Parse the content
        parsed = self.parser.parse(content)

        # Basic assertions to verify parsing worked
        assert parsed is not None
        assert isinstance(parsed, dict)
        assert "asyncapi" in parsed
        assert parsed["asyncapi"] == "1.2.0"
        assert "baseTopic" in parsed
        assert parsed["baseTopic"] == "slack.events"
        assert "info" in parsed
        assert "title" in parsed["info"]
        assert parsed["info"]["title"] == "Slack Events API"

    def test_parse_github_yaml(self):
        """Test parsing GitHub OpenAPI YAML file."""
        # Read the GitHub YAML file
        with Path(self.github_yaml_path).open("rb") as f:
            content = f.read()

        # Parse the content
        parsed = self.parser.parse(content)

        # Basic assertions to verify parsing worked
        assert parsed is not None
        assert isinstance(parsed, dict)
        assert "openapi" in parsed
        assert "info" in parsed
        assert "title" in parsed["info"]
        assert "GitHub v3 REST API" in parsed["info"]["title"]

    def test_extract_endpoints_from_slack_yaml(self):
        """Test extracting endpoints from Slack AsyncAPI YAML file."""
        # Read and parse the Slack YAML file
        with Path(self.slack_yaml_path).open("rb") as f:
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
            assert "id" in endpoint
            assert "path" in endpoint
            assert "method" in endpoint
            assert endpoint["spec_type"] == "asyncapi"
            assert endpoint["schema_title"] == "Slack Events API"
            assert "tags" in endpoint

        # Verify we have endpoints for specific Slack events
        event_paths = [endpoint["path"] for endpoint in endpoints]
        expected_events = ["slack.events.app.mention", "slack.events.team.rename"]

        for event in expected_events:
            assert any(event in path for path in event_paths), f"Expected event {event} not found"

    def test_extract_endpoints_from_github_yaml(self):
        """Test extracting endpoints from GitHub OpenAPI YAML file."""
        # Read and parse the GitHub YAML file
        with Path(self.github_yaml_path).open("rb") as f:
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
            assert "id" in endpoint
            assert "path" in endpoint
            assert "method" in endpoint
            assert endpoint["spec_type"] == "openapi"
            assert "GitHub v3 REST API" in endpoint["schema_title"]

        # Verify we have endpoints for specific GitHub API paths
        paths = [endpoint["path"] for endpoint in endpoints]
        methods = [endpoint["method"] for endpoint in endpoints]

        # Check for some common GitHub API endpoints
        assert "/repos/{owner}/{repo}" in paths
        assert "GET" in methods
        assert "POST" in methods

    def test_get_text_for_embedding_slack(self):
        """Test generating text for embedding from Slack AsyncAPI endpoints."""
        # Read, parse, and extract endpoints
        with Path(self.slack_yaml_path).open("rb") as f:
            content = f.read()
        parsed = self.parser.parse(content)
        endpoints = self.parser.extract_endpoints(parsed)

        # Get the first endpoint
        endpoint = endpoints[0]
        text = f"test {endpoint['path']} {endpoint['summary'] or endpoint['description']} {', '.join(endpoint['tags'])}"
        # Generate text for embedding
        text = self.parser.get_text_for_embedding(endpoint)

        # Verify text generation worked
        assert text is not None
        assert isinstance(text, str)
        assert len(text) > 0

        # Check for expected content in the text
        assert "Path:" in text
        assert "Method:" in text
        assert "Type: ASYNCAPI" in text
        assert endpoint["path"] in text
        assert endpoint["method"] in text

        # Check for AsyncAPI-specific content
        if "external_docs" in endpoint:
            assert "External Documentation:" in text

    def test_get_text_for_embedding_github(self):
        """Test generating text for embedding from GitHub OpenAPI endpoints."""
        # Read, parse, and extract endpoints
        with Path(self.github_yaml_path).open("rb") as f:
            content = f.read()
        parsed = self.parser.parse(content)
        endpoints = self.parser.extract_endpoints(parsed)

        # Get the first endpoint with parameters (more interesting for text generation)
        endpoint = next((e for e in endpoints if e.get("parameters")), endpoints[0])
        text = f"test {endpoint['path']} {endpoint['summary'] or endpoint['description']} {', '.join(endpoint['tags'])}"

        # Verify text generation worked
        assert text is not None
        assert isinstance(text, str)
        assert len(text) > 0

        # Check for expected content in the text
        assert endpoint["path"] in text

        # Check for OpenAPI-specific content
        if endpoint.get("parameters"):
            assert "Parameters:" in text

    def test_parse_with_bytes_content(self):
        """Test parsing with bytes content."""
        # Read the Slack YAML file as bytes
        with Path(self.slack_yaml_path).open("rb") as f:
            content = f.read()

        # Parse the content
        parsed = self.parser.parse(content)
        assert parsed is not None
        assert isinstance(parsed, dict)

    def test_parse_with_string_content(self):
        """Test parsing with string content."""
        # Read the Slack YAML file as string
        with Path(self.slack_yaml_path).open("r", encoding="utf-8") as f:
            content = f.read()

        # Parse the content
        parsed = self.parser.parse(content)
        assert parsed is not None
        assert isinstance(parsed, dict)

    def test_extract_schema_metadata(self):
        """Test extracting schema metadata."""
        # Read and parse the Slack YAML file
        with Path(self.slack_yaml_path).open("rb") as f:
            content = f.read()
        parsed = self.parser.parse(content)

        # Extract metadata
        title, version, checksum = self.parser.extract_schema_metadata(parsed)

        # Verify metadata
        assert title == "Slack Events API"
        assert version == "1.0.0"
        assert checksum is not None
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 hex digest length

    def test_extract_schema_metadata_github(self):
        """Test extracting schema metadata from GitHub yaml."""
        # Read and parse the GitHub YAML file
        with Path(self.github_yaml_path).open("rb") as f:
            content = f.read()
        parsed = self.parser.parse(content)

        # Extract metadata
        title, version, checksum = self.parser.extract_schema_metadata(parsed)

        # Verify metadata
        assert "GitHub v3 REST API" in title
        assert version is not None
        assert checksum is not None
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 hex digest length


if __name__ == "__main__":
    pytest.main()

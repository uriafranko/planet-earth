"""Service module for parsing and extracting information from API specifications (OpenAPI and AsyncAPI)."""

import hashlib
import json
from typing import Any, Union

import yaml
from jsonref import JsonRef
from openapi_spec_validator import validate as validate_openapi
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError

from app.core.logging import get_logger

logger = get_logger(__name__)


class APISpecParser:
    """Service for parsing and extracting endpoints from API specifications (OpenAPI and AsyncAPI)."""

    def __init__(self, *, fail_fast: bool = False):
        """Initialize the API specification parser.

        Args:
            fail_fast: Whether to stop processing on first error
        """
        self.fail_fast = fail_fast

    def parse(self, content: Union[bytes, str]) -> dict[str, Any]:
        """Parse API specification content and return the parsed document.

        Args:
            content: Raw content (bytes or string) of the API spec

        Returns:
            dict containing the parsed API spec

        Raises:
            ValueError: If the content cannot be parsed as YAML or JSON
        """
        try:
            content_str = content.decode("utf-8") if isinstance(content, bytes) else content

            # Parse content as JSON or YAML
            parsed = self._parse_content(content_str)

            # Resolve JSON references
            parsed = self._resolve_references(parsed)

            # Attempt to determine the spec type and validate if possible
            self._identify_and_validate_spec(parsed)

            return parsed
        except Exception as e:
            logger.exception("Error parsing API spec")
            raise ValueError(f"Failed to parse API spec: {e!s}") from e

    def _parse_content(self, content_str: str) -> dict:
        """Parse content string as JSON or YAML.

        Args:
            content_str: String content to parse

        Returns:
            Parsed dictionary

        Raises:
            ValueError: If content cannot be parsed
        """
        try:
            return json.loads(content_str)
        except json.JSONDecodeError:
            try:
                return yaml.safe_load(content_str)
            except yaml.YAMLError as e:
                logger.exception("Failed to parse content as YAML")
                error_message = f"Content could not be parsed as JSON or YAML: {str(e)}"
                raise ValueError(error_message) from e

    def _resolve_references(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Resolve JSON references in the parsed spec.

        Args:
            parsed: dict

        Returns:
            Spec with resolved references

        Raises:
            ValueError: If references cannot be resolved
        """
        try:
            return JsonRef.replace_refs(parsed)
        except Exception as e:
            logger.exception("Error resolving references in API spec")
            error_message = f"Failed to resolve references in the API spec: {str(e)}"
            raise ValueError(error_message) from e

    def _identify_and_validate_spec(self, spec: dict[str, Any]) -> str:
        """Identify the type of API spec and validate if possible.

        Args:
            spec: Parsed API spec

        Returns:
            String identifying the spec type ("openapi", "asyncapi", or "unknown")
        """
        # Determine if it's OpenAPI or AsyncAPI
        if "openapi" in spec:
            spec_type = "openapi"
            if self.fail_fast:
                try:
                    validate_openapi(spec)
                    logger.info("OpenAPI spec validation successful")
                except OpenAPIValidationError as e:
                    logger.exception(f"OpenAPI validation error: {str(e)}")
                    raise
                except Exception as e:
                    logger.warning(f"OpenAPI validation warning: {str(e)}")
            else:
                try:
                    validate_openapi(spec)
                    logger.info("OpenAPI spec validation successful")
                except Exception as e:
                    logger.warning(f"OpenAPI validation warning (continuing): {str(e)}")

        elif "asyncapi" in spec:
            spec_type = "asyncapi"
            # AsyncAPI validation is not implemented yet, as there's no standard library
            # But we'll accept it and provide a log message
            logger.info("AsyncAPI spec detected, validation skipped")
        else:
            spec_type = "unknown"
            logger.warning("Unknown API spec format - neither OpenAPI nor AsyncAPI detected")

        return spec_type

    def extract_endpoints(self, spec: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract individual endpoints from a parsed API specification.

        Args:
            spec: Parsed API spec

        Returns:
            list of endpoint dictionaries, each containing information about a single operation
        """
        endpoints = []

        # Determine the spec type
        if "openapi" in spec:
            endpoints = self._extract_openapi_endpoints(spec)
        elif "asyncapi" in spec:
            endpoints = self._extract_asyncapi_endpoints(spec)
        else:
            logger.warning("Unknown API spec format - could not extract endpoints")

        return endpoints

    def _extract_openapi_endpoints(self, spec: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract endpoints from an OpenAPI specification.

        Args:
            spec: Parsed OpenAPI spec

        Returns:
            list of endpoint dictionaries
        """
        endpoints = []
        paths = spec.get("paths", {})

        for path, path_item in paths.items():
            # Skip path parameters and other non-operation fields
            for method, operation in path_item.items():
                if method in ["get", "post", "put", "delete", "patch", "head", "options", "trace"]:
                    try:
                        endpoint = {
                            "path": path,
                            "method": method.upper(),
                            "operation_id": operation.get("operationId", ""),
                            "summary": operation.get("summary", ""),
                            "description": operation.get("description", ""),
                            "tags": operation.get("tags", []),
                            "parameters": operation.get("parameters", []),
                            "request_body": operation.get("requestBody", {}),
                            "responses": operation.get("responses", {}),
                            "spec_type": "openapi",
                            "deprecated": operation.get("deprecated", False),
                            "schema_title": spec.get("info", {}).get("title", ""),
                            "schema_version": spec.get("info", {}).get("version", ""),
                            # Store only the relevant operation data, not the entire spec
                            "spec": self._ensure_json_serializable({
                                "path": path,
                                "method": method.upper(),
                                "operation_id": operation.get("operationId", ""),
                                "parameters": operation.get("parameters", []),
                                "request_body": operation.get("requestBody", {}),
                                "responses": operation.get("responses", {}),
                            }),
                        }

                        # Generate a unique identifier for the endpoint
                        endpoint["hash"] = self._generate_endpoint_id(endpoint)

                        endpoints.append(endpoint)
                    except Exception as e:
                        logger.warning(
                            f"Error extracting OpenAPI endpoint {path} {method}: {str(e)}"
                        )
                        if self.fail_fast:
                            raise

        return endpoints

    def _extract_asyncapi_endpoints(self, spec: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract endpoints from an AsyncAPI specification.

        Args:
            spec: Parsed AsyncAPI spec

        Returns:
            list of endpoint dictionaries
        """
        endpoints = []
        topics = spec.get("topics", {})
        base_topic = spec.get("baseTopic", "")

        # Process each topic (equivalent to paths in OpenAPI)
        for topic, topic_item in topics.items():
            # AsyncAPI typically uses publish/subscribe pattern
            for operation_type in ["subscribe", "publish"]:
                if operation_item := topic_item.get(operation_type):
                    try:
                        # Build full topic path with base topic if present
                        full_topic = f"{base_topic}.{topic}" if base_topic else topic

                        # Extract relevant data
                        endpoint = {
                            "path": full_topic,
                            "method": operation_type.upper(),
                            "operation_id": f"{topic}.{operation_type}",
                            "summary": operation_item.get("summary", ""),
                            "description": operation_item.get("description", ""),
                            "tags": [tag.get("name") for tag in operation_item.get("tags", [])],
                            "parameters": [],  # AsyncAPI handles parameters differently
                            "payload": operation_item.get("payload", {}),
                            "spec_type": "asyncapi",
                            "deprecated": operation_item.get("deprecated", False),
                            "schema_title": spec.get("info", {}).get("title", ""),
                            "schema_version": spec.get("info", {}).get("version", ""),
                            "external_docs": operation_item.get("externalDocs", {}),
                            # Store only the relevant operation data, not the entire spec
                            "spec": self._ensure_json_serializable({
                                "operation_type": operation_type,
                                "topic": full_topic,
                                "payload": operation_item.get("payload", {}),
                                "headers": operation_item.get("headers", {}),
                                "message": operation_item.get("message", {}),
                            }),
                        }

                        # Generate a unique identifier for the endpoint
                        endpoint["hash"] = self._generate_endpoint_id(endpoint)

                        endpoints.append(endpoint)
                    except Exception as e:
                        logger.warning(
                            f"Error extracting AsyncAPI endpoint {topic} {operation_type}: {str(e)}"
                        )
                        if self.fail_fast:
                            raise

        return endpoints

    def _ensure_json_serializable(self, obj: Any) -> Any:
        """Ensure an object is JSON serializable.

        Recursively processes dictionaries and lists to ensure all values
        are JSON serializable types (str, int, float, bool, None, list, dict).

        Args:
            obj: Object to make JSON serializable

        Returns:
            JSON serializable version of the object
        """
        if obj is None or isinstance(obj, str | int | float | bool):
            return obj
        if isinstance(obj, list):
            return [self._ensure_json_serializable(item) for item in obj]
        if isinstance(obj, dict):
            return {
                str(key): self._ensure_json_serializable(value)
                for key, value in obj.items()
            }
        # Convert any other types to strings
        return str(obj)

    def _generate_endpoint_id(self, endpoint: dict[str, Any]) -> str:
        """Generate a unique ID for an endpoint based on its properties.

        Args:
            endpoint: Endpoint dictionary

        Returns:
            A unique ID string
        """
        # Create a string combining key properties for uniqueness
        id_string = f"{endpoint['spec_type']}:{endpoint['schema_title']}:{endpoint['path']}:{endpoint['method']}"

        # Generate a hash for a shorter ID
        return hashlib.md5(id_string.encode()).hexdigest()[:12]  # noqa: S324

    def extract_schema_metadata(self, spec: dict[str, Any]) -> tuple[str, str, str]:
        """Extract title, version, and generate a checksum from the API spec.

        Args:
            spec: Parsed API spec

        Returns:
            Tuple of (title, version, checksum)
        """
        info = spec.get("info", {})
        title = info.get("title", "Untitled API")
        version = info.get("version", "0.0.0")

        return title, version

    def get_text_for_embedding(self, title: str, endpoint: dict[str, Any]) -> str:
        """Generate a text representation of an endpoint for embedding.

        This creates a textual representation of the endpoint that captures
        its semantic meaning for the embedding model.

        Args:
            title: Title of the API
            endpoint: Endpoint dictionary extracted from API spec

        Returns:
            String containing a textual representation of the endpoint
        """
        text_parts = [title]

        # Add basic endpoint information
        self._add_basic_info(endpoint, text_parts)

        # Process information based on spec type
        if endpoint.get("spec_type") == "openapi":
            # Add OpenAPI-specific information
            self._add_response_info(endpoint, text_parts)
        elif endpoint.get("spec_type") == "asyncapi":
            # Add AsyncAPI-specific information
            self._add_external_docs_info(endpoint, text_parts)

        return "\n".join(text_parts)

    def _add_basic_info(self, endpoint: dict[str, Any], text_parts: list[str]) -> None:
        """Add basic endpoint information to text parts."""
        text_parts.append(f"Path: {endpoint['path']}")
        if endpoint.get("summary"):
            text_parts.append(f"Summary: {endpoint['summary']}")

        if endpoint.get("description"):
            text_parts.append(f"Description: {endpoint['description']}")

        if endpoint.get("tags"):
            tags = endpoint["tags"]
            if isinstance(tags, list):
                text_parts.append(f"Tags: {', '.join(tags)}")

    def _add_parameters_info(self, endpoint: dict[str, Any], text_parts: list[str]) -> None:
        """Add parameters information to text parts for OpenAPI endpoints."""
        if not endpoint.get("parameters"):
            return

        param_texts = []
        for param in endpoint["parameters"]:
            try:
                param_name = param.get("name", "unknown")
                param_in = param.get("in", "unknown")
                param_desc = param.get("description", "")
                param_required = "required" if param.get("required") else "optional"
                param_text = f"{param_name} ({param_in}, {param_required})"
                if param_desc:
                    param_text += f": {param_desc}"
                param_texts.append(param_text)
            except Exception as e:
                logger.warning(f"Error processing parameter {param}: {str(e)}")

        if param_texts:
            text_parts.append("Parameters:")
            text_parts.extend([f"- {p}" for p in param_texts])

    def _add_request_body_info(self, endpoint: dict[str, Any], text_parts: list[str]) -> None:
        """Add request body information to text parts for OpenAPI endpoints."""
        request_body = endpoint.get("request_body")
        if not request_body:
            return

        text_parts.append("Request Body:")

        if description := request_body.get("description"):
            text_parts.append(f"Description: {description}")

        if content := request_body.get("content"):
            content_types = list(content.keys())
            text_parts.append(f"Content Types: {', '.join(content_types)}")

            # Add more detailed schema information if available
            for content_type, content_info in content.items():
                if schema := content_info.get("schema"):
                    # Add schema type
                    if schema_type := schema.get("type"):
                        text_parts.append(f"Schema Type: {schema_type}")

                    # Add properties for objects
                    if properties := schema.get("properties"):
                        text_parts.append("Properties:")
                        for prop_name, prop_info in properties.items():
                            prop_desc = prop_info.get("description", "")
                            prop_type = prop_info.get("type", "unknown")
                            text_parts.append(f"- {prop_name} ({prop_type}): {prop_desc}")

    def _add_response_info(self, endpoint: dict[str, Any], text_parts: list[str]) -> None:
        """Add response information to text parts for OpenAPI endpoints."""
        responses = endpoint.get("responses")
        if not responses:
            return

        text_parts.append("Responses:")
        for status, response in responses.items():
            try:
                resp_desc = response.get("description", "")
                text_line = f"- {status}: {resp_desc}"

                # Add content type information if available
                if content := response.get("content"):
                    content_types = list(content.keys())
                    text_line += f" ({', '.join(content_types)})"

                text_parts.append(text_line)
            except Exception as e:
                logger.warning(f"Error processing response {status}: {str(e)}")

    def _add_asyncapi_payload_info(self, endpoint: dict[str, Any], text_parts: list[str]) -> None:
        """Add payload information to text parts for AsyncAPI endpoints."""
        payload = endpoint.get("payload")
        if not payload:
            return

        text_parts.append("Payload:")

        # Add any examples
        if examples := payload.get("examples"):
            text_parts.append(examples)

    def _add_external_docs_info(self, endpoint: dict[str, Any], text_parts: list[str]) -> None:
        """Add external documentation information for AsyncAPI endpoints."""
        external_docs = endpoint.get("external_docs")
        if not external_docs:
            return

        desc = external_docs.get("description", "")

        if desc:
            text_parts.append("External Documentation:")
            text_parts.append(f"- {desc}")


# Keep the legacy class name for backward compatibility
class OpenAPIParser(APISpecParser):
    """Legacy class name for backward compatibility."""

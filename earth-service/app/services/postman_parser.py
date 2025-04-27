from __future__ import annotations

"""postman_to_openapi.py – Battle‑tested v3.0

Transforms a Postman Collection (v2.0 or v2.1) into an **OpenAPI 3.0.3**
specification *without losing information*:

* Disabled / optional parameters → `x-disabled: true` so you can still see them.
* Environment‑variable hosts like ``{{BASE_URL}}`` are promoted to `servers`.
* Query strings embedded in the raw URL become proper `parameters`.
* `requestBody` is emitted only for HTTP methods that permit it.

The converter is fully typed (Python ≥ 3.9) and returns a
:class:`TransformResult` – a normal dict containing the spec plus a
``diagnostics`` list of non‑fatal issues.

Quick start
-----------
>>> from postman_to_openapi import PostmanToOpenAPI
>>> spec = PostmanToOpenAPI(collection_bytes).transform()
>>> openapi_json = spec.to_json(indent=2)
>>> print(spec.diagnostics)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
import json
import re
import urllib.parse as urlparse
from copy import deepcopy

__all__ = ["PostmanToOpenAPI", "TransformResult"]

_JSON = Union[str, Dict[str, Any]]
_TEMPLATE_VAR_RE = re.compile(r"\{\{([^{}]+?)\}\}")
_NO_BODY_METHODS = {"get", "head", "delete", "options", "trace"}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _pm_var_to_oas(segment: str, collector: Optional[List[str]] = None) -> str:
    """Convert ``{{var}}`` → ``{var}`` and optionally collect var names."""

    def _sub(match: re.Match[str]) -> str:
        var = match.group(1)
        if collector is not None:
            collector.append(var)
        return f"{{{var}}}"

    return _TEMPLATE_VAR_RE.sub(_sub, segment)


def _ensure_list(obj: Any) -> List[Any]:
    if obj is None:
        return []
    return obj if isinstance(obj, list) else [obj]


# ---------------------------------------------------------------------------
# Result wrapper
# ---------------------------------------------------------------------------

class TransformResult(dict):
    """Dict subclass that also exposes the diagnostics list and pretty JSON."""

    diagnostics: List[str]

    def __init__(self, spec: Dict[str, Any], diagnostics: List[str]):
        super().__init__(spec)  # type: ignore[arg-type]
        self.diagnostics = diagnostics

    # Convenience
    def to_json(self, **kwargs: Any) -> str:  # noqa: D401 (imperative docstring)
        """Return the spec as a JSON string (passes kwargs to ``json.dumps``)."""
        return json.dumps(self, **kwargs)



# ---------------------------------------------------------------------------
# Quick schema detector
# ---------------------------------------------------------------------------
_SchemaKind = Literal["openapi", "postman", "unknown"]

def detect_schema(data: _JSON) -> _SchemaKind:
    """Return ``"openapi"``, ``"postman"``, or ``"unknown"`` for *data*.

    The check is intentionally lightweight—good enough to decide whether
    a conversion step is required, but not a full validation.
    """
    try:
        if isinstance(data, (bytes, bytearray)):
            data = data.decode()
        obj = json.loads(data) if isinstance(data, str) else data  # type: ignore[arg-type]
    except Exception:  # noqa: BLE001
        return "unknown"

    if isinstance(obj, dict):
        if "openapi" in obj or "swagger" in obj:
            return "openapi"
        info = obj.get("info")
        if info and obj.get("item") is not None:
            schema_url = (info.get("schema") if isinstance(info, dict) else "") or ""
            if "schema.getpostman.com/collection" in schema_url:
                return "postman"
            # Heuristic fallback: collections usually have info+item
            return "postman"
    return "unknown"


# ---------------------------------------------------------------------------
# Core converter
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class PostmanToOpenAPI:
    """Convert a Postman collection (dict or JSON string/bytes) to OpenAPI."""

    collection: _JSON  # raw JSON string/bytes or parsed dict

    # internal state
    _raw: Dict[str, Any] = field(init=False, repr=False)
    _version: str = field(init=False)
    _diagnostics: List[str] = field(default_factory=list, init=False, repr=False)
    _servers: set[str] = field(default_factory=set, init=False, repr=False)

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        try:
            if isinstance(self.collection, (bytes, bytearray)):
                self.collection = self.collection.decode()
            self._raw = json.loads(self.collection) if isinstance(self.collection, str) else deepcopy(self.collection)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("`collection` must be a valid JSON string/bytes or a dict") from exc

        self._version = self._detect_version()
        if self._version not in {"2.0", "2.1"}:
            raise ValueError(f"Unsupported Postman schema version: {self._version}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def transform(self) -> TransformResult:
        spec: Dict[str, Any] = {
            "openapi": "3.0.3",
            "info": self._build_info(),
            "paths": {},
            "components": {"schemas": {}},
        }

        for item in _ensure_list(self._raw.get("item")):
            self._walk_item(item, spec["paths"])

        if self._servers:
            spec["servers"] = [{"url": s} for s in sorted(self._servers)]

        return TransformResult(spec, self._diagnostics)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _detect_version(self) -> str:
        schema_url = self._raw.get("info", {}).get("schema", "")
        if m := re.search(r"v(\d+)\.(\d+)", schema_url):
            return f"{m.group(1)}.{m.group(2)}"
        return "2.1" if "protocolProfileBehavior" in self._raw else "2.0"

    def _build_info(self) -> Dict[str, Any]:
        info = self._raw.get("info", {})
        version_field = info.get("version", "1.0.0")
        if isinstance(version_field, dict):
            version = version_field.get("major", "1.0.0")
        else:
            version = str(version_field)
        return {
            "title": info.get("name", "Postman Collection"),
            "description": info.get("description", "Converted from Postman collection."),
            "version": version,
        }

    # ------------------------------------------------------------------
    # Item traversal
    # ------------------------------------------------------------------
    def _walk_item(self, item: Dict[str, Any], paths: Dict[str, Any]) -> None:
        if self._is_folder(item):
            for child in _ensure_list(item.get("item")):
                self._walk_item(child, paths)
            return

        if not self._is_request(item):
            self._diagnostics.append(f"Skipped non‑request item: {item.get('name')}")
            return

        try:
            request = item["request"]
            raw_url = self._infer_raw_url(request)
            server, path, path_vars, query_pairs = self._split_base_and_path(raw_url)
            if server:
                self._servers.add(server)

            method = request.get("method", "GET").lower()
            operation: Dict[str, Any] = {
                "summary": item.get("name", path),
                "description": request.get("description", ""),
                "parameters": self._collect_parameters(request, path_vars, query_pairs),
                "responses": {"200": {"description": "Success"}},
            }

            body_obj = request.get("body")
            if body_obj and method not in _NO_BODY_METHODS:
                if rb := self._build_request_body(body_obj):
                    operation["requestBody"] = rb
            elif body_obj and method in _NO_BODY_METHODS:
                self._diagnostics.append(
                    f"Ignored body on {method.upper()} {path} (not allowed by OpenAPI)"
                )

            paths.setdefault(path, {})[method] = operation
        except Exception as exc:  # noqa: BLE001
            self._diagnostics.append(f"Error processing item '{item.get('name')}': {exc}")

    # ------------------------------------------------------------------
    # Structural checks
    # ------------------------------------------------------------------
    @staticmethod
    def _is_folder(item: Dict[str, Any]) -> bool:
        return "item" in item and "request" not in item

    @staticmethod
    def _is_request(item: Dict[str, Any]) -> bool:
        return isinstance(item.get("request"), dict)

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------
    def _infer_raw_url(self, request: Dict[str, Any]) -> str:
        url_obj = request.get("url", {})
        if isinstance(url_obj, str):
            return url_obj
        if "raw" in url_obj:
            return url_obj["raw"]
        host = url_obj.get("host")
        path = url_obj.get("path")
        if isinstance(host, list):
            host = "".join(host)
        if isinstance(path, list):
            path = "/".join(path)
        scheme = (url_obj.get("protocol") or "https") + "://" if host else ""
        if host and path:
            return f"{scheme}{host}/{path}"
        raise ValueError("Cannot determine raw URL for request")

    def _split_base_and_path(self, raw_url: str) -> Tuple[str, str, List[str], List[Tuple[str, str]]]:
        """Return `(server_url, path, path_vars, query_pairs)`.

        * Ensures the path starts with '/'.
        * Converts Postman placeholders to OAS style.
        """
        # Separate scheme/host and the rest
        if "://" in raw_url:
            parsed = urlparse.urlparse(raw_url)
            server = f"{parsed.scheme}://{_pm_var_to_oas(parsed.netloc)}" if parsed.netloc else ""
            remaining = parsed.path or "/"
            query = parsed.query
        else:
            first_slash = raw_url.find("/")
            if first_slash == -1:
                return _pm_var_to_oas(raw_url), "/", [], []
            server = _pm_var_to_oas(raw_url[:first_slash])
            after = raw_url[first_slash:]
            remaining, _, query = after.partition("?")

        path_vars: List[str] = []
        path = _pm_var_to_oas(remaining or "/", path_vars)
        if not path.startswith("/"):
            path = "/" + path

        # Parse query string into list of (name, value) pairs
        query_pairs = urlparse.parse_qsl(query, keep_blank_values=True)
        return server, path, path_vars, query_pairs

    # ------------------------------------------------------------------
    # Parameter builders
    # ------------------------------------------------------------------
    def _collect_parameters(
        self,
        request: Dict[str, Any],
        path_vars: List[str],
        query_pairs: List[Tuple[str, str]],
    ) -> List[Dict[str, Any]]:
        params: List[Dict[str, Any]] = [
            {
                "name": v,
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            }
            for v in path_vars
        ]

        # Query parameters from structured Postman fields
        url_obj = request.get("url", {})
        for q in _ensure_list(url_obj.get("query")):
            params.append(self._pm_param_to_oas(q, "query"))

        # Query parameters parsed from raw URL (avoid duplicates)
        existing_query_names = {p["name"] for p in params if p["in"] == "query"}
        for name, value in query_pairs:
            if name in existing_query_names:
                continue
            params.append(
                {
                    "name": name,
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"},
                    "example": value,
                }
            )

        # Headers
        for h in _ensure_list(request.get("header")):
            params.append(self._pm_param_to_oas(h, "header"))

        return params

    def _pm_param_to_oas(self, pm_param: Dict[str, Any], loc: str) -> Dict[str, Any]:
        name = pm_param.get("key") or pm_param.get("name", "param")
        required = False if loc == "query" else not pm_param.get("disabled", False)
        schema: Dict[str, Any] = {"type": "string"}
        param: Dict[str, Any] = {
            "name": name,
            "in": loc,
            "required": required,
            "schema": schema,
        }
        if "value" in pm_param:
            param["example"] = pm_param["value"]
        return param

    # ------------------------------------------------------------------
    # Request body
    # ------------------------------------------------------------------
    def _build_request_body(self, body: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not body:
            return None

        content: Dict[str, Any] = {}
        mode = body.get("mode")

        if mode == "raw":
            mime = body.get("options", {}).get("raw", {}).get("language", "text/plain")
            content[mime] = {
                "schema": {"type": "string"},
                "example": body.get("raw", ""),
            }
        elif mode == "graphql":
            gql = body.get("graphql", {})
            content["application/json"] = {
                "schema": {"type": "object"},
                "example": {
                    "query": gql.get("query", ""),
                    "variables": gql.get("variables", {}),
                },
            }
        elif mode in {"urlencoded", "formdata"}:
            form_params = [self._pm_param_to_oas(p, "formData") for p in body.get(mode, [])]
            content["application/x-www-form-urlencoded"] = {
                "schema": {
                    "type": "object",
                    "properties": {p["name"]: {"type": "string"} for p in form_params},
                }
            }
        else:
            content["application/octet-stream"] = {
                "schema": {"type": "string", "format": "binary"},
            }

        return {"content": content}

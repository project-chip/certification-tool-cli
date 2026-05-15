#!/usr/bin/env python3
#
# Copyright (c) 2026 Project CHIP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
Modern API client generator using datamodel-code-generator.

This replaces the Docker-based openapi-generator approach with a pure Python solution:
- Uses datamodel-code-generator for Pydantic v2 models
- Generates API endpoint classes from OpenAPI specification
- No Docker required, faster generation, cleaner output
- Minimal/no postprocessing needed
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any

import click
import httpx


class OpenAPIParser:
    """Parse OpenAPI specification and extract information for code generation."""

    def __init__(self, spec: dict[str, Any]):
        self.spec = spec
        self.schemas = spec.get("components", {}).get("schemas", {})

    def get_endpoints_by_tag(self) -> dict[str, list[dict[str, Any]]]:
        """Group API endpoints by their tags."""
        endpoints_by_tag: dict[str, list[dict[str, Any]]] = {}

        for path, path_item in self.spec.get("paths", {}).items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method not in path_item:
                    continue

                operation = path_item[method]
                tags = operation.get("tags", ["default"])
                tag = tags[0] if tags else "default"

                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []

                endpoints_by_tag[tag].append(
                    {
                        "path": path,
                        "method": method.upper(),
                        "operation_id": operation.get("operationId", f"{method}_{path.replace('/', '_')}"),
                        "summary": operation.get("summary", ""),
                        "description": operation.get("description", ""),
                        "parameters": operation.get("parameters", []),
                        "request_body": operation.get("requestBody"),
                        "responses": operation.get("responses", {}),
                    }
                )

        return endpoints_by_tag

    def get_parameter_info(self, param: dict[str, Any]) -> dict[str, Any]:
        """Extract parameter information."""
        schema = param.get("schema", {})
        param_type = self._get_python_type(schema)
        required = param.get("required", False)

        return {
            "name": param["name"],
            "type": param_type,
            "required": required,
            "in": param.get("in", "query"),
            "description": param.get("description", ""),
        }

    def get_request_body_info(self, request_body: dict[str, Any] | None) -> dict[str, Any] | None:
        """Extract request body information."""
        if not request_body:
            return None

        content = request_body.get("content", {})
        # Try JSON first, then form data
        for content_type in ["application/json", "multipart/form-data", "application/x-www-form-urlencoded"]:
            if content_type in content:
                schema = content[content_type].get("schema", {})
                return {
                    "type": self._get_python_type(schema, resolve_ref=True),
                    "required": request_body.get("required", False),
                    "content_type": content_type,
                    "is_multipart": content_type == "multipart/form-data",
                    "schema": schema,  # Keep the original schema for field inspection
                }

        return None

    def get_schema_fields(self, schema: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract field information from a schema, resolving $ref if needed."""
        # Resolve $ref if present
        if "$ref" in schema:
            ref = schema["$ref"]
            schema_name = ref.split("/")[-1]
            schema = self.schemas.get(schema_name, {})

        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])

        fields = []
        for field_name, field_schema in properties.items():
            field_type = field_schema.get("type", "string")
            field_format = field_schema.get("format", "")

            # Determine if this is a file field
            # In OpenAPI, file uploads are typically: type=string, format=binary
            is_file = (field_type == "string" and field_format == "binary")

            fields.append({
                "name": field_name,
                "type": field_type,
                "format": field_format,
                "is_file": is_file,
                "required": field_name in required_fields,
                "schema": field_schema,
            })

        return fields

    def get_response_type(self, responses: dict[str, Any]) -> str:
        """Extract response type from responses."""
        # Try 200, 201, then any 2xx
        for status in ["200", "201"]:
            if status in responses:
                response = responses[status]
                content = response.get("content", {})
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    return self._get_python_type(schema, resolve_ref=True)
                if "application/zip" in content:
                    schema = content["application/zip"].get("schema", {})
                    return self._get_python_type(schema, resolve_ref=True)

        # Check for any 2xx response
        for status, response in responses.items():
            if status.startswith("2"):
                content = response.get("content", {})
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    return self._get_python_type(schema, resolve_ref=True)

        return "None"

    def _get_python_type(self, schema: dict[str, Any], resolve_ref: bool = False) -> str:
        """Convert OpenAPI schema type to Python type hint."""
        if "$ref" in schema:
            ref = schema["$ref"]
            model_name = ref.split("/")[-1]
            if model_name.startswith("Body_"):
            # TODO: handle schema names that conflicts with the models names.
                model_name = "".join(word.capitalize() for word in model_name.split("_"))
            if resolve_ref:
                return f"m.{model_name}"
            return model_name

        schema_type = schema.get("type", "object")
        schema_format = schema.get("format")

        # Handle arrays
        if schema_type == "array":
            items = schema.get("items", {})
            item_type = self._get_python_type(items, resolve_ref=resolve_ref)
            return f"list[{item_type}]"

        # Handle objects
        if schema_type == "object":
            additional_props = schema.get("additionalProperties")
            if additional_props:
                value_type = self._get_python_type(additional_props, resolve_ref=resolve_ref)
                return f"dict[str, {value_type}]"
            return "dict[str, Any]"

        # Primitive types
        type_mapping = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
        }

        # Handle string formats
        if schema_type == "string":
            format_mapping = {
                "date-time": "datetime",
                "date": "date",
                "uuid": "UUID",
                "binary": "bytes",
            }
            if schema_format in format_mapping:
                return format_mapping[schema_format]

        return type_mapping.get(schema_type, "Any")


class APIGenerator:
    """Generate API client code from OpenAPI specification."""

    def __init__(self, spec_path: str, output_dir: Path, import_name: str = "th_cli.api_lib_autogen"):
        self.spec_path = spec_path
        self.output_dir = output_dir
        self.import_name = import_name
        self.spec = self._load_spec()
        self.parser = OpenAPIParser(self.spec)

    def _load_spec(self) -> dict[str, Any]:
        """Load OpenAPI specification from file or URL."""
        if self.spec_path.startswith("http://") or self.spec_path.startswith("https://"):
            click.echo(f"📥 Downloading OpenAPI spec from {self.spec_path}")
            response = httpx.get(self.spec_path, follow_redirects=True)
            response.raise_for_status()
            return response.json()
        else:
            click.echo(f"📂 Loading OpenAPI spec from {self.spec_path}")
            with open(self.spec_path) as f:
                return json.load(f)

    def generate(self):
        """Generate complete API client."""
        click.echo(f"🚀 Generating API client to {self.output_dir}")

        # Clean output directory
        if self.output_dir.exists():

            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Generate Pydantic models
        self._generate_models()

        # Step 2: Generate API endpoint classes
        self._generate_api_classes()

        # Step 3: Generate api_client.py
        self._generate_api_client()

        # Step 4: Generate exceptions.py
        self._generate_exceptions()

        # Step 5: Generate __init__.py files
        self._generate_init_files()

        # Step 6: Add py.typed marker
        self._add_py_typed()

        click.echo("✨ Generation complete!")

    def _generate_models(self):
        """Generate Pydantic v2 models using datamodel-code-generator."""
        click.echo("📦 Generating Pydantic v2 models...")

        models_file = self.output_dir / "models.py"

        # Save spec to temp file if it's a URL
        spec_file = self.spec_path
        if self.spec_path.startswith("http"):
            temp_spec = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            json.dump(self.spec, temp_spec)
            temp_spec.close()
            spec_file = temp_spec.name

        cmd = [
            "poetry",
            "run",
            "datamodel-codegen",
            "--input",
            spec_file,
            "--output",
            str(models_file),
            "--input-file-type",
            "openapi",
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--use-standard-collections",
            "--use-union-operator",
            "--target-python-version",
            "3.10",
            "--use-annotated",
            "--field-constraints",
            "--collapse-root-models",
            "--enum-field-as-literal",
            "one",
            "--use-title-as-name",
            "--reuse-model",
            "--output-datetime-class",
            "datetime",
        ]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            if result.stdout:
                click.echo(result.stdout)
            click.echo(f"  ✓ Generated {models_file.relative_to(self.output_dir.parent)}")
        except subprocess.CalledProcessError as e:
            click.echo(f"  ✗ Error generating models: {e.stderr}", err=True)
            raise
        except FileNotFoundError:
            click.echo(
                "  ✗ Error: datamodel-code-generator not found. Please verify the module installation.",
                err=True,
            )
            raise

        # Clean up temp file if created
        if self.spec_path.startswith("http") and spec_file != self.spec_path:
            os.unlink(spec_file)

    def _generate_api_classes(self):
        """Generate API endpoint classes."""
        click.echo("🔌 Generating API endpoint classes...")

        api_dir = self.output_dir / "api"
        api_dir.mkdir(exist_ok=True)

        endpoints_by_tag = self.parser.get_endpoints_by_tag()

        for tag, endpoints in endpoints_by_tag.items():
            self._generate_api_class_file(tag, endpoints, api_dir)

    def _generate_api_class_file(self, tag: str, endpoints: list[dict[str, Any]], api_dir: Path):
        """Generate a single API class file."""
        class_name = self._tag_to_class_name(tag)
        file_name = f"{tag.replace('-', '_').replace(' ', '_')}_api.py"
        file_path = api_dir / file_name

        # Generate imports
        imports = self._generate_imports()

        # Generate base class
        base_class = self._generate_base_api_class(class_name, endpoints)

        # Generate async class
        async_class = self._generate_async_api_class(class_name, endpoints)

        # Generate sync class
        sync_class = self._generate_sync_api_class(class_name, endpoints)

        content = f'''{imports}

{base_class}


{async_class}


{sync_class}
'''

        file_path.write_text(content)
        click.echo(f"  ✓ Generated {file_path.relative_to(self.output_dir.parent)}")

    def _generate_imports(self) -> str:
        """Generate import statements."""
        return f'''#
# Copyright (c) 2026 Project CHIP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# flake8: noqa E501
from asyncio import get_event_loop
from typing import Coroutine, IO, TYPE_CHECKING, Any

from {self.import_name} import models as m

if TYPE_CHECKING:
    from {self.import_name}.api_client import ApiClient'''

    def _generate_base_api_class(self, class_name: str, endpoints: list[dict[str, Any]]) -> str:
        """Generate base API class with _build_for methods."""
        methods = []

        for endpoint in endpoints:
            method = self._generate_build_method(endpoint)
            methods.append(method)

        methods_code = "\n\n".join(methods)

        return f'''class _{class_name}:
    def __init__(self, api_client: "ApiClient"):
        self.api_client = api_client

{methods_code}'''

    def _generate_build_method(self, endpoint: dict[str, Any]) -> str:
        """Generate _build_for method for an endpoint."""
        operation_id = endpoint["operation_id"]
        method = endpoint["method"]
        path = endpoint["path"]
        parameters = endpoint["parameters"]
        request_body = endpoint.get("request_body")
        responses = endpoint["responses"]

        # Parse parameters
        params = [self.parser.get_parameter_info(p) for p in parameters]
        path_params = [p for p in params if p["in"] == "path"]
        query_params = [p for p in params if p["in"] == "query"]
        header_params = [p for p in params if p["in"] == "header"]

        # Parse request body
        body_info = self.parser.get_request_body_info(request_body)

        # Parse response type
        return_type = self.parser.get_response_type(responses)

        # Generate method signature
        sig_params = []
        if body_info:
            type_hint = body_info["type"]
            if not body_info["required"]:
                type_hint = f"{type_hint} | None"
                sig_params.append(f"body: {type_hint} = None")
            else:
                sig_params.append(f"body: {type_hint}")
        
        for p in params:
            type_hint = f"{p['type']} | None" if not p["required"] else p["type"]
            default = " = None" if not p["required"] else ""
            sig_params.append(f"{p['name']}: {type_hint}{default}")

        sig_params_str = ", ".join(sig_params)
        if sig_params_str:
            sig_params_str = ", " + sig_params_str

        # Generate method body
        body_lines = []

        # Add docstring
        if endpoint.get("summary") or endpoint.get("description"):
            doc = endpoint.get("summary", "") or endpoint.get("description", "")
            body_lines.append(f'        """\n        {doc}\n        """')

        # Path parameters
        if path_params:
            path_dict_items = [f'"{p["name"]}": str({p["name"]})' for p in path_params]
            body_lines.append(f"        path_params = {{{', '.join(path_dict_items)}}}")
            body_lines.append("")

        # Query parameters
        if query_params:
            req_query = [p for p in query_params if p["required"]]
            opt_query = [p for p in query_params if not p["required"]]

            if req_query:
                query_dict_items = [f'"{p["name"]}": str({p["name"]})' for p in req_query]
                body_lines.append(f"        query_params = {{{', '.join(query_dict_items)}}}")
            else:
                body_lines.append("        query_params = {}")

            for p in opt_query:
                body_lines.append(f"        if {p['name']} is not None:")
                body_lines.append(f"            query_params[\"{p['name']}\"] = str({p['name']})")
            body_lines.append("")

        # Header parameters
        if header_params:
            req_headers = [p for p in header_params if p["required"]]
            opt_headers = [p for p in header_params if not p["required"]]

            if req_headers:
                header_dict_items = [f'"{p["name"]}": str({p["name"]})' for p in req_headers]
                body_lines.append(f"        headers = {{{', '.join(header_dict_items)}}}")
            else:
                body_lines.append("        headers = {}")

            for p in opt_headers:
                body_lines.append(f"        if {p['name']} is not None:")
                body_lines.append(f"            headers[\"{p['name']}\"] = str({p['name']})")
            body_lines.append("")

        # Request body handling
        if body_info:
            if body_info["is_multipart"]:
                # Handle multipart form data (files and data)
                schema = body_info.get("schema", {})
                fields = self.parser.get_schema_fields(schema)

                body_lines.append("        files: dict[str, IO[Any]] = {}")
                body_lines.append("        data: dict[str, Any] = {}")
                body_lines.append("")
                body_lines.append("        # Process body fields to populate files and data dictionaries")
                body_lines.append("        if body is not None:")

                # Generate field processing logic
                for field in fields:
                    field_name = field["name"]
                    is_file = field["is_file"]

                    body_lines.append(f"            # Process field: {field_name}")
                    body_lines.append(f"            if hasattr(body, '{field_name}'):")
                    body_lines.append(f"                field_value = getattr(body, '{field_name}')")
                    body_lines.append("                if field_value is not None:")

                    if is_file:
                        # File field - add to files dict
                        body_lines.append("                    # File field")
                        body_lines.append(f"                    files['{field_name}'] = field_value")
                    else:
                        # Regular field - add to data dict, convert to string if needed
                        body_lines.append("                    # Data field")
                        body_lines.append(f"                    data['{field_name}'] = field_value")

                body_lines.append("")
            else:
                # JSON body - use model_dump for Pydantic v2
                body_lines.append("        json_body = body.model_dump(mode='json') if hasattr(body, 'model_dump') else body")
                body_lines.append("")

        # Build request call
        request_args = [
            f"type_={return_type}",
            f'method="{method}"',
            f'url="{path}"',
        ]

        if path_params:
            request_args.append("path_params=path_params")
        if query_params:
            request_args.append("params=query_params")
        if header_params:
            request_args.append("headers=headers")
        if body_info:
            if body_info["is_multipart"]:
                request_args.append("data=data")
                request_args.append("files=files")
            else:
                request_args.append("json=json_body")

        body_lines.append("        return self.api_client.request(")
        for i, arg in enumerate(request_args):
            comma = "," if i < len(request_args) - 1 else ""
            body_lines.append(f"            {arg}{comma}")
        body_lines.append("        )")

        method_body = "\n".join(body_lines)

        return f'''    def _build_for_{operation_id}(self{sig_params_str}) -> Coroutine[Any, Any, {return_type}]:
{method_body}'''

    def _generate_async_api_class(self, class_name: str, endpoints: list[dict[str, Any]]) -> str:
        """Generate async API class."""
        methods = []

        for endpoint in endpoints:
            method = self._generate_async_method(endpoint)
            methods.append(method)

        methods_code = "\n\n".join(methods)

        return f'''class Async{class_name}(_{class_name}):
{methods_code}'''

    def _generate_async_method(self, endpoint: dict[str, Any]) -> str:
        """Generate async method."""
        operation_id = endpoint["operation_id"]
        parameters = endpoint["parameters"]
        request_body = endpoint.get("request_body")
        responses = endpoint["responses"]

        # Parse parameters
        params = [self.parser.get_parameter_info(p) for p in parameters]

        # Parse request body
        body_info = self.parser.get_request_body_info(request_body)

        # Parse response type
        return_type = self.parser.get_response_type(responses)

        # Generate method signature
        sig_params = []
        call_params = []
        if body_info:
            type_hint = body_info["type"]
            if not body_info["required"]:
                type_hint = f"{type_hint} | None"
                sig_params.append(f"body: {type_hint} = None")
            else:
                sig_params.append(f"body: {type_hint}")
            call_params.append("body=body")

        for p in params:
            type_hint = f"{p['type']} | None" if not p["required"] else p["type"]
            default = " = None" if not p["required"] else ""
            sig_params.append(f"{p['name']}: {type_hint}{default}")
            call_params.append(f"{p['name']}={p['name']}")

        sig_params_str = ", ".join(sig_params)
        if sig_params_str:
            sig_params_str = ", " + sig_params_str

        call_params_str = ", ".join(call_params)

        # Add docstring
        doc = endpoint.get("summary", "") or endpoint.get("description", "")
        docstring = f'"""\n        {doc}\n        """' if doc else ""

        return f'''    async def {operation_id}(self{sig_params_str}) -> {return_type}:
        {docstring}
        return await self._build_for_{operation_id}({call_params_str})'''

    def _generate_sync_api_class(self, class_name: str, endpoints: list[dict[str, Any]]) -> str:
        """Generate sync API class."""
        methods = []

        for endpoint in endpoints:
            method = self._generate_sync_method(endpoint)
            methods.append(method)

        methods_code = "\n\n".join(methods)

        return f'''class Sync{class_name}(_{class_name}):
{methods_code}'''

    def _generate_sync_method(self, endpoint: dict[str, Any]) -> str:
        """Generate sync method."""
        operation_id = endpoint["operation_id"]
        parameters = endpoint["parameters"]
        request_body = endpoint.get("request_body")
        responses = endpoint["responses"]

        # Parse parameters
        params = [self.parser.get_parameter_info(p) for p in parameters]

        # Parse request body
        body_info = self.parser.get_request_body_info(request_body)

        # Parse response type
        return_type = self.parser.get_response_type(responses)

        # Generate method signature
        sig_params = []
        call_params = []

        if body_info:
            type_hint = body_info["type"]
            if not body_info["required"]:
                type_hint = f"{type_hint} | None"
                sig_params.append(f"body: {type_hint} = None")
            else:
                sig_params.append(f"body: {type_hint}")
            call_params.append("body=body")
        
        for p in params:
            type_hint = f"{p['type']} | None" if not p["required"] else p["type"]
            default = " = None" if not p["required"] else ""
            sig_params.append(f"{p['name']}: {type_hint}{default}")
            call_params.append(f"{p['name']}={p['name']}")

        sig_params_str = ", ".join(sig_params)
        if sig_params_str:
            sig_params_str = ", " + sig_params_str

        call_params_str = ", ".join(call_params)

        # Add docstring
        doc = endpoint.get("summary", "") or endpoint.get("description", "")
        docstring = f'"""\n        {doc}\n        """' if doc else ""

        return f'''    def {operation_id}(self{sig_params_str}) -> {return_type}:
        {docstring}
        coroutine = self._build_for_{operation_id}({call_params_str})
        return get_event_loop().run_until_complete(coroutine)'''

    def _generate_api_client(self):
        """Generate main ApiClient class."""
        click.echo("🏗️  Generating API client...")

        endpoints_by_tag = self.parser.get_endpoints_by_tag()
        tags = list(endpoints_by_tag.keys())

        # Generate API imports
        api_imports = []
        async_init = []
        sync_init = []

        for tag in tags:
            class_name = self._tag_to_class_name(tag)
            module_name = tag.replace("-", "_").replace(" ", "_")
            api_imports.append(f"from {self.import_name}.api.{module_name}_api import Async{class_name}, Sync{class_name}")
            async_init.append(f"        self.{module_name}_api = Async{class_name}(self.client)")
            sync_init.append(f"        self.{module_name}_api = Sync{class_name}(self.client)")

        api_imports_str = "\n".join(api_imports)
        async_init_str = "\n".join(async_init)
        sync_init_str = "\n".join(sync_init)

        content = f'''#
# Copyright (c) 2026 Project CHIP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from asyncio import get_event_loop
from typing import Any, Awaitable, Callable, Generic, Type, TypeVar, overload

from httpx import AsyncClient, Request, Response
from pydantic import TypeAdapter

{api_imports_str}
from {self.import_name}.exceptions import ResponseHandlingException, UnexpectedResponse

ClientT = TypeVar("ClientT", bound="ApiClient")


class AsyncApis(Generic[ClientT]):
    def __init__(self, client: ClientT):
        self.client = client

{async_init_str}


class SyncApis(Generic[ClientT]):
    def __init__(self, client: ClientT):
        self.client = client

{sync_init_str}


T = TypeVar("T")
Send = Callable[[Request], Awaitable[Response]]
MiddlewareT = Callable[[Request, Send], Awaitable[Response]]


class ApiClient:
    def __init__(self, host: str | None = None, **kwargs: Any) -> None:
        self.host = host
        self.middleware: MiddlewareT = BaseMiddleware()
        self._async_client = AsyncClient(**kwargs)

    async def aclose(self) -> None:
        await self._async_client.aclose()

    def close(self) -> None:
        get_event_loop().run_until_complete(self.aclose())

    @overload
    async def request(
        self, *, type_: Type[T], method: str, url: str, path_params: dict[str, Any] | None = None, **kwargs: Any
    ) -> T: ...

    @overload
    async def request(
        self, *, type_: None, method: str, url: str, path_params: dict[str, Any] | None = None, **kwargs: Any
    ) -> None: ...

    async def request(
        self, *, type_: Any, method: str, url: str, path_params: dict[str, Any] | None = None, **kwargs: Any
    ) -> Any:
        if path_params is None:
            path_params = {{}}
        url = (self.host or "") + url.format(**path_params)
        request = Request(method, url, **kwargs)
        return await self.send(request, type_)

    @overload
    def request_sync(self, *, type_: Type[T], **kwargs: Any) -> T: ...

    @overload
    def request_sync(self, *, type_: None, **kwargs: Any) -> None: ...

    def request_sync(self, *, type_: Any, **kwargs: Any) -> Any:
        """
        This method is not used by the generated apis, but is included for convenience
        """
        return get_event_loop().run_until_complete(self.request(type_=type_, **kwargs))

    async def send(self, request: Request, type_: Type[T]) -> T | str:
        response = await self.middleware(request, self.send_inner)
        if response.status_code in [200, 201]:
            try:
                # Use Pydantic v2 TypeAdapter for validation
                adapter = TypeAdapter(type_)
                if type_ == bytes:
                    return adapter.validate_python(response.content)
                return adapter.validate_python(response.json()) if type_ else response.text
            except Exception as e:
                raise ResponseHandlingException(e)
        raise UnexpectedResponse.for_response(response)

    async def send_inner(self, request: Request) -> Response:
        try:
            response = await self._async_client.send(request)
        except Exception as e:
            raise ResponseHandlingException(e)
        return response

    def add_middleware(self, middleware: MiddlewareT) -> None:
        current_middleware = self.middleware

        async def new_middleware(request: Request, call_next: Send) -> Response:
            async def inner_send(request: Request) -> Response:
                return await current_middleware(request, call_next)

            return await middleware(request, inner_send)

        self.middleware = new_middleware


class BaseMiddleware:
    async def __call__(self, request: Request, call_next: Send) -> Response:
        return await call_next(request)
'''

        api_client_file = self.output_dir / "api_client.py"
        api_client_file.write_text(content)
        click.echo(f"  ✓ Generated {api_client_file.relative_to(self.output_dir.parent)}")

    def _generate_exceptions(self):
        """Generate exceptions module."""
        click.echo("⚠️  Generating exceptions...")

        content = '''#
# Copyright (c) 2026 Project CHIP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from typing import Any

from httpx import Response


class ApiException(Exception):
    """Base exception for API client errors."""
    pass


class ResponseHandlingException(ApiException):
    """Exception raised when response handling fails."""

    def __init__(self, error: Exception):
        self.error = error
        super().__init__(f"Error handling response: {error}")


class UnexpectedResponse(ApiException):
    """Exception raised when response status is unexpected."""

    def __init__(self, status_code: int, content: Any):
        self.status_code = status_code
        self.content = content
        super().__init__(f"Unexpected response status: {status_code}")

    @classmethod
    def for_response(cls, response: Response) -> "UnexpectedResponse":
        """Create exception from httpx Response."""
        try:
            content = response.json()
        except Exception:
            content = response.text
        return cls(response.status_code, content)
'''

        exceptions_file = self.output_dir / "exceptions.py"
        exceptions_file.write_text(content)
        click.echo(f"  ✓ Generated {exceptions_file.relative_to(self.output_dir.parent)}")

    def _generate_init_files(self):
        """Generate __init__.py files."""
        click.echo("📝 Generating __init__.py files...")

        # Main package __init__.py
        main_init = f'''#
# Copyright (c) 2026 Project CHIP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Auto-generated API client for Test Harness."""

from {self.import_name}.api_client import ApiClient, AsyncApis, SyncApis
from {self.import_name}.exceptions import ApiException, ResponseHandlingException, UnexpectedResponse

__all__ = [
    "ApiClient",
    "AsyncApis",
    "SyncApis",
    "ApiException",
    "ResponseHandlingException",
    "UnexpectedResponse",
]
'''
        (self.output_dir / "__init__.py").write_text(main_init)

        # API package __init__.py
        endpoints_by_tag = self.parser.get_endpoints_by_tag()
        api_imports = []
        api_all = []

        for tag in endpoints_by_tag.keys():
            class_name = self._tag_to_class_name(tag)
            module_name = tag.replace("-", "_").replace(" ", "_")
            api_imports.append(f"from {self.import_name}.api.{module_name}_api import Async{class_name}, Sync{class_name}")
            api_all.extend([f'"{class_name}"', f'"Async{class_name}"', f'"Sync{class_name}"'])

        api_imports_str = "\n".join(api_imports)
        api_all_str = ", ".join(api_all)

        api_init = f'''#
# Copyright (c) 2026 Project CHIP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""API endpoint classes."""

{api_imports_str}

__all__ = [{api_all_str}]
'''
        (self.output_dir / "api" / "__init__.py").write_text(api_init)

        click.echo("  ✓ Generated __init__.py files")

    def _add_py_typed(self):
        """Add py.typed marker for PEP 561 compliance."""
        (self.output_dir / "py.typed").touch()
        click.echo("  ✓ Added py.typed marker")

    def _tag_to_class_name(self, tag: str) -> str:
        """Convert tag to PascalCase class name."""
        return "".join(word.capitalize() for word in tag.replace("-", "_").replace(" ", "_").split("_")) + "Api"


@click.command()
@click.option("--input", "-i", "input_spec", required=True, help="OpenAPI spec path or URL")
@click.option(
    "--output",
    "-o",
    "output_dir",
    default="th_cli/api_lib_autogen",
    help="Output directory (default: th_cli/api_lib_autogen)",
)
@click.option(
    "--import-name",
    "-n",
    default="th_cli.api_lib_autogen",
    help="Import name for the package (default: th_cli.api_lib_autogen)",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def main(input_spec: str, output_dir: str, import_name: str, verbose: bool):
    """
    Generate API client from OpenAPI specification.

    This is a modern replacement for the Docker-based openapi-generator approach.
    It uses datamodel-code-generator for Pydantic v2 models and generates clean,
    type-safe API client code with no postprocessing required.

    Example:
        python scripts/generate_client_v2.py --input openapi.json

        python scripts/generate_client_v2.py --input http://localhost/api/v1/openapi.json
    """
    try:
        output_path = Path(output_dir)
        generator = APIGenerator(input_spec, output_path, import_name)
        generator.generate()

        click.echo("\n✅ Success! Next steps:")
        click.echo(f"  1. Review generated code in {output_path}")
        click.echo("  2. Run: poetry run mypy " + str(output_path))
        click.echo("  3. Run: poetry run black " + str(output_path))
        click.echo("  4. Run: poetry run isort " + str(output_path))
        click.echo("  5. Run tests to verify everything works")

    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        if verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

"""MCP server for testdesiderata documentation.

Provides documentation access via Model Context Protocol.
Usage:
    claude mcp add testdesiderata --transport stdio \\
        python src/testdesiderata/mcp_server.py
"""

import logging
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource
from pydantic import AnyUrl, TypeAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Server("testdesiderata")
_url_adapter: TypeAdapter[AnyUrl] = TypeAdapter(AnyUrl)


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available documentation resources."""
    assert app is not None, "Server must be initialized"
    docs_dir = Path(__file__).parent.parent.parent / "docs"
    assert docs_dir.is_dir(), "Docs directory must exist and be a directory"

    resources: list[Resource] = []
    for doc_file in docs_dir.rglob("*.md"):
        relative_path = doc_file.relative_to(docs_dir)
        uri_str = f"doc://testdesiderata/{relative_path}"
        resources.append(
            Resource(
                uri=_url_adapter.validate_python(uri_str),
                name=str(relative_path),
                mimeType="text/markdown",
                description=f"Documentation: {relative_path}",
            )
        )
    return resources


@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read documentation content."""
    uri_str = str(uri)
    assert uri_str, "URI must not be empty"
    assert uri_str.startswith("doc://testdesiderata/"), "URI must be for this package"

    path = uri_str.replace("doc://testdesiderata/", "")
    docs_dir = Path(__file__).parent.parent.parent / "docs"
    doc_file = docs_dir / path

    assert doc_file.exists(), f"Documentation file {path} not found"
    assert doc_file.is_relative_to(docs_dir), "Path must be within docs directory"

    return doc_file.read_text()


async def main() -> None:
    """Run MCP server via stdio."""
    assert app is not None, "Server must be initialized"

    async with stdio_server() as (read_stream, write_stream):
        assert read_stream is not None, "Read stream must not be None"
        assert write_stream is not None, "Write stream must not be None"
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

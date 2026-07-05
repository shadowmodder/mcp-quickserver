"""Entry point: python -m mcpquickserver [--transport stdio|sse]

SSE host/port are configured via MCP_HOST / MCP_PORT env vars (default 127.0.0.1:8000).
"""
import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(description="mcp-quickserver")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="stdio (default, for Claude Desktop / Claude Code) or sse (HTTP)",
    )
    args = parser.parse_args()
    from .server import mcp
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()

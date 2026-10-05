"""CLI entrypoint.

    ai-employee-mcp keygen
    ai-employee-mcp serve --transport stdio
    ai-employee-mcp serve --transport http --port 8080
"""

from __future__ import annotations

import argparse
import sys

from .config import Settings
from .crypto import CredentialCipher
from .server import AppState, configure, mcp


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-employee-mcp")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("keygen", help="Print a fresh base64 AES-256 master key.")

    serve = sub.add_parser("serve", help="Run the MCP server.")
    serve.add_argument(
        "--transport",
        choices=("stdio", "http"),
        default="stdio",
        help="stdio for local agents; http (streamable) is required on Cloud Run.",
    )
    serve.add_argument("--host", default=None)
    serve.add_argument("--port", type=int, default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "keygen":
        print(CredentialCipher.generate_master_key())
        return 0

    try:
        settings = Settings()
    except Exception as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    try:
        configure(AppState.build(settings=settings))
    except RuntimeError as exc:
        print(f"Refusing to start: {exc}", file=sys.stderr)
        return 2

    host = args.host or settings.host
    port = args.port or settings.port

    if args.transport == "stdio":
        mcp.run(transport="stdio")
        return 0

    import uvicorn

    app = mcp.streamable_http_app()
    uvicorn.run(app, host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
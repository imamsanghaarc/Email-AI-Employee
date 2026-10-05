"""AI Employee MCP - one server for Odoo, Gmail and LinkedIn.

No LLM calls are made anywhere in this package. The connecting agent performs
all reasoning; this process performs I/O on behalf of the authenticated user.
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = ["__version__"]
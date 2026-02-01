"""Main entry point for GenAI Spine."""

from __future__ import annotations

import uvicorn

from genai_spine.api.app import create_app
from genai_spine.settings import get_settings

app = create_app()


def main() -> None:
    """Run the GenAI Spine server."""
    settings = get_settings()
    uvicorn.run(
        "genai_spine.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()

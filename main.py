#!/usr/bin/env python3
"""
Jira API Proxy Server Entry Point
"""

if __name__ == "__main__":
    import uvicorn
    from app.config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.proxy_host,
        port=settings.proxy_port,
        reload=settings.debug
    )

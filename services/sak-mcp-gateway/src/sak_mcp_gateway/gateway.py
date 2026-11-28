"""FastAPI HTTP Gateway implementing the Model Context Protocol (MCP) RemoteMCPServer."""

from __future__ import annotations

import json
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from sak_mcp_gateway.auth import AuthenticationError, EntraJWTValidator
from sak_mcp_gateway.config import GatewayConfig
from sak_mcp_gateway.tools import TOOL_DEFINITIONS, execute_tool


def create_app(config: GatewayConfig | None = None) -> FastAPI:
    cfg = config or GatewayConfig.from_env()
    validator = EntraJWTValidator(cfg)
    app = FastAPI(title="Sak MCP Gateway", version="1.0.0")

    async def get_token_claims(authorization: str | None = Header(None)) -> dict[str, Any]:
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid Authorization header format. Expected 'Bearer <token>'",
            )
        token = parts[1]
        try:
            return validator.validate_token(token)
        except AuthenticationError as err:
            raise HTTPException(status_code=401, detail=str(err)) from err

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "healthy",
            "service": "sak-mcp-gateway",
            "public_host": cfg.public_host,
            "version": "1.0.0",
        }

    @app.post("/mcp")
    async def mcp_endpoint(
        request: Request,
        claims: dict[str, Any] = Depends(get_token_claims),  # noqa: B008
    ) -> Response:
        try:
            body = await request.json()
        except Exception as err:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {err}"},
                },
            )

        req_id = body.get("id")
        method = body.get("method")
        params = body.get("params") or {}

        if not method:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32600, "message": "Invalid Request: missing method"},
                },
            )

        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "sak-mcp-gateway", "version": "1.0.0"},
            }
            return JSONResponse(content={"jsonrpc": "2.0", "id": req_id, "result": result})

        if method == "tools/list":
            return JSONResponse(
                content={"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOL_DEFINITIONS}}
            )

        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments") or {}
            try:
                out = execute_tool(tool_name, arguments)
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(out, indent=2)}],
                            "isError": not out.get("ok", True),
                        },
                    }
                )
            except Exception as err:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Error executing tool '{tool_name}': {err}",
                                }
                            ],
                            "isError": True,
                        },
                    }
                )

        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method '{method}' not found"},
            },
        )

    return app


app = create_app()

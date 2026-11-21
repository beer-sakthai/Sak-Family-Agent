"""CLI commands for the SakThai Runtime Gateway."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any

import click

from ..gateway.config import resolve_gateway_config
from ..gateway.server import RuntimeGatewayServer


def _make_request(
    url: str,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    token: str | None = None,
    timeout: float = 10.0,
) -> tuple[int, dict[str, Any] | str]:
    """Helper to execute HTTP requests against the gateway."""
    data = json.dumps(body).encode("utf-8") if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
            status_code = resp.status
            raw_text = resp.read().decode("utf-8")
            try:
                return status_code, json.loads(raw_text)
            except json.JSONDecodeError:
                return status_code, raw_text
    except urllib.error.HTTPError as err:
        err_text = err.read().decode("utf-8")
        try:
            return err.code, json.loads(err_text)
        except Exception:
            return err.code, err_text
    except Exception as exc:
        raise RuntimeError(f"Connection to gateway failed: {exc}") from exc


@click.group(name="gateway")
def gateway_cmd() -> None:
    """Manage the OpenAI-compatible and REST API Runtime Gateway."""


@gateway_cmd.command("serve")
@click.option("--host", "-h", default="127.0.0.1", help="Host address to bind.")
@click.option("--port", "-p", default=8080, type=int, help="Port number to bind.")
@click.option("--token", "-t", default=None, help="Bearer token for API authentication.")
@click.option("--cors", default=None, help="Allowed CORS origin header.")
@click.option(
    "--default-persona",
    default="sakthai",
    help="Default persona for unrouted chat requests.",
)
def serve_cmd(
    host: str,
    port: int,
    token: str | None,
    cors: str | None,
    default_persona: str,
) -> None:
    """Start the live Runtime Gateway HTTP server."""
    cfg = resolve_gateway_config(
        host=host,
        port=port,
        bearer_token=token,
        cors_origin=cors,
        default_persona=default_persona,
    )
    server = RuntimeGatewayServer(config=cfg)

    click.echo(f"🚀 Launching SakThai Runtime Gateway on http://{cfg.host}:{cfg.port}")
    click.echo(f"  Default Persona: {cfg.default_persona}")
    if cfg.bearer_token:
        click.echo("  Authentication:  Enabled (Bearer Token)")
    else:
        click.echo(
            "  Authentication:  NO TOKEN CONFIGURED — every request except /health "
            "will be refused (401).\n"
            "                   Pass --token, set SAKTHAI_GATEWAY_TOKEN, or run "
            "`sakthai web setup`."
        )
    click.echo("Press Ctrl+C to stop.\n")

    try:
        server.start(background=False)
    except KeyboardInterrupt:
        click.echo("\nStopping Runtime Gateway...")
        server.shutdown()
        click.echo("✓ Runtime Gateway stopped cleanly.")


@gateway_cmd.command("status")
@click.option("--url", "-u", default="http://127.0.0.1:8080", help="Gateway URL.")
@click.option("--token", "-t", default=None, help="Optional Bearer token.")
@click.option("--json", "as_json", is_flag=True, help="Emit status as JSON.")
def status_cmd(url: str, token: str | None, as_json: bool) -> None:
    """Check the health and operational status of a Runtime Gateway."""
    clean_url = url.rstrip("/")
    try:
        code, data = _make_request(f"{clean_url}/health", token=token)
        if as_json:
            click.echo(json.dumps(data, indent=2))
            return

        if code == 200 and isinstance(data, dict):
            click.echo(f"✓ Gateway Status:    {data.get('status', 'ok').upper()}")
            click.echo(f"  Version:           {data.get('version')}")
            click.echo(f"  Uptime:            {data.get('uptime_seconds')}s")
            click.echo(f"  Active Personas:   {', '.join(data.get('personas', []))}")
            click.echo(f"  Available Models:  {data.get('models_count')}")
            click.echo(f"  Registered Tools:  {data.get('tools_count')}")
        else:
            click.echo(f"❌ Gateway returned status {code}: {data}", err=True)
            sys.exit(1)
    except Exception as exc:
        click.echo(f"❌ Failed to reach Gateway at {clean_url}: {exc}", err=True)
        sys.exit(1)


@gateway_cmd.command("models")
@click.option("--url", "-u", default="http://127.0.0.1:8080", help="Gateway URL.")
@click.option("--token", "-t", default=None, help="Optional Bearer token.")
@click.option("--json", "as_json", is_flag=True, help="Emit models list as JSON.")
def models_cmd(url: str, token: str | None, as_json: bool) -> None:
    """List models and personas served by the Runtime Gateway."""
    clean_url = url.rstrip("/")
    try:
        code, data = _make_request(f"{clean_url}/v1/models", token=token)
        if as_json:
            click.echo(json.dumps(data, indent=2))
            return

        if code == 200 and isinstance(data, dict) and "data" in data:
            models_list = data["data"]
            click.echo(f"Models served by Gateway at {clean_url} ({len(models_list)}):")
            for m in models_list:
                m_id = m.get("id")
                desc = m.get("description", "")
                owner = m.get("owned_by", "")
                click.echo(f"  • {m_id:<32} ({owner}) - {desc}")
        else:
            click.echo(f"❌ Failed to retrieve models (status {code}): {data}", err=True)
            sys.exit(1)
    except Exception as exc:
        click.echo(f"❌ Error querying Gateway: {exc}", err=True)
        sys.exit(1)


@gateway_cmd.command("chat")
@click.argument("prompt", type=str)
@click.option("--url", "-u", default="http://127.0.0.1:8080", help="Gateway URL.")
@click.option("--model", "-m", default="sakthai", help="Target model or persona name.")
@click.option("--token", "-t", default=None, help="Optional Bearer token.")
@click.option("--stream", "-s", is_flag=True, help="Stream response tokens.")
def chat_cmd(prompt: str, url: str, model: str, token: str | None, stream: bool) -> None:
    """Send a chat completion request to the Runtime Gateway."""
    clean_url = url.rstrip("/")
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": stream,
    }

    if not stream:
        try:
            code, data = _make_request(
                f"{clean_url}/v1/chat/completions", method="POST", body=body, token=token
            )
            if code == 200 and isinstance(data, dict):
                choices = data.get("choices", [])
                if choices and "message" in choices[0]:
                    click.echo(choices[0]["message"].get("content", ""))
                else:
                    click.echo(json.dumps(data, indent=2))
            else:
                click.echo(f"❌ Request failed (status {code}): {data}", err=True)
                sys.exit(1)
        except Exception as exc:
            click.echo(f"❌ Error communicating with Gateway: {exc}", err=True)
            sys.exit(1)
    else:
        # Streaming SSE
        import urllib.request

        data_bytes = json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(
            f"{clean_url}/v1/chat/completions", data=data_bytes, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30.0) as resp:  # nosec B310
                for line in resp:
                    decoded = line.decode("utf-8").strip()
                    if not decoded.startswith("data: "):
                        continue
                    payload = decoded[6:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                sys.stdout.write(content)
                                sys.stdout.flush()
                    except json.JSONDecodeError:
                        pass
                click.echo()
        except Exception as exc:
            click.echo(f"\n❌ Streaming error: {exc}", err=True)
            sys.exit(1)


@gateway_cmd.command("bench")
@click.option("--concurrency", "-c", default=10, type=int, help="Number of concurrent workers.")
@click.option("--requests", "-n", default=50, type=int, help="Total benchmark requests.")
@click.option("--persona", "-p", default="sakjules", help="Target persona to benchmark.")
@click.option("--stream/--no-stream", default=True, help="Benchmark streaming SSE vs buffered.")
@click.option("--json", "as_json", is_flag=True, help="Output benchmark results as JSON.")
def bench_cmd(
    concurrency: int,
    requests: int,
    persona: str,
    stream: bool,
    as_json: bool,
) -> None:
    """Run high-concurrency performance and TTFT benchmarks against the Gateway."""
    from ..gateway.bench import run_gateway_benchmark

    result = run_gateway_benchmark(
        concurrency=concurrency,
        num_requests=requests,
        persona=persona,
        stream=stream,
    )
    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    lat = result["latency_ms"]
    ttft = result["ttft_ms"]
    click.echo(
        f"⚡ SakThai Gateway Benchmark ({result['requests']} reqs @ {result['concurrency']} workers)"
    )
    click.echo(f"  • Persona      : {result['persona']} (stream={result['stream']})")
    click.echo(
        f"  • Throughput   : {result['requests_per_sec']} req/s | {result['tokens_per_sec']} tok/s"
    )
    click.echo(
        f"  • Latency (ms) : avg={lat['avg']} | p50={lat['p50']} | p95={lat['p95']} | p99={lat['p99']}"
    )
    click.echo(
        f"  • TTFT (ms)    : avg={ttft['avg']} | p50={ttft['p50']} | p95={ttft['p95']} | p99={ttft['p99']}"
    )
    click.echo(f"  • Errors       : {result['errors']}")

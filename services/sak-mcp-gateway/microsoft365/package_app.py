"""Package Microsoft 365 Copilot Declarative Agent with MCP plugin schema v2.4."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path


def validate_json_file(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Missing required file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise ValueError(f"Malformed JSON in {path}: {err}") from err
    return data


def validate_package(m365_dir: Path, strict: bool = False) -> list[str]:
    warnings: list[str] = []

    # 1. Manifest
    manifest_path = m365_dir / "manifest.json"
    manifest = validate_json_file(manifest_path)
    if manifest.get("manifestVersion") != "1.17":
        warnings.append(
            f"Expected manifestVersion '1.17', found {manifest.get('manifestVersion')!r}"
        )

    # 2. Declarative Agent
    da_path = m365_dir / "declarativeAgent.json"
    validate_json_file(da_path)

    # 3. AI Plugin
    plugin_path = m365_dir / "ai-plugin.json"
    plugin = validate_json_file(plugin_path)
    if plugin.get("schema_version") not in ("2.4", "v2.4"):
        warnings.append(
            f"Expected schema_version '2.4' or 'v2.4', found {plugin.get('schema_version')!r}"
        )
    mcp_cap = plugin.get("capabilities", {}).get("mcp", {})
    if mcp_cap.get("type") != "RemoteMCPServer":
        warnings.append(
            f"Expected mcp capability type 'RemoteMCPServer', found {mcp_cap.get('type')!r}"
        )

    # 4. Icons
    color_icon = m365_dir / "assets" / "color.png"
    outline_icon = m365_dir / "assets" / "outline.png"
    if not color_icon.is_file():
        warnings.append(f"Missing color icon at {color_icon}")
    if not outline_icon.is_file():
        warnings.append(f"Missing outline icon at {outline_icon}")

    # 5. Placeholder check if strict
    placeholders = ("YOUR_DOMAIN.example", "YOUR_AUTH_CONFIG_ID", "YOUR_EMAIL@example.com")
    for f in (manifest_path, da_path, plugin_path):
        content = f.read_text(encoding="utf-8")
        found = [p for p in placeholders if p in content]
        if found:
            msg = f"File {f.name} contains unresolved placeholder(s): {', '.join(found)}"
            if strict:
                raise ValueError(msg)
            warnings.append(msg)

    return warnings


def package_app(m365_dir: Path, output_zip: Path, strict: bool = False) -> None:
    warnings = validate_package(m365_dir, strict=strict)
    for w in warnings:
        print(f"[WARN] {w}", file=sys.stderr)

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(m365_dir / "manifest.json", "manifest.json")
        zf.write(m365_dir / "declarativeAgent.json", "declarativeAgent.json")
        zf.write(m365_dir / "ai-plugin.json", "ai-plugin.json")
        zf.write(m365_dir / "assets" / "color.png", "color.png")
        zf.write(m365_dir / "assets" / "outline.png", "outline.png")

    print(f"[OK] Packaged M365 Copilot agent package to: {output_zip}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Package Microsoft 365 Copilot agent")
    parser.add_argument(
        "--dir", type=Path, default=Path(__file__).parent, help="Directory containing manifests"
    )
    parser.add_argument(
        "--out", type=Path, default=Path("sak-family-m365.zip"), help="Output ZIP archive"
    )
    parser.add_argument("--strict", action="store_true", help="Disallow placeholders")
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate without generating ZIP archive"
    )
    args = parser.parse_args()

    m365_dir = args.dir.resolve()
    if args.dry_run:
        warnings = validate_package(m365_dir, strict=args.strict)
        for w in warnings:
            print(f"[WARN] {w}", file=sys.stderr)
        print(f"[OK] Validation successful for {m365_dir}")
        return

    package_app(m365_dir, args.out.resolve(), strict=args.strict)


if __name__ == "__main__":
    main()

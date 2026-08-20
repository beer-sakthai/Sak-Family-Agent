from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from sakthai.memory.store import MemoryStore

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "setup_servicequotebot.py"
SCRIPT_SPEC = importlib.util.spec_from_file_location("setup_servicequotebot", SCRIPT_PATH)
assert SCRIPT_SPEC is not None and SCRIPT_SPEC.loader is not None
SCRIPT_MODULE = importlib.util.module_from_spec(SCRIPT_SPEC)
sys.modules[SCRIPT_SPEC.name] = SCRIPT_MODULE
SCRIPT_SPEC.loader.exec_module(SCRIPT_MODULE)

build_customer_bundle = SCRIPT_MODULE.build_customer_bundle
parse_user_ids = SCRIPT_MODULE.parse_user_ids


def test_parse_user_ids_accepts_commas_and_spaces() -> None:
    assert parse_user_ids("123, 456 789") == [123, 456, 789]


def test_build_customer_bundle_writes_env_service_and_ingests_price_book(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    price_book = tmp_path / "price-book.md"
    price_book.write_text(
        "# Price Book\n\n- Window cleaning -> $100\n- Gutter cleaning -> $150\n",
        encoding="utf-8",
    )

    bundle = build_customer_bundle(
        repo_root=repo_root,
        target_dir=tmp_path / "bundle",
        price_book=price_book,
        anthropic_api_key="sk-test",
        telegram_bot_token="123:abc",
        telegram_allowed_user_ids=[123, 456],
    )

    assert bundle.env_file.read_text(encoding="utf-8") == (
        f"ANTHROPIC_API_KEY=sk-test\n"
        f"TELEGRAM_BOT_TOKEN=123:abc\n"
        "TELEGRAM_ALLOWED_USER_IDS=123,456\n"
        f"SAKTHAI_HOME={bundle.state_dir}\n"
    )
    assert repo_root.as_posix() in bundle.service_file.read_text(encoding="utf-8")
    assert str(bundle.env_file) in bundle.service_file.read_text(encoding="utf-8")
    assert bundle.price_book_copy.exists()

    with MemoryStore(bundle.memory_db) as store:
        snapshot = store.export_to_dict()

    assert len(snapshot["facts"]) == 2

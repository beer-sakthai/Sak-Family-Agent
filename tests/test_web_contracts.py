"""Tests for the shared web contract and its TypeScript generator.

The contract in ``sakthai/web/contracts.py`` is the single definition both
runtimes agree on. These tests defend two properties: the generator's output is
deterministic (so ``git diff --exit-code`` is a valid staleness check in CI),
and the committed ``contracts.generated.ts`` actually matches the contract.
"""

from __future__ import annotations

import importlib.util
import sys
import typing
from pathlib import Path
from typing import Any, Literal, get_origin

import pytest

from sakthai.web import contracts

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = REPO_ROOT / "scripts" / "gen_dashboard_types.py"


def _load_generator() -> Any:
    """Import the generator by path — ``scripts/`` is not an importable package."""
    spec = importlib.util.spec_from_file_location("gen_dashboard_types", GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen() -> Any:
    return _load_generator()


class TestContractModule:
    def test_all_names_exist(self) -> None:
        for name in contracts.__all__:
            assert hasattr(contracts, name), f"__all__ names missing member {name}"

    def test_all_has_no_duplicates(self) -> None:
        # Duplicates would emit the same interface twice and still round-trip
        # the determinism check, so assert it directly.
        assert len(contracts.__all__) == len(set(contracts.__all__))

    def test_every_exported_member_is_emittable(self) -> None:
        """Only string constants, Literal aliases, and TypedDicts are allowed."""
        for name in contracts.__all__:
            obj = getattr(contracts, name)
            emittable = (
                isinstance(obj, str) or typing.is_typeddict(obj) or get_origin(obj) is Literal
            )
            assert emittable, f"contracts.{name} is not an emittable kind: {type(obj)!r}"

    def test_data_source_values(self) -> None:
        assert typing.get_args(contracts.DataSource) == ("local", "api", "demo")

    def test_unattributed_is_not_a_persona_name(self) -> None:
        """The bucket must not collide with a real persona."""
        from sakthai.config import PERSONA_NAMES

        assert contracts.UNATTRIBUTED not in PERSONA_NAMES

    def test_envelope_is_generic(self) -> None:
        assert getattr(contracts.ApiEnvelope, "__parameters__", ()) != ()

    def test_session_persona_is_optional(self) -> None:
        """Sessions written before persona attribution must stay representable."""
        hints = typing.get_type_hints(contracts.SessionSummary)
        assert type(None) in typing.get_args(hints["persona"])


class TestRenderType:
    @pytest.mark.parametrize(
        ("annotation", "expected"),
        [
            (str, "string"),
            (bool, "boolean"),
            (int, "number"),
            (float, "number"),
            (object, "unknown"),
            (list[str], "string[]"),
            (dict[str, int], "Record<string, number>"),
            (Literal["a", "b"], '"a" | "b"'),
        ],
    )
    def test_primitives_and_containers(self, gen: Any, annotation: Any, expected: str) -> None:
        assert gen.render_type(annotation) == expected

    def test_bool_renders_before_int(self, gen: Any) -> None:
        """bool subclasses int; a naive issubclass check would emit `number`."""
        assert gen.render_type(bool) == "boolean"

    def test_optional_renders_as_null_union(self, gen: Any) -> None:
        assert gen.render_type(int | None) == "number | null"

    def test_list_of_union_is_parenthesised(self, gen: Any) -> None:
        """`A | null[]` would parse as `A | (null[])` — the parens matter."""
        assert gen.render_type(list[int | None]) == "(number | null)[]"

    def test_typeddict_renders_as_its_name(self, gen: Any) -> None:
        assert gen.render_type(contracts.TokenStats) == "TokenStats"

    def test_alias_map_is_preferred_over_inlining(self, gen: Any) -> None:
        aliases = gen._alias_names()
        assert gen.render_type(contracts.DataSource, aliases) == "DataSource"
        # Without the map it still renders, just inlined.
        assert gen.render_type(contracts.DataSource) == '"local" | "api" | "demo"'

    def test_unsupported_annotation_raises(self, gen: Any) -> None:
        class NotAContractType:
            pass

        with pytest.raises(gen.UnsupportedAnnotation):
            gen.render_type(NotAContractType)

    def test_non_str_dict_key_raises(self, gen: Any) -> None:
        with pytest.raises(gen.UnsupportedAnnotation):
            gen.render_type(dict[int, str])


class TestRenderMember:
    def test_string_constant(self, gen: Any) -> None:
        assert gen.render_member("X", "hello", {}) == 'export const X = "hello";'

    def test_literal_alias_does_not_self_reference(self, gen: Any) -> None:
        """Rendering the alias's own declaration must not emit `= DataSource`."""
        aliases = gen._alias_names()
        rendered = gen.render_member("DataSource", contracts.DataSource, aliases)
        assert rendered == 'export type DataSource = "local" | "api" | "demo";'

    def test_generic_typeddict_gets_a_default_param(self, gen: Any) -> None:
        rendered = gen.render_member("ApiEnvelope", contracts.ApiEnvelope, {})
        assert rendered.startswith("export interface ApiEnvelope<T = unknown> {")
        assert "  data: T;" in rendered

    def test_unsupported_member_kind_raises(self, gen: Any) -> None:
        with pytest.raises(gen.UnsupportedAnnotation):
            gen.render_member("nope", 42, {})


class TestGeneratedFile:
    def test_generation_is_deterministic(self, gen: Any) -> None:
        assert gen.generate() == gen.generate()

    def test_banner_carries_no_timestamp(self, gen: Any) -> None:
        """A timestamp would make `git diff --exit-code` fail on every run."""
        banner = gen.generate().split("\n\n", 1)[0]
        assert "DO NOT EDIT" in banner
        assert not any(char.isdigit() for char in banner)

    def test_every_exported_name_appears(self, gen: Any) -> None:
        rendered = gen.generate()
        for name in contracts.__all__:
            assert name in rendered, f"{name} missing from generated output"

    def test_committed_file_is_up_to_date(self, gen: Any) -> None:
        """The check CI runs. If this fails, run scripts/gen_dashboard_types.py."""
        assert gen.OUTPUT_PATH.exists(), f"{gen.OUTPUT_PATH} has never been generated"
        committed = gen.OUTPUT_PATH.read_text(encoding="utf-8")
        assert committed == gen.generate(), (
            "contracts.generated.ts is stale; run scripts/gen_dashboard_types.py"
        )

    def test_check_mode_passes_when_current(self, gen: Any, capsys: Any) -> None:
        assert gen.main(["--check"]) == 0
        assert "up to date" in capsys.readouterr().out

    def test_check_mode_fails_when_stale(
        self, gen: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Any
    ) -> None:
        stale = tmp_path / "contracts.generated.ts"
        stale.write_text("// stale\n", encoding="utf-8")
        monkeypatch.setattr(gen, "OUTPUT_PATH", stale)
        monkeypatch.setattr(gen, "REPO_ROOT", tmp_path)
        assert gen.main(["--check"]) == 1
        assert "stale" in capsys.readouterr().out

    def test_check_mode_fails_when_missing(
        self, gen: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(gen, "OUTPUT_PATH", tmp_path / "absent.ts")
        monkeypatch.setattr(gen, "REPO_ROOT", tmp_path)
        assert gen.main(["--check"]) == 1

    def test_write_mode_creates_parent_dirs(
        self, gen: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        target = tmp_path / "nested" / "dir" / "contracts.generated.ts"
        monkeypatch.setattr(gen, "OUTPUT_PATH", target)
        monkeypatch.setattr(gen, "REPO_ROOT", tmp_path)
        assert gen.main([]) == 0
        assert target.read_text(encoding="utf-8") == gen.generate()

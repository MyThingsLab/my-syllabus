from __future__ import annotations

from pathlib import Path

import pytest

from mysyllabus.cli import main

_PROGRAM = (
    "Unsupervised Learning program. Module 1: latent-variable models. "
    "Module 2: k-means and Gaussian mixture models."
)


@pytest.fixture
def program(tmp_path: Path) -> Path:
    p = tmp_path / "program.txt"
    p.write_text(_PROGRAM, encoding="utf-8")
    return p


def test_noop_decompose_is_soft_failure(program: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # No Engine -> no topics -> exit 1, but the program was read (not "not found").
    rc = main(["decompose", "--program", str(program)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "no program files" not in out


def test_missing_program_files_is_an_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(["decompose", "--program", str(tmp_path / "nope")])
    assert rc == 1
    assert "no program files found" in capsys.readouterr().out


def test_out_writes_a_toml_file(program: Path, tmp_path: Path, monkeypatch) -> None:
    # Scripted engine via a fake so the CLI produces real topics without billing.
    from mythings.testing import ScriptedEngine

    import mysyllabus.cli as cli

    reply = '{"topics": [{"title": "k-means", "unit": "Clustering"}]}'
    monkeypatch.setattr(cli, "_engine", lambda _name: ScriptedEngine(reply=reply))
    out = tmp_path / "topics.toml"
    rc = main(["decompose", "--program", str(program), "--engine", "claude", "--out", str(out)])
    assert rc == 0
    assert out.exists()
    assert 'slug = "k-means"' in out.read_text(encoding="utf-8")

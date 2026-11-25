"""The Linux loader reads DT_NEEDED to preload the Intel runtimes that a pip
install puts in <prefix>/lib (see pywfm._dll._open)."""
import platform
import shutil

import pytest

from pywfm import _dll


@pytest.mark.unit
def test_elf_needed_of_non_elf_is_empty(tmp_path):
    f = tmp_path / "not_elf.so"
    f.write_bytes(b"not an ELF file")
    assert _dll._elf_needed(f) == []
    assert _dll._elf_needed(tmp_path / "missing.so") == []


@pytest.mark.unit
@pytest.mark.skipif(platform.system() != "Linux", reason="ELF only")
def test_elf_needed_lists_libc():
    ls = shutil.which("ls")
    assert "libc.so.6" in _dll._elf_needed(ls)


@pytest.mark.unit
def test_runtime_needed_orders_dependencies_first(tmp_path, monkeypatch):
    # a needs b and c; b needs c: c must come before b, and b before a's load
    deps = {"a": ["b", "c", "libc.so.6"], "b": ["c"], "c": []}
    for name in deps:
        (tmp_path / name).write_bytes(b"")
    monkeypatch.setattr(_dll, "_elf_needed", lambda p: deps.get(getattr(p, "name", p), []))
    order = [p.name for p in _dll._runtime_needed("a", tmp_path, [], set())]
    assert order == ["c", "b"]

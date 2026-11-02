from __future__ import annotations

import shutil

import pytest

from econlab import core

PUBLIC_CACHE = core.RAW


@pytest.fixture
def lab(tmp_path, monkeypatch):
    """Disposable database with real public cache; never mutates the demo database."""
    shutil.copytree(PUBLIC_CACHE, tmp_path / "data/raw")
    for key, value in {"ROOT": tmp_path, "RAW": tmp_path / "data/raw",
                       "DB": tmp_path / "data/econ_lab.db", "OUT": tmp_path / "outputs"}.items():
        monkeypatch.setattr(core, key, value)
    core.reset()
    return tmp_path

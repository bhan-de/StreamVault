"""Smoke test: the virtual environment has every agreed library."""
import importlib
import pytest

@pytest.mark.parametrize("module", [
    "requests", "requests_cache", "tenacity", "pandas", "numpy", "pyarrow", "dotenv",
])
def test_import(module):
    importlib.import_module(module)

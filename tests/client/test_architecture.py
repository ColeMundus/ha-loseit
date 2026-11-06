"""Client boundary contracts, using only synthetic values and local imports."""

import dataclasses
import subprocess
import sys

import pytest
from test_client import PATH, load
from test_daily import DAY, dated_empty_wire


@pytest.mark.parametrize(
    "name",
    [
        "Account",
        "DailySnapshot",
        "LoseItError",
        "LoseItAuthError",
        "LoseItAccessError",
        "LoseItProtocolError",
        "LoseItConnectionError",
        "LoseItRateLimitError",
    ],
)
def test_public_client_imports_are_the_original_model_types(name):
    assert getattr(load(), name) is getattr(load("models"), name)


def test_result_models_remain_frozen_and_missing_metrics_remain_unknown():
    models = load("models")
    snapshot = models.DailySnapshot(DAY)
    assert snapshot.food_kcal is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        snapshot.food_kcal = 0
    with pytest.raises(dataclasses.FrozenInstanceError):
        models.Account("731").account_id = "732"


def test_decoder_and_projection_share_objects_and_public_results():
    gwt = load("gwt")
    response = gwt.decode_response(dated_empty_wire())
    fields = gwt.fields(response, "LoseItRemoteServiceResponse")
    snapshot = load("snapshot").parse_daily(fields[3], DAY)
    assert type(snapshot) is load().DailySnapshot
    assert snapshot.day == DAY
    assert snapshot.logged_food_count == 0


def test_pure_modules_import_without_home_assistant_or_transport():
    # A fresh interpreter makes this independent of HA's full-suite imports.
    # Use the real source files and relative imports, not a copied implementation.
    code = f"""
import importlib
import importlib.util
import sys
spec = importlib.util.spec_from_loader('pure_loseit', loader=None, is_package=True)
package = importlib.util.module_from_spec(spec)
package.__path__ = [{str(PATH)!r}]
sys.modules[spec.name] = package
for name in ('models', 'schemas', 'gwt', 'protocol', 'snapshot'):
    importlib.import_module('pure_loseit.' + name)
assert not any(
    n == 'homeassistant' or n.startswith('homeassistant.') for n in sys.modules
)
assert 'aiohttp' not in sys.modules
importlib.import_module('pure_loseit.client')
assert not any(
    n == 'homeassistant' or n.startswith('homeassistant.') for n in sys.modules
)
"""
    subprocess.run([sys.executable, "-I", "-c", code], check=True, capture_output=True)

"""Unit tests for Novo Nordisk Research Data Services client (nn_data_service)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest

from druggability.nn_data_service import (
    NNDataServiceClient,
    escape_odata_string,
)


def test_escape_odata_string() -> None:
    assert escape_odata_string("GLP1R") == "GLP1R"
    assert escape_odata_string("O'Brien's") == "O''Brien''s"


def test_token_cache_read_and_expiry(tmp_path: Path) -> None:
    cache_file = tmp_path / "token.json"
    client = NNDataServiceClient(token_cache_path=cache_file)
    assert client.get_access_token() is None

    # Save valid token
    client._save_token_cache({"access_token": "tok_valid_123", "expires_in": 3600})
    assert client.get_access_token() == "tok_valid_123"

    # Expired token without refresh_token returns None
    cache_file.write_text(
        json.dumps({"access_token": "tok_old", "expires_at": time.time() - 10}),
        encoding="utf-8",
    )
    assert client.get_access_token(auto_refresh=False) is None


def test_render_molblock_invalid_format(tmp_path: Path) -> None:
    client = NNDataServiceClient(token_cache_path=tmp_path / "tok.json")
    with pytest.raises(ValueError, match="image_format"):
        client.render_molblock("M  END", image_format=99)


def test_domain_queries_construct_expected_odata_params(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = NNDataServiceClient(
        token="dummy_bearer_token",
        token_cache_path=tmp_path / "tok.json",
    )
    captured: list[tuple[str, str, dict[str, Any] | None]] = []

    def fake_odata_get(
        service: str, entity_path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        captured.append((service, entity_path, params))
        return {"value": [{"Id": 1}]}

    monkeypatch.setattr(client, "odata_get", fake_odata_get)

    res_sirna = client.search_sirna_pools("inhbe", top=10)
    assert res_sirna == [{"Id": 1}]
    svc, path, params = captured[-1]
    assert svc == "NNSamples"
    assert path == "Pools"
    assert params is not None
    assert "INHBE" in params["$filter"]
    assert params["$expand"] == "Samples"

    res_struct = client.search_internal_structures("GLP1R", top=5)
    assert res_struct == [{"Id": 1}]
    svc, path, params = captured[-1]
    assert svc == "NNStructures"
    assert path == "PDBFiles"
    assert params is not None
    assert "contains(Name,'GLP1R')" in params["$filter"]

    res_results = client.get_compound_results("0113-0000-1001", top=20)
    assert res_results == [{"Id": 1}]
    svc, path, params = captured[-1]
    assert svc == "NNResults"
    assert path == "Results"
    assert params is not None
    assert "0113-0000-1001" in params["$filter"]
    assert params["$expand"] == "ExperimentVarResults"

    res_eln = client.search_eln_experiments("myotube", owner="igwu", top=15)
    assert res_eln == [{"Id": 1}]
    svc, path, params = captured[-1]
    assert svc == "NNExperiments"
    assert path == "Experiments"
    assert params is not None
    assert "contains(Name,'myotube')" in params["$filter"]
    assert "OwnedBy eq 'IGWU'" in params["$filter"]

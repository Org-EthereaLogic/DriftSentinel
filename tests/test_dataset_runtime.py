"""Tests for trusted dataset loading used by dataset-backed orchestration."""

from __future__ import annotations

import gzip
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.orc as orc  # type: ignore[import-untyped]
import pytest
from deltalake import write_deltalake
from fastavro import writer as avro_writer
from pandas.testing import assert_frame_equal

from driftsentinel.orchestration import dataset_runtime
from driftsentinel.orchestration.dataset_runtime import (
    load_baseline_dataset,
    load_current_dataset,
    load_tabular_dataset,
)


def _contract(path: str) -> dict[str, Any]:
    return {
        "dataset": {"name": "runtime_ds", "contract_version": "1.0.0"},
        "source": {
            "system": "pytest",
            "format": "csv",
            "landing_path": path,
        },
        "contract": {
            "required_columns": [{"column_name": "id", "type": "long", "nullable": False}],
            "business_key": ["id"],
            "batch_identifier": "batch_id",
        },
    }


def test_load_current_dataset_csv(tmp_path: Path) -> None:
    path = tmp_path / "current.csv"
    pd.DataFrame([
        {"id": 1, "batch_id": "B-1", "amount": 10.0},
        {"id": 2, "batch_id": "B-1", "amount": 11.0},
    ]).to_csv(path, index=False)

    loaded = load_current_dataset(_contract(str(path)))

    assert loaded.source_format == "csv"
    assert loaded.frame.shape == (2, 3)
    assert loaded.files_loaded == (str(path),)


def test_load_current_dataset_csv_gz_with_read_options(tmp_path: Path) -> None:
    path = tmp_path / "current.csv.gz"
    path.write_bytes(gzip.compress(b"id,amount\n1,10\n2,20\n"))
    contract = _contract(str(path))
    contract["source"]["read_options"] = {"compression": "gzip"}

    loaded = load_current_dataset(contract)

    assert loaded.source_format == "csv"
    assert loaded.frame.shape == (2, 2)
    assert loaded.frame["id"].tolist() == [1, 2]


def test_load_current_dataset_headerless_csv_gz_with_names(tmp_path: Path) -> None:
    path = tmp_path / "noaa_like.csv.gz"
    path.write_bytes(
        gzip.compress(b"STATION,20240101,PRCP,0,,,C,\nSTATION,20240102,TMAX,10,,,C,\n")
    )
    contract = _contract(str(path))
    contract["source"]["read_options"] = {
        "compression": "gzip",
        "header": None,
        "names": ["station_id", "obs_date", "element", "value", "mflag", "qflag", "sflag", "obstime"],
    }

    loaded = load_current_dataset(contract)

    assert loaded.frame.columns.tolist() == [
        "station_id", "obs_date", "element", "value", "mflag", "qflag", "sflag", "obstime",
    ]
    assert loaded.frame.iloc[0]["element"] == "PRCP"


def test_load_tabular_dataset_parquet(tmp_path: Path) -> None:
    path = tmp_path / "baseline.parquet"
    expected = pd.DataFrame([
        {"id": 1, "batch_id": "B-1", "amount": 10.0},
        {"id": 2, "batch_id": "B-1", "amount": 11.0},
    ])
    expected.to_parquet(path, index=False)

    loaded = load_tabular_dataset(path, "parquet", context="Test parquet path")

    assert loaded.source_format == "parquet"
    assert loaded.frame.equals(expected)


def test_load_tabular_dataset_tsv(tmp_path: Path) -> None:
    path = tmp_path / "baseline.tsv"
    path.write_text("id\tbatch_id\tamount\n1\tB-1\t10.0\n2\tB-1\t11.0\n", encoding="utf-8")

    loaded = load_tabular_dataset(path, "tsv", context="Test tsv path")

    assert loaded.source_format == "tsv"
    assert loaded.frame["amount"].tolist() == [10.0, 11.0]


def test_load_tabular_dataset_rejects_schema_mismatched_csv_directory(tmp_path: Path) -> None:
    root = tmp_path / "csv_dir"
    root.mkdir()
    (root / "part-1.csv").write_text("id,batch_id,amount\n1,B-1,10.0\n", encoding="utf-8")
    (root / "part-2.csv").write_text("id,batch_id,total\n2,B-1,11.0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="schema-mismatched files"):
        load_tabular_dataset(root, "csv", context="Test csv dir")


def test_load_tabular_dataset_txt_with_sniffed_delimiter(tmp_path: Path) -> None:
    path = tmp_path / "baseline.txt"
    path.write_text("id|batch_id|amount\n1|B-1|10.0\n2|B-1|11.0\n", encoding="utf-8")

    loaded = load_tabular_dataset(path, "txt", context="Test txt path")

    assert loaded.source_format == "txt"
    assert loaded.frame.columns.tolist() == ["id", "batch_id", "amount"]


def test_load_tabular_dataset_excel(tmp_path: Path) -> None:
    path = tmp_path / "baseline.xlsx"
    expected = pd.DataFrame([
        {"id": 1, "batch_id": "B-1", "amount": 10.0},
        {"id": 2, "batch_id": "B-1", "amount": 11.0},
    ])
    expected.to_excel(path, index=False)

    loaded = load_tabular_dataset(path, "excel", context="Test excel path")

    assert loaded.source_format == "excel"
    assert_frame_equal(loaded.frame, expected, check_dtype=False)


def test_load_tabular_dataset_avro(tmp_path: Path) -> None:
    path = tmp_path / "baseline.avro"
    schema = {
        "type": "record",
        "name": "row",
        "fields": [
            {"name": "id", "type": "long"},
            {"name": "batch_id", "type": "string"},
            {"name": "amount", "type": "double"},
        ],
    }
    with path.open("wb") as handle:
        avro_writer(
            handle,
            schema,
            [
                {"id": 1, "batch_id": "B-1", "amount": 10.0},
                {"id": 2, "batch_id": "B-1", "amount": 11.0},
            ],
        )

    loaded = load_tabular_dataset(path, "avro", context="Test avro path")

    assert loaded.source_format == "avro"
    assert loaded.frame.shape == (2, 3)


def test_load_tabular_dataset_orc(tmp_path: Path) -> None:
    path = tmp_path / "baseline.orc"
    expected = pd.DataFrame([
        {"id": 1, "batch_id": "B-1", "amount": 10.0},
        {"id": 2, "batch_id": "B-1", "amount": 11.0},
    ])
    orc.write_table(pa.Table.from_pandas(expected), path)

    loaded = load_tabular_dataset(path, "orc", context="Test orc path")

    assert loaded.source_format == "orc"
    assert loaded.frame.equals(expected)


def test_load_tabular_dataset_delta(tmp_path: Path) -> None:
    path = tmp_path / "delta_table"
    expected = pd.DataFrame([
        {"id": 1, "batch_id": "B-1", "amount": 10.0},
        {"id": 2, "batch_id": "B-1", "amount": 11.0},
    ])
    write_deltalake(str(path), expected, mode="overwrite")

    loaded = load_tabular_dataset(path, "delta", context="Test delta path")

    assert loaded.source_format == "delta"
    assert loaded.frame.equals(expected)


def test_load_tabular_dataset_table_via_active_spark_session(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = pd.DataFrame([
        {"id": 1, "batch_id": "B-1", "amount": 10.0, "extra": "x"},
        {"id": 2, "batch_id": "B-1", "amount": 11.0, "extra": "y"},
    ])

    class FakeSparkFrame:
        def __init__(self, frame: pd.DataFrame) -> None:
            self._frame = frame

        def select(self, *columns: str) -> "FakeSparkFrame":
            return FakeSparkFrame(self._frame.loc[:, list(columns)].copy())

        def limit(self, n: int) -> "FakeSparkFrame":
            return FakeSparkFrame(self._frame.head(n).copy())

        def toPandas(self) -> pd.DataFrame:
            return self._frame.copy()

    class FakeSparkSession:
        def table(self, table_name: str) -> FakeSparkFrame:
            assert table_name == "adb_dev.default.enterprise_orders"
            return FakeSparkFrame(expected)

    monkeypatch.setattr(dataset_runtime, "_active_spark_session", lambda: FakeSparkSession())

    loaded = load_tabular_dataset(
        "adb_dev.default.enterprise_orders",
        "table",
        context="Test table path",
        read_options={"columns": ["id", "amount"], "limit": 1},
    )

    assert loaded.source_format == "table"
    assert loaded.source_path == "adb_dev.default.enterprise_orders"
    assert loaded.files_loaded == ("adb_dev.default.enterprise_orders",)
    assert loaded.frame.to_dict(orient="records") == [{"id": 1, "amount": 10.0}]


def test_load_tabular_dataset_table_rejects_non_fully_qualified_name() -> None:
    with pytest.raises(ValueError, match="fully qualified three-part table name"):
        load_tabular_dataset("default.enterprise_orders", "table", context="Test table path")


def test_load_tabular_dataset_table_rejects_whitespace_bearing_name() -> None:
    with pytest.raises(ValueError, match="without surrounding whitespace"):
        load_tabular_dataset("adb_dev.default. enterprise_orders", "table", context="Test table path")


def test_load_baseline_dataset_from_policy_path(tmp_path: Path) -> None:
    current_path = tmp_path / "current.csv"
    baseline_path = tmp_path / "baseline.csv"
    pd.DataFrame([{"id": 1, "batch_id": "B-1"}]).to_csv(current_path, index=False)
    pd.DataFrame([{"id": 2, "batch_id": "B-0"}]).to_csv(baseline_path, index=False)

    contract = _contract(str(current_path))
    drift_policy = {
        "drift_policy": {
            "dataset": "runtime_ds",
            "contract_version": "1.0.0",
            "policy_version": "1.0.0",
            "name": "runtime_ds_drift",
            "monitored_columns": [{"column_name": "id", "method": "shannon_entropy"}],
            "baseline": {"path": str(baseline_path), "format": "csv", "min_rows": 1},
            "gates": {"health_score_threshold": 0.70},
        }
    }

    loaded = load_baseline_dataset(contract, drift_policy)

    assert loaded.source_path == str(baseline_path)
    assert loaded.frame.iloc[0]["id"] == 2


def test_load_baseline_dataset_uses_read_options_override(tmp_path: Path) -> None:
    current_path = tmp_path / "current.csv"
    baseline_path = tmp_path / "baseline.csv.gz"
    pd.DataFrame([{"id": 1, "batch_id": "B-1"}]).to_csv(current_path, index=False)
    baseline_path.write_bytes(gzip.compress(b"2,B-0\n"))

    contract = _contract(str(current_path))
    drift_policy = {
        "drift_policy": {
            "dataset": "runtime_ds",
            "contract_version": "1.0.0",
            "policy_version": "1.0.0",
            "name": "runtime_ds_drift",
            "monitored_columns": [{"column_name": "id", "method": "shannon_entropy"}],
            "baseline": {
                "path": str(baseline_path),
                "format": "csv",
                "read_options": {
                    "compression": "gzip",
                    "header": None,
                    "names": ["id", "batch_id"],
                },
                "min_rows": 1,
            },
            "gates": {"health_score_threshold": 0.70},
        }
    }

    loaded = load_baseline_dataset(contract, drift_policy)

    assert loaded.frame.iloc[0]["id"] == 2
    assert loaded.frame.iloc[0]["batch_id"] == "B-0"


def test_load_current_dataset_uses_dataset_table_when_format_is_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSparkFrame:
        def __init__(self, frame: pd.DataFrame) -> None:
            self._frame = frame

        def toPandas(self) -> pd.DataFrame:
            return self._frame.copy()

    class FakeSparkSession:
        def table(self, table_name: str) -> FakeSparkFrame:
            assert table_name == "adb_dev.default.orders"
            return FakeSparkFrame(pd.DataFrame([{"id": 1, "batch_id": "B-1", "amount": 10.0}]))

    monkeypatch.setattr(dataset_runtime, "_active_spark_session", lambda: FakeSparkSession())
    contract = {
        "dataset": {
            "name": "runtime_ds",
            "contract_version": "1.0.0",
            "catalog": "adb_dev",
            "schema": "default",
            "table": "orders",
        },
        "source": {
            "system": "pytest",
            "format": "table",
        },
        "contract": {
            "required_columns": [{"column_name": "id", "type": "long", "nullable": False}],
            "business_key": ["id"],
            "batch_identifier": "batch_id",
        },
    }

    loaded = load_current_dataset(contract)

    assert loaded.source_path == "adb_dev.default.orders"
    assert loaded.frame.iloc[0]["id"] == 1


def test_load_current_dataset_accepts_unity_catalog_table_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSparkFrame:
        def __init__(self, frame: pd.DataFrame) -> None:
            self._frame = frame

        def toPandas(self) -> pd.DataFrame:
            return self._frame.copy()

    class FakeSparkSession:
        def table(self, table_name: str) -> FakeSparkFrame:
            assert table_name == "adb_dev.default.enterprise_orders"
            return FakeSparkFrame(pd.DataFrame([{"id": 7, "batch_id": "B-7", "amount": 70.0}]))

    monkeypatch.setattr(dataset_runtime, "_active_spark_session", lambda: FakeSparkSession())
    contract = {
        "dataset": {
            "name": "runtime_ds",
            "contract_version": "1.0.0",
        },
        "source": {
            "system": "pytest",
            "format": "unity_catalog_table",
            "table_name": "adb_dev.default.enterprise_orders",
        },
        "contract": {
            "required_columns": [{"column_name": "id", "type": "long", "nullable": False}],
            "business_key": ["id"],
            "batch_identifier": "batch_id",
        },
    }

    loaded = load_current_dataset(contract)

    assert loaded.source_format == "table"
    assert loaded.source_path == "adb_dev.default.enterprise_orders"
    assert loaded.frame.iloc[0]["id"] == 7

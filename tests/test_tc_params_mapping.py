#
# Copyright (c) 2026 Project CHIP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Unit tests for load_tc_params_mapping (utils) and validate_tc_params_file (validation)."""

import json
from pathlib import Path

import pytest

from th_cli.exceptions import CLIError
from th_cli.utils import load_tc_params_mapping
from th_cli.validation import validate_tc_params_file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_mapping(tmp_path: Path, data: dict, filename: str = "mapping.json") -> Path:
    """Write *data* as JSON to *tmp_path / filename* and return the path."""
    p = tmp_path / filename
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# validate_tc_params_file
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestValidateTcParamsFile:
    """Tests for validate_tc_params_file."""

    def test_valid_mapping_file_returns_path(self, tmp_path: Path) -> None:
        """A well-formed mapping file returns its resolved Path."""
        p = _write_mapping(tmp_path, {"TC-ACE-1.1": {"int-arg": "PIXIT.ACE.EP:1"}})
        result = validate_tc_params_file(str(p))
        assert result.is_file()

    def test_empty_mapping_is_valid(self, tmp_path: Path) -> None:
        """An empty JSON object {} is a valid (but empty) mapping file."""
        p = _write_mapping(tmp_path, {})
        result = validate_tc_params_file(str(p))
        assert result.is_file()

    def test_file_not_found_raises(self, tmp_path: Path) -> None:
        """A non-existent path raises CLIError."""
        missing = tmp_path / "no_such_mapping.json"
        with pytest.raises(CLIError, match="File not found"):
            validate_tc_params_file(str(missing))

    def test_directory_instead_of_file_raises(self, tmp_path: Path) -> None:
        """Passing a directory raises CLIError."""
        with pytest.raises(CLIError, match="not a file"):
            validate_tc_params_file(str(tmp_path))

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        """A file with broken JSON raises CLIError mentioning 'Invalid JSON'."""
        p = tmp_path / "bad.json"
        p.write_text('{"TC-ACE-1.1": {', encoding="utf-8")
        with pytest.raises(CLIError, match="Invalid JSON"):
            validate_tc_params_file(str(p))

    def test_json_array_root_raises(self, tmp_path: Path) -> None:
        """A JSON array at the top level raises CLIError."""
        p = tmp_path / "array.json"
        p.write_text('[{"int-arg": "x"}]', encoding="utf-8")
        with pytest.raises(CLIError, match="Expected a JSON object at the top level"):
            validate_tc_params_file(str(p))

    def test_non_dict_value_raises(self, tmp_path: Path) -> None:
        """An entry whose value is not a dict raises CLIError listing the bad TC ID."""
        p = _write_mapping(tmp_path, {"TC-ACE-1.1": "not-a-dict"})
        with pytest.raises(CLIError, match="TC-ACE-1.1"):
            validate_tc_params_file(str(p))

    def test_multiple_non_dict_values_listed_in_error(self, tmp_path: Path) -> None:
        """All bad TC IDs are listed in the error message."""
        p = _write_mapping(tmp_path, {
            "TC-ACE-1.1": 42,
            "TC-CC-1.1": ["list", "value"],
            "TC-OK-1.1": {"int-arg": "PIXIT.OK:1"},
        })
        with pytest.raises(CLIError) as exc_info:
            validate_tc_params_file(str(p))
        msg = str(exc_info.value)
        assert "TC-ACE-1.1" in msg
        assert "TC-CC-1.1" in msg
        assert "TC-OK-1.1" not in msg  # valid entry must NOT appear in error

    def test_valid_multi_entry_mapping(self, tmp_path: Path) -> None:
        """Multiple valid entries with varied parameter keys are all accepted."""
        p = _write_mapping(tmp_path, {
            "TC-ACE-1.1": {"int-arg": "PIXIT.ACE.EP:1", "timeout": "300"},
            "TC-AVSM-2.10": {"int-arg": "PIXIT.AVSM.EP:1 PIXIT.AVSM.ST:1"},
            "TC-MCORE-FS-1.3": {"string-arg": "PIXIT.MCORE.EP:3"},
        })
        result = validate_tc_params_file(str(p))
        assert result.exists()


# ---------------------------------------------------------------------------
# load_tc_params_mapping
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLoadTcParamsMapping:
    """Tests for load_tc_params_mapping."""

    # ------------------------------------------------------------------
    # Happy-path: matching behaviour
    # ------------------------------------------------------------------

    def test_exact_match_returns_params(self, tmp_path: Path) -> None:
        """A TC ID that matches exactly returns its params."""
        p = _write_mapping(tmp_path, {
            "TC-ACE-1.1": {"int-arg": "PIXIT.ACE.EP:1"},
        })
        params, missing = load_tc_params_mapping(str(p), ["TC-ACE-1.1"])
        assert params == {"int-arg": "PIXIT.ACE.EP:1"}
        assert missing == []

    def test_dash_underscore_normalisation(self, tmp_path: Path) -> None:
        """Mapping key uses dashes; caller uses underscores — both normalise the same."""
        p = _write_mapping(tmp_path, {
            "TC-ACE-1.1": {"int-arg": "PIXIT.ACE.EP:1"},
        })
        params, missing = load_tc_params_mapping(str(p), ["TC_ACE_1_1"])
        assert params == {"int-arg": "PIXIT.ACE.EP:1"}
        assert missing == []

    def test_dot_normalisation(self, tmp_path: Path) -> None:
        """Dots in TC IDs are treated the same as dashes and underscores."""
        p = _write_mapping(tmp_path, {
            "TC.ACE.1.1": {"timeout": "300"},
        })
        params, missing = load_tc_params_mapping(str(p), ["TC-ACE-1.1"])
        assert params == {"timeout": "300"}
        assert missing == []

    def test_case_insensitive_match(self, tmp_path: Path) -> None:
        """Keys and test IDs are compared case-insensitively."""
        p = _write_mapping(tmp_path, {
            "tc-ace-1.1": {"int-arg": "PIXIT.ACE.EP:1"},
        })
        params, missing = load_tc_params_mapping(str(p), ["TC-ACE-1.1"])
        assert params == {"int-arg": "PIXIT.ACE.EP:1"}
        assert missing == []

    def test_multiple_ids_merged(self, tmp_path: Path) -> None:
        """Params from multiple matched TC IDs are all merged into one dict."""
        p = _write_mapping(tmp_path, {
            "TC-ACE-1.1": {"int-arg": "PIXIT.ACE.EP:1"},
            "TC-CC-1.1": {"timeout": "600"},
        })
        params, missing = load_tc_params_mapping(str(p), ["TC-ACE-1.1", "TC-CC-1.1"])
        assert params == {"int-arg": "PIXIT.ACE.EP:1", "timeout": "600"}
        assert missing == []

    def test_unmatched_ids_reported_in_missing(self, tmp_path: Path) -> None:
        """TC IDs absent from the mapping are reported in the missing list."""
        p = _write_mapping(tmp_path, {
            "TC-ACE-1.1": {"int-arg": "PIXIT.ACE.EP:1"},
        })
        params, missing = load_tc_params_mapping(str(p), ["TC-ACE-1.1", "TC-NONEXISTENT-1.1"])
        assert params == {"int-arg": "PIXIT.ACE.EP:1"}
        assert "TC-NONEXISTENT-1.1" in missing

    def test_all_ids_unmatched(self, tmp_path: Path) -> None:
        """When no IDs match, merged_params is empty and all IDs are in missing."""
        p = _write_mapping(tmp_path, {"TC-CC-1.1": {"timeout": "300"}})
        params, missing = load_tc_params_mapping(str(p), ["TC-ACE-1.1"])
        assert params == {}
        assert missing == ["TC-ACE-1.1"]

    def test_empty_mapping_all_missing(self, tmp_path: Path) -> None:
        """An empty mapping file yields an empty params dict and all IDs as missing."""
        p = _write_mapping(tmp_path, {})
        params, missing = load_tc_params_mapping(str(p), ["TC-ACE-1.1", "TC-CC-1.1"])
        assert params == {}
        assert set(missing) == {"TC-ACE-1.1", "TC-CC-1.1"}

    def test_empty_test_ids_list(self, tmp_path: Path) -> None:
        """An empty test_ids list yields empty results without error."""
        p = _write_mapping(tmp_path, {"TC-ACE-1.1": {"int-arg": "PIXIT.ACE.EP:1"}})
        params, missing = load_tc_params_mapping(str(p), [])
        assert params == {}
        assert missing == []

    # ------------------------------------------------------------------
    # Merge-order: last match wins on key conflicts
    # ------------------------------------------------------------------

    def test_key_conflict_last_sorted_id_wins(self, tmp_path: Path) -> None:
        """When two matched entries share a key, the alphabetically later TC ID wins."""
        p = _write_mapping(tmp_path, {
            "TC-ACE-1.1": {"int-arg": "PIXIT.ACE.EP:1", "timeout": "100"},
            "TC-CC-1.1":  {"int-arg": "PIXIT.CC.EP:2",  "timeout": "999"},
        })
        params, missing = load_tc_params_mapping(str(p), ["TC-ACE-1.1", "TC-CC-1.1"])
        # Sorted alphabetically: TC-ACE-1.1 first, TC-CC-1.1 second → CC wins
        assert params["int-arg"] == "PIXIT.CC.EP:2"
        assert params["timeout"] == "999"
        assert missing == []

    def test_non_conflicting_keys_all_present(self, tmp_path: Path) -> None:
        """Disjoint parameter keys from multiple TCs are all present in result."""
        p = _write_mapping(tmp_path, {
            "TC-ACE-1.1": {"int-arg": "PIXIT.ACE.EP:1"},
            "TC-CC-1.1":  {"string-arg": "PIXIT.CC.NAME:foo"},
            "TC-ICT-1.1": {"timeout": "500"},
        })
        params, _ = load_tc_params_mapping(str(p), ["TC-ACE-1.1", "TC-CC-1.1", "TC-ICT-1.1"])
        assert params["int-arg"] == "PIXIT.ACE.EP:1"
        assert params["string-arg"] == "PIXIT.CC.NAME:foo"
        assert params["timeout"] == "500"

    # ------------------------------------------------------------------
    # Error paths
    # ------------------------------------------------------------------

    def test_file_not_found_raises(self, tmp_path: Path) -> None:
        """A non-existent mapping file raises CLIError."""
        missing_file = str(tmp_path / "no_file.json")
        with pytest.raises(CLIError, match="File not found|failed to read"):
            load_tc_params_mapping(missing_file, ["TC-ACE-1.1"])

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        """Broken JSON raises CLIError."""
        p = tmp_path / "bad.json"
        p.write_text("{bad json", encoding="utf-8")
        with pytest.raises(CLIError, match="Invalid JSON"):
            load_tc_params_mapping(str(p), ["TC-ACE-1.1"])

    def test_array_root_raises(self, tmp_path: Path) -> None:
        """A JSON array at root raises CLIError."""
        p = tmp_path / "arr.json"
        p.write_text("[]", encoding="utf-8")
        with pytest.raises(CLIError, match="Expected a JSON object"):
            load_tc_params_mapping(str(p), ["TC-ACE-1.1"])

    def test_non_dict_entry_value_raises(self, tmp_path: Path) -> None:
        """An entry whose value is not a dict raises CLIError."""
        p = _write_mapping(tmp_path, {"TC-ACE-1.1": "just-a-string"})
        with pytest.raises(CLIError, match="must be a JSON object"):
            load_tc_params_mapping(str(p), ["TC-ACE-1.1"])

    def test_null_entry_value_raises(self, tmp_path: Path) -> None:
        """A null entry value raises CLIError (null is not a dict)."""
        p = _write_mapping(tmp_path, {"TC-ACE-1.1": None})
        with pytest.raises(CLIError, match="must be a JSON object"):
            load_tc_params_mapping(str(p), ["TC-ACE-1.1"])

    # ------------------------------------------------------------------
    # Real-world format variations
    # ------------------------------------------------------------------

    def test_multiple_space_separated_values_in_int_arg(self, tmp_path: Path) -> None:
        """Space-separated NAME:VALUE pairs in int-arg are passed through unchanged."""
        p = _write_mapping(tmp_path, {
            "TC-AVSM-2.10": {
                "int-arg": "PIXIT.AVSM.ENDPOINT:1 PIXIT.AVSM.STREAMTYPE:1",
                "timeout": "600",
            }
        })
        params, missing = load_tc_params_mapping(str(p), ["TC-AVSM-2.10"])
        assert params["int-arg"] == "PIXIT.AVSM.ENDPOINT:1 PIXIT.AVSM.STREAMTYPE:1"
        assert params["timeout"] == "600"
        assert missing == []

    def test_mapping_keys_with_mixed_separators(self, tmp_path: Path) -> None:
        """Mapping file keys with mixed -/_ separators are all normalised correctly."""
        p = _write_mapping(tmp_path, {
            "TC-MCORE_FS-1.3": {"string-arg": "PIXIT.MCORE.EP:3"},
        })
        # Caller uses the same mixed format
        params, missing = load_tc_params_mapping(str(p), ["TC-MCORE_FS-1.3"])
        assert params == {"string-arg": "PIXIT.MCORE.EP:3"}
        assert missing == []

    def test_mapping_superset_only_requested_ids_merged(self, tmp_path: Path) -> None:
        """Params for TC IDs not in test_ids are not included in merged_params."""
        p = _write_mapping(tmp_path, {
            "TC-ACE-1.1": {"int-arg": "PIXIT.ACE.EP:1"},
            "TC-CC-1.1":  {"timeout": "300"},
            "TC-ICT-1.1": {"string-arg": "PIXIT.ICT.NAME:foo"},
        })
        params, missing = load_tc_params_mapping(str(p), ["TC-ACE-1.1"])
        assert params == {"int-arg": "PIXIT.ACE.EP:1"}
        assert "timeout" not in params
        assert "string-arg" not in params

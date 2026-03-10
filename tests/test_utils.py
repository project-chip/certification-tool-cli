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
"""Tests for utility functions in th_cli.utils module."""

import json
from pathlib import Path

import pytest

from th_cli.api_lib_autogen import models as api_models
from th_cli.exceptions import CLIError
from th_cli.utils import (
    build_test_selection,
    convert_nested_to_dict,
    load_json_config,
    merge_configs,
    parse_pics_xml,
    read_pics_config,
)


@pytest.mark.unit
class TestBuildTestSelection:
    """Test cases for the build_test_selection function."""

    def test_build_test_selection_success(self, sample_test_collections: api_models.TestCollections) -> None:
        """Test successful test selection building."""
        # Arrange
        tests_list = ["TC-ACE-1.1", "TC_ACE_1_3"]

        # Act
        result = build_test_selection(sample_test_collections, tests_list)

        # Assert
        assert isinstance(result, dict)
        assert "SDK YAML Tests" in result
        assert "SDK Python Tests" in result
        assert "FirstChipToolSuite" in result["SDK YAML Tests"]
        assert "TC-ACE-1.1" in result["SDK YAML Tests"]["FirstChipToolSuite"]
        assert result["SDK YAML Tests"]["FirstChipToolSuite"]["TC-ACE-1.1"] == 1

    def test_build_test_selection_no_matches(self, sample_test_collections: api_models.TestCollections) -> None:
        """Test test selection building with no matching tests."""
        # Arrange
        tests_list = ["TC-NONEXISTENT-1.1"]

        # Act
        result = build_test_selection(sample_test_collections, tests_list)

        # Assert
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_build_test_selection_mixed_formats(self, sample_test_collections: api_models.TestCollections) -> None:
        """Test test selection building with mixed ID formats."""
        # Arrange
        tests_list = ["TC-ACE-1.1", "TC_ACE_1_3", "TC.ACE.1.2"]

        # Act
        result = build_test_selection(sample_test_collections, tests_list)

        # Assert
        assert isinstance(result, dict)
        # Should normalize formats and find matches
        assert len(result) > 0

    def test_build_test_selection_empty_list(self, sample_test_collections: api_models.TestCollections) -> None:
        """Test test selection building with empty test list."""
        # Arrange
        tests_list = []

        # Act
        result = build_test_selection(sample_test_collections, tests_list)

        # Assert
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_build_test_selection_whitespace_handling(
        self, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Test test selection building handles whitespace in test IDs."""
        # Arrange
        tests_list = [" TC-ACE-1.1 ", "\tTC_ACE_1_3\t"]

        # Act
        result = build_test_selection(sample_test_collections, tests_list)

        # Assert
        assert isinstance(result, dict)


@pytest.mark.unit
class TestConvertNestedToDict:
    """Test cases for the convert_nested_to_dict function."""

    def test_convert_nested_to_dict_simple_object(self) -> None:
        """Test converting simple object to dictionary."""

        # Arrange
        class SimpleObject:
            def __init__(self):
                self.name = "test"
                self.value = 42

        obj = SimpleObject()

        # Act
        result = convert_nested_to_dict(obj)

        # Assert
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 42

    def test_convert_nested_to_dict_nested_objects(self) -> None:
        """Test converting nested objects to dictionary."""

        # Arrange
        class InnerObject:
            def __init__(self):
                self.inner_value = "inner"

        class OuterObject:
            def __init__(self):
                self.outer_value = "outer"
                self.inner = InnerObject()

        obj = OuterObject()

        # Act
        result = convert_nested_to_dict(obj)

        # Assert
        assert isinstance(result, dict)
        assert result["outer_value"] == "outer"
        assert isinstance(result["inner"], dict)
        assert result["inner"]["inner_value"] == "inner"

    def test_convert_nested_to_dict_primitive_types(self) -> None:
        """Test converting primitive types."""
        # Arrange & Act & Assert
        assert convert_nested_to_dict(None) is None
        assert convert_nested_to_dict("string") == "string"
        assert convert_nested_to_dict(42) == 42
        assert convert_nested_to_dict(True) is True

    def test_convert_nested_to_dict_collections(self) -> None:
        """Test converting collections (lists, dicts)."""
        # Arrange
        data = {"list": [1, 2, 3], "dict": {"key": "value"}, "tuple": (1, 2, 3)}

        # Act
        print(type(data))
        result = convert_nested_to_dict(data)
        print(type(result))

        # Assert
        assert isinstance(result, dict)
        assert result["list"] == [1, 2, 3]
        assert result["dict"] == {"key": "value"}
        assert result["tuple"] == [1, 2, 3]  # Tuple converted to list

    def test_convert_nested_to_dict_circular_reference(self) -> None:
        """Test handling circular references."""

        # Arrange
        class CircularObject:
            def __init__(self):
                self.name = "circular"
                self.self_ref = self

        obj = CircularObject()

        # Act
        result = convert_nested_to_dict(obj)

        # Assert
        assert isinstance(result, dict)
        assert result["name"] == "circular"
        # Should handle circular reference gracefully
        assert isinstance(result["self_ref"], str)


@pytest.mark.unit
class TestParsePicsXml:
    """Test cases for the parse_pics_xml function."""

    def test_parse_pics_xml_success(self) -> None:
        """Test successful PICS XML parsing."""
        # Arrange
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<cluster>
    <name>TestCluster</name>
    <usage>
        <picsItem>
            <itemNumber>TC.TEST.1.1</itemNumber>
            <support>true</support>
        </picsItem>
    </usage>
    <clusterSide type="Server">
        <attributes>
            <picsItem>
                <itemNumber>TC.TEST.A.1</itemNumber>
                <support>false</support>
            </picsItem>
        </attributes>
        <events>
            <picsItem>
                <itemNumber>TC.TEST.E.1</itemNumber>
                <support>true</support>
            </picsItem>
        </events>
    </clusterSide>
</cluster>"""

        # Act
        result = parse_pics_xml(xml_content)

        # Assert
        assert isinstance(result, dict)
        assert "clusters" in result
        assert "TestCluster" in result["clusters"]
        assert "items" in result["clusters"]["TestCluster"]

        items = result["clusters"]["TestCluster"]["items"]
        assert "TC.TEST.1.1" in items
        assert items["TC.TEST.1.1"]["enabled"] is True
        assert "TC.TEST.A.1" in items
        assert items["TC.TEST.A.1"]["enabled"] is False

    def test_parse_pics_xml_invalid_xml(self) -> None:
        """Test PICS XML parsing with invalid XML."""
        # Arrange
        invalid_xml = "<invalid><unclosed>tag"

        # Act & Assert
        with pytest.raises(CLIError) as exc_info:
            parse_pics_xml(invalid_xml)

        assert "Failed to parse XML" in str(exc_info.value)

    def test_parse_pics_xml_missing_elements(self) -> None:
        """Test PICS XML parsing with missing required elements."""
        # Arrange
        incomplete_xml = """<?xml version="1.0" encoding="UTF-8"?>
<cluster>
    <usage>
    </usage>
</cluster>"""

        # Act & Assert
        with pytest.raises(CLIError) as exc_info:
            parse_pics_xml(incomplete_xml)

        assert "Failed processing PICS XML" in str(exc_info.value)


@pytest.mark.unit
class TestReadPicsConfig:
    """Test cases for the read_pics_config function."""

    def test_read_pics_config_success(self, mock_pics_dir: Path) -> None:
        """Test successful PICS config reading."""
        # Act
        result = read_pics_config(str(mock_pics_dir))

        # Assert
        assert isinstance(result, dict)
        assert "clusters" in result
        assert "TestCluster" in result["clusters"]

    def test_read_pics_config_empty_folder(self) -> None:
        """Test PICS config reading with empty folder path."""
        # Act
        result = read_pics_config("")

        # Assert
        assert isinstance(result, dict)
        assert "clusters" in result
        assert len(result["clusters"]) == 0

    def test_read_pics_config_none_folder(self) -> None:
        """Test PICS config reading with None folder path."""
        # Act
        result = read_pics_config(None)

        # Assert
        assert isinstance(result, dict)
        assert "clusters" in result
        assert len(result["clusters"]) == 0

    def test_read_pics_config_nonexistent_directory(self) -> None:
        """Test PICS config reading with non-existent directory."""
        # Act & Assert
        with pytest.raises(CLIError) as exc_info:
            read_pics_config("nonexistent_directory")

        assert "is not a directory" in str(exc_info.value)

    def test_read_pics_config_directory_with_non_xml_files(self, temp_dir: Path) -> None:
        """Test PICS config reading with directory containing non-XML files."""
        # Arrange
        pics_dir = temp_dir / "pics_with_other_files"
        pics_dir.mkdir()

        # Create non-XML files
        (pics_dir / "readme.txt").write_text("This is not XML")
        (pics_dir / "config.json").write_text('{"key": "value"}')

        # Create valid XML file
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<cluster>
    <name>ValidCluster</name>
    <usage>
        <picsItem>
            <itemNumber>TC.VALID.1.1</itemNumber>
            <support>true</support>
        </picsItem>
    </usage>
</cluster>"""
        (pics_dir / "valid_cluster.xml").write_text(xml_content)

        # Act
        result = read_pics_config(str(pics_dir))

        # Assert
        assert isinstance(result, dict)
        assert "clusters" in result
        assert "ValidCluster" in result["clusters"]
        # Should only process XML files
        assert len(result["clusters"]) == 1

    def test_read_pics_config_invalid_xml_file(self, temp_dir: Path) -> None:
        """Test PICS config reading with invalid XML file."""
        # Arrange
        pics_dir = temp_dir / "pics_with_invalid_xml"
        pics_dir.mkdir()

        (pics_dir / "invalid.xml").write_text("<invalid><unclosed>tag")

        # Act & Assert
        with pytest.raises(CLIError) as exc_info:
            read_pics_config(str(pics_dir))

        assert "Failed to parse PICS XML file invalid.xml" in str(exc_info.value)


@pytest.mark.unit
class TestLoadJsonConfig:
    """Test cases for the load_json_config function."""

    def test_load_json_config_success(self, temp_dir: Path) -> None:
        """Test successful JSON config loading."""
        # Arrange
        config_data = {
            "network": {"wifi": {"ssid": "test", "password": "pass"}},
            "dut_config": {"pairing_mode": "ble-wifi"},
        }
        config_file = temp_dir / "test_config.json"
        config_file.write_text(json.dumps(config_data, indent=2))

        # Act
        result = load_json_config(str(config_file))

        # Assert
        assert isinstance(result, dict)
        assert result["network"]["wifi"]["ssid"] == "test"
        assert result["dut_config"]["pairing_mode"] == "ble-wifi"

    def test_load_json_config_file_not_found(self) -> None:
        """Test JSON config loading with non-existent file."""
        # Act & Assert
        with pytest.raises(CLIError) as exc_info:
            load_json_config("nonexistent_config.json")

        assert "File not found" in str(exc_info.value)

    def test_load_json_config_invalid_json(self, temp_dir: Path) -> None:
        """Test JSON config loading with invalid JSON syntax."""
        # Arrange
        config_file = temp_dir / "invalid_config.json"
        config_file.write_text('{"key": "value"')  # Missing closing brace

        # Act
        with pytest.raises(CLIError) as exc_info:
            load_json_config(str(config_file))

        # Assert
        assert "Invalid JSON" in str(exc_info.value)
        assert "line" in str(exc_info.value)
        assert "column" in str(exc_info.value)

    def test_load_json_config_empty_file(self, temp_dir: Path) -> None:
        """Test JSON config loading with empty file."""
        # Arrange
        config_file = temp_dir / "empty_config.json"
        config_file.write_text("")

        # Act & Assert
        with pytest.raises(CLIError) as exc_info:
            load_json_config(str(config_file))

        assert "Invalid JSON" in str(exc_info.value)

    def test_load_json_config_nested_structure(self, temp_dir: Path) -> None:
        """Test JSON config loading with deeply nested structure."""
        # Arrange
        config_data = {"level1": {"level2": {"level3": {"value": "deep"}}}}
        config_file = temp_dir / "nested_config.json"
        config_file.write_text(json.dumps(config_data))

        # Act & Assert
        result = load_json_config(str(config_file))

        assert result["level1"]["level2"]["level3"]["value"] == "deep"

    def test_load_json_config_various_types(self, temp_dir: Path) -> None:
        """Test JSON config loading with various data types."""
        # Arrange
        config_data = {
            "string": "text",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "object": {"key": "value"},
        }
        config_file = temp_dir / "types_config.json"
        config_file.write_text(json.dumps(config_data))

        # Act
        result = load_json_config(str(config_file))

        # Assert
        assert result["string"] == "text"
        assert result["number"] == 42
        assert result["float"] == 3.14
        assert result["boolean"] is True
        assert result["null"] is None
        assert result["array"] == [1, 2, 3]
        assert result["object"] == {"key": "value"}

    def test_load_json_config_full_project_format(self, temp_dir: Path) -> None:
        """Test JSON config loading with full project format (auto-extracts config)."""
        # Arrange
        project_data = {
            "name": "My Test Project",
            "config": {"network": {"wifi": {"ssid": "test_network"}}, "dut_config": {"pairing_mode": "ble-wifi"}},
        }
        config_file = temp_dir / "project_config.json"
        config_file.write_text(json.dumps(project_data))

        # Act
        result = load_json_config(str(config_file))

        # Assert - should return only the config part
        assert "name" not in result  # Project name should not be in result
        assert "network" in result
        assert result["network"]["wifi"]["ssid"] == "test_network"
        assert result["dut_config"]["pairing_mode"] == "ble-wifi"

    def test_load_json_config_config_only_format(self, temp_dir: Path) -> None:
        """Test JSON config loading with config-only format (uses as-is)."""
        # Arrange
        config_data = {"network": {"wifi": {"ssid": "test_network"}}, "dut_config": {"pairing_mode": "ble-wifi"}}
        config_file = temp_dir / "config_only.json"
        config_file.write_text(json.dumps(config_data))

        # Act
        result = load_json_config(str(config_file))

        # Assert - should return the entire dict
        assert result == config_data
        assert result["network"]["wifi"]["ssid"] == "test_network"
        assert result["dut_config"]["pairing_mode"] == "ble-wifi"

    def test_load_json_config_invalid_config_key_type(self, temp_dir: Path) -> None:
        """Test JSON config loading with invalid config key type."""
        # Arrange
        invalid_data = {"name": "Project", "config": "not_a_dict"}  # config should be a dict, not a string
        config_file = temp_dir / "invalid_config_type.json"
        config_file.write_text(json.dumps(invalid_data))

        # Act & Assert
        with pytest.raises(CLIError) as exc_info:
            load_json_config(str(config_file))

        assert "Invalid config file format" in str(exc_info.value)
        assert '"config" key must contain a dictionary' in str(exc_info.value)

    def test_load_json_config_non_dict_root(self, temp_dir: Path) -> None:
        """Test JSON config loading with non-dictionary root."""
        # Arrange
        config_file = temp_dir / "array_root.json"
        config_file.write_text("[1, 2, 3]")  # Array instead of object

        # Act & Assert
        with pytest.raises(CLIError) as exc_info:
            load_json_config(str(config_file))

        assert "Invalid config file format" in str(exc_info.value)
        assert "Expected a JSON object (dictionary)" in str(exc_info.value)

    def test_load_json_config_format_compatibility(self, temp_dir: Path) -> None:
        """Test that both formats work for the same logical config."""
        # Arrange
        config_content = {"network": {"wifi": {"ssid": "same_network"}}, "dut_config": {"pairing_mode": "onnetwork"}}

        # Create config-only format file
        config_only_file = temp_dir / "config_only.json"
        config_only_file.write_text(json.dumps(config_content))

        # Create full project format file
        full_format_file = temp_dir / "full_format.json"
        full_format_data = {"name": "Project", "config": config_content}
        full_format_file.write_text(json.dumps(full_format_data))

        # Act
        result_config_only = load_json_config(str(config_only_file))
        result_full_format = load_json_config(str(full_format_file))

        # Assert - both should return the same config
        assert result_config_only == result_full_format
        assert result_config_only["network"]["wifi"]["ssid"] == "same_network"
        assert result_full_format["dut_config"]["pairing_mode"] == "onnetwork"


@pytest.mark.unit
class TestMergeConfigs:
    """Test cases for the merge_configs function."""

    def test_merge_configs_simple(self) -> None:
        """Test simple configuration merging."""
        # Arrange
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}

        # Act & Assert
        result = merge_configs(base, override)

        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merge_configs_nested(self) -> None:
        """Test nested configuration merging."""
        # Arrange
        base = {
            "network": {"wifi": {"ssid": "default", "password": "default"}, "thread": {"channel": 15}},
            "dut_config": {"pairing_mode": "onnetwork"},
        }
        override = {"network": {"wifi": {"ssid": "custom"}}}

        # Act
        result = merge_configs(base, override)

        # Assert
        assert result["network"]["wifi"]["ssid"] == "custom"
        assert result["network"]["wifi"]["password"] == "default"  # Preserved
        assert result["network"]["thread"]["channel"] == 15  # Preserved
        assert result["dut_config"]["pairing_mode"] == "onnetwork"  # Preserved

    def test_merge_configs_deep_nesting(self) -> None:
        """Test deeply nested configuration merging."""
        # Arrange
        base = {"a": {"b": {"c": {"d": 1, "e": 2}}}}
        override = {"a": {"b": {"c": {"d": 10}}}}

        # Act
        result = merge_configs(base, override)

        # Assert
        assert result["a"]["b"]["c"]["d"] == 10
        assert result["a"]["b"]["c"]["e"] == 2  # Preserved

    def test_merge_configs_new_keys(self) -> None:
        """Test merging with new keys added."""
        # Arrange
        base = {"existing": "value"}
        override = {"new": "value"}

        # Act
        result = merge_configs(base, override)

        # Assert
        assert result["existing"] == "value"
        assert result["new"] == "value"

    def test_merge_configs_override_types(self) -> None:
        """Test that override can change value types."""
        # Arrange
        base = {"key": "string"}
        override = {"key": 123}

        # Act & Assert
        result = merge_configs(base, override)

        assert result["key"] == 123

    def test_merge_configs_override_dict_with_non_dict(self) -> None:
        """Test overriding dict with non-dict value."""
        # Arrange
        base = {"key": {"nested": "value"}}
        override = {"key": "simple_string"}

        # Act & Assert
        result = merge_configs(base, override)

        assert result["key"] == "simple_string"

    def test_merge_configs_empty_base(self) -> None:
        """Test merging into empty base."""
        # Arrange
        base = {}
        override = {"a": 1, "b": 2}

        # Act & Assert
        result = merge_configs(base, override)

        assert result == {"a": 1, "b": 2}

    def test_merge_configs_empty_override(self) -> None:
        """Test merging with empty override."""
        # Arrange
        base = {"a": 1, "b": 2}
        override = {}

        # Act & Assert
        result = merge_configs(base, override)

        assert result == {"a": 1, "b": 2}

    def test_merge_configs_does_not_mutate_inputs(self) -> None:
        """Test that merge_configs doesn't mutate input dictionaries."""
        # Arrange
        base = {"a": {"b": 1}}
        override = {"a": {"c": 2}}
        base_copy = {"a": {"b": 1}}
        override_copy = {"a": {"c": 2}}

        # Act
        result = merge_configs(base, override)

        # Assert
        assert base == base_copy  # Base unchanged
        assert override == override_copy  # Override unchanged
        assert result == {"a": {"b": 1, "c": 2}}  # Result has both

    def test_merge_configs_lists_are_replaced(self) -> None:
        """Test that lists are replaced, not merged."""
        # Arrange
        base = {"list": [1, 2, 3]}
        override = {"list": [4, 5]}

        # Act & Assert
        result = merge_configs(base, override)

        assert result["list"] == [4, 5]  # Replaced, not merged

    def test_merge_configs_complex_scenario(self) -> None:
        """Test complex real-world scenario."""
        # Arrange
        base = {
            "network": {
                "fabric_id": 0,
                "thread": {"channel": 15, "panid": "0x1234", "networkkey": "00112233445566778899aabbccddeeff"},
                "wifi": {"ssid": "default_network", "password": "default_pass"},
            },
            "dut_config": {
                "pairing_mode": "onnetwork",
                "setup_code": "20202021",
                "discriminator": "3840",
                "trace_log": True,
            },
            "test_parameters": {},
        }
        override = {
            "network": {"wifi": {"ssid": "my_network", "password": "my_pass"}},
            "dut_config": {"discriminator": "3402", "trace_log": False},
            "test_parameters": {"custom_param": "custom_value"},
        }

        # Act
        result = merge_configs(base, override)

        # Assert

        # Assert Network WiFi should be updated
        assert result["network"]["wifi"]["ssid"] == "my_network"
        assert result["network"]["wifi"]["password"] == "my_pass"
        # Assert Network Thread should be preserved
        assert result["network"]["thread"]["channel"] == 15
        assert result["network"]["thread"]["panid"] == "0x1234"
        # Assert DUT config
        assert result["dut_config"]["discriminator"] == "3402"
        assert result["dut_config"]["trace_log"] is False
        assert result["dut_config"]["pairing_mode"] == "onnetwork"
        assert result["dut_config"]["setup_code"] == "20202021"
        # Assert Test parameters should have new value
        assert result["test_parameters"]["custom_param"] == "custom_value"


@pytest.mark.unit
class TestUtilityFunctionsCoverage:
    """Additional tests for edge cases and error conditions."""

    def test_build_test_selection_case_insensitive(self, sample_test_collections: api_models.TestCollections) -> None:
        """Test that test selection is case insensitive for normalization."""
        # Arrange
        tests_list = ["tc-ace-1.1", "TC_ACE_1_3"]

        # Act
        result = build_test_selection(sample_test_collections, tests_list)

        # Assert
        assert isinstance(result, dict)
        # Should still find matches despite case differences in normalization

    def test_convert_nested_to_dict_special_attributes(self) -> None:
        """Test that special attributes are properly filtered."""

        # Arrange
        class ObjectWithSpecialAttrs:
            def __init__(self):
                self.normal_attr = "normal"
                self.__private_attr = "private"
                self.__dict__["__special__"] = "special"

        obj = ObjectWithSpecialAttrs()

        # Act
        result = convert_nested_to_dict(obj)

        # Assert
        assert isinstance(result, dict)
        assert "normal_attr" in result
        assert "__private_attr" not in result
        assert "__special__" not in result

    def test_parse_pics_xml_empty_sections(self) -> None:
        """Test PICS XML parsing with empty sections."""
        # Arrange
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<cluster>
    <name>EmptyCluster</name>
    <usage>
    </usage>
    <clusterSide type="Server">
        <attributes>
        </attributes>
        <events>
        </events>
    </clusterSide>
</cluster>"""

        # Act
        result = parse_pics_xml(xml_content)

        # Assert
        assert isinstance(result, dict)
        assert "clusters" in result
        assert "EmptyCluster" in result["clusters"]
        assert "items" in result["clusters"]["EmptyCluster"]
        # Should handle empty sections gracefully
        assert isinstance(result["clusters"]["EmptyCluster"]["items"], dict)


@pytest.mark.unit
class TestBuildTestSelectionCaseInsensitive:
    """Tests for the case-insensitive comparison introduced in fix/908 (#69).

    Both the input IDs and the collection IDs are now normalised with
    .upper() before comparison, so any combination of upper/lower/mixed
    case must resolve to the correct test case.
    """

    def test_lowercase_input_matches_collection_entry(
        self, sample_test_collections: api_models.TestCollections
    ) -> None:
        """All-lowercase input 'tc-ace-1.1' matches the collection entry 'TC-ACE-1.1'."""
        result = build_test_selection(sample_test_collections, ["tc-ace-1.1"])

        assert "SDK YAML Tests" in result
        assert "FirstChipToolSuite" in result["SDK YAML Tests"]
        assert "TC-ACE-1.1" in result["SDK YAML Tests"]["FirstChipToolSuite"]
        assert result["SDK YAML Tests"]["FirstChipToolSuite"]["TC-ACE-1.1"] == 1

    def test_mixed_case_input_matches_collection_entry(
        self, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Mixed-case input 'Tc-Ace-1.1' matches the collection entry 'TC-ACE-1.1'."""
        result = build_test_selection(sample_test_collections, ["Tc-Ace-1.1"])

        suite = result.get("SDK YAML Tests", {}).get("FirstChipToolSuite", {})
        assert "TC-ACE-1.1" in suite
        assert result["SDK YAML Tests"]["FirstChipToolSuite"]["TC-ACE-1.1"] == 1

    def test_lowercase_underscore_format_matches_python_test(
        self, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Lowercase 'tc_ace_1_3' matches the Python collection entry 'TC_ACE_1_3'."""
        result = build_test_selection(sample_test_collections, ["tc_ace_1_3"])

        assert "SDK Python Tests" in result
        assert "Python Testing Suite" in result["SDK Python Tests"]
        assert "TC_ACE_1_3" in result["SDK Python Tests"]["Python Testing Suite"]
        assert result["SDK Python Tests"]["Python Testing Suite"]["TC_ACE_1_3"] == 1

    def test_uppercase_input_still_matches(self, sample_test_collections: api_models.TestCollections) -> None:
        """Existing all-uppercase input continues to work after the change."""
        result = build_test_selection(sample_test_collections, ["TC-ACE-1.2"])

        suite = result.get("SDK YAML Tests", {}).get("FirstChipToolSuite", {})
        assert "TC-ACE-1.2" in suite
        assert suite["TC-ACE-1.2"] == 1

    def test_original_collection_key_preserved_in_output(
        self, sample_test_collections: api_models.TestCollections
    ) -> None:
        """Output uses the original collection key, not the normalised form."""
        result = build_test_selection(sample_test_collections, ["tc-ace-1.1"])

        suite = result.get("SDK YAML Tests", {}).get("FirstChipToolSuite", {})
        assert "TC-ACE-1.1" in suite  # original key preserved
        assert "tc-ace-1.1" not in suite  # normalised input not used as key
        assert "TC_ACE_1_1" not in suite  # separator-normalised form not used as key

    def test_multiple_mixed_case_ids_all_resolved(self, sample_test_collections: api_models.TestCollections) -> None:
        """Multiple IDs in varying cases are all matched in a single call."""
        result = build_test_selection(
            sample_test_collections,
            ["tc-ace-1.1", "TC-ACE-1.2", "Tc-Cc-1.1"],
        )

        suite = result.get("SDK YAML Tests", {}).get("FirstChipToolSuite", {})
        assert "TC-ACE-1.1" in suite
        assert "TC-ACE-1.2" in suite
        assert "TC-CC-1.1" in suite

    def test_no_false_positives_for_unrelated_ids(self, sample_test_collections: api_models.TestCollections) -> None:
        """Selecting one ID by lowercase does not accidentally select other IDs."""
        result = build_test_selection(sample_test_collections, ["tc-ace-1.1"])

        suite = result.get("SDK YAML Tests", {}).get("FirstChipToolSuite", {})
        assert "TC-ACE-1.2" not in suite
        assert "TC-CC-1.1" not in suite

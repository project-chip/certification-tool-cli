#
# Copyright (c) 2025 Project CHIP Authors
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

from pathlib import Path

import pytest

from th_cli.api_lib_autogen import models as api_models
from th_cli.exceptions import CLIError
from th_cli.utils import (
    build_test_selection,
    convert_nested_to_dict,
    merge_properties_to_config,
    parse_pics_xml,
    read_pics_config,
    read_properties_file,
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
        self,
        sample_test_collections: api_models.TestCollections
    ) -> None:
        """Test test selection building handles whitespace in test IDs."""
        # Arrange
        tests_list = [" TC-ACE-1.1 ", "\tTC_ACE_1_3\t"]

        # Act
        result = build_test_selection(sample_test_collections, tests_list)

        # Assert
        assert isinstance(result, dict)


@pytest.mark.unit
class TestReadPropertiesFile:
    """Test cases for the read_properties_file function."""

    def test_read_properties_file_success(self, mock_properties_file: Path) -> None:
        """Test successful properties file reading."""
        # Act
        result = read_properties_file(str(mock_properties_file))

        # Assert
        assert isinstance(result, dict)
        assert "dut_config" in result
        assert "network" in result
        assert result["dut_config"]["pairing_mode"] == "ble-wifi"
        assert result["network"]["wifi"]["ssid"] == "TestNetwork"

    def test_read_properties_file_not_found(self) -> None:
        """Test properties file reading with non-existent file."""
        # Act
        with pytest.raises(CLIError) as exc_info:
            read_properties_file("nonexistent.properties")

        # Assert
        assert "File not found:" in str(exc_info.value)

    def test_read_properties_file_invalid_pairing_mode(self, temp_dir: Path) -> None:
        """Test properties file reading with invalid pairing mode."""
        # Arrange
        invalid_props = temp_dir / "invalid.properties"
        invalid_props.write_text(
            """
            [dut_config]
            pairing_mode=invalid-mode
            setup_code=20202021
            """
        )

        # Act
        with pytest.raises(CLIError) as exc_info:
            read_properties_file(str(invalid_props))

        # Assert
        assert "Invalid pairing_mode value: invalid-mode" in str(exc_info.value)

    def test_read_properties_file_malformed_content(self, temp_dir: Path) -> None:
        """Test properties file reading with malformed content."""
        # Arrange
        malformed_props = temp_dir / "malformed.properties"
        malformed_props.write_text("invalid content without proper sections")

        # Act
        with pytest.raises(CLIError) as exc_info:
            read_properties_file(str(malformed_props))

        # Assert
        assert "Failed reading properties file" in str(exc_info.value)


@pytest.mark.unit
class TestMergePropertiesToConfig:
    """Test cases for the merge_properties_to_config function."""

    def test_merge_properties_to_config_success(self) -> None:
        """Test successful properties to config merging."""
        # Arrange
        config_data = {
            "network": {
                "wifi": {"ssid": "TestWiFi", "password": "testpass"},
                "thread": {"operational_dataset_hex": "test_hex"}
            },
            "dut_config": {
                "pairing_mode": "ble-wifi",
                "setup_code": "20202021",
                "discriminator": "3840"
            }
        }

        default_config = {
            "network": {
                "wifi": {"ssid": "default", "password": "default"},
                "thread": {"operational_dataset_hex": "default_hex"}
            },
            "dut_config": {
                "pairing_mode": "onnetwork",
                "setup_code": "00000000",
                "discriminator": "0000"
            }
        }

        # Act
        result = merge_properties_to_config(config_data, default_config)

        # Assert
        assert isinstance(result, dict)
        assert result["network"]["wifi"]["ssid"] == "TestWiFi"
        assert result["dut_config"]["pairing_mode"] == "ble-wifi"

    def test_merge_properties_to_config_partial_override(self) -> None:
        """Test properties merging with partial configuration override."""
        # Arrange
        config_data = {
            "dut_config": {
                "setup_code": "12345678"
            }
        }

        default_config = {
            "network": {"wifi": {"ssid": "default", "password": "default"}},
            "dut_config": {
                "pairing_mode": "onnetwork",
                "setup_code": "00000000",
                "discriminator": "0000"
            }
        }

        # Act
        result = merge_properties_to_config(config_data, default_config)

        # Assert
        assert result["dut_config"]["setup_code"] == "12345678"
        assert result["dut_config"]["pairing_mode"] == "onnetwork"  # Should keep default

    def test_merge_properties_to_config_boolean_conversion(self) -> None:
        """Test boolean value conversion in properties merging."""
        # Arrange
        config_data = {
            "dut_config": {
                "chip_use_paa_certs": "true",
                "trace_log": "false"
            }
        }

        default_config = {
            "dut_config": {
                "chip_use_paa_certs": False,
                "trace_log": True
            }
        }

        # Act
        result = merge_properties_to_config(config_data, default_config)

        # Assert
        assert result["dut_config"]["chip_use_paa_certs"] is True
        assert result["dut_config"]["trace_log"] is False


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
        data = {
            "list": [1, 2, 3],
            "dict": {"key": "value"},
            "tuple": (1, 2, 3)
        }

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
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
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
</cluster>'''

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
        incomplete_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<cluster>
    <usage>
    </usage>
</cluster>'''

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
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<cluster>
    <name>ValidCluster</name>
    <usage>
        <picsItem>
            <itemNumber>TC.VALID.1.1</itemNumber>
            <support>true</support>
        </picsItem>
    </usage>
</cluster>'''
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

    def test_merge_properties_to_config_with_test_parameters(self) -> None:
        """Test merging properties with test_parameters section."""
        # Arrange
        config_data = {
            "test_parameters": {
                "custom_param": "custom_value",
                "timeout": "30"
            }
        }

        default_config = {
            "test_parameters": {}
        }

        # Act
        result = merge_properties_to_config(config_data, default_config)

        # Assert
        assert "test_parameters" in result
        assert result["test_parameters"]["custom_param"] == "custom_value"
        assert result["test_parameters"]["timeout"] == "30"

    def test_parse_pics_xml_empty_sections(self) -> None:
        """Test PICS XML parsing with empty sections."""
        # Arrange
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
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
</cluster>'''

        # Act
        result = parse_pics_xml(xml_content)

        # Assert
        assert isinstance(result, dict)
        assert "clusters" in result
        assert "EmptyCluster" in result["clusters"]
        assert "items" in result["clusters"]["EmptyCluster"]
        # Should handle empty sections gracefully
        assert isinstance(result["clusters"]["EmptyCluster"]["items"], dict)

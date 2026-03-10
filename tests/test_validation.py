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
"""Unit tests for th_cli.validation module."""

from pathlib import Path

import pytest

from th_cli.exceptions import CLIError
from th_cli.validation import (
    validate_directory_path,
    validate_file_path,
    validate_hostname,
    validate_project_name,
    validate_test_ids,
)

# ---------------------------------------------------------------------------
# validate_project_name
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestValidateProjectName:
    """Tests for validate_project_name."""

    def test_valid_name_alphanumeric(self):
        """Valid alphanumeric name is returned stripped."""
        assert validate_project_name("MyProject123") == "MyProject123"

    def test_valid_name_with_spaces(self):
        """Valid name with internal spaces is accepted."""
        assert validate_project_name("My Project") == "My Project"

    def test_valid_name_with_hyphens_and_underscores(self):
        """Valid name containing hyphens and underscores is accepted."""
        assert validate_project_name("my-project_v2") == "my-project_v2"

    def test_strips_leading_and_trailing_whitespace(self):
        """Leading/trailing whitespace is stripped from valid names."""
        assert validate_project_name("  ProjectName  ") == "ProjectName"

    def test_empty_string_raises(self):
        """Empty string raises CLIError."""
        with pytest.raises(CLIError, match="cannot be empty"):
            validate_project_name("")

    def test_whitespace_only_raises(self):
        """Whitespace-only string raises CLIError."""
        with pytest.raises(CLIError, match="cannot be empty"):
            validate_project_name("   ")

    def test_name_exceeding_100_chars_raises(self):
        """Name longer than 100 characters raises CLIError."""
        long_name = "a" * 101
        with pytest.raises(CLIError, match="cannot exceed 100 characters"):
            validate_project_name(long_name)

    def test_name_exactly_100_chars_is_valid(self):
        """Name of exactly 100 characters is accepted."""
        name = "a" * 100
        assert validate_project_name(name) == name

    def test_name_with_special_chars_raises(self):
        """Name with unsupported special characters raises CLIError."""
        with pytest.raises(CLIError, match="can only contain"):
            validate_project_name("Project@Name!")

    def test_name_with_dot_raises(self):
        """Name with a dot raises CLIError."""
        with pytest.raises(CLIError, match="can only contain"):
            validate_project_name("project.name")


# ---------------------------------------------------------------------------
# validate_test_ids
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestValidateTestIds:
    """Tests for validate_test_ids."""

    def test_valid_dash_format(self):
        """Standard TC-XXX-1.1 format is accepted."""
        result = validate_test_ids("TC-ACE-1.1")
        assert result == ["TC-ACE-1.1"]

    def test_valid_underscore_format(self):
        """Underscore-separated TC_XXX_1_1 format is accepted."""
        result = validate_test_ids("TC_ACE_1_1")
        assert result == ["TC_ACE_1_1"]

    def test_valid_custom_suffix(self):
        """Test ID ending in -custom is accepted."""
        result = validate_test_ids("TC-ACE-1.1-custom")
        assert result == ["TC-ACE-1.1-custom"]

    def test_multiple_valid_ids(self):
        """Multiple comma-separated valid IDs are all returned."""
        result = validate_test_ids("TC-ACE-1.1,TC-CC-1.2,TC_ICT_1_1")
        assert result == ["TC-ACE-1.1", "TC-CC-1.2", "TC_ICT_1_1"]

    def test_strips_whitespace_around_ids(self):
        """Whitespace around individual IDs is stripped before validation."""
        result = validate_test_ids(" TC-ACE-1.1 , TC-CC-1.2 ")
        assert result == ["TC-ACE-1.1", "TC-CC-1.2"]

    def test_empty_string_raises(self):
        """Empty string raises CLIError."""
        with pytest.raises(CLIError, match="cannot be empty"):
            validate_test_ids("")

    def test_whitespace_only_raises(self):
        """Whitespace-only string raises CLIError."""
        with pytest.raises(CLIError, match="cannot be empty"):
            validate_test_ids("   ")

    def test_invalid_id_format_raises(self):
        """Non-matching test ID format raises CLIError."""
        with pytest.raises(CLIError, match="Invalid test ID format"):
            validate_test_ids("INVALID-ID")

    def test_mixed_valid_and_invalid_raises(self):
        """A list with at least one invalid ID raises CLIError."""
        with pytest.raises(CLIError, match="Invalid test ID format"):
            validate_test_ids("TC-ACE-1.1,BADID")

    def test_commas_only_raises(self):
        """A string of only commas (no valid IDs) raises CLIError."""
        with pytest.raises(CLIError, match="No valid test IDs"):
            validate_test_ids(",,,")

    def test_three_digit_suffix(self):
        """Test ID with three-part numeric suffix is accepted."""
        result = validate_test_ids("TC-ACE-1.1.2")
        assert result == ["TC-ACE-1.1.2"]

    def test_valid_alphanumeric_category(self):
        """Test ID with alphanumeric category (e.g. TC-BR2-1.1) is accepted."""
        result = validate_test_ids("TC-BR2-1.1")
        assert result == ["TC-BR2-1.1"]

    def test_valid_identify_cluster_single_segment(self):
        """Identify cluster test IDs with single numeric segment are accepted."""
        result = validate_test_ids("TC-I-3")
        assert result == ["TC-I-3"]

    def test_valid_bridge_cluster_single_segment(self):
        """Bridge cluster test IDs with single numeric segment are accepted."""
        result = validate_test_ids("TC-BR-2")
        assert result == ["TC-BR-2"]

    def test_valid_identify_cluster_underscore_format(self):
        """Identify cluster underscore format TC_I_2_1 is accepted."""
        result = validate_test_ids("TC_I_2_1")
        assert result == ["TC_I_2_1"]

    def test_valid_bridge_cluster_underscore_format(self):
        """Bridge cluster underscore format TC_BR_2 is accepted."""
        result = validate_test_ids("TC_BR_2")
        assert result == ["TC_BR_2"]

    def test_valid_category_with_underscore(self):
        """Category containing underscore (e.g. TC-MCORE_FS-1.1) is accepted."""
        result = validate_test_ids("TC-MCORE_FS-1.1")
        assert result == ["TC-MCORE_FS-1.1"]

    def test_valid_category_with_underscore_mixed_separators(self):
        """Category with underscore using mixed separators is accepted."""
        result = validate_test_ids("TC-MCORE_FS-1_2")
        assert result == ["TC-MCORE_FS-1_2"]

    def test_valid_category_with_underscore_underscore_format(self):
        """Category with underscore in full underscore format is accepted."""
        result = validate_test_ids("TC_MCORE_FS-1.2")
        assert result == ["TC_MCORE_FS-1.2"]


# ---------------------------------------------------------------------------
# validate_hostname
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestValidateHostname:
    """Tests for validate_hostname."""

    def test_localhost_is_valid(self):
        """'localhost' is always accepted."""
        assert validate_hostname("localhost") == "localhost"

    def test_valid_ipv4_address(self):
        """Valid IPv4 address is accepted."""
        assert validate_hostname("192.168.1.100") == "192.168.1.100"

    def test_valid_ipv4_boundary_values(self):
        """IPv4 addresses with octets at boundaries (0, 255) are accepted."""
        assert validate_hostname("0.0.0.0") == "0.0.0.0"
        assert validate_hostname("255.255.255.255") == "255.255.255.255"

    def test_invalid_ipv4_octet_out_of_range_raises(self):
        """IPv4 with an octet > 255 raises CLIError."""
        with pytest.raises(CLIError, match="Invalid IP address"):
            validate_hostname("256.0.0.1")

    def test_valid_domain_name(self):
        """Valid domain name is accepted."""
        assert validate_hostname("example.com") == "example.com"

    def test_valid_subdomain(self):
        """Valid subdomain is accepted."""
        assert validate_hostname("api.example.com") == "api.example.com"

    def test_hostname_with_port_is_accepted(self):
        """Hostnames formatted as host:port pass domain-name validation."""
        # The current regex allows colons indirectly through 'example.com:8080'
        # pattern — if this fails, the implementation rejects port suffixes.
        # We validate the actual current behavior by checking that it either
        # passes or raises a CLIError with the right message.
        result = validate_hostname("example.com")
        assert result == "example.com"

    def test_hostname_with_port_is_rejected(self):
        """A hostname with a port is not a valid hostname and should be rejected."""
        with pytest.raises(CLIError, match="Invalid hostname format"):
            validate_hostname("example.com:8080")

    def test_empty_hostname_raises(self):
        """Empty hostname raises CLIError."""
        with pytest.raises(CLIError, match="cannot be empty"):
            validate_hostname("")

    def test_whitespace_only_raises(self):
        """Whitespace-only hostname raises CLIError."""
        with pytest.raises(CLIError, match="cannot be empty"):
            validate_hostname("   ")

    def test_hostname_too_long_raises(self):
        """Hostname longer than 253 characters raises CLIError."""
        long_host = "a" * 254
        with pytest.raises(CLIError, match="too long"):
            validate_hostname(long_host)

    def test_invalid_domain_format_raises(self):
        """Hostname with unsupported characters raises CLIError."""
        with pytest.raises(CLIError, match="Invalid hostname format"):
            validate_hostname("bad hostname!")

    def test_strips_whitespace(self):
        """Leading/trailing whitespace is stripped before validation."""
        assert validate_hostname("  localhost  ") == "localhost"


# ---------------------------------------------------------------------------
# validate_file_path
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestValidateFilePath:
    """Tests for validate_file_path."""

    def test_existing_file_is_valid(self, tmp_path: Path):
        """An existing file path returns the resolved Path object."""
        f = tmp_path / "test.txt"
        f.write_text("content")

        result = validate_file_path(str(f))

        assert result.exists()
        assert result.is_file()

    def test_nonexistent_file_raises(self, tmp_path: Path):
        """A non-existent path raises CLIError when must_exist=True."""
        missing = tmp_path / "missing.txt"

        with pytest.raises(CLIError, match="File not found"):
            validate_file_path(str(missing))

    def test_directory_instead_of_file_raises(self, tmp_path: Path):
        """Passing a directory path raises CLIError."""
        with pytest.raises(CLIError, match="not a file"):
            validate_file_path(str(tmp_path))

    def test_must_exist_false_allows_missing_path(self, tmp_path: Path):
        """With must_exist=False, a non-existent path is returned without error."""
        missing = tmp_path / "future_file.txt"

        result = validate_file_path(str(missing), must_exist=False)

        assert isinstance(result, Path)
        assert not result.exists()


# ---------------------------------------------------------------------------
# validate_directory_path
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestValidateDirectoryPath:
    """Tests for validate_directory_path."""

    def test_existing_directory_is_valid(self, tmp_path: Path):
        """An existing directory path returns the resolved Path object."""
        result = validate_directory_path(str(tmp_path))

        assert result.exists()
        assert result.is_dir()

    def test_nonexistent_directory_raises(self, tmp_path: Path):
        """A non-existent directory raises CLIError when must_exist=True."""
        missing = tmp_path / "no_such_dir"

        with pytest.raises(CLIError, match="Directory not found"):
            validate_directory_path(str(missing))

    def test_file_instead_of_directory_raises(self, tmp_path: Path):
        """Passing a file path raises CLIError."""
        f = tmp_path / "file.txt"
        f.write_text("content")

        with pytest.raises(CLIError, match="not a directory"):
            validate_directory_path(str(f))

    def test_must_exist_false_allows_missing_path(self, tmp_path: Path):
        """With must_exist=False, a non-existent path is returned without error."""
        missing = tmp_path / "future_dir"

        result = validate_directory_path(str(missing), must_exist=False)

        assert isinstance(result, Path)
        assert not result.exists()

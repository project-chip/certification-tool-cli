#
# Copyright (c) 2025-2026 Project CHIP Authors
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
"""Unit tests for th_cli/async_cmd.py."""

import asyncio

import pytest

from th_cli.async_cmd import async_cmd


# ---------------------------------------------------------------------------
# @async_cmd decorator
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAsyncCmd:
    def test_wrapped_async_function_runs_synchronously(self):
        @async_cmd
        async def my_async_func():
            return "result"

        result = my_async_func()
        assert result == "result"

    def test_return_value_is_propagated(self):
        @async_cmd
        async def compute():
            return 42

        assert compute() == 42

    def test_positional_arguments_forwarded(self):
        @async_cmd
        async def add(a, b):
            return a + b

        assert add(3, 4) == 7

    def test_keyword_arguments_forwarded(self):
        @async_cmd
        async def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = greet(name="World", greeting="Hi")
        assert result == "Hi, World!"

    def test_wraps_preserves_function_name(self):
        @async_cmd
        async def original_name():
            pass

        assert original_name.__name__ == "original_name"

    def test_wraps_preserves_docstring(self):
        @async_cmd
        async def documented():
            """My docstring."""
            pass

        assert documented.__doc__ == "My docstring."

    def test_async_operations_are_executed(self):
        executed = []

        @async_cmd
        async def side_effects():
            await asyncio.sleep(0)  # real async operation
            executed.append("done")

        side_effects()
        assert executed == ["done"]

    def test_exception_propagates_from_async_body(self):
        @async_cmd
        async def raises():
            raise ValueError("async error")

        with pytest.raises(ValueError, match="async error"):
            raises()

    def test_none_return_value(self):
        @async_cmd
        async def returns_none():
            return None

        assert returns_none() is None

    def test_can_decorate_multiple_functions_independently(self):
        @async_cmd
        async def func_a():
            return "a"

        @async_cmd
        async def func_b():
            return "b"

        assert func_a() == "a"
        assert func_b() == "b"

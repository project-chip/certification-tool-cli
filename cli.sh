#! /usr/bin/env bash
 #
 # Copyright (c) 2023 Project CHIP Authors
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

# Warning: this script is deprecated. Please use the th-cli tool instead.
# In case the th-cli command is not found, please refer to the README.md and install the tool.

#Using an array to store the arguments, to handle 'whitespaces' correctly
args=("$@")
poetry run th-cli "${args[@]}"
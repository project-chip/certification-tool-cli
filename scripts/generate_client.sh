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

set -e

# Prevent automatic path conversions by MSYS-based bash.
# It's revelant only for Windows
export MSYS_NO_PATHCONV=1

CMDNAME=${0##*/}

PACKAGE_NAME=api_lib_autogen
OUTPUT_DIR="th_cli"
PACKAGE_PATH=$OUTPUT_DIR/$PACKAGE_NAME
OPENAPI_PATH="."
OPENAPI_FILE="openapi.json"
OPENAPI_IP_ADDRESS=""

usage() {
  exitcode="$1"
  cat <<USAGE >&2

Generate API client from OpenAPI specification

Usage:
  $CMDNAME [OPTIONS]

Options:
  -i, --ip IP_ADDRESS    Use remote OpenAPI spec from http://IP_ADDRESS/api/v1/openapi.json
                         If not provided, uses local openapi.json file
  -h, --help             Show this message

Examples:
  # Generate from local file
  $CMDNAME

  # Generate from remote server
  $CMDNAME --ip 192.168.1.100
  $CMDNAME -i 10.0.0.50

USAGE
  exit "$exitcode"
}

main() {
  PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"

  # Set OPENAPI_PATH based on whether IP was provided
  if [ -n "$OPENAPI_IP_ADDRESS" ]; then
    OPENAPI_PATH="http://$OPENAPI_IP_ADDRESS/api/v1"
    echo "Using remote OpenAPI spec from: $OPENAPI_PATH/$OPENAPI_FILE"
  else
    OPENAPI_PATH="."
    echo "Using local OpenAPI spec: $OPENAPI_PATH/$OPENAPI_FILE"
  fi

  [ -d "$PACKAGE_PATH" ] && rm -rf "$PACKAGE_PATH"

  ./client_generator/scripts/generate.sh -i $OPENAPI_PATH/$OPENAPI_FILE -t "/tmp" -p $PACKAGE_NAME -o $OUTPUT_DIR -n $OUTPUT_DIR.$PACKAGE_NAME

  echo "Running type checking with mypy..."
  poetry run mypy ./$PACKAGE_PATH

  echo "Running code formatters..."
  poetry run black ./$PACKAGE_PATH
  poetry run flake8 ./$PACKAGE_PATH
  poetry run isort ./$PACKAGE_PATH

  echo "API client generation completed successfully! ✨"
}

# Parse command line arguments
while [ $# -gt 0 ]; do
  case "$1" in
  -i | --ip)
    OPENAPI_IP_ADDRESS=$2
    shift 2
    ;;
  -h | --help)
    usage 0
    ;;
  *)
    echo "Unknown argument: $1"
    usage 1
    ;;
  esac
done

main

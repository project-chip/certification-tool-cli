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
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"
cd "${PROJECT_ROOT}"

CMDNAME=${0##*/}

PACKAGE_NAME=""
WORK_DIR=""

usage() {
  exitcode="$1"
  cat <<USAGE >&2

Use docker to postprocess the output of openapi-generator

Usage:
  $CMDNAME -p PACKAGE_NAME

Options:
  -p, --package-name       The name to use for the generated package
  -w, --work-dir           The working directory used for generator output
  -h, --help               Show this message
USAGE
  exit "$exitcode"
}

main() {
  validate_inputs
  docker build -t fastapi-client-generator:latest .
  docker run --rm --user $(id -u):$(id -g) -v "$WORK_DIR":/generator-output fastapi-client-generator:latest -p "${PACKAGE_NAME}"
  add_py_typed
}

add_py_typed() {
  touch "$WORK_DIR"/"${PACKAGE_NAME}"/py.typed
  echo "include ${PACKAGE_NAME}/py.typed" > "$WORK_DIR"/MANIFEST.in
}

validate_inputs() {
  if [ -z "$PACKAGE_NAME" ]; then
    echo "Error: you need to provide --package-name argument"
    usage 2
  fi
  if [ -z "$WORK_DIR" ]; then
    echo "Error: you need to provide --work-dir argument"
    usage 2
  fi
}

while [ $# -gt 0 ]; do
  case "$1" in
  -p | --package-name)
    PACKAGE_NAME=$2
    shift 2
    ;;
  -w | --work-dir)
    WORK_DIR=$2
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

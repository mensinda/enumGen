#!/usr/bin/env bash

TEST_DIR="testDir"
REQUIRED_CMD=(gcc python awk grep)

msg1() { echo -e "\x1b[1;32m==> \x1b[39m$*\x1b[0m"; }
msg2() { echo -e "\x1b[1;34m  --> \x1b[39m$*\x1b[0m"; }

error() { echo -e "\x1b[1;31mERROR: \x1b[0;31m$*\x1b[0m"; }

cd "$(dirname "$0")"


CMD=""

requireOK() {
  msg2 "Running '$*'"
  CMD="$*"
  "$@"
  RES=$?
  if (( RES != 0 )); then
    error "Command $* failed"
  fi
}

exists() {
  local i
  for i in $*; do
    if [ ! -e $i ]; then
      error "File $i does not exist"
    fi
  done
}

test_baseTest() {
  requireOK ../enumGen.py parse ../test/test1.hpp      test1.json
  requireOK ../enumGen.py parse ../test/vulkan_core.h  vulkan_core.json
  exists test1.json vulkan_core.json
  requireOK ../enumGen.py -c ../test/cfg.json generate Enum2Str Enum2Str.{hpp,cpp} *.json
  exists Enum2Str.{hpp,cpp}
  requireOK gcc -c -Wall -fpic Enum2Str.cpp
  requireOK gcc -shared -o Enum2Str.so Enum2Str.o
}


main() {
  # check for requirements
  local ERRORS=0
  for i in "${REQUIRED_CMD[@]}"; do
    which "$i" &> /dev/null
    RET=$?
    if (( RET != 0 )); then
      error "Required command $i not found"
      (( ERRORS++ ))
    fi
  done
  (( ERRORS > 0 )) && exit 1

  # Setup test env
  [ -d "$TEST_DIR" ] && rm -rf "$TEST_DIR"
  mkdir "$TEST_DIR"
  cd "$TEST_DIR"

  local i
  for i in $(typeset -f | awk '/ \(\) $/ {print $1}' | grep test_); do
    msg1 "Running test '$i'"
    $i
  done
}

main

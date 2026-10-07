#!/usr/bin/env bash
# Print the numbers for a built region: ./stats.sh dc-box
source "$(dirname "$0")/lib/common.sh"
region "$1"
cd "$ROOT"
duckdb -readonly "$OUT/build.duckdb" < sql/stats.sql

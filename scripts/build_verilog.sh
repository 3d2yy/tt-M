#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/ghdl
ghdl -a --std=08 --workdir=build/ghdl src/tt_um_3d2yy_correlator.vhdl
trap 'rm -f build/correlator.v.tmp' EXIT
ghdl --synth --std=08 --workdir=build/ghdl --out=verilog tt_um_3d2yy_correlator > build/correlator.v.tmp
mv build/correlator.v.tmp build/correlator.v

# 4-bit Array Multiplier — RTL to GDSII (SKY130)

## Team

| Name | Roll number |
|------|-------------|
| Gopal | 2023112006 |
| Manya | 2024102068 |

## Environment

All steps were run in the IIC-OSIC-TOOLS Docker image (`hpretl/iic-osic-tools:latest`:
Icarus Verilog 14.0 (devel), Yosys 0.70, OpenSTA 3.1.0, LibreLane, KLayout), with this
repository mounted under `/foss/designs`. All commands are run from the repository root
unless noted otherwise.

```sh
iverilog -V | head -1
yosys -V
sta -version
echo $PDK_ROOT $PDK        # the image defaults to ihp-sg13g2, so:
sak-pdk sky130A            # (equivalently: export PDK=sky130A)
```

## Part A — RTL design and verification

```sh
iverilog -g2012 -o sim tb/tb_mult.v rtl/full_adder.v rtl/mult_array.v
vvp sim
gtkwave mult.vcd
```

Result:

```
PASS: 256 vectors checked, 0 errors
```

Error-injection check: `assign sum = a ^ b ^ cin;` in `rtl/full_adder.v` was temporarily
changed to `assign sum = a ^ b;` and the same two commands were run:

```
FAIL: 256 vectors checked, 95 errors
```

The change was then undone and the testbench printed `PASS` again.

Hand-worked example: Gopal's roll number 2023112006 ends in 6, so A = 6 + 5 = 11 and B = 7.
11 × 7 = 77 = `0100_1101`. In `mult.vcd` the inputs are applied at 5520 ns, captured at
the 5525 ns clock edge and `p = 77` appears at the 5535 ns edge (see `report/report.pdf`).

## Part B — Logic synthesis with Yosys

```sh
yosys -c synth/synth.tcl
```

Gate-level netlist simulation:

```sh
CELLS=$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/verilog
iverilog -g2012 -DFUNCTIONAL -DUNIT_DELAY=#1 -o gls \
  tb/tb_mult.v $CELLS/primitives.v $CELLS/sky130_fd_sc_hd.v synth/mult_array_netlist.v
vvp gls
```

| Metric | Value |
|--------|-------|
| Total number of cells | 61 |
| Number of flip-flops | 16 (`sky130_fd_sc_hd__dfrtp_1`) |
| Total cell area (µm²) | 756.976 |
| Flip-flop area (µm²) | 16 × 25.024 = 400.384 |
| Flip-flop area (% of total) | 52.89 % |
| 3 most-used cell types | `dfrtp_1` × 16, `nand2_1` × 7, `and2_0` × 4 and `maj3_1` × 4 (tied) |
| Netlist simulation result | `PASS: 256 vectors checked, 0 errors` |

## Part C — Static timing analysis with OpenSTA

`sta/sta.tcl` uses T = 10 ns by default; the period can be overridden with `STA_PERIOD`.

```sh
sta sta/sta.tcl                      # T = 10 ns -> worst slack 7.213 ns
STA_PERIOD=2.79 sta sta/sta.tcl      # T = Tmin  -> worst slack 0.003 ns
sta sta/sta.tcl                      # regenerate sta/mult_array_timing.rpt at T = 10 ns
```

| Metric | Value |
|--------|-------|
| Worst slack at T = 10 ns | 7.213 ns |
| Tmin | 10 − 7.213 = 2.787 ns |
| Fmax | 1000 / 2.787 = 358.8 MHz |
| Slack at T = Tmin (2.79 ns) | +0.003 ns |
| Critical path start point | `a_r[1]` flip-flop (`_91_`, `dfrtp_1`, CLK) |
| Critical path end point | `p[6]` flip-flop (`_88_`, `dfrtp_1`, D) |
| Number of cells on the critical path | 9 (launch flip-flop + 8 logic cells) |
| Latency = 2 × Tmin | 5.574 ns |
| Throughput | 358.8 million results per second |

Cells on the critical path, in order: `dfrtp_1` → `clkinv_1` → `o311ai_0` → `a21oi_1` →
`maj3_1` → `xnor3_1` → `maj3_1` → `maj3_1` → `xor3_1` → (`dfrtp_1` D pin).

## Part D — Physical design with LibreLane

```sh
cd pnr
librelane config.json
cp runs/<final run>/final/metrics.json metrics.json
cp runs/<final run>/final/gds/mult_array.gds mult_array.gds
klayout mult_array.gds
```

Every attempt (`CLOCK_PERIOD` = 1.2 × 2.787 = 3.344 ns, rounded up to 3.5 ns, then +0.5 ns
per failed attempt). LibreLane signs off setup in all nine PVT corners; the worst one is
always the slow-slow corner (`ss_100C_1v60`).

| Run | Run directory | CLOCK_PERIOD (ns) | Worst setup slack (ns) | tt-corner slack (ns) | DRC / LVS | Result |
|-----|---------------|-------------------|------------------------|----------------------|-----------|--------|
| 1 | `RUN_2026-10-24_09-01-12` | 3.5 | −2.546 | +0.431 | 0 / 0 | setup violations |
| 2 | `RUN_2026-10-24_09-03-35` | 4.0 | −2.027 | +0.929 | 0 / 0 | setup violations |
| 3 | `RUN_2026-10-24_09-05-20` | 4.5 | −1.527 | +1.429 | 0 / 0 | setup violations |
| 4 | `RUN_2026-10-24_09-07-03` | 5.0 | −1.027 | +1.929 | 0 / 0 | setup violations |
| 5 | `RUN_2026-10-24_09-08-49` | 5.5 | −0.527 | +2.429 | 0 / 0 | setup violations |
| 6 | `RUN_2026-10-24_09-10-36` | 6.0 | −0.037 | +2.911 | 0 / 0 | setup violations |
| 7 | `RUN_2026-10-24_09-12-18` | 6.5 | −0.205 | +3.111 | 0 / 0 | setup violations |
| 8 | `RUN_2026-10-24_09-13-57` | 7.0 | −0.116 | +3.526 | 0 / 0 | setup violations |
| 9 | `RUN_2026-10-24_09-15-37` | 7.5 | −0.138 | +3.722 | 0 / 0 | setup violations |
| 10 | `RUN_2026-10-24_09-17-16` | 8.0 | +0.362 | +4.222 | 0 / 0 | **pass** |

`pnr/metrics.json` and `pnr/mult_array.gds` are copied from run 10.

| Metric | Value |
|--------|-------|
| CLOCK_PERIOD used | 8.0 ns |
| Number of runs needed | 10 |
| Core area | 17 759.5 µm² (die area 22 500 µm²) |
| Cells after synthesis (Part B) | 61 |
| Cells after place and route | 1884 (331 excluding fill/decap) |
| Kinds of cells added | 245 tap, 1299 decap, 254 fill, 17 `buf_2` I/O buffers, 3 `clkbuf_16` clock tree, 4 `clkdlybuf` repair buffers |
| Wirelength | 2518 µm |
| Setup slack | +0.362 ns (worst corner `max_ss_100C_1v60`) |
| Post-route Fmax | 1000 / (8.0 − 0.362) = 130.9 MHz |
| Fmax from Part C | 358.8 MHz |
| DRC errors | 0 |
| LVS errors | 0 |

Layout screenshots (rendered with KLayout in batch mode):

```sh
klayout -zz -r report/figs/layout_shots.py
```

## Report

`report/report.pdf` contains all result tables, the hand-worked example, the block diagram,
the annotated waveform, the layout screenshots and the answers to the questions in Section 10.
It is built from `report/report.typ`:

```sh
cd report && typst compile report.typ report.pdf
```

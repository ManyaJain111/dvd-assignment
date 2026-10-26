# 4-bit Array Multiplier : RTL to GDSII (SKY130)

A 4-bit × 4-bit unsigned array multiplier (16 AND gates, 12 full adders, 16 flip-flops,
2-cycle latency) taken from Verilog RTL through simulation, Yosys synthesis, OpenSTA timing
analysis and LibreLane place-and-route to a GDSII layout on SkyWater SKY130 (`sky130_fd_sc_hd`).

## Team

| Name | Roll number |
|------|-------------|
| Gopal | 2023112006 |
| Manya | 2024102068 |

## Repository layout

```
rtl/full_adder.v             full adder (assign statements only)
rtl/mult_array.v             4x4 array multiplier, 12 full_adder instances
tb/tb_mult.v                 exhaustive self-checking testbench (writes mult.vcd)
synth/synth.tcl              Yosys script
synth/mult_array_netlist.v   gate-level netlist           (generated)
synth/mult_array_stat.rpt    cell and area report         (generated)
sta/sta.tcl                  OpenSTA script
sta/mult_array_timing.rpt    critical path report         (generated)
pnr/config.json              LibreLane configuration
pnr/metrics.json             metrics of the final LibreLane run
pnr/mult_array.gds           final layout
report/report.pdf            report (source: report/report.typ, figures in report/figs/)
```

## 0. Setup

Everything runs in the IIC-OSIC-TOOLS Docker image (Icarus Verilog 14.0 (devel), Yosys 0.70,
OpenSTA 3.1.0, LibreLane, KLayout). Give Docker at least 8 GB RAM and 4 CPUs.

Start a shell in the container with this repository mounted:

```sh
docker run -it --rm -v <path-to-this-repo>:/foss/designs/assignment \
  hpretl/iic-osic-tools:latest --skip bash
```

Inside the container:

```sh
cd /foss/designs/assignment
sak-pdk sky130A            # the image defaults to ihp-sg13g2
echo $PDK_ROOT $PDK        # should print: /foss/pdks sky130A
iverilog -V | head -1
yosys -V
sta -version
```

All commands below are run from the repository root inside the container, unless noted.

## Part A : RTL simulation

**Run**

```sh
iverilog -g2012 -o sim tb/tb_mult.v rtl/full_adder.v rtl/mult_array.v
vvp sim
gtkwave mult.vcd           # optional: view the waveform
```

**Expected output** (summary line):

```
PASS: 256 vectors checked, 0 errors
```

**Error-injection check.** In `rtl/full_adder.v` change `assign sum = a ^ b ^ cin;` to
`assign sum = a ^ b;`, run the two commands above again, and you get:

```
FAIL: 256 vectors checked, 95 errors
```

Undo the change afterwards and check that the testbench prints `PASS` again.

**Hand-worked example.** Gopal's roll number 2023112006 ends in 6, so A = 6 + 5 = 11 and B = 7.
11 × 7 = 77 = `0100_1101`. In `mult.vcd` the inputs are applied at 5520 ns, captured at the
5525 ns clock edge, and `p = 77` appears at the 5535 ns edge: a latency of 2 clock edges (see
`report/report.pdf`).

## Part B : Synthesis with Yosys

**Run**

```sh
yosys -c synth/synth.tcl
```

This rewrites `synth/mult_array_netlist.v` and `synth/mult_array_stat.rpt`.

**Gate-level netlist simulation** (proves synthesis didn't change the behaviour):

```sh
CELLS=$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/verilog
iverilog -g2012 -DFUNCTIONAL -DUNIT_DELAY=#1 -o gls \
  tb/tb_mult.v $CELLS/primitives.v $CELLS/sky130_fd_sc_hd.v synth/mult_array_netlist.v
vvp gls
```

**Expected output:** `PASS: 256 vectors checked, 0 errors`

**Results** (from `synth/mult_array_stat.rpt`)

| Metric | Value |
|--------|-------|
| Total number of cells | 61 |
| Number of flip-flops | 16 (`sky130_fd_sc_hd__dfrtp_1`) |
| Total cell area (µm²) | 756.976 |
| Flip-flop area (µm²) | 16 × 25.024 = 400.384 |
| Flip-flop area (% of total) | 52.89 % |
| 3 most-used cell types | `dfrtp_1` × 16, `nand2_1` × 7, `and2_0` × 4 and `maj3_1` × 4 (tied) |
| Netlist simulation result | `PASS: 256 vectors checked, 0 errors` |

## Part C : Static timing analysis with OpenSTA

Run Part B first: STA reads `synth/mult_array_netlist.v`. The clock period defaults to 10 ns and
can be changed with the `STA_PERIOD` environment variable.

**Run**

```sh
sta sta/sta.tcl                      # T = 10 ns   -> worst slack 7.213 ns
STA_PERIOD=2.79 sta sta/sta.tcl      # T = Tmin    -> worst slack 0.003 ns (≈ 0)
sta sta/sta.tcl                      # run at 10 ns again so sta/mult_array_timing.rpt is the 10 ns report
```

Tmin = T − WNS = 10 − 7.213 = 2.787 ns, and Fmax = 1000 / Tmin.

**Results**

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

## Part D : Place and route with LibreLane

LibreLane reads the RTL directly (`VERILOG_FILES` in `pnr/config.json`). A run takes 5–15 minutes
and creates `pnr/runs/RUN_<date>_<time>/`. That folder isn't committed because it is very large.

**Run**

```sh
cd pnr
librelane config.json                # or: python3 -m librelane config.json
```

**Copy the results** of the successful run into `pnr/`:

```sh
RUN=$(ls -d runs/RUN_* | tail -1)    # the newest run
cp $RUN/final/metrics.json metrics.json
cp $RUN/final/gds/mult_array.gds mult_array.gds
```

**Check the results**

```sh
python3 -c "import json; m = json.load(open('metrics.json')); \
  [print(k, m[k]) for k in ['design__instance__count', 'design__core__area', 'design__die__area', \
  'route__wirelength', 'timing__setup__ws', 'magic__drc_error__count', 'design__lvs_error__count']]"
klayout mult_array.gds               # view the layout
cd ..
```

**Goal:** 0 DRC errors, 0 LVS errors, setup slack ≥ 0. If setup fails, raise `CLOCK_PERIOD` in
`pnr/config.json` by 0.5 ns and run again.

**Every attempt.** The starting `CLOCK_PERIOD` was 1.2 × 2.787 = 3.344 ns, rounded up to 3.5 ns,
then +0.5 ns after each failed attempt. LibreLane signs off setup in all nine PVT corners; the
worst one was always the slow-slow corner (`ss_100C_1v60`).

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

**Results**

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

**Layout screenshots** for the report (whole die and zoomed view), rendered by KLayout in batch
mode from the repository root:

```sh
klayout -zz -r report/figs/layout_shots.py
```

## Report

`report/report.pdf` contains all result tables, the hand-worked example, the block diagram,
the annotated waveform, the layout screenshots, the answers to the questions and the division of
work. To rebuild it (needs [Typst](https://typst.app), runs on the host):

```sh
cd report && typst compile report.typ report.pdf
```

## Run everything in one go

From the repository root inside the container (after `sak-pdk sky130A`):

```sh
iverilog -g2012 -o sim tb/tb_mult.v rtl/full_adder.v rtl/mult_array.v && vvp sim | grep -E "PASS|FAIL"
yosys -q -c synth/synth.tcl
CELLS=$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/verilog
iverilog -g2012 -DFUNCTIONAL -DUNIT_DELAY=#1 -o gls \
  tb/tb_mult.v $CELLS/primitives.v $CELLS/sky130_fd_sc_hd.v synth/mult_array_netlist.v && vvp gls | grep -E "PASS|FAIL"
sta sta/sta.tcl
(cd pnr && librelane config.json)
```

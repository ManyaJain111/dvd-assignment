#!/usr/bin/env python3
"""Generate the block diagram of mult_array (block_diagram.svg)."""

W, H = 1100, 820
COLX = {j: 360 + (3 - j) * 150 for j in range(4)}   # MSB on the left
AND_Y = {i: 80 + i * 160 for i in range(4)}          # top of AND gates in row i
FA_Y = {i: AND_Y[i] + 55 for i in range(1, 4)}       # top of full adders in row i
FA_W, FA_H = 84, 50
AND_W, AND_H = 34, 28
REG_X = 980

out = []


def line(pts, color="#222", width=1.6, arrow=True, dash=None):
    d = " ".join(f"{x},{y}" for x, y in pts)
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    marker = ' marker-end="url(#arr)"' if arrow else ""
    out.append(f'<polyline points="{d}" fill="none" stroke="{color}" '
               f'stroke-width="{width}"{extra}{marker}/>')


def rect(x, y, w, h, fill, stroke="#222", rx=4):
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
               f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')


def text(x, y, s, size=13, anchor="middle", weight="normal", color="#111", italic=False):
    st = ' font-style="italic"' if italic else ""
    out.append(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
               f'font-weight="{weight}" fill="{color}"{st}>{s}</text>')


def and_out(i, j):
    """Bottom-centre of AND gate pp_i[j]."""
    return COLX[j] - 22, AND_Y[i] + AND_H


def fa_pin(i, j, pin):
    x, y = COLX[j], FA_Y[i]
    return {
        "a": (x - 22, y),                 # pp_i[j]
        "b": (x + 22, y),                 # r_{i-1}[j]
        "cin": (x + FA_W / 2, y + FA_H / 2),
        "cout": (x - FA_W / 2, y + FA_H / 2),
        "sum": (x, y + FA_H),
    }[pin]


# ---------------------------------------------------------------- AND gates
for i in range(4):
    for j in range(4):
        x, y = and_out(i, j)
        rect(x - AND_W / 2, AND_Y[i], AND_W, AND_H, "#fde8c8")
        text(x, AND_Y[i] + 19, "&amp;", 15, weight="bold")
        text(x - AND_W / 2 - 4, AND_Y[i] + 11, f"pp{i}[{j}]", 10, anchor="end", color="#7a4b00")
    text(256, AND_Y[i] + 19, f"Row {i}", 15, weight="bold")

# ---------------------------------------------------------------- full adders
for i in range(1, 4):
    for j in range(4):
        x, y = COLX[j], FA_Y[i]
        rect(x - FA_W / 2, y, FA_W, FA_H, "#d6e6fb")
        text(x, y + 22, "FA", 15, weight="bold")
        text(x, y + 39, f"fa{i}_{j}", 11, color="#24518f")
        # pp_i[j] into a
        ax, ay = and_out(i, j)
        line([(ax, ay), fa_pin(i, j, "a")])
        # carry chain
        if j < 3:
            line([fa_pin(i, j, "cout"), fa_pin(i, j + 1, "cin")], color="#b3261e")
    cx, cy = fa_pin(i, 0, "cin")
    line([(cx + 30, cy), (cx, cy)], color="#b3261e")
    text(cx + 36, cy + 4, "0", 12, anchor="start", color="#b3261e")

# r0 = {0, pp0[3], pp0[2], pp0[1]} into row 1
for j in range(4):
    bx, by = fa_pin(1, j, "b")
    if j < 3:
        sx, sy = and_out(0, j + 1)
        mid = AND_Y[1] - 40 + 9 * j
        line([(sx, sy), (sx, mid), (bx, mid), (bx, by)])
    else:
        line([(bx, by - 30), (bx, by)])
        text(bx, by - 34, "0", 12)

# r_i = {c_i[4], s_i[3], s_i[2], s_i[1]} into row i+1
for i in range(1, 3):
    for j in range(4):
        mid = AND_Y[i + 1] - 40 + 9 * j
        bx, by = fa_pin(i + 1, j, "b")
        if j < 3:
            sx, sy = fa_pin(i, j + 1, "sum")
            line([(sx, sy), (sx, mid), (bx, mid), (bx, by)])
        else:
            cx, cy = fa_pin(i, 3, "cout")
            line([(cx, cy), (cx - 20, cy), (cx - 20, mid), (bx, mid), (bx, by)], color="#b3261e")

# ---------------------------------------------------------------- output register
reg_top, reg_bot = AND_Y[0] - 10, 770
rect(REG_X, reg_top, 70, reg_bot - reg_top, "#d9f0dc")
text(REG_X + 35, (reg_top + reg_bot) / 2 - 10, "p reg", 14, weight="bold")
text(REG_X + 35, (reg_top + reg_bot) / 2 + 10, "8 × DFF", 12)
text(REG_X + 35, (reg_top + reg_bot) / 2 + 28, "dfrtp", 11, italic=True, color="#2d6a35")

pin_y = {}
# p[0] from pp0[0]
x, y = and_out(0, 0)
pin_y[0] = AND_Y[0] + AND_H / 2
line([(x + AND_W / 2, pin_y[0]), (REG_X, pin_y[0])], color="#2d6a35")
# p[1..3] from s_i[0]
for i in range(1, 4):
    sx, sy = fa_pin(i, 0, "sum")
    py = sy + 8
    pin_y[i] = py
    line([(sx, sy), (sx, py), (REG_X, py)], color="#2d6a35")
# p[7:4] = {c3[4], s3[3], s3[2], s3[1]}
bus_y = {4: 700, 5: 715, 6: 730, 7: 745}
for k, j in zip((4, 5, 6), (1, 2, 3)):
    sx, sy = fa_pin(3, j, "sum")
    line([(sx, sy), (sx, bus_y[k]), (REG_X, bus_y[k])], color="#2d6a35", width=1.3)
cx, cy = fa_pin(3, 3, "cout")
line([(cx, cy), (cx - 20, cy), (cx - 20, bus_y[7]), (REG_X, bus_y[7])], color="#2d6a35", width=1.3)
for k in range(8):
    py = pin_y[k] if k < 4 else bus_y[k]
    text(REG_X - 6, py - 3, f"p[{k}]", 10, anchor="end", color="#2d6a35")

line([(REG_X + 70, (reg_top + reg_bot) / 2), (REG_X + 110, (reg_top + reg_bot) / 2)], width=3)
text(REG_X + 90, (reg_top + reg_bot) / 2 - 10, "p[7:0]", 13, weight="bold")

# ---------------------------------------------------------------- input registers
for k, (name, y) in enumerate((("a", 250), ("b", 420))):
    rect(60, y, 90, 80, "#d9f0dc")
    text(105, y + 30, f"{name}_r reg", 14, weight="bold")
    text(105, y + 48, "4 × DFF", 12)
    text(105, y + 64, "dfrtp", 11, italic=True, color="#2d6a35")
    line([(0, y + 40), (60, y + 40)], width=3)
    text(4, y + 30, f"{name}[3:0]", 12, anchor="start", weight="bold")
    line([(150, y + 40), (215, y + 40)], width=3)
    text(183, y + 32, f"{name}_r[3:0]", 10)
out.append('<rect x="215" y="70" width="10" height="580" fill="#888"/>')
text(8, 690, "pp_i[j] = a_r[j] AND b_r[i]", 12, anchor="start", italic=True)
text(8, 706, "(bus feeds every AND gate)", 11, anchor="start", italic=True, color="#555")

# clk / rst_n
text(8, 600, "clk, rst_n → all 16 flip-flops", 12, anchor="start", italic=True)
text(8, 616, "(async active-low reset)", 11, anchor="start", italic=True, color="#555")

# legend
text(W / 2, 28, "mult_array: 16 AND gates, 12 full adders, 16 flip-flops (2-cycle latency)",
     17, weight="bold")
text(W / 2, 48, "red = carry chain · green = product bits to the output register", 12, color="#555")

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
       f'viewBox="0 0 {W} {H}" font-family="DejaVu Sans, sans-serif">'
       '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
       'markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="context-stroke"/>'
       '</marker></defs><rect width="100%" height="100%" fill="white"/>'
       + "".join(out) + "</svg>")
open(__file__.replace(".py", ".svg"), "w").write(svg)

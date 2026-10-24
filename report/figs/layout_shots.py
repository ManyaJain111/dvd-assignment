# KLayout batch script: render the whole die and a zoomed view of mult_array.gds
# Run: klayout -zz -r report/figs/layout_shots.py
import os
import pya

pdk = os.environ["PDK_ROOT"]
lyp = f"{pdk}/sky130A/libs.tech/klayout/tech/sky130A.lyp"

view = pya.LayoutView()
view.set_config("background-color", "#000000")
view.set_config("grid-visible", "false")
view.load_layout("pnr/mult_array.gds", True)
view.load_layer_props(lyp)
view.max_hier()

# Whole die
view.zoom_fit()
view.save_image("report/figs/layout_die.png", 1400, 1400)

# Zoomed: standard cell rows and metal wires near the middle of the core
view.zoom_box(pya.DBox(60, 60, 90, 80))
view.save_image("report/figs/layout_zoom.png", 1500, 1000)

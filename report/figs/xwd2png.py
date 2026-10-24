"""Convert a 24/32-bit ZPixmap XWD screen dump to PNG (used for the GTKWave screenshot)."""
import struct, sys
from PIL import Image
data = open(sys.argv[1], 'rb').read()
h = struct.unpack('>25I', data[:100])
hsize, width, height, bpl, ncolors = h[0], h[4], h[5], h[12], h[19]
off = hsize + ncolors * 12
img = Image.frombuffer('RGB', (width, height), data[off:off + bpl * height], 'raw', 'BGRX', bpl, 1)
img.save(sys.argv[2])

#!/usr/bin/env python

# generate.py - A multires tile set generator for Pannellum
# Copyright (c) 2014 Matthew Petroff
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import argparse
from PIL import Image
import os
import math

# Parse input
parser = argparse.ArgumentParser(description='Generate a Pannellum multires tile set from an equirectangular panorama.')
parser.add_argument('inputFile', metavar='INPUT',
                    help='full equirectangular panorama to be processed')
parser.add_argument('-o', '--output', dest='output', default='./output',
                    help='output directory (default: ./output)')
parser.add_argument('-s', '--tilesize', dest='tileSize', default=512, type=int,
                    help='tile size in pixels (default: 512)')
parser.add_argument('--png', action='store_true',
                    help='output PNG tiles instead of JPEG tiles')
args = parser.parse_args()

# Create output directory
os.makedirs(args.output)

# Process input image information
print('Processing input image information...')
origWidth, origHeight = Image.open(args.inputFile).size
cubeSize = 8 * int(origWidth / 3.14159265 / 8)
levels = math.ceil(math.log(cubeSize / args.tileSize, 2)) + 1
origHeight = str(origHeight)
origWidth = str(origWidth)
origFilename = os.path.join(os.getcwd(), args.inputFile)
extension = '.jpg'
if args.png:
    extension = '.png'

# Generate PTO file for nona to generate cube faces
# Face order: front, back, up, down, left, right
faceLetters = ['f', 'b', 'u', 'd', 'l', 'r']
text = []
text.append('p E0 R0 f0 h' + str(cubeSize) + ' n"TIFF_m" u0 v90 w' + str(cubeSize))
text.append('m g1 i0 m2 p0.00784314')
text.append('i a0 b0 c0 d0 e0 f4 h' + origHeight + ' n"' + origFilename + '" p0 r0 v360 w' + origWidth + ' y0')
text.append('i a0 b0 c0 d0 e0 f4 h' + origHeight + ' n"' + origFilename + '" p0 r0 v360 w' + origWidth + ' y180')
text.append('i a0 b0 c0 d0 e0 f4 h' + origHeight + ' n"' + origFilename + '" p-90 r0 v360 w' + origWidth + ' y0')
text.append('i a0 b0 c0 d0 e0 f4 h' + origHeight + ' n"' + origFilename + '" p90 r0 v360 w' + origWidth + ' y0')
text.append('i a0 b0 c0 d0 e0 f4 h' + origHeight + ' n"' + origFilename + '" p0 r0 v360 w' + origWidth + ' y90')
text.append('i a0 b0 c0 d0 e0 f4 h' + origHeight + ' n"' + origFilename + '" p0 r0 v360 w' + origWidth + ' y-90')
text.append('v')
text.append('*')
text = '\n'.join(text)
with open(os.path.join(args.output, 'cubic.pto'), 'w') as f:
    f.write(text)

# Create cube faces
print('Generating cube faces...')
os.system('nona -o ' + os.path.join(args.output, 'face') + ' ' + os.path.join(args.output, 'cubic.pto'))
faces = ['face0000.tif', 'face0001.tif', 'face0002.tif', 'face0003.tif', 'face0004.tif', 'face0005.tif']

# Generate tiles
print('Generating tiles...')
for f in range(0, 6):
    size = cubeSize
    face = Image.open(os.path.join(args.output, faces[f]))
    for level in range(levels, 0, -1):
        os.makedirs(os.path.join(args.output, str(level)), exist_ok=True)
        tiles = math.ceil(size / args.tileSize)
        if (level < levels):
            face = face.resize([size, size], Image.ANTIALIAS)
        for i in range(0, tiles):
            for j in range(0, tiles):
                left = j * 512
                upper = i * 512
                right = min(j * 512 + 512, size)
                lower = min(i * 512 + 512, size)
                tile = face.crop([left, upper, right, lower])
                tile.load()
                tile.save(os.path.join(args.output, str(level), faceLetters[f] + str(i) + '_' + str(j) + extension))
        size = int(size / 2)

# Clean up temporary files
os.remove(os.path.join(args.output, 'cubic.pto'))
for face in faces:
    os.remove(os.path.join(args.output, face))

# Generate config file
text = []
text.append('{')
text.append('    "type": "multires",')
text.append('    ')
text.append('    "multiRes": {')
text.append('        "path": "./%l/%s%y_%x",')
text.append('        "extension": "jpg",')
text.append('        "tileResolution": ' + str(args.tileSize) + ',')
text.append('        "maxLevel": ' + str(levels) + ',')
text.append('        "cubeResolution": ' + str(cubeSize))
text.append('    }')
text.append('}')
text = '\n'.join(text)
with open(os.path.join(args.output, 'config.json'), 'w') as f:
    f.write(text)

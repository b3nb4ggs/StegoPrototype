from PIL import Image
from bit_operators import BitFeederString, BitSaver
import os, sys
from arguments import avg_parser

class CoordGenerator():
    """CoordGenerator serializes pixel/color channel indices to 
    linearly loop through image.
    """    
    def __init__(self, w, h, channel, start_position=[0,0,0]):
        self.w = w
        self.h = h
        self.channel = channel
                      #    h  w  c height width channel
        # self.position = [0, 0, 0]
        self.position = start_position
        self.exit = False
    
    def get_n(self, n):
        output_coordinates = []
        while len(output_coordinates) < n and not self.exit:

            output_coordinates.append(self.position.copy())
            self._increment_position()
        return output_coordinates

    def _increment_position(self):
        if self.position[2] < (self.channel-1):
            self.position[2] += 1
        
        elif self.position[1] < (self.w-1):
            self.position[2] = 0
            self.position[1] += 1

        elif self.position[0] < (self.h-1):
            self.position[2] = 0
            self.position[1] = 0
            self.position[0] += 1
        
        else:
            print("no more pixels left")
            self.exit = True

def get_pixel_byte_group(image, coord_obj, pixel_no):
    coords = coord_obj.get_n(pixel_no)
    pixel_group = []
    for c in coords:
        byte_value = image.getpixel((c[0],c[1]))[c[2]]
        pixel_group.append(byte_value)

    return pixel_group

args = avg_parser.parse_args()
command = args.command
cover = args.cover
message = args.message
method = args.method
lsb = args.lsb
pixel_no = args.pixelno

im = Image.open(cover)
if command == 'encode':
    pass

if command == 'decode':
    pass
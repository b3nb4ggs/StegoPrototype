from PIL import Image
from bit_operators import BitFeederString, BitSaver, read_lsb_avg, write_lsb_avg, read_lsb_sum, write_lsb_sum, replace_lsb
import os, sys
from arguments import avg_parser
import pdb

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

def get_pixel_byte_group(image, coords):
    pixel_group = []
    for c in coords:
        byte_value = image.getpixel((c[1],c[0]))[c[2]]
        pixel_group.append(byte_value)

    return pixel_group

def update_pixel(image, coords, new_pixels):
    for i in range(len(coords)):
        c = coords[i]
        new_byte = new_pixels[i]

        original = list(image.getpixel((c[1],c[0])))
        original[c[2]] = new_byte
        updated = tuple(original)
        
        image.putpixel((c[1], c[0]), updated)

def save_metadata(output, message_size, message_extension):
    # start at 0,0 pixel, use 4 lsb in corner
    size_bits = bin(message_size)[2:]
    size_bits = '0'*(32-len(size_bits)) + size_bits # pad with zeros
    size_bits = [size_bits[i:i+4] for i in range(0, len(size_bits), 4)]
    
    extension_length = len(message_extension)
    if extension_length > 4:
        raise ValueError("extension length should be less than 4 char")
    ext_length_bits = bin(extension_length)[2:]
    ext_length_bits = '0'*(4-len(ext_length_bits)) + ext_length_bits

    extension_bytes = [ord(x) for x in message_extension]
    extension_bits = [bin(x)[2:] for x in extension_bytes]
    extension_8bits = ['0'*(8-len(x)) + x for x in extension_bits]
    extension_8bits = [byte[i:i+4] for byte in extension_8bits for i in range(0,len(byte), 4)]

    metadata = size_bits + [ext_length_bits] + extension_8bits
    cg2 = CoordGenerator(output.size[0], output.size[1], 3, start_position=[0,0,0]) 
    coord_set = cg2.get_n(len(metadata))
    for i in range(len(coord_set)):
        c = coord_set[i]
        original = list(output.getpixel((c[1],c[0])))
        byte = original[c[2]]
        new_byte = replace_lsb(metadata[i], byte, 4) # default 4 lsb for metadata

        original[c[2]] = new_byte
        updated = tuple(original)
        
        output.putpixel((c[1], c[0]), updated) 

def get_metadata(image):
    cg2 = CoordGenerator(image.size[0], image.size[1], 3, start_position=[0,0,0])
    coordinate_set = cg2.get_n(32)
    for i in range(len(coordinate_set))

    return message_size, message_extension

args = avg_parser.parse_args()
command = args.command
cover = args.cover
message = args.message
method = args.method
nlsb = int(args.lsb) # number of lsb bits to use
pixel_no = int(args.pixelno)

im = Image.open(cover)
output = im.copy()

if command == 'encode':
    bf = BitFeederString(message)
    cg = CoordGenerator(im.size[0], im.size[1], 3, start_position=[1, 0, 0]) # start on second row of the image

    message_size = int(bf.get_length()/8)
    message_extension = message.split(".")[-1]

    save_metadata(output, message_size, message_extension)
    while not bf.finished and not cg.exit:
        coordinate_set = cg.get_n(pixel_no)
        pixel_group = get_pixel_byte_group(im, coordinate_set) 

        if method == 'sum':
            new_bytes = write_lsb_sum(pixel_group, bf.get_bits(nlsb), nlsb)

        elif method == 'avg':
            new_bytes = write_lsb_avg(pixel_group, bf.get_bits(nlsb), nlsb)
        
        # update output
        update_pixel(output, coordinate_set, new_bytes)
        
    if bf.finished:
        print("success")

    print(f"original 0,1 pixel: {im.getpixel((0,1))}")
    print(f"output 0,1 pixel: {output.getpixel((0,1))}")

    output.save('output.' + cover.split('.')[-1])

if command == 'decode':
    print(f"cover 0,1 pixel: {output.getpixel((0,1))}")
    bs = BitSaver(file_length=405216) # hard code test file size for now TODO FILE METADATA
    # bs = BitSaver(file_length=1112) # hard code test file size for now TODO FILE METADATA
    cg = CoordGenerator(im.size[0], im.size[1], 3, start_position=[1,0,0])

    while not bs.finished:
        coordinate_set = cg.get_n(pixel_no)
        pixel_group = get_pixel_byte_group(im, coordinate_set) 

        if method == 'sum':
            bits = read_lsb_sum(pixel_group, nlsb)

        elif method == 'avg':
            bits = read_lsb_avg(pixel_group, nlsb)
        
        # add bits to file
        bs.add_bits(bits, datatype=int, nlsb=nlsb)
    
    bs.save_file('test_output.jpg')
    # bs.save_file('test_output.txt')
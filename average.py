from PIL import Image
from bit_operators import BitFeederString, BitSaver, read_lsb_avg, write_lsb_avg, read_lsb_sum, write_lsb_sum, get_lsb, replace_lsb
import os, sys
from arguments import avg_parser
import pdb
from datetime import datetime

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
    metadata = []
    for i in range(len(coordinate_set)):
        c = coordinate_set[i]
        pixel = image.getpixel((c[1], c[0]))
        bits = get_lsb(pixel[c[2]], 4)
        bits = bin(bits)[2:]
        bits = '0'*(4-len(bits)) + bits
        metadata.append(bits)

    message_size = ''.join(metadata[:8])
    message_size = int(message_size, 2)
    
    ext_length = int(metadata[8],2)

    ext_data = metadata[9:9+ext_length*2]
    ext_data = [''.join(ext_data[i:i+2]) for i in range(0,len(ext_data),2)]
    ext_data = [chr(int(x,2)) for x in ext_data]
    message_extension = ''.join(ext_data)
    return message_size, message_extension

args = avg_parser.parse_args()
command = args.command
cover = args.cover
message = args.message
method = args.method
nlsb = int(args.lsb) # number of lsb bits to use
pixel_no = int(args.pixelno)

print(cover)
print(message)
print(message)

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
            new_bytes = write_lsb_sum(pixel_group.copy(), bf.get_bits(nlsb), nlsb)

        elif method == 'avg':
            new_bytes = write_lsb_avg(pixel_group.copy(), bf.get_bits(nlsb), nlsb)
        
        # update output
        update_pixel(output, coordinate_set, new_bytes)

    if bf.finished:
        print("success")
    else:
        print('ran out of pixels for data storage')

    output.save('output.' + cover.split('.')[-1])

if command == 'decode':
    message_length, extension = get_metadata(im)
    print(f"expected message size: {message_length}")

    bs = BitSaver(file_length=message_length*8) 
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
    
    base = 'message_extract'
    if extension != '':
        bs.save_file(base + '.' + extension)
    else:
        bs.save_file(base)
    

# In [1]: %run -m cProfile average.py encode colortest.png cat.jpg --lsb 4 --pixelno 4 --method avg                                    

#          12412326 function calls in 6.670 seconds

#    Ordered by: standard name

#    ncalls  tottime  percall  cumtime  percall filename:lineno(function)
#         1    0.000    0.000    0.000    0.000 <frozen importlib._bootstrap>:1017(_handle_fromlist)
#         1    0.000    0.000    0.000    0.000 BmpImagePlugin.py:45(_accept)
#         1    0.000    0.000    0.000    0.000 BmpImagePlugin.py:49(_dib_accept)
#         1    0.000    0.000    0.000    0.000 GifImagePlugin.py:39(_accept)
#         1    0.000    0.000    0.041    0.041 Image.py:1107(copy)
#    810447    0.502    0.000    1.431    0.000 Image.py:1354(getpixel)
#    405231    0.288    0.000    0.696    0.000 Image.py:1708(putpixel)
#         1    0.000    0.000    0.140    0.140 Image.py:2081(save)
#         1    0.000    0.000    0.000    0.000 Image.py:2819(_decompression_bomb_check)
#         1    0.000    0.000    0.000    0.000 Image.py:2839(open)
#         1    0.000    0.000    0.000    0.000 Image.py:2893(_open_core)
#         2    0.000    0.000    0.000    0.000 Image.py:347(preinit)
#         1    0.000    0.000    0.000    0.000 Image.py:419(_getdecoder)
#         1    0.000    0.000    0.000    0.000 Image.py:442(_getencoder)
#         2    0.000    0.000    0.000    0.000 Image.py:530(__init__)
#        11    0.000    0.000    0.000    0.000 Image.py:551(size)
#         1    0.000    0.000    0.000    0.000 Image.py:555(_new)
#         1    0.000    0.000    0.000    0.000 Image.py:616(_ensure_mutable)
#   1215682    0.593    0.000    0.803    0.000 Image.py:810(load)
#    405217    0.200    0.000    0.501    0.000 ImageFile.py:150(load)
#         1    0.000    0.000    0.001    0.001 ImageFile.py:284(load_prepare)
#         1    0.000    0.000    0.139    0.139 ImageFile.py:484(_save)
#         6    0.000    0.000    0.000    0.000 ImageFile.py:546(_safe_read)
#         2    0.000    0.000    0.000    0.000 ImageFile.py:77(_tilesort)
#         1    0.000    0.000    0.000    0.000 ImageFile.py:90(__init__)
#         1    0.000    0.000    0.000    0.000 JpegImagePlugin.py:325(_accept)
#        26    0.000    0.000    0.000    0.000 PngImagePlugin.py:104(_crc32)
#         1    0.000    0.000    0.000    0.000 PngImagePlugin.py:113(__init__)
#         1    0.000    0.000    0.139    0.139 PngImagePlugin.py:1132(_save)
#        12    0.000    0.000    0.000    0.000 PngImagePlugin.py:118(read)
#         1    0.000    0.000    0.000    0.000 PngImagePlugin.py:143(close)
#         7    0.000    0.000    0.000    0.000 PngImagePlugin.py:150(call)
#         6    0.000    0.000    0.000    0.000 PngImagePlugin.py:156(crc)
#         1    0.000    0.000    0.000    0.000 PngImagePlugin.py:209(__new__)
#         1    0.000    0.000    0.000    0.000 PngImagePlugin.py:304(__init__)
#         1    0.000    0.000    0.000    0.000 PngImagePlugin.py:321(check_text_memory)
#         1    0.000    0.000    0.000    0.000 PngImagePlugin.py:341(chunk_iCCP)
#         1    0.000    0.000    0.000    0.000 PngImagePlugin.py:370(chunk_IHDR)
#         1    0.000    0.000    0.000    0.000 PngImagePlugin.py:385(chunk_IDAT)
#         1    0.000    0.000    0.000    0.000 PngImagePlugin.py:458(chunk_pHYs)
#         1    0.000    0.000    0.000    0.000 PngImagePlugin.py:526(chunk_iTXt)
#         1    0.000    0.000    0.000    0.000 PngImagePlugin.py:567(chunk_eXIf)
#         2    0.000    0.000    0.000    0.000 PngImagePlugin.py:623(_accept)
#         1    0.000    0.000    0.000    0.000 PngImagePlugin.py:636(_open)
#         1    0.000    0.000    0.001    0.001 PngImagePlugin.py:823(load_prepare)
#         5    0.000    0.000    0.001    0.000 PngImagePlugin.py:832(load_read)
#         1    0.000    0.000    0.000    0.000 PngImagePlugin.py:865(load_end)
#         1    0.000    0.000    0.000    0.000 PngImagePlugin.py:96(_safe_zlib_decompress)
#         7    0.000    0.000    0.001    0.000 PngImagePlugin.py:970(putchunk)
#         1    0.000    0.000    0.000    0.000 PngImagePlugin.py:984(__init__)
#         3    0.000    0.000    0.001    0.000 PngImagePlugin.py:988(write)
#         1    0.000    0.000    0.000    0.000 PpmImagePlugin.py:39(_accept)
#         1    0.000    0.000    0.000    0.000 TiffImagePlugin.py:257(_accept)
#        10    0.000    0.000    0.000    0.000 __init__.py:1412(debug)
#        10    0.000    0.000    0.000    0.000 __init__.py:1677(isEnabledFor)
#         9    0.000    0.000    0.000    0.000 _binary.py:21(i8)
#         1    0.000    0.000    0.000    0.000 _binary.py:50(i32le)
#        22    0.000    0.000    0.000    0.000 _binary.py:74(i32be)
#        16    0.000    0.000    0.000    0.000 _binary.py:91(o32be)
#         3    0.000    0.000    0.000    0.000 _util.py:10(isPath)
#         1    0.000    0.000    0.000    0.000 abc.py:96(__instancecheck__)
#         1    0.000    0.000    0.000    0.000 argparse.py:1240(__init__)
#         6    0.000    0.000    0.000    0.000 argparse.py:1312(_registry_get)
#         6    0.000    0.000    0.000    0.000 argparse.py:1676(identity)
#         1    0.000    0.000    0.000    0.000 argparse.py:1759(_get_positional_actions)
#         1    0.000    0.000    0.000    0.000 argparse.py:1760(<listcomp>)
#         1    0.000    0.000    0.000    0.000 argparse.py:1767(parse_args)
#         1    0.000    0.000    0.000    0.000 argparse.py:1774(parse_known_args)
#         1    0.000    0.000    0.000    0.000 argparse.py:1809(_parse_known_args)
#         6    0.000    0.000    0.000    0.000 argparse.py:1856(take_action)
#         3    0.000    0.000    0.000    0.000 argparse.py:1877(consume_optional)
#         2    0.000    0.000    0.000    0.000 argparse.py:1954(consume_positionals)
#         4    0.000    0.000    0.000    0.000 argparse.py:1983(<listcomp>)
#         3    0.000    0.000    0.000    0.000 argparse.py:2084(_match_argument)
#         2    0.000    0.000    0.000    0.000 argparse.py:2106(_match_arguments_partial)
#         1    0.000    0.000    0.000    0.000 argparse.py:2112(<listcomp>)
#         1    0.000    0.000    0.000    0.000 argparse.py:2116(<listcomp>)
#         9    0.000    0.000    0.000    0.000 argparse.py:2122(_parse_optional)
#         6    0.000    0.000    0.000    0.000 argparse.py:2225(_get_nargs_pattern)
#         6    0.000    0.000    0.000    0.000 argparse.py:2358(_get_values)
#         6    0.000    0.000    0.000    0.000 argparse.py:2414(_get_value)
#         6    0.000    0.000    0.000    0.000 argparse.py:2440(_check_value)
#         6    0.000    0.000    0.000    0.000 argparse.py:880(__call__)
#         1    0.274    0.274    6.670    6.670 average.py:1(<module>)
#         2    0.000    0.000    0.000    0.000 average.py:11(__init__)
#    101305    0.389    0.000    0.729    0.000 average.py:20(get_n)
#    405231    0.196    0.000    0.196    0.000 average.py:28(_increment_position)
#    101304    0.274    0.000    1.138    0.000 average.py:45(get_pixel_byte_group)
#    101304    0.511    0.000    1.830    0.000 average.py:53(update_pixel)
#         1    0.000    0.000    0.000    0.000 average.py:64(save_metadata)
#         1    0.000    0.000    0.000    0.000 average.py:68(<listcomp>)
#         1    0.000    0.000    0.000    0.000 average.py:7(CoordGenerator)
#         1    0.000    0.000    0.000    0.000 average.py:76(<listcomp>)
#         1    0.000    0.000    0.000    0.000 average.py:77(<listcomp>)
#         1    0.000    0.000    0.000    0.000 average.py:78(<listcomp>)
#         1    0.000    0.000    0.000    0.000 average.py:79(<listcomp>)
#        15    0.000    0.000    0.000    0.000 bit_operators.py:122(replace_lsb)
#         1    0.001    0.001    0.059    0.059 bit_operators.py:14(__init__)
#    101304    0.075    0.000    0.075    0.000 bit_operators.py:143(get_lsb)
#    101304    1.753    0.000    2.338    0.000 bit_operators.py:157(write_lsb_avg)
#         1    0.000    0.000    0.000    0.000 bit_operators.py:21(_load_bytes)
#    218840    0.041    0.000    0.041    0.000 bit_operators.py:213(<genexpr>)
#         1    0.039    0.039    0.058    0.058 bit_operators.py:25(_make_bitstring)
#    101304    0.075    0.000    0.180    0.000 bit_operators.py:254(read_lsb_avg)
#         1    0.000    0.000    0.000    0.000 bit_operators.py:33(get_length)
#    101304    0.093    0.000    0.107    0.000 bit_operators.py:36(get_bits)
#         1    0.000    0.000    0.000    0.000 genericpath.py:121(_splitext)
#         1    0.000    0.000    0.000    0.000 posixpath.py:117(splitext)
#         4    0.000    0.000    0.000    0.000 re.py:188(match)
#         4    0.000    0.000    0.000    0.000 re.py:289(_compile)
#         1    0.001    0.001    0.001    0.001 {built-in method PIL._imaging.new}
#         1    0.000    0.000    0.000    0.000 {built-in method PIL._imaging.zip_decoder}
#         1    0.000    0.000    0.000    0.000 {built-in method PIL._imaging.zip_encoder}
#         1    0.000    0.000    0.000    0.000 {built-in method __new__ of type object at 0x1065ec808}
#         1    0.000    0.000    0.000    0.000 {built-in method _abc._abc_instancecheck}
#        16    0.000    0.000    0.000    0.000 {built-in method _struct.pack}
#        23    0.000    0.000    0.000    0.000 {built-in method _struct.unpack_from}
#         1    0.000    0.000    0.000    0.000 {built-in method builtins.__build_class__}
#   2928795    0.248    0.000    0.248    0.000 {built-in method builtins.abs}
#     50657    0.008    0.000    0.008    0.000 {built-in method builtins.bin}
#         6    0.000    0.000    0.000    0.000 {built-in method builtins.callable}
#         1    0.000    0.000    6.670    6.670 {built-in method builtins.exec}
#         9    0.000    0.000    0.000    0.000 {built-in method builtins.getattr}
#        14    0.000    0.000    0.000    0.000 {built-in method builtins.hasattr}
#        15    0.000    0.000    0.000    0.000 {built-in method builtins.isinstance}
#         1    0.000    0.000    0.000    0.000 {built-in method builtins.iter}
#   1063747    0.117    0.000    0.117    0.000 {built-in method builtins.len}
#         2    0.000    0.000    0.000    0.000 {built-in method builtins.max}
#         9    0.000    0.000    0.000    0.000 {built-in method builtins.min}
#         3    0.000    0.000    0.000    0.000 {built-in method builtins.ord}
#         4    0.000    0.000    0.000    0.000 {built-in method builtins.print}
#        12    0.000    0.000    0.000    0.000 {built-in method builtins.setattr}
#    399673    0.111    0.000    0.152    0.000 {built-in method builtins.sum}
#         3    0.000    0.000    0.000    0.000 {built-in method io.open}
#         1    0.000    0.000    0.000    0.000 {built-in method posix.fspath}
#         1    0.000    0.000    0.000    0.000 {built-in method zlib.compress}
#        26    0.000    0.000    0.000    0.000 {built-in method zlib.crc32}
#         1    0.000    0.000    0.000    0.000 {built-in method zlib.decompressobj}
#        12    0.000    0.000    0.000    0.000 {method 'add' of 'set' objects}
#    861111    0.095    0.000    0.095    0.000 {method 'append' of 'list' objects}
#         1    0.000    0.000    0.000    0.000 {method 'cleanup' of 'ImagingDecoder' objects}
#         1    0.000    0.000    0.000    0.000 {method 'cleanup' of 'ImagingEncoder' objects}
#         1    0.000    0.000    0.000    0.000 {method 'close' of '_io.BufferedRandom' objects}
#         1    0.000    0.000    0.000    0.000 {method 'close' of '_io.BufferedReader' objects}
#         1    0.005    0.005    0.005    0.005 {method 'copy' of 'ImagingCore' objects}
#         1    0.000    0.000    0.000    0.000 {method 'copy' of 'dict' objects}
#    506535    0.061    0.000    0.061    0.000 {method 'copy' of 'list' objects}
#         5    0.033    0.007    0.033    0.007 {method 'decode' of 'ImagingDecoder' objects}
#        11    0.000    0.000    0.000    0.000 {method 'decode' of 'bytes' objects}
#         1    0.000    0.000    0.000    0.000 {method 'decompress' of 'zlib.Decompress' objects}
#         1    0.000    0.000    0.000    0.000 {method 'disable' of '_lsprof.Profiler' objects}
#         3    0.138    0.046    0.138    0.046 {method 'encode' of 'ImagingEncoder' objects}
#         2    0.000    0.000    0.000    0.000 {method 'extend' of 'list' objects}
#         1    0.000    0.000    0.000    0.000 {method 'find' of 'bytes' objects}
#         1    0.000    0.000    0.000    0.000 {method 'flush' of '_io.BufferedRandom' objects}
#        27    0.000    0.000    0.000    0.000 {method 'get' of 'dict' objects}
#    810447    0.187    0.000    0.187    0.000 {method 'getpixel' of 'ImagingCore' objects}
#         3    0.000    0.000    0.000    0.000 {method 'group' of 're.Match' objects}
#         1    0.000    0.000    0.000    0.000 {method 'groups' of 're.Match' objects}
#         7    0.000    0.000    0.000    0.000 {method 'join' of 'bytes' objects}
#         3    0.001    0.000    0.001    0.000 {method 'join' of 'str' objects}
#         1    0.000    0.000    0.000    0.000 {method 'lower' of 'str' objects}
#        16    0.000    0.000    0.000    0.000 {method 'match' of 're.Pattern' objects}
#   1215681    0.211    0.000    0.211    0.000 {method 'pixel_access' of 'ImagingCore' objects}
#         1    0.000    0.000    0.000    0.000 {method 'pop' of 'dict' objects}
#    405231    0.147    0.000    0.147    0.000 {method 'putpixel' of 'ImagingCore' objects}
#        37    0.000    0.000    0.000    0.000 {method 'read' of '_io.BufferedReader' objects}
#         7    0.000    0.000    0.000    0.000 {method 'remove' of 'list' objects}
#         6    0.000    0.000    0.000    0.000 {method 'replace' of 'str' objects}
#         2    0.000    0.000    0.000    0.000 {method 'rfind' of 'str' objects}
#         3    0.000    0.000    0.000    0.000 {method 'seek' of '_io.BufferedReader' objects}
#         1    0.000    0.000    0.000    0.000 {method 'setimage' of 'ImagingDecoder' objects}
#         1    0.000    0.000    0.000    0.000 {method 'setimage' of 'ImagingEncoder' objects}
#         2    0.000    0.000    0.000    0.000 {method 'sort' of 'list' objects}
#         2    0.000    0.000    0.000    0.000 {method 'split' of 'bytes' objects}
#         2    0.000    0.000    0.000    0.000 {method 'split' of 'str' objects}
#         1    0.000    0.000    0.000    0.000 {method 'startswith' of 'bytes' objects}
#        12    0.000    0.000    0.000    0.000 {method 'tell' of '_io.BufferedReader' objects}
#         2    0.000    0.000    0.000    0.000 {method 'upper' of 'str' objects}
#        22    0.000    0.000    0.000    0.000 {method 'write' of '_io.BufferedRandom' objects}
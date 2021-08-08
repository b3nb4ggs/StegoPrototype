# created by Group 6 
#  Ben Baggs, Rongrong Wei
# steganography project
# this is the bit depth hiding program

from sys import exit
from PIL import Image
from bit_operators import BitFeederString, BitSaver
import os
import argparse

#returns file type
def get_type(input):
    type = os.path.splitext(input)
    output = str(type[-1])
    return output
#returns string from bits
def bits2string(b=None):
    return ''.join([chr(int(x, 2)) for x in b])
#Makes sure we have an 8 bit byte from int
def byte_maker(color):
    return f'{color:08b}'
#returns an int from byte bin string
def int_maker(color):
    return int(color, 2)
#Return bitstring to encode in first 32 bits
def length_in_bits(length):
    bits = bin(length)[2:]
    bits = '0'*(32-len(bits)) + bits
    return bits
#a helper function to turn a 32 bit bin string to an int
def length_in_int(binary_input):
    return int(binary_input, 2)
#encodes 1 bit at specified bit level
def encoder(cover,message,level=8):
    cover = cover[:level-1]+message+cover[level:]
    return cover
#decodes 1 bit at specified bit level
def decoder(cover,level=8):
    return cover[level-1:level]
#returns file extension
def get_type(input):
    type = os.path.splitext(input)
    output = str(type[-1])
    return output
#A very ugly function to get the number of encoded bits 
def get_length_from_file(x:Image,level=8):
    i = 0
    message_length_string = ''
    for j in range(11):
        color = x.getpixel((i,j))
        for RGB in range(len(color)):
            output=byte_maker(color[RGB])
            bit = decoder(output,level=level)
            message_length_string = message_length_string + bit
    message_length_string = message_length_string[:32]
    return(length_in_int(message_length_string)+72)
#Get metadata about file type from the .bmp
def get_extension_from_file(x:Image,level=8):
    i = 0
    bit_string = ''
    for j in range(25):
            color = x.getpixel((i,j))
            for RGB in range(len(color)):
                output=byte_maker(color[RGB])
                    #print(output)
                bit = decoder(output,level=level)
                bit_string = bit_string + bit
    bit_string = bit_string[32:72]
    return bit_string

parser = argparse.ArgumentParser(description='Inputs for the stego program.')
parser.add_argument('command', metavar='command', help='Options:<encode><decode>')
parser.add_argument('cover', metavar='cover', help='The .bmp file your hiding in.')
parser.add_argument('message', metavar='message', help="The file to hide inside of .bmp OR <output> on decode")
parser.add_argument('--bit_depth', metavar='bit', 
help='(1-8) Which bit to hide in (8=LSB) default=8', default=8)
args = parser.parse_args()

command = args.command
cover = args.cover
message = args.message
bit_depth = args.bit_depth

if command == 'encode':
    print("Bit depth ="+ str(bit_depth))
    filesize = os.path.getsize(message)
    x = Image.open(cover)
    if x.mode != 'RGB':
        print("Please use a full color bitmap")
        exit()
    pic_size = x.size
    num_of_pixels = pic_size[0]*pic_size[1]
    available_bytes=(num_of_pixels*(3))/8
    print("Filesize="+str(filesize)+"\nCapacity="+str(int(available_bytes)))
    if filesize > available_bytes:
        print("Your file is too large and will not fit.")
        print("Proceeding with partial embed")
    
    name = get_type(message)
    info = []
    for letter in name:
        info.append(ord(letter))
    bits = ""
    for stuff in info:
        bits += byte_maker(stuff)
    bits = bits.zfill(40)
    bfeed = BitFeederString(message)
    length = bfeed.get_length()
    encoded_length = length_in_bits(length)
    length_index = 0
    for i in range(pic_size[0]):
        for j in range(pic_size[1]):
            color = x.getpixel((i,j))
            modified = []
            for RGB in range(len(color)):
                    input = color[RGB]
                    cover = byte_maker(input)
                    if length_index < 32:
                        message = encoded_length[length_index]
                        length_index +=1
                    elif length_index >= 32 and length_index <72:
                        message = bits[length_index-32]
                        length_index +=1
                    else:
                        message = bfeed.get_bits(1)
                    encoded = encoder(cover,message,level=int(bit_depth))
                    output = int(encoded, 2)
                    modified.append(output)
            x.putpixel( (i , j), (modified[0], modified[1], modified[2], 255))
            
            if bfeed.finished == True or i >=pic_size[0]-1 and j>=pic_size[1]-1:
                x.save("Encoded_output.bmp", format="BMP")
                exit()

if command == 'decode':
    x = Image.open(cover)
    pic_size = x.size
    index = 0
    finish = get_length_from_file(x, int(bit_depth))
    type = get_extension_from_file(x, int(bit_depth))
    new_list=["".join(type[i:i + 8]) for i in range(0, len(type), 8)]
    output_string = bits2string(new_list)
    extension = output_string.split(".",1)[1]
    print(extension)
    bs = BitSaver(file_length=finish-72)
    for i in range(pic_size[0]):
        for j in range(pic_size[1]): 
            color = x.getpixel((i,j))
            for RGB in range(len(color)):
                if index < finish:
                    output=byte_maker(color[RGB])
                    #print(output)
                    bit = decoder(output,level = int(bit_depth))
                    if index < 72:
                        index+=1
                    else:
                    #print(bit)
                        bs.add_bits(bit)
                        index += 1
                
bs.save_file("output."+extension)
exit()

    


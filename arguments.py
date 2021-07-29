import argparse

parser = argparse.ArgumentParser(description='Inputs for the stego program.')
parser.add_argument('command', metavar='command', help='Options:<encode><decode>')
parser.add_argument('cover', metavar='cover', help='The .bmp file your hiding in.')
parser.add_argument('message', metavar='message', help="Any file type you want to hide inside the .bmp")
parser.add_argument('--bit_depth', metavar='bit', 
help='(1-8) Which bit to hide in (8=LSB) default=8', default=8)

avg_parser = argparse.ArgumentParser(description='Inputs for the avg/sum stego program.')
avg_parser.add_argument('command', metavar='command', help='Options:<encode><decode>')
avg_parser.add_argument('cover', metavar='cover', help='The .bmp file your hiding in.')
avg_parser.add_argument('message', metavar='message', help="Any file type you want to hide inside the .bmp")
avg_parser.add_argument('--method', metavar='method', 
    help='the method to hide lsb data. either avg or sum', default='avg')
avg_parser.add_argument('--lsb', metavar='lsb', 
    help='(1-7) number of lsb to replace in the average (8=LSB) default=1', default=1)
avg_parser.add_argument('--pixelno', metavar='pixelno', 
    help='(1-8) number of pixels to hide data in default=2', default=2)
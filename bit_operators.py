
class BitFeederString:
    """This class will take a file_name and convert it into string-based bits
    that can be extracted in small pieces.
    
    example syntax:
    bfeed = BitFeederString(my_message_file)
    first_three_bits = bfeed.get_bits(3)
    next_three_bits = bfeed.get_bits(3)
    following_two bits = bfeed.get_bits(2)
    """

    def __init__(self, file_name):       
        self.file_name = file_name
        self._load_bytes()
        self._make_bitstring()
        self.index = 0
        self.finished = False

    def _load_bytes(self):
        with open(self.file_name, 'rb') as in_file:
            self.bytes = in_file.read()

    def _make_bitstring(self):
        bitsarray = []
        for byte in self.bytes:
            bits = bin(byte)[2:]
            bits = '0'*(8-len(bits)) + bits
            bitsarray.append(bits)
        self.bitstring = ''.join(bitsarray)

    def get_length(self):
        return(len(self.bitstring))

    def get_bits(self, n, returntype=str):
        """this function returns n bits 
            
            x = bitfeederobj.get_bits(6, returntype=str)
            print(x)

            '101110'

            x = bitfeederobj.get_bits(6, returntype=int)
            print(x)

            46

        Args:
            n (int): Number of bits requested back
            returntype (type): The requested data return type. 
                Currently supports str and intDefaults to str.
                


        Returns:
            str: bit data
            or 
            int: bit data
            (return type depends on input parameter)
        """        
        start = self.index
        self.index += n
        if self.index < len(self.bitstring):
            r = self.bitstring[start:self.index]

        else:
            r = self.bitstring[start:]
            self.finished=True

        if returntype == int:
            return int(r, 2)
        return r


class BitSaver:
    """Saves bits extracted from a file. Can check to see if length of data read is expected amount of data
    bitsaver = BitSaver(file_length=1024) # bits

    bitsaver.add('1010001')
    ...
    bitsaver.add('111')

    bitsaver.bits = '1010001............111'

    bitsaver.save_file(file_name) # save bits to file

    while not bitsaver.finished:
        new_bits = read_data()
        bitsaver.add(new_bits)
    """    
    def __init__(self, file_length=None):
        self.bits = []
        self.file_length = file_length
        self.read_length = 0
        self.finished = False

    def add_bits(self, bits, datatype=str):
        if datatype == int:
            bits = bin(bits)[2:]
        
        self.bits.append(bits)
        self.read_length += len(bits)

        if self.file_length is not None:
            if self.read_length >= self.file_length:
                self.bits = ''.join(self.bits)
                self.bits = self.bits[:self.file_length]
                self.finished = True

    def save_file(self, file_name):
        self.bytes = bytearray()
        index = 0
        bit_len = len(self.bits)
        while index <= bit_len-7:
            self.bytes.append(int(self.bits[index:index+8],2))
            index += 8
        with open(file_name, 'wb') as out_file:
            out_file.write(self.bytes)

def replace_lsb(bits, target_byte, n):
    """replaces the bits of the target byte with the bits argument
       example:
           new_byte = replace_lsb('101',34, 3)
           new_byte = replace_lsb(5,34, 3)

    Args:
        bits (str or int): bits that will replace the lsb of the target_byte
        target_byte (int): byte that will get the lsb replaced
        n (int): number of lsb bits to replace

    Returns:
        int: new byte with new lsb
    """    
    if type(bits) == str:
        bits = int(bits, 2) # assume format is '0101110'

    base = target_byte >> n << n
    output = base | bits
    return output

def get_lsb(byte, n):
    """gets the n lsb bits from a byte

    Args:
        byte (int): int that represents byte from which lsb bits will be extracted
        n (int): number of lsb bytes to extract

    Returns:
        int: lsb bits
    """    
    mask = int('0'*(8-n) + '1'*n,2)
    lsb = byte & mask
    return lsb


if __name__ == "__main__":
    test_input = 'sample.pptx'
    test_output = 'test.pptx'

    bf = BitFeederString(test_input)
    bs = BitSaver(file_length=len(bf.bytes)*8)

    while not bf.finished:
        bs.add_bits(bf.get_bits(30))

    bs.save_file(test_output)

# In [1]: %run -m cProfile bit_operators.py
#          3462197 function calls in 1.232 seconds

#    Ordered by: standard name

#    ncalls  tottime  percall  cumtime  percall filename:lineno(function)
#         1    0.297    0.297    0.335    0.335 bit_operators.py:107(save_file)
#         1    0.012    0.012    0.588    0.588 bit_operators.py:13(__init__)
#         1    0.072    0.072    1.232    1.232 bit_operators.py:2(<module>)
#         1    0.000    0.000    0.000    0.000 bit_operators.py:2(BitFeederString)
#         1    0.000    0.000    0.000    0.000 bit_operators.py:20(_load_bytes)
#         1    0.407    0.407    0.577    0.577 bit_operators.py:24(_make_bitstring)
#    173109    0.094    0.000    0.106    0.000 bit_operators.py:32(get_bits)
#         1    0.000    0.000    0.000    0.000 bit_operators.py:72(BitSaver)
#         1    0.000    0.000    0.000    0.000 bit_operators.py:88(__init__)
#    173109    0.100    0.000    0.131    0.000 bit_operators.py:94(add_bits)
#         2    0.000    0.000    0.000    0.000 {built-in method builtins.__build_class__}
#    649158    0.073    0.000    0.073    0.000 {built-in method builtins.bin}
#         1    0.000    0.000    1.232    1.232 {built-in method builtins.exec}
#    995378    0.064    0.000    0.064    0.000 {built-in method builtins.len}
#         2    0.000    0.000    0.000    0.000 {built-in method io.open}
#    649158    0.038    0.000    0.038    0.000 {method 'append' of 'bytearray' objects}
#    822267    0.061    0.000    0.061    0.000 {method 'append' of 'list' objects}
#         1    0.000    0.000    0.000    0.000 {method 'disable' of '_lsprof.Profiler' objects}
#         2    0.014    0.007    0.014    0.007 {method 'join' of 'str' objects}
#         1    0.000    0.000    0.000    0.000 {method 'read' of '_io.BufferedReader' objects}
#         1    0.000    0.000    0.000    0.000 {method 'write' of '_io.BufferedWriter' objects}
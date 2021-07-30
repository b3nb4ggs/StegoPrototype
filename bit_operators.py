import pdb

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

    def add_bits(self, bits, datatype=str, nlsb=None):
        if datatype == int:
            bits = '0'*7 + bin(bits)[2:] # add padding zero bits before
            bits = bits[-nlsb:]
        
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

def write_lsb_avg(byte_list, bits, n):
    """takes a list of bytes, a sequence of message bits and the number of bits
    and returns a list of modified bytes with the secret message encoded. 

    replaces the lsb bytes so that the average of the group equals the message 
    bits.

    syntax: 
    write_lsb_avg(byte_list, bits, n)

    Args:
        byte_list (List[int]): A list of hidden bytes
        bits (string): The hidden message bits
        n (int): The number of bytes (LSB) to be hidden

    Returns:
        List[int]: List of final byte values to be stored in the output cover
    """    
    # make sure bits are right size (add padding if needed)
    # for example lsb = 3 but bits are '01'
    # add dummy padding after so '010'
    if len(bits) < n:
        bits = bits + (n - len(bits))*'0'

    # sum byte
    m = len(byte_list)
    sum_byte = sum(byte_list) 
    target_average = int(sum_byte / m - (sum_byte / m) % (2**n) + int(bits,2))
    diff = target_average * m - sum_byte

    # diff = (int(bits, 2) * m) % (2**n) - sum_lsb
    # diff = (int(bits, 2) * m) - sum_lsb

    # target '100' / lsb 3
    # 388 / 3 = 129.33
    # what is the smallest number to add to x to make the average have the right lsb
    # (132) is the closest average
    # how to get 132?
    # target_average = (388 / 3) - (388 / 3) % 2**3 + '100'
    # target_average = sum_byte / m - (sum_byte /m ) % (2**lsb) + int(bits,2)
    # diff = target_average * m - sum_byte

    # average = avg = [a + b + c] / n
    # desired average = z = [a + b + c + x] / n
    # x?
    # x = z * n - [a + b + c]


    i = 0
    while diff != 0:
        if diff > 0:
            byte_list[i] = byte_list[i] + 1 
            diff -= 1
        else:
            byte_list[i] = byte_list[i] - 1 
            diff += 1
        i += 1
        i %= m # same as i = i % m (rotate through bytes e.g. 0, 1, 2, 0, 1, 2)
    
    if target_average != sum(byte_list)/m:
        print("bad target average")
        pdb.set_trace()

    if read_lsb_avg(byte_list, n) != int(bits,2):
        print("bad final bit")
        pdb.set_trace()

    return byte_list

def read_lsb_avg(byte_list, n_lsb):
    """Reads a list of bytes and extracts the message for n_lsb using the avg
    method. Takes the average of byte list and pulls n_lsb.

    string_bits = read_lsb_sum(byte_list, n_lsb)

    Args:
        byte_list (List[int]): list of bytes from the cover file w/ hidden message
        n_lsb (int): number of bits to extract from message

    Returns:
        str: bit string of hidden message (use with BitSaver class)
    """    
    avg_byte = sum(byte_list) // len(byte_list)
    return get_lsb(avg_byte, n_lsb)

def read_lsb_sum(byte_list, n_lsb):
    """Reads a list of bytes and extracts the message for n_lsb using the sum
    method.

    string_bits = read_lsb_sum(byte_list, n_lsb)

    Args:
        byte_list (List[int]): list of bytes from the cover file w/ hidden message
        n_lsb (int): number of bits to extract from message

    Returns:
        str: bit string of hidden message (use with BitSaver class)
    """    
    sum_byte = sum(byte_list)
    return get_lsb(sum_byte, n_lsb)


def write_lsb_sum(byte_list, bits, n):
    """takes a list of bytes, a sequence of message bits and the number of bits
    and returns a list of modified bytes with the secret message encoded. 

    replaces the lsb bytes so that the sum of the group equals the message 
    bits.

    syntax: 
    write_lsb_sum(byte_list, bits, n)

    Args:
        byte_list (List[int]): A list of hidden bytes
        bits (string): The hidden message bits
        n (int): The number of bytes (LSB) to be hidden

    Returns:
        List[int]: List of final byte values to be stored in the output cover
    """ 
    m = len(byte_list)
    sum_byte = sum(byte_list)
    sum_lsb = get_lsb(sum_byte, n)
    diff = int(bits, 2) - sum_lsb

    i = 0
    while diff != 0:
        if diff > 0:
            byte_list[i] = byte_list[i] + 1 
            diff -= 1
        else:
            byte_list[i] = byte_list[i] - 1 
            diff += 1
        i += 1
        i %= m # same as i = i % m 

    return byte_list


if __name__ == "__main__":
    test_input = 'sample.pptx'
    test_output = 'test.pptx'

    bf = BitFeederString(test_input)
    bs = BitSaver(file_length=len(bf.bytes)*8)

    while not bf.finished:
        bs.add_bits(bf.get_bits(30))

    bs.save_file(test_output)

# Performance Profile:
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
import subprocess

FILE_LENGTH = 50000

zero_data = bytes(FILE_LENGTH)
with open('zero_test.txt','wb') as f_zero:
    f_zero.write(zero_data)

lsb = 5
pixelno = 7
method = 'avg'

x = subprocess.run(
    [
        'python3.8',
        'average.py',
        'encode',
        'codepic.png',
        'zero_test.txt',
        '--lsb',
        str(lsb),
        '--pixelno',
        str(pixelno),
        '--method',
        method
    ], capture_output=True
)
print('finished encode')
print(x.stdout)

y = subprocess.run(
    [
        'python3.8',
        'average.py',
        'decode',
        'output.png',
        'zero_test.txt',
        '--lsb',
        str(lsb),
        '--pixelno',
        str(pixelno),
        '--method',
        method
    ], capture_output=True
)
print('finished decode')
print(y.stdout)

with open('test_output.txt', 'rb') as output_file:
    result_data = output_file.read()

print(sum(result_data))
bad_bytes = [i for i in range(len(result_data)) if result_data[i] != 0]
print(bad_bytes[:10])
print(len(bad_bytes))
from contextlib import redirect_stdout

with open('out.txt', 'w') as f:
    with redirect_stdout(f):
        print('data')
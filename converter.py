import os
from pathlib import Path
import time

def read_file(file_path):
    os.system(f"lowriter --headless --convert-to txt {file_path}")
    path = Path(f'{file_path}')
    path = (path.stem + '.txt')
    text = ''
    time.sleep(0.3)
    with open(path, mode='r') as f:
        text = f.read()
    print(text)

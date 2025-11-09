import argparse
import subprocess
import base64
import socketserver
import ssl
import pefile

from http.server import SimpleHTTPRequestHandler
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

class ArgumentFormatter(argparse.HelpFormatter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_help_position', 28) 
        super().__init__(*args, **kwargs)

    def _get_help_string(self, action):
        help_str = action.help
        if action.default is not None and action.default != argparse.SUPPRESS:
            help_str += f' (default: {action.default})'
        return help_str

class HTTPServer:
    def __init__(self, host='0.0.0.0', port=8000, directory=None, certfile=None, keyfile=None):
        self.host = host
        self.port = port
        self.certfile = certfile
        self.keyfile = keyfile
        self.directory = directory
        
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=directory, **kwargs)
        
        class TCPServer(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
        
        try:
            self.httpd = TCPServer((self.host, self.port), Handler)
        except OSError:
            self.host = '0.0.0.0'
            self.httpd = TCPServer((self.host, self.port), Handler)
        
        if self.certfile and self.keyfile:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile,)
            self.httpd.socket = ctx.wrap_socket(self.httpd.socket, server_side=True)

    def serve_forever(self):
        print_info(f'Staging payload on {self.host}:{self.port}')
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            print('\r', end='')
            print_info('Server stopping...')
            self.httpd.server_close()

    def shutdown(self):
        self.httpd.shutdown()
        self.httpd.server_close()

def render(template, **variables):
    result = template
    for key, value in variables.items():
        result = result.replace('{{'+key.upper()+'}}', str(value))
    return result

def aes_encrypt(data, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    return cipher.encrypt(pad(data, AES.block_size))

def rot_encrypt(data, key):
    return bytes(b+key & 0XFF for b in data)

def rot_decrypt(data, key):
    return bytes(b-key & 0XFF for b in data)

def xor_encrypt(data, key):
    return bytes(b^key for b in data)

def xor_decrypt(data, key):
    return bytes(b^key for b in data)

def ps_encode(command):
    return base64.b64encode(command.encode('utf-16le')).decode()

def get_arch(file):
    pe = pefile.PE(file)
    if pe.OPTIONAL_HEADER.Magic == 0x10b:
        return 'x32'
    elif pe.OPTIONAL_HEADER.Magic == 0x20b:
        return 'x64'
    else:
        return 'any'

def build(command, verbose):
    if verbose:
        print_debug(' '.join(command))
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if 'error' in result.stdout.lower() or 'error' in result.stderr.lower():
        print_warn('Build failed:')
        print_error(' '.join(command))
        if(result.stdout):
            print_error(result.stdout)
        if(result.stderr):
            print_error(result.stderr)
        input('press any button to continue ...')
        exit(-1)

def print_error(string):
    for line in  string.strip().split('\n'):
        print('\t\033[31m' + line + '\033[0m')

def print_warn(*args, sep=' ', end='\n'):
    print('\033[1;31m[!]\033[0m ', end='')
    print(*args, sep=sep, end=end)

def print_success(*args, sep=' ', end='\n'):
    print('\033[1;32m[*]\033[0m ', end='')
    print(*args, sep=sep, end=end)

def print_debug(*args, sep=' ', end='\n'):
    print('\033[1;35m[-]\033[0m DEBUG: ', end='')
    print(*args, sep=sep, end=end)

def print_info(*args, sep=' ', end='\n'):
    print('\033[1;36m[*]\033[0m ', end='')
    print(*args, sep=sep, end=end)

def print_banner():
    banner = '''\033[38;2;50;175;50m
     ▄████▄   ██▀███   ▄▄▄        █████▒▄▄▄█████▓
    ▒██▀ ▀█  ▓██ ▒ ██▒▒████▄    ▓██   ▒ ▓  ██▒ ▓▒
    ▒▓█    ▄ ▓██ ░▄█ ▒▒██  ▀█▄  ▒████ ░ ▒ ▓██░ ▒░
    ▒▓▓▄ ▄██▒▒██▀▀█▄  ░██▄▄▄▄██ ░▓█▒  ░ ░ ▓██▓ ░ 
    ▒ ▓███▀ ░░██▓ ▒██▒ ▓█   ▓██▒░▒█░      ▒██▒ ░ 
    ░ ░▒ ▒  ░░ ▒▓ ░▒▓░ ▒▒   ▓▒█░ ▒ ░      ▒ ░░   
    ░  ▒     ░▒ ░ ▒░  ▒   ▒▒ ░ ░          ░    
    ░          ░░   ░   ░   ▒    ░ ░      ░      
    ░ ░         ░           ░  ░     By Exil ⛤           
    ░\033[0m'''

    print(banner)
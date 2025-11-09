import pefile
import os

from .utils import *

path = os.path.dirname(__file__)

def dll_proxy(dll_name, dll_path, ps_command):
    with open(os.path.join(path,'templates/c/proxy.c'), 'r') as f:
        dll_code = f.read()
    dll_code = render(dll_code, cmdline=ps_command)
    
    pe = pefile.PE(dll_name)
    dll_name = os.path.basename(dll_name)
    dll_path = os.path.join(dll_path, os.path.splitext(dll_name)[0]).replace('/', '\\').replace('\\', '\\\\')
    
    def_code = f'LIBRARY "{dll_name}"\n'
    def_code += 'EXPORTS\n'
    for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
        ordinal = exp.ordinal
        if exp.name is None:
            def_code += f'  _proxy{ordinal}="{dll_path}".#{ordinal} @{ordinal} NONAME\n'
        else:
            name = exp.name.decode()
            def_code += f'  {name}="{dll_path}".{name} @{ordinal}\n'    
    return dll_code, def_code
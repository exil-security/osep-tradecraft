# OSEP Tradecraft

## Install

```bash
$ sudo apt install mingw-w64 mono-devel
$ pipx install git+https://github.com/exil-security/osep-tradecraft
```

## Usage

```
$ craft --help
usage: craft [-h] -i INPUT -o OUTPUT [-s SERVER] [-c _CLASS] [-m METHOD] [-a ARGS [ARGS ...]] [--process PROCESS] [--proxy] [--dll DLL] [--dll-path PATH] [--staged] [--reflection] [--bypass] [--sandbox] [--unhook] [--clm]
             [--applocker [{msbuild,workflow_compiler,installutil}]] [--applocker-path PATH] [--platform {windows,linux}] [--arch {x32,x64,any}] [-e {None,AES,XOR,ROT}] [--hide] [--doc {shell,wmi,wscript}] [-v] [-q]
             {run,inject,hollow}

Tradcrafts automation for Offensive Security PEN-300 (OSEP)

positional arguments:
  {run,inject,hollow}       shellcode execution method (default: run)

options:
  -h, --help                show this help message and exit
  -i, --input INPUT         input file format: (.raw, .bin, .txt, .exe, .dll)
  -o, --output OUTPUT       output file format: (.elf, .exe, .dll, .ps1, .ps, .doc, .docm, .hta, .js, .lnk, .msi)
  -s, --server SERVER       stage the payload
  -c, --class _CLASS        class name (required for .NET DLL)
  -m, --method METHOD       method for DLL. (required for .NET DLL)
  -a, --args ARGS [ARGS ...]
                            payload arguments
  --process PROCESS         target process (default: explorer.exe)
  --proxy                   dll proxying {c} (default: False)
  --dll DLL                 path to the DLL to generate a proxy for
  --dll-path PATH           path to original path (default: C:\Windows\System32)
  --staged                  staged shellcode payload (default: False)
  --reflection              assembly reflection {cs, ps1} (default: False)
  --bypass                  amsi and etw patch {cs, ps1} (default: False)
  --sandbox                 sandbox bypass {cs} (default: False)
  --unhook                  unhook ntdll {cs} (default: False)
  --clm                     clm bypass (default: False)
  --applocker [{msbuild,workflow_compiler,installutil}]
                            applocker bypass {cs}
  --applocker-path PATH     applocker bypass path (default: C:\Windows\Tasks)
  --platform {windows,linux}
                            payload platform (default: windows)
  --arch {x32,x64,any}      payload architecture (default: any)
  -e, --encrypt {None,AES,XOR,ROT}
                            encrypt the payload (default: AES)
  --hide                    hide windows console (default: False)
  --doc {shell,wmi,wscript}
                            doc execution method (default: shell)
  -v, --verbose             verbose output
  -q, --quiet               hide banner (default: False)

```

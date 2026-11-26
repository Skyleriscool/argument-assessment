param([ValidateSet('quality','prepare','assess','challenge','train','test','server','ui')][string]$Command='ui')
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
if ($Command -eq 'server') {
    & "$root\runtime\llama-server.exe" -m "$root\weights\Qwen3-1.7B-Q4_K_M.gguf" --host 127.0.0.1 --port 8766 -c 8192 -np 1 -t 4 --reasoning off --log-disable --no-cache-prompt --cache-ram 0 --offline
    exit $LASTEXITCODE
}
$pythonExe=if(Test-Path "$root\.venv\Scripts\python.exe"){"$root\.venv\Scripts\python.exe"}else{'python'}
$env:OPENBLAS_NUM_THREADS='2'
if($Command -eq 'ui'){ & $pythonExe "$root\web_app.py" }
elseif($Command -eq 'train'){ & $pythonExe "$root\train.py" }
elseif($Command -eq 'test'){ & $pythonExe -m unittest discover -s $root -p 'test_*.py' -v }
else { $input | & $pythonExe "$root\assess.py" $Command }
exit $LASTEXITCODE


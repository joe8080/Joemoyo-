<#
.SYNOPSIS
    Install the voice generator on Windows.

.DESCRIPTION
    Run from the repository root in PowerShell:

        powershell -ExecutionPolicy Bypass -File voice\setup.ps1

    Creates a virtual environment in .venv, installs PyTorch matching your
    CUDA driver, and installs VibeVoice. Safe to re-run.

.PARAMETER Cpu
    Force the CPU-only build even if an NVIDIA card is present.

.PARAMETER CudaVersion
    CUDA wheel tag to install, e.g. cu124 or cu121. Defaults to cu124.
#>
param(
    [switch]$Cpu,
    [string]$CudaVersion = "cu124"
)

$ErrorActionPreference = "Stop"

$VoiceDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = Split-Path -Parent $VoiceDir
$VendorDir = Join-Path $VoiceDir "vendor"
$RepoDir   = Join-Path $VendorDir "VibeVoice"
# Microsoft withdrew the original repo in Sept 2025; this is the MIT-licensed
# community preservation fork of the same code.
$RepoUrl   = "https://github.com/vibevoice-community/VibeVoice.git"

function Require-Command($name, $hint) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Error "$name not found on PATH. $hint"
    }
}

Write-Host "==> Checking prerequisites" -ForegroundColor Cyan
Require-Command "git" "Install from https://git-scm.com/download/win"
Require-Command "python" "Install Python 3.10 or 3.11 from https://python.org and tick 'Add to PATH'"

$pyVersion = (python -c "import sys; print('%d.%d' % sys.version_info[:2])").Trim()
Write-Host "Python $pyVersion"
if ($pyVersion -notin @("3.9", "3.10", "3.11", "3.12")) {
    Write-Warning "VibeVoice targets Python 3.9-3.12. $pyVersion may not resolve dependencies cleanly."
}

Write-Host ""
Write-Host "==> Checking for an NVIDIA GPU" -ForegroundColor Cyan
$useCuda = $false
if (-not $Cpu) {
    if (Get-Command "nvidia-smi" -ErrorAction SilentlyContinue) {
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
        $useCuda = $true

        $vramMb = (nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | Select-Object -First 1)
        if ([int]$vramMb -lt 8000) {
            Write-Warning "Under 8 GB VRAM. The 1.5B model normally wants ~7 GB, so add --low-vram and lower --chunk-chars if generation fails."
        }
    } else {
        Write-Warning "No NVIDIA driver detected. Installing the CPU build."
        Write-Warning "CPU generation is far slower than real time - use voice\notebooks\VibeVoice_Colab.ipynb instead."
    }
}

Write-Host ""
Write-Host "==> Creating virtual environment (.venv)" -ForegroundColor Cyan
# A venv avoids the system-package conflicts that break 'pip install -e' on
# machines with a managed Python.
$venvPath = Join-Path $RepoRoot ".venv"
if (-not (Test-Path $venvPath)) { python -m venv $venvPath }
$venvPy = Join-Path $venvPath "Scripts\python.exe"
& $venvPy -m pip install --quiet --upgrade pip setuptools wheel

Write-Host ""
Write-Host "==> Fetching VibeVoice source" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $VendorDir | Out-Null
if (Test-Path (Join-Path $RepoDir ".git")) {
    git -C $RepoDir pull --ff-only
} else {
    git clone --depth 1 $RepoUrl $RepoDir
}

Write-Host ""
Write-Host "==> Installing PyTorch" -ForegroundColor Cyan
if ($useCuda) {
    Write-Host "Using CUDA wheels ($CudaVersion). If this fails, re-run with -CudaVersion cu121."
    & $venvPy -m pip install --quiet torch torchaudio --index-url "https://download.pytorch.org/whl/$CudaVersion"
} else {
    & $venvPy -m pip install --quiet torch torchaudio --index-url "https://download.pytorch.org/whl/cpu"
}

Write-Host ""
Write-Host "==> Installing VibeVoice" -ForegroundColor Cyan
& $venvPy -m pip install --quiet -e $RepoDir

# flash-attn is deliberately skipped: it needs a full CUDA toolchain and MSVC to
# build on Windows and almost never succeeds. generate.py falls back to sdpa.

Write-Host ""
& $venvPy -c "import torch; print('torch', torch.__version__, '| CUDA available:', torch.cuda.is_available())"

if (-not (Get-Command "ffmpeg" -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Warning "ffmpeg is not on PATH - voice\prepare_voice.py needs it."
    Write-Host "         Install with:  winget install Gyan.FFmpeg"
    Write-Host "         Then open a NEW terminal so PATH refreshes."
}

Write-Host @"

==> Done.

Activate the environment in each new terminal:
    .venv\Scripts\Activate.ps1

Then:
  1. Make a voice sample per speaker (15-25s of clean speech):
       python voice\prepare_voice.py --input you.mp4  --name Joe  --gender man
       python voice\prepare_voice.py --input her.wav  --name Maya --gender woman

  2. Check a script parses correctly (no GPU needed):
       python voice\generate.py --script voice\scripts\example_2p.txt --voices Joe Maya --dry-run

  3. Generate:
       python voice\generate.py --script voice\scripts\example_2p.txt --voices Joe Maya

If you hit out-of-memory, add:  --low-vram --chunk-chars 2000
"@ -ForegroundColor Green

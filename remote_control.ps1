#!/usr/bin/env powershell
# Remote PowerShell script for phone access

# Enable PowerShell Remoting (run once as Administrator)
# Enable-PSRemoting -Force
# Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force

# Then from your phone (using apps like Termius), you can run:
# Enter-PSSession -ComputerName YOUR_PC_IP -Credential YOUR_USERNAME

# Commands to run DVR:
function Start-DVRWithProwlarr {
    Set-Location $PSScriptRoot
    
    # Set environment variables
    $env:PROWLARR_API_KEY = "your_prowlarr_api_key_here"
    $env:PROWLARR_API_URL = "http://127.0.0.1:9696"
    
    # Start the application
    Start-Process -FilePath ".\run_dvr_with_prowlarr.bat" -WorkingDirectory "."
    
    Write-Host "DVR started with Prowlarr integration!"
}

function Stop-DVR {
    Get-Process -Name "python" | Where-Object {$_.CommandLine -like "*dvr_web.py*"} | Stop-Process -Force
    Write-Host "DVR stopped!"
}

function Get-DVRStatus {
    $processes = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*dvr_web.py*"}
    if ($processes) {
        Write-Host "DVR is running (PID: $($processes.Id))"
    } else {
        Write-Host "DVR is not running"
    }
}

# Export functions
Export-ModuleMember -Function Start-DVRWithProwlarr, Stop-DVR, Get-DVRStatus
# Windows Debugging Helper Script for Dora-OpenAI-WebSocket
# This script helps diagnose and fix connection issues on Windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Dora WebSocket Windows Debugging Helper" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a command exists
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Step 1: Check Dora installation
Write-Host "Step 1: Checking Dora installation..." -ForegroundColor Yellow
if (Test-Command "dora") {
    $doraVersion = dora --version
    Write-Host "✓ Dora found: $doraVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Dora not found in PATH" -ForegroundColor Red
    Write-Host "  Please install Dora or add it to your PATH" -ForegroundColor Gray
    exit 1
}

# Step 2: Check daemon status
Write-Host ""
Write-Host "Step 2: Checking Dora daemon..." -ForegroundColor Yellow
$daemonStatus = dora daemon status 2>&1
if ($daemonStatus -match "running") {
    Write-Host "✓ Daemon is running" -ForegroundColor Green
} else {
    Write-Host "⚠ Daemon not running, starting it..." -ForegroundColor Yellow
    dora daemon start
    Start-Sleep -Seconds 2
    $daemonStatus = dora daemon status 2>&1
    if ($daemonStatus -match "running") {
        Write-Host "✓ Daemon started successfully" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to start daemon" -ForegroundColor Red
        Write-Host "  Error: $daemonStatus" -ForegroundColor Gray
    }
}

# Step 3: Check coordinator port
Write-Host ""
Write-Host "Step 3: Checking coordinator port (6832)..." -ForegroundColor Yellow
$tcpConnection = Test-NetConnection -ComputerName localhost -Port 6832 -InformationLevel Quiet
if ($tcpConnection) {
    Write-Host "✓ Port 6832 is accessible" -ForegroundColor Green
} else {
    Write-Host "✗ Port 6832 is not accessible" -ForegroundColor Red
    Write-Host "  This might be a firewall issue" -ForegroundColor Gray
    
    # Check Windows Firewall
    Write-Host ""
    Write-Host "  Checking Windows Firewall rules..." -ForegroundColor Yellow
    $firewallRule = Get-NetFirewallRule -DisplayName "*dora*" -ErrorAction SilentlyContinue
    if ($firewallRule) {
        Write-Host "  Found Dora firewall rule: $($firewallRule.DisplayName)" -ForegroundColor Gray
    } else {
        Write-Host "  No Dora firewall rules found" -ForegroundColor Gray
        Write-Host "  Creating firewall exception..." -ForegroundColor Yellow
        
        # Try to add firewall rule (requires admin)
        try {
            New-NetFirewallRule -DisplayName "Dora Coordinator" `
                -Direction Inbound -Protocol TCP -LocalPort 6832 `
                -Action Allow -ErrorAction Stop | Out-Null
            Write-Host "  ✓ Firewall rule created" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠ Could not create firewall rule (requires admin)" -ForegroundColor Yellow
            Write-Host "    Run this script as Administrator to auto-fix" -ForegroundColor Gray
        }
    }
}

# Step 4: Check template files
Write-Host ""
Write-Host "Step 4: Checking template files..." -ForegroundColor Yellow
$templates = @(
    "whisper-template.yml",
    "whisper-template-metal.yml"
)

$foundTemplate = $false
foreach ($template in $templates) {
    if (Test-Path $template) {
        Write-Host "✓ Found template: $template" -ForegroundColor Green
        $foundTemplate = $true
        
        # Check if it has the correct structure
        $content = Get-Content $template -Raw
        if ($content -match "path:\s*dynamic") {
            Write-Host "  ✓ Template has 'path: dynamic' (correct)" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Template missing 'path: dynamic'" -ForegroundColor Red
        }
        
        if ($content -match "NODE_ID") {
            Write-Host "  ✓ Template has NODE_ID placeholder" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Template missing NODE_ID placeholder" -ForegroundColor Red
        }
    }
}

if (-not $foundTemplate) {
    Write-Host "✗ No template files found in current directory" -ForegroundColor Red
    Write-Host "  Expected: whisper-template.yml or whisper-template-metal.yml" -ForegroundColor Gray
}

# Step 5: Test dataflow creation
Write-Host ""
Write-Host "Step 5: Testing dataflow creation..." -ForegroundColor Yellow

# Create test dataflow
$testId = Get-Random -Maximum 9999
$testNodeId = "test-$testId"
$testDataflow = "test-$testId.yml"

# Find a template to use
$templateToUse = $null
foreach ($template in $templates) {
    if (Test-Path $template) {
        $templateToUse = $template
        break
    }
}

if ($templateToUse) {
    Write-Host "  Using template: $templateToUse" -ForegroundColor Gray
    
    # Copy and modify template
    $content = Get-Content $templateToUse -Raw
    $content = $content -replace "NODE_ID", $testNodeId
    Set-Content -Path $testDataflow -Value $content
    
    Write-Host "  Created test dataflow: $testDataflow" -ForegroundColor Gray
    
    # Try to start it
    Write-Host "  Starting dataflow..." -ForegroundColor Gray
    $startOutput = dora start $testDataflow --name $testNodeId --detach 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Dataflow started successfully" -ForegroundColor Green
        
        # Check if it's running
        Start-Sleep -Seconds 2
        $listOutput = dora list 2>&1
        if ($listOutput -match $testNodeId) {
            Write-Host "✓ Dataflow appears in 'dora list'" -ForegroundColor Green
        } else {
            Write-Host "✗ Dataflow not found in 'dora list'" -ForegroundColor Red
            Write-Host "  Output: $listOutput" -ForegroundColor Gray
        }
        
        # Clean up
        Write-Host "  Cleaning up test dataflow..." -ForegroundColor Gray
        dora destroy $testNodeId 2>&1 | Out-Null
    } else {
        Write-Host "✗ Failed to start dataflow" -ForegroundColor Red
        Write-Host "  Error: $startOutput" -ForegroundColor Gray
    }
    
    # Remove test file
    Remove-Item $testDataflow -ErrorAction SilentlyContinue
} else {
    Write-Host "⚠ Cannot test dataflow creation (no template found)" -ForegroundColor Yellow
}

# Step 6: Environment variables
Write-Host ""
Write-Host "Step 6: Checking environment variables..." -ForegroundColor Yellow

$envVars = @{
    "DORA_COORDINATOR_ADDR" = $env:DORA_COORDINATOR_ADDR
    "RUST_LOG" = $env:RUST_LOG
    "RUST_BACKTRACE" = $env:RUST_BACKTRACE
}

foreach ($var in $envVars.GetEnumerator()) {
    if ($var.Value) {
        Write-Host "  $($var.Key) = $($var.Value)" -ForegroundColor Gray
    } else {
        Write-Host "  $($var.Key) = (not set)" -ForegroundColor DarkGray
    }
}

# Step 7: Recommendations
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Recommendations:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "1. Set debug environment variables:" -ForegroundColor Yellow
Write-Host '   $env:RUST_LOG = "debug"' -ForegroundColor Gray
Write-Host '   $env:RUST_BACKTRACE = "full"' -ForegroundColor Gray
Write-Host '   $env:DORA_COORDINATOR_ADDR = "127.0.0.1:6832"' -ForegroundColor Gray

Write-Host ""
Write-Host "2. Run WebSocket server with logging:" -ForegroundColor Yellow
Write-Host '   cargo run --release -p dora-openai-websocket 2>&1 | Tee-Object -FilePath debug.log' -ForegroundColor Gray

Write-Host ""
Write-Host "3. Monitor in another terminal:" -ForegroundColor Yellow
Write-Host '   dora daemon status' -ForegroundColor Gray
Write-Host '   dora list --watch' -ForegroundColor Gray

Write-Host ""
Write-Host "4. If still failing, try:" -ForegroundColor Yellow
Write-Host '   - Run as Administrator' -ForegroundColor Gray
Write-Host '   - Disable Windows Defender temporarily' -ForegroundColor Gray
Write-Host '   - Check Event Viewer for system errors' -ForegroundColor Gray
Write-Host '   - Increase timeout in main.rs (line 466)' -ForegroundColor Gray

Write-Host ""
Write-Host "Debug script completed!" -ForegroundColor Green
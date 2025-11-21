#Requires -RunAsAdministrator

# --- OS Detection ---
$IsWindows = $env:OS -match "Windows_NT"
$IsMacOS = $false # PowerShell Core on Mac usually doesn't set this automatically, check uname if needed, but simple check:
if (!$IsWindows -and (uname) -eq "Darwin") { $IsMacOS = $true }
$IsLinux = (!$IsWindows -and !$IsMacOS)

Write-Host "Detected OS: $(if ($IsWindows) {'Windows'} elseif ($IsMacOS) {'macOS'} else {'Linux'})" -ForegroundColor Cyan

# --- Windows Setup ---
if ($IsWindows) {
    try {
        Write-Host "Starting Windows Setup..."
        
        # Python
        Write-Host "Downloading Python 3.12.2..."
        $pythonUrl = "https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe"
        $pythonInstaller = "$env:TEMP\python.exe"
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller -ErrorAction Stop
        Write-Host "Installing Python..."
        Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait -ErrorAction Stop
        Remove-Item $pythonInstaller -ErrorAction SilentlyContinue

        # Sejda
        Write-Host "Downloading Sejda PDF Desktop..."
        $sejdaUrl = "https://downloads.sejda.com/sejda-desktop_7.7.0_windows.exe"
        $sejdaInstaller = "$env:TEMP\sejda.exe"
        Invoke-WebRequest -Uri $sejdaUrl -OutFile $sejdaInstaller -ErrorAction Stop
        Write-Host "Installing Sejda..."
        Start-Process -FilePath $sejdaInstaller -ArgumentList "/S" -Wait -ErrorAction Stop
        Remove-Item $sejdaInstaller -ErrorAction SilentlyContinue
    }
    catch {
        Write-Error "Windows installation failed: $_"
        exit 1
    }
}

# --- macOS Setup (via Homebrew) ---
elseif ($IsMacOS) {
    try {
        Write-Host "Starting macOS Setup..."
        
        if (!(Get-Command brew -ErrorAction SilentlyContinue)) {
            Write-Error "Homebrew is not installed. Please install Homebrew first."
            exit 1
        }

        Write-Host "Installing Python 3..."
        Start-Process brew -ArgumentList "install python@3.12" -Wait -NoNewWindow

        Write-Host "Installing Sejda PDF..."
        Start-Process brew -ArgumentList "install --cask sejda-pdf" -Wait -NoNewWindow
    }
    catch {
        Write-Error "macOS installation failed: $_"
        exit 1
    }
}

# --- Linux Setup (Debian/Ubuntu based) ---
elseif ($IsLinux) {
    try {
        Write-Host "Starting Linux Setup..."
        
        # Check for sudo
        if ((Measure-Command { sudo -n true } 2>&1).ToString() -ne "") {
            Write-Warning "Sudo password may be required."
        }

        # Python (Repo usually has recent versions, or use deadsnakes PPA if needed for specific 3.12)
        Write-Host "Installing Python 3..."
        Start-Process sudo -ArgumentList "apt-get update" -Wait -NoNewWindow
        Start-Process sudo -ArgumentList "apt-get install -y python3 python3-pip" -Wait -NoNewWindow

        # Sejda
        Write-Host "Downloading Sejda PDF Desktop..."
        $sejdaUrl = "https://downloads.sejda.com/sejda-desktop_7.7.0_linux_amd64.deb"
        $sejdaInstaller = "/tmp/sejda.deb"
        Invoke-WebRequest -Uri $sejdaUrl -OutFile $sejdaInstaller -ErrorAction Stop
        
        Write-Host "Installing Sejda..."
        Start-Process sudo -ArgumentList "dpkg -i $sejdaInstaller" -Wait -NoNewWindow
        Start-Process sudo -ArgumentList "apt-get install -f -y" -Wait -NoNewWindow # Fix dependencies
        Remove-Item $sejdaInstaller -ErrorAction SilentlyContinue
    }
    catch {
        Write-Error "Linux installation failed: $_"
        exit 1
    }
}

Write-Host "Setup completed successfully." -ForegroundColor Green

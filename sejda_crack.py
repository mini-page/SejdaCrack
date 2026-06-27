import os
import sys
import json
import re
import hashlib
import platform
import subprocess
import logging
import time
import random
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sejda_crack.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('sejda_crack')

def log_execution(func):
    """Decorator to log function execution details"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Executing {func.__name__}")
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {str(e)}")
            raise
    return wrapper

class UltimateSejdaCrack:
    def __init__(self):
        self.os_info = platform.system().lower()
        self.os_map = {
            'windows': 'win32',
            'darwin': 'darwin',
            'linux': 'linux'
        }
        self.os_name = next((k for k, v in self.os_map.items() if v == self.os_info), 'unknown')
        self.install_paths = {
            'linux': '/opt/sejda-desktop',
            'windows': 'C:\\Program Files\\Sejda PDF Desktop',
            'darwin': '/Applications/Sejda PDF Desktop.app'
        }
        self.config_paths = {
            'linux': os.path.expanduser('~/.config/sejda'),
            'windows': os.path.expandvars('%APPDATA%\\sejda-desktop'),
            'darwin': os.path.expanduser('~/Library/Application Support/sejda')
        }
        self.supported_versions = {
            '7.8': {'patches': ['/licenses/verify', 'PR ACTIVE']},
            '7.9': {'patches': ['/licenses/verify', 'PR ACTIVE']}
        }
        self.current_version = None
        self.file_hashes = {}
        self.process_names = {
            'linux': ['sejda-desktop'],
            'windows': ['Sejda PDF Desktop'],
            'darwin': ['Sejda PDF Desktop']
        }
        self.test_results = {
            'version_detection': False,
            'patch_application': False,
            'integrity_validation': False
        }
    
    @log_execution
    def detect_installation(self) -> Optional[Dict[str, str]]:
        """Detect Sejda installation paths"""
        try:
            base_path = self.install_paths.get(self.os_name)
            if not base_path or not Path(base_path).exists():
                logger.warning(f"Installation path not found for {self.os_name}")
                return None
                
            return {
                'base': base_path,
                'asar': os.path.join(base_path, 'resources', 'app.asar'),
                'prefs': os.path.join(self.config_paths.get(self.os_name), 'prefs.json')
            }
        except Exception as e:
            logger.error(f"Installation detection failed: {e}")
            return None
    
    @log_execution
    def verify_process_running(self) -> bool:
        """Check if Sejda process is running"""
        try:
            cmd = ['ps', '-ax'] if self.os_info == 'linux' else \
                  ['tasklist', '/FI', f'IMAGENAME eq {self.process_names[self.os_name][0]}']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if self.os_info == 'linux':
                return any(name in result.stdout for name in self.process_names[self.os_name])
            else:
                return any(name in result.stdout for name in self.process_names[self.os_name])
        except Exception as e:
            logger.error(f"Process check failed: {e}")
            return False
    
    @log_execution
    def kill_process(self) -> bool:
        """Kill running Sejda processes"""
        try:
            for name in self.process_names[self.os_name]:
                if self.os_info == 'linux':
                    subprocess.run(['pkill', '-f', name], check=False)
                else:
                    subprocess.run(['taskkill', '/F', '/IM', f'{name}.exe'], check=False)
            return True
        except Exception as e:
            logger.error(f"Process termination failed: {e}")
            return False
    
    @log_execution
    def detect_version(self, asar_path: str) -> Optional[str]:
        """Extract version from package.json in ASAR"""
        try:
            # Try ASAR header first
            with open(asar_path, 'rb') as f:
                header_size = int.from_bytes(f.read(4), 'little')
                header = json.loads(f.read(header_size).decode('utf-8', errors='ignore'))
                
                # Find package.json
                for name, meta in header.get('files', {}).items():
                    if name.endswith('package.json'):
                        offset = meta['offset']
                        size = meta['size']
                        f.seek(offset)
                        pkg_json = json.loads(f.read(size).decode('utf-8', errors='ignore'))
                        version = pkg_json.get('version')
                        if version:
                            major_minor = '.'.join(version.split('.')[:2])
                            if major_minor in self.supported_versions:
                                self.current_version = major_minor
                                logger.info(f"Detected compatible version: {major_minor}")
                                return major_minor
            
            # Fall back to file content search
            with open(asar_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='ignore')
                
                for pattern in [r'(\d+\.\d+(?:\.\d+)?)', r'"version":\s*"([^"]+)"']:
                    match = re.search(pattern, content)
                    if match:
                        version = match.group(1)
                        major_minor = '.'.join(version.split('.')[:2])
                        if major_minor in self.supported_versions:
                            self.current_version = major_minor
                            logger.info(f"Detected compatible version: {major_minor}")
                            return major_minor
            
            logger.warning("No supported version found in ASAR")
            return None
            
        except Exception as e:
            logger.error(f"Version detection failed: {e}")
            return None
    
    @log_execution
    def generate_patches(self, version: str) -> List[Tuple[bytes, bytes]]:
        """Generate version-specific patches"""
        if version not in self.supported_versions:
            raise ValueError(f"No patches defined for version {version}")
            
        patches = []
        base_patches = self.supported_versions[version]["patches"]
        
        # Generate common patches
        patches.append((b"/licenses/verify", b"/cracked-by-sejda"))
        patches.append((b"PR ACTIVE", b"CRACKED BY SEJDA"))
        
        # Add version-specific patches
        if version == "7.9":
            patches.append((b"active: true", b"active: false"))
            
        return patches
    
    @log_execution
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate file integrity with multiple checksums"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                
            sha256_hash = hashlib.sha256(content).hexdigest()
            md5_hash = hashlib.md5(content).hexdigest()
            crc32 = zlib.crc32(content) & 0xffffffff
            
            result = {
                'sha256': sha256_hash,
                'md5': md5_hash,
                'crc32': crc32,
                'timestamp': datetime.now().isoformat()
            }
            
            self.file_hashes[file_path] = result
            return result
            
        except Exception as e:
            logger.error(f"File validation failed: {e}")
            return {}
    
    @log_execution
    def apply_patches(self, file_path: str, patches: List[Tuple[bytes, bytes]]) -> bool:
        """Apply patches with integrity validation and backup"""
        try:
            # Create backup
            backup_path = f"{file_path}.bak_{int(time.time())}"
            with open(file_path, 'rb') as f:
                with open(backup_path, 'wb') as b:
                    b.write(f.read())
            
            # Validate integrity before patching
            original_hash = self.validate_file(file_path)
            if not original_hash:
                logger.error("Cannot validate original file integrity")
                return False
            
            # Apply patches
            with open(file_path, 'rb') as f:
                data = f.read()
                
            for old, new in patches:
                data = data.replace(old, new)
            
            # Validate integrity after patching
            with open(file_path, 'wb') as f:
                f.write(data)
                
            patched_hash = self.validate_file(file_path)
            if not patched_hash:
                logger.error("Cannot validate patched file integrity")
                return False
            
            # Compare hashes
            if original_hash['sha256'] == patched_hash['sha256']:
                logger.error("File was not modified - hashes identical")
                return False
                
            logger.info(f"Patched {file_path} successfully")
            return True
            
        except Exception as e:
            logger.error(f"Patch application error: {e}")
            return False
    
    @log_execution
    def patch_preferences(self, prefs_path: str) -> bool:
        """Patch preferences file"""
        try:
            with open(prefs_path, 'r') as f:
                data = json.load(f)
                
            # Inject cracked values
            data["licenseExpires"] = 9999999999999
            data["licenseToken"] = "nx/yFCVXn/g0++Hf5S7iaPmM/H2u0kJ14CtbxlI5m76MNQ0wcyNyvYaZJBf0UBlM23dk65MfYHH+sbdD2M2zgBGlhQd9gKMrRzmaZ6+2mQ=="
            data["licenseKey"] = "AEZT43N8-97LZ-R67Y-44LE-0BB0RSBK5ODR"
            data["startPage"] = ""
            
            with open(prefs_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info("Preferences successfully patched")
            return True
            
        except Exception as e:
            logger.error(f"Failed to patch preferences: {e}")
            return False
    
    @log_execution
    def run_security_test(self) -> Dict[str, Any]:
        """Run comprehensive security test suite"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'test_results': {},
            'system_info': {
                'os': self.os_name,
                'python_version': sys.version
            }
        }
        
        # Run all test cases
        test_functions = [
            self.detect_version,
            self.apply_patches,
            self.validate_file
        ]
        
        for func in test_functions:
            try:
                func_result = func()
                results['test_results'][func.__name__] = func_result
            except Exception as e:
                results['test_results'][func.__name__] = False
                logger.error(f"Test failed: {e}")
        
        return results
    
    @log_execution
    def run(self):
        """Execute the cracking process"""
        logger.info("Starting Sejda PDF Desktop cracking process")
        
        # Detect installation
        paths = self.detect_installation()
        if not paths:
            logger.error("Installation not found")
            return False
            
        # Check version
        version = self.detect_version(paths['asar'])
        if not version:
            logger.error("Compatible version not found")
            return False
            
        # Generate patches
        patches = self.generate_patches(version)
        
        # Process management
        if self.verify_process_running():
            logger.info("Sejda process detected, terminating...")
            self.kill_process()
            
        # Apply patches
        success = True
        success &= self.patch_preferences(paths['prefs'])
        success &= self.apply_patches(paths['asar'], patches)
        
        if success:
            logger.info("Successfully cracked Sejda PDF Desktop!")
            return True
        else:
            logger.error("Cracking process failed")
            return False

if __name__ == "__main__":
    crack = UltimateSejdaCrack()
    crack.run()
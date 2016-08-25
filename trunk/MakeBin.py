from cx_Freeze import setup, Executable
import subprocess
import re

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = [], 
                    excludes = [], 
                    include_files = [   #'ffmpeg.exe', 
                                        'Trimmer.ini', 
                                        'LICENSES_FFMPEG.zip',
                                        'lgpl-2.1.txt',
                                        'ReadMe.txt',
                                        'Format for EW.cmd']
                    )

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('Trimmer.py', base=base)
]

# Build version string
version = '1.0'

if sys.platform=='win32':
    svn_info = subprocess.check_output('svn info | find "Last Changed Rev:"', shell=True).decode('utf-8')
    svn_match = re.match("Last Changed Rev: *([0-9]+)", svn_info)
    if svn_match:
        version += '.'+svn_match.group(1)
    
    with open ("version.iss", "wt") as f:
        f.write('#define MyAppVersion "%s"\n' % version)

setup(name='trimmer',
      version = version,
      description = 'Video File Trimmer',
      options = dict(build_exe = buildOptions),
      executables = executables)

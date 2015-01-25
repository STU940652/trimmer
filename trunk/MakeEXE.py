from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = [], 
                    excludes = [], 
                    include_files = ['ffmpeg.exe', 'Trimmer.ini', 'Format for EW.cmd'],
                    build_exe = "dist/Trimmer"
                    )

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('Trimmer.py', base=base)
]

setup(name='trimmer',
      version = '1.0',
      description = 'Video File Trimmer',
      options = dict(build_exe = buildOptions),
      executables = executables)

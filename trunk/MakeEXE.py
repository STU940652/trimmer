from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = [], 
                    excludes = [], 
                    include_files = [   'ffmpeg.exe', 
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

setup(name='trimmer',
      version = '1.0',
      description = 'Video File Trimmer',
      options = dict(build_exe = buildOptions),
      executables = executables)

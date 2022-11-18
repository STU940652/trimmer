# -*- mode: python -*-
import sys
import subprocess
import re
import os

from PyInstaller.utils.hooks import copy_metadata

block_cipher = None

# Build version string
version = os.environ["version_number"]
print ("Version number:", version)

# TODO
# svn_info = subprocess.check_output('svn info', shell=True).decode('utf-8')
# svn_match = re.search("Last Changed Rev: *([0-9]+)", svn_info)
# if svn_match:
#     version += '.'+svn_match.group(1)
# 
# with open ("version.iss", "wt") as f:
#     f.write('#define MyAppVersion "%s"\n' % version)
# with open ("version", "wt") as f:
#     f.write(version)
# with open ("version.py", "wt") as f:
#     f.write("VERSION=' %s'" % version)


datas = [('Trimmer.ini','.'),
         ('lgpl-2.1.txt','.'),
         ('LICENSES_FFMPEG.zip','.')]
datas += copy_metadata('google-api-python-client')

icon = None

if sys.platform.startswith('win'):
    datas.append( ('ext/Win64/ffmpeg.exe','.') )
    datas.append( ('ext/Win64/chromedriver.exe','.') )
    icon='ext/Win64/icon.ico'
    
if sys.platform.startswith('darwin'):
    datas.append( ('ext/OSX/ffmpeg','.') )
    datas.append( ('ext/OSX/chromedriver','.') )
    icon='ext/OSX/icon.icns'


a = Analysis(['Trimmer.py'],
             pathex=[os.getcwd()],
             binaries=None,
             datas=datas,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Trimmer',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon=icon)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Trimmer')
if sys.platform.startswith('darwin'):
    app = BUNDLE(coll,
                 name='Trimmer.app',
                 icon=icon,
                 bundle_identifier=None)

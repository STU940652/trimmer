# -*- mode: python -*-
import sys
import subprocess
import re

block_cipher = None

# Build version string
version = '1.9'

svn_info = subprocess.check_output('svn info', shell=True).decode('utf-8')
svn_match = re.search("Last Changed Rev: *([0-9]+)", svn_info)
if svn_match:
    version += '.'+svn_match.group(1)

with open ("version.iss", "wt") as f:
    f.write('#define MyAppVersion "%s"\n' % version)
with open ("version", "wt") as f:
    f.write(version)
with open ("version.py", "wt") as f:
    f.write("VERSION=' %s'" % version)


datas = [('Trimmer.ini','.'),
         ('lgpl-2.1.txt','.'),
         ('LICENSES_FFMPEG.zip','.')]
icon = None

if sys.platform.startswith('win'):
    datas.append( ('../Win64/ext/ffmpeg.exe','.') )
    datas.append( ('../Win64/ext/chromedriver.exe','.') )
    # datas.append( ('../Win64/ext/phantomjs.exe','.') )
    icon='../Win64/ext/icon.ico'
    
if sys.platform.startswith('darwin'):
    datas.append( ('../OSX/ext/ffmpeg','.') )
    datas.append( ('../OSX/ext/chromedriver','.') )
    # datas.append( ('../OSX/ext/phantomjs','.') )
    icon='../OSX/ext/icon.icns'


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

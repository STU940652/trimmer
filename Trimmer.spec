# -*- mode: python -*-

block_cipher = None


a = Analysis(['Trimmer.py'],
             pathex=['/Users/projection/Andy_Projects/trimmer-code/src'],
             binaries=None,
             datas=None,
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
          console=False , icon='icon.icns')
coll = COLLECT(exe,
               a.binaries + 
                  [('ffmpeg','ffmpeg','DATA'),
                   # ('ffmpeg.exe','ffmpeg.exe','DATA'), 
                   # ('Format for EW.cmd','Format for EW.cmd','DATA'),  
                   ('Trimmer.ini','Trimmer.ini','DATA')],
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Trimmer')
app = BUNDLE(coll,
             name='Trimmer.app',
             icon='icon.icns',
             bundle_identifier=None)

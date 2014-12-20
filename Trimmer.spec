# -*- mode: python -*-
a = Analysis(['Trimmer.py'],
             pathex=[r'C:\Users\AndynDeanna\Documents\Projects\Trimmer\trunk'],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\Trimmer', 'Trimmer.exe'),
          debug=False,
          strip=None,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries + [('ffmpeg.exe','ffmpeg.exe','DATA'), ('Trimmer.ini','Trimmer.ini','DATA'), ('Format for EW.cmd','Format for EW.cmd','DATA')],
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name=os.path.join('dist', 'Trimmer'))
app = BUNDLE(coll,
             name=os.path.join('dist', 'Trimmer.app'))

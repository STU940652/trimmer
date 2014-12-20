@echo off
set UNSQUISH=False
set FFPATH=C:\Users\AndynDeanna\Documents\Projects\PyVLC
if "%UNSQUISH%" equ "True" (
    set FFOPTS=-vf "scale=1024:576,setdar=dar=4:3"
    set FILE_SUFFIX=_1250
) else (
    set FFOPTS=-vf "scale=w=1024:h=1024/a"
    set FILE_SUFFIX= 
)    
set FFOPTS=%FFOPTS% -vcodec libx264 -profile:v baseline -x264opts keyint=123:min-keyint=25:crf=19 -vsync cfr
set FFOPTS=%FFOPTS% -acodec libvo_aacenc -ac 2 -ar 44100 -ab 128k -profile:a aac_low

for %%i in (%*) do (
	echo "%FFPATH%\ffmpeg" -i %%i %FFOPTS% "%%~dpiEW_%%~ni%FILE_SUFFIX%.mp4"
	"%FFPATH%\ffmpeg" -i %%i %FFOPTS% "%%~dpiEW_%%~ni%FILE_SUFFIX%.mp4"
)
	
pause
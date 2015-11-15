import configparser
import os
import datetime

# #Sample ini file
# [FilePaths]
# SourcePath = r"D:\PRIVATE\AVCHD\BDMV\STREAM"
# DestPath = r"C:\Documents and Settings\AndynDeanna\My Documents\Sandbox"
# AutoStart = True
#
# [GlobalSettings]
# FileCopy = True
# NameTemplate = %m_%d_%Y
#
# [Segment1]
# Seg1_Name = "Before Prayer"
# Seg1_EncodeString = 'ffmpeg ....'
# Seg1_Completion = "None"
#
# [Segment2]
# Seg2_Name = "(Vimeo) After Prayer"
# Seg2_EncodeString = 'ffmpeg ....'
# Seg2_Completion = "VimeoUpload();AudioFTP()"

TrimmerConfig=configparser.SafeConfigParser()

# Put in some default values
TrimmerConfig.add_section('FilePaths')
TrimmerConfig.set('FilePaths', 'SourcePath', '.')
TrimmerConfig.set('FilePaths', 'DestPath', '.')
TrimmerConfig.set('FilePaths', 'AutoStart', 'false')

TrimmerConfig.add_section('GlobalSettings')
TrimmerConfig.set('GlobalSettings', 'FileCopy', 'true')
TrimmerConfig.set('GlobalSettings', 'CropControls', 'false')
TrimmerConfig.set('GlobalSettings', 'NameTemplate', '%%Y%%m%%d')

if "APPDATA" in os.environ:
    # For Windows
    TrimmerConfig.set('FilePaths', 'LogPath', os.path.realpath(os.path.join(os.environ["APPDATA"], "TrimmerData")))
elif "HOME" in os.environ:
    # For *nix (untested)
    TrimmerConfig.set('FilePaths', 'LogPath', os.path.realpath(os.path.join(os.environ["HOME"], "TrimmerData")))
else:
    TrimmerConfig.set('FilePaths', 'LogPath', os.path.realpath(os.path.join('.', "TrimmerData")))


TrimmerConfig.add_section('Segment1')
TrimmerConfig.set('Segment1', 'Name', '')
TrimmerConfig.set('Segment1', 'EncodeString', 'ffmpeg -report -nostdin -i "$InFile$" '+\
                    '-vf "crop=(in_h*4/3),fade=in:st=$FadeInStart$:d=$FadeLength$,fade=out:st=$FadeOutStart$:d=$FadeLength$" '+\
                    '-vcodec libx264 -profile:v baseline -x264opts keyint=123:min-keyint=25:crf=19 -vsync cfr '+\
                    '-af "afade=in:st=$FadeInStart$:d=$FadeLength$,afade=out:st=$FadeOutStart$:d=$FadeLength$" '+\
                    '-acodec libvo_aacenc -ac 2 -ar 44100 -ab 128k -profile:a aac_low '+\
                    '-ss $OutputStart$ -t $OutputLength$ "$OutFile$.mp4"')


# And read from the ini file
try:
    TrimmerConfig.read(['Trimmer.ini', os.path.join(TrimmerConfig.get('FilePaths', 'LogPath'),'Trimmer.ini')])
except:
    pass
    
# Figure out the "Date of Record"
time_of_record = datetime.datetime.now()
while time_of_record.weekday() != 6:
    time_of_record += datetime.timedelta(days=1)

    
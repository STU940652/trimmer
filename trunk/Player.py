import wx
import os
import os.path
import platform
import datetime
from Settings import *
from CmsManager import *
try:
    import vlc
    HAVE_VLC = True
except:
    HAVE_VLC = False


def ms_to_hms (ms):
    try:
        h = int(ms/(60*60*1000))
        msl = ms - h*60*60*1000
        m = int(msl/(60*1000))
        msl = msl - m*60*1000
        s = msl/1000.0
        return "%02i:%02i:%06.3f" % (h,m,s)
    except:
        return ""
    
def hms_to_ms (s):
    d = s.split(':')
    mult = 1000.0
    ms = 0
    try:
        while len (d):
            ms = ms + float(d.pop(-1))*mult
            mult = mult * 60.0
        return int(ms)
    except:
        return 0
        
Tags = {}

class AdditionalInputPanel (wx.Panel):
    def __init__(self, parent, name):
        wx.Panel.__init__(self, parent)

        box = wx.BoxSizer(wx.HORIZONTAL)
        self.Name = name
        if (name[0] == "&"):
            # Boolean Checkbox
            self.Input = wx.CheckBox(self, label=name[1:].replace("_"," "))
            box.AddSpacer(120)
            box.Add(self.Input, 1)
        else:
            # Text Box
            FilenameLabel=wx.StaticText(self, label=name.replace("_"," ").replace("@"," "), size=(120, -1), style = wx.TE_RIGHT)
            box.Add(FilenameLabel)
            self.Input = wx.TextCtrl(self, size=(120, -1))
            box.Add(self.Input, 1)
            if (name[0] == "@"):
                FileButton = wx.Button(self, label='...', size=(20,-1))
                self.Bind(wx.EVT_BUTTON, self._SelectFile, FileButton)
                box.Add(FileButton, 0)
        self.SetSizer(box)
        self.Layout()

    def _SelectFile (self, evt):
        openFileDialog = wx.FileDialog(self, "Select File", "", "",
                                       "All Files (*.*)|*.*|MP4 (*.mp4)|*.mp4|JPEG (*.jpg)|*.jpg", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if (openFileDialog.ShowModal() == wx.ID_OK):
            self.Input.SetValue(openFileDialog.GetPath())
            
    def GetStringValue (self):
        if (self.Name[0] == "&"):
            # Boolean Checkbox
            if self.Input.IsChecked():
                return "True"
            else:
                return ""
        return self.Input.GetValue()
        
    def GetName (self):
        return self.Name
        
        
    
class Player(wx.Panel):
    """The main window has to deal with events.
    """
    TagNames = ["Title", "Series", "Speaker", "Date", "Comment", "Summary", "Keywords"]
    MultiLineTags = ["Summary", "Keywords"]
    UploadPanel = None
    
    def __init__(self, parent, SubmitJobCallback, StatusBar):
        wx.Panel.__init__(self, parent)

        # See if VLC loaded
        if not HAVE_VLC:
            m = wx.MessageDialog(self, message = "Please download and install %s VLC Media Player\nfrom www.VideoLAN.org." % platform.architecture()[0],
                                caption = "Could not find VLC Media Player.",
                                style = wx.ICON_ERROR|wx.OK)
            m.ShowModal()

        self.MediaFileName = ''
        self.StatusBar = StatusBar
        self.VideoSize = (0, 0)

        # Panels
        # The first panel holds the video and it's all black
        self.videopanel = wx.Panel(self, -1)
        self.videopanel.SetBackgroundColour(wx.BLACK)

        # The second panel holds controls
        ctrlpanel = wx.Panel(self, -1 )
        self.ctrlpanel = ctrlpanel
        
        # Crop Slider
        self.cropslider = wx.ScrollBar(ctrlpanel, -1, style = wx.SB_HORIZONTAL )
        self.cropslider.Disable()
        self.cropCheckbox = wx.CheckBox(ctrlpanel, -1, "Adjust Crop Position")
        if TrimmerConfig.get('GlobalSettings', 'CropControls').lower() == "false":
            self.cropCheckbox.Disable()
            self.cropCheckbox.Hide()
            self.cropslider.Hide()
        
        # Time Slider
        self.timeslider = wx.Slider(ctrlpanel, -1, 0, 0, 1000)
        self.timeslider.SetRange(0, 1000)
        self.timeText = wx.TextCtrl(ctrlpanel, size=(100, -1))
        next   = wx.Button(ctrlpanel, label="Next")
        pause  = wx.Button(ctrlpanel, label="Pause")
        play   = wx.Button(ctrlpanel, label="Play")
        stop   = wx.Button(ctrlpanel, label="Stop")
        volume = wx.Button(ctrlpanel, label="Volume")
        self.volslider = wx.Slider(ctrlpanel, -1, 0, 0, 100, size=(100, -1))
        
        #My Stuff
        StartLabel = wx.StaticText(ctrlpanel, label="Start Time ", size=(100, -1), style = wx.TE_RIGHT)
        StartFill = wx.Button(ctrlpanel, label="Fill", size=(50, -1))
        self.StartTime = wx.TextCtrl(ctrlpanel, size=(100, -1))
        self.StartTime.SetValue("00:00:00.000")
        self.StartPlayFrom = wx.Button(ctrlpanel, label="Play From")
        self.StartPlayTo = wx.Button(ctrlpanel, label="Play To")

        # Give a pretty layout to the controls
        ctrlbox = wx.BoxSizer(wx.VERTICAL)
        
        # Reset Video size
        (self.width, self.height) = (0,0)
        ctrlbox.Add(self.cropslider, flag=wx.EXPAND | wx.BOTTOM | wx.TOP, border=5)
        ctrlbox.Add(self.cropCheckbox, flag=wx.EXPAND | wx.BOTTOM | wx.TOP, border=5)

        # box1 contains the timeslider
        box1 = wx.BoxSizer(wx.HORIZONTAL)
        box1.Add(self.timeslider, 2)
        box1.Add(self.timeText)
        # box2 contains some buttons and the volume controls
        box2 = wx.BoxSizer(wx.HORIZONTAL)
        box2.Add(play, flag=wx.RIGHT, border=5)
        box2.Add(pause)
        box2.Add(next)
        box2.Add(stop)
        box2.Add((-1, -1), 1)
        box2.Add(volume)
        box2.Add(self.volslider, flag=wx.TOP | wx.LEFT, border=5)
        # box3 contains Start stuff
        box4 = wx.FlexGridSizer(cols = 7)
        box4.AddGrowableCol(0,1)
        box4.Add((-1, -1), 1)
        box4.Add(StartLabel)
        box4.Add(StartFill)
        box4.Add(self.StartTime)
        box4.Add(self.StartPlayFrom)
        box4.Add(self.StartPlayTo)
        box4.Add((-1, -1), 1)
        # Merge box1 and box2 to the ctrlsizer
        ctrlbox.Add(box1, flag=wx.EXPAND | wx.BOTTOM | wx.TOP, border=5)
        ctrlbox.Add(box2, 1, wx.EXPAND)
        
        StopLabel = wx.StaticText(ctrlpanel, label="Stop Time", size=(100, -1), style = wx.TE_RIGHT)
        self.StopFill = wx.Button(ctrlpanel, label="Fill", size=(50, -1))
        self.Bind(wx.EVT_BUTTON, self.OnStopFill, self.StopFill)
        self.StopTime = wx.TextCtrl(ctrlpanel, size=(100, -1))
        self.StopTime.SetValue("00:00:00.000")
        self.StopPlayTo = wx.Button(ctrlpanel, label="Play To")
        self.Bind(wx.EVT_BUTTON, self.OnStopPlayTo, self.StopPlayTo)

        self.TimeToStop = None
        self.EncodeButton = wx.Button(ctrlpanel, label="Encode")
        self.Bind(wx.EVT_BUTTON, self.OnEncode, self.EncodeButton)
        # box4 contains Stop stuff
        box4.Add((-1, -1), 1)
        box4.Add(StopLabel)
        box4.Add(self.StopFill)
        box4.Add(self.StopTime)
        box4.Add(self.StopPlayTo)
        box4.Add((-1, -1), 1)
        box4.Add(self.EncodeButton)
                
        ctrlbox.Add(box4, 0, wx.EXPAND)
        
        self.SectionSelect = wx.ComboBox(ctrlpanel, style=wx.CB_READONLY)
        for section in TrimmerConfig.sections():
            if section[:7]=="Segment":
            	try:
                	self.SectionSelect.Append(TrimmerConfig.get(section,'Name'), section)
            	except:
            		continue
        self.SectionSelect.SetSelection(0)
        ctrlbox.Add(self.SectionSelect, flag=wx.EXPAND)        
        
        # box 5 for filename
        box5 = wx.BoxSizer(wx.HORIZONTAL)
        FilenameLabel=wx.StaticText(ctrlpanel, label="Output Filename", size=(120, -1), style = wx.TE_RIGHT)
        box5.Add(FilenameLabel)
        self.OutputFileName = wx.TextCtrl(ctrlpanel, size=(120, -1))
        box5.Add(self.OutputFileName, 1)
        ctrlbox.Add(box5, 0, flag=wx.EXPAND | wx.BOTTOM | wx.TOP, border=5)
        
        # Sizer for additional inputs
        self.AdditionalInputsSizer = wx.BoxSizer(wx.VERTICAL)
        ctrlbox.Add(self.AdditionalInputsSizer, 0, flag=wx.EXPAND)
        
        ctrlpanel.SetSizer(ctrlbox)
        
        # Info for MP3 tags
        tagpanel = wx.Panel(self, -1 )
        temp_box = wx.BoxSizer(wx.VERTICAL)
        self.Tags = {}
        for label in self.TagNames:
            temp_label = wx.StaticText(tagpanel, label=label, size=(60, -1), style = wx.TE_LEFT)
            temp_box.Add(temp_label, 0, flag=wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, border=5)
            if label in self.MultiLineTags:
                self.Tags[label] = wx.TextCtrl(tagpanel, size=(120, -1), style = wx.TE_MULTILINE)
                temp_box.Add(self.Tags[label], 1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border = 5)
            else:
                self.Tags[label] = wx.TextCtrl(tagpanel, size=(120, -1))
                temp_box.Add(self.Tags[label], 0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border = 5)

        # Combobox to select the sermon
        self.select_event = wx.Choice (tagpanel)
        temp_box.Add(self.select_event, 0,  flag=wx.EXPAND | wx.BOTTOM | wx.TOP)
        
        # Include non-Draft
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.include_published = wx.CheckBox(tagpanel, -1, "Include Published")
        sizer.Add(self.include_published, 1, flag=wx.EXPAND)
        
        # Import Tags button
        self.import_tag = wx.Button(tagpanel, label="Import from CMS")
        sizer.Add(self.import_tag, 0, flag=wx.EXPAND | wx.ALIGN_RIGHT)
        temp_box.Add(sizer, 0,  flag=wx.EXPAND | wx.BOTTOM | wx.TOP)
        tagpanel.SetSizer(temp_box)

        # Put everything together
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        sizer2.Add(self.videopanel, 1, flag=wx.EXPAND)
        sizer2.Add(ctrlpanel, flag=wx.EXPAND | wx.BOTTOM | wx.TOP)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(sizer2, 2, flag=wx.EXPAND)
        sizer.Add(wx.StaticLine(self, style=wx.LI_VERTICAL), 0, flag=wx.EXPAND)
        sizer.Add(tagpanel, 1, flag=wx.EXPAND)
        sizer.Layout()
        self.SetSizer(sizer)
        self.SetMinSize((500, 300))

        # Bind controls to events
        self.Bind(wx.EVT_BUTTON, self.OnPlay, play)
        self.Bind(wx.EVT_BUTTON, self.OnPause, pause)
        self.Bind(wx.EVT_BUTTON, self.OnNext, next)
        self.Bind(wx.EVT_BUTTON, self.OnStop, stop)
        self.Bind(wx.EVT_BUTTON, self.OnToggleVolume, volume)
        self.Bind(wx.EVT_SLIDER, self.OnSetVolume, self.volslider)
        self.Bind(wx.EVT_SLIDER, self.OnSetTime, self.timeslider)
        self.Bind(wx.EVT_BUTTON, self.OnImportFromCMS, self.import_tag)
        
        # Bind stuff
        self.Bind(wx.EVT_BUTTON, self.OnStartPlayFrom, self.StartPlayFrom)
        self.Bind(wx.EVT_BUTTON, self.OnStartPlayTo, self.StartPlayTo)
        self.Bind(wx.EVT_BUTTON, self.OnStartFill, StartFill)
        self.Bind(wx.EVT_COMBOBOX, self.OnChangeSelection, self.SectionSelect)
        self.Bind(wx.EVT_CHECKBOX, self.OnCropCheckbox, self.cropCheckbox)

        # finally create the timer, which updates the timeslider
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

        # VLC player controls
        if HAVE_VLC:
            self.Instance = vlc.Instance()
            self.player = self.Instance.media_player_new()
        
        # Command queue to the Encode thread
        self.SubmitJobCallback = SubmitJobCallback
        
        self.OnChangeSelection()

        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
        
    def OnDestroy (self, evt):
        # Cleanup Timer
        self.timer.Stop()
        
        # Let the event pass
        evt.Skip()
        
    def OnImportFromCMS(self, evt=None):
        global Tags
        self.import_tag.Enable(False)
        event = None
        if (self.select_event.GetCount() > 0) and ('event_list' in Tags) and (self.select_event.GetSelection() != wx.NOT_FOUND):
            event = Tags['event_list'][self.select_event.GetSelection()][1]
        
        self.CMSThread = ImportFromCMSThread(self, self.ImportFromCMSCallback, event, self.include_published.GetValue())
        self.CMSThread.start()
    
    def ImportFromCMSCallback(thread, self, info):
        global Tags
        if info:
            Tags.update(info)
            for key in info:
                if key == 'event_list':
                    l = []
                    for e in info[key]:
                        l.append(e[0])
                    self.select_event.SetItems(l)
                    self.select_event.SetSelection(0)
                for textBox in self.Tags:                
                    if key.lower() == textBox.lower():
                        self.Tags[textBox].SetValue(info[key])
                        
            if self.UploadPanel:
                self.UploadPanel.UploadCMSCallback(info)
                
        self.import_tag.Enable(True)
        
    def OnCropCheckbox(self, evt=None):
        self.cropslider.Show(self.cropCheckbox.IsChecked())
        self.cropslider.Enable(self.cropCheckbox.IsChecked())
        
    def OnChangeSelection(self, evt=None):
        section = self.SectionSelect.GetClientData(self.SectionSelect.GetSelection())
        self.OutputFileName.SetValue(os.path.join(\
            TrimmerConfig.get('FilePaths','DestPath'),\
            self.Substitute(TrimmerConfig.get(section,'DefaultOutFileName', fallback=''))))
            
        # Set up inputs for additional Inputs

        # First store the existing values
        t = {}
        for i in self.AdditionalInputsSizer.GetChildren():
            t[i.GetWindow().GetName()]=i.GetWindow().GetStringValue()
        
        # Remove existing Addition Inputs
        self.AdditionalInputsSizer.Clear(delete_windows=True)
        
        # Add new Additional Inputs
        for input_name in TrimmerConfig.get(section,'AdditionalInputs', fallback = '').split(','):
            if input_name:
                a = AdditionalInputPanel(self.ctrlpanel, input_name.strip())
                self.AdditionalInputsSizer.Add(a, 0, flag=wx.EXPAND | wx.BOTTOM | wx.TOP, border=5)
                try:
                    a.Input.SetValue(t[input_name.strip()])
                except:
                    pass
        self.ctrlpanel.Layout()
        self.Layout()

            
        
    def Substitute (self, s):
        ClipOfInterestStart = hms_to_ms(self.StartTime.GetValue())/1000.0
        ClipOfInterestStop  = hms_to_ms(self.StopTime.GetValue() )/1000.0
        
        FadeLength = 0.5 # 0.5 second of fade.  Fixed for now
        OutputStart  = ClipOfInterestStart - (5.0) # 5 seconds of black
        if (OutputStart < 0):
            OutputStart = 0
        FadeInStart  = ClipOfInterestStart
        if (FadeInStart < 0):
            FadeInStart = 0
        FadeOutStart = ClipOfInterestStop - FadeLength
        OutputLength = ClipOfInterestStop - ClipOfInterestStart + 5.0 + FadeLength + 10.0
        OutputLengthNoHT = FadeOutStart + 0.5 - FadeInStart
        
        CropXString = ''
        if (self.cropCheckbox.IsChecked()):
            CropXString = ":x=%i" % self.cropslider.GetThumbPosition()
        
        # Substitute Tags
        tags = self.GetTags()
        tags['SpeakerLast'] = tags['Speaker'].split(' ')[-1] # Speaker Last Name tag
        for tag in tags:
            s = s.replace("$%s$" % (tag), str(tags[tag]))
        
        # Substitute other variables
        s = s\
                    .replace("$ClipStart$",  str(FadeInStart))\
                    .replace("$ClipLength$",  str(ClipOfInterestStop - ClipOfInterestStart))\
                    .replace("$ClipFade$",  str(ClipOfInterestStop - ClipOfInterestStart - 0.5))\
                    .replace("$CropX$",  CropXString)\
                    .replace("$OutputStart$",  str(OutputStart))\
                    .replace("$OutputLength$", str(OutputLength))\
                    .replace("$OutputLengthNoHT$", str(OutputLengthNoHT))\
                    .replace("$FadeInStart$",  str(FadeInStart))\
                    .replace("$FadeOutStart$", str(FadeOutStart))\
                    .replace("$FadeLength$", str(FadeLength))\
                    .replace("$InFile$", self.MediaFileName)\
                    .replace("$InFileName$", os.path.basename(self.MediaFileName).rsplit('.',1)[0])\
                    .replace("$OutFileName$", self.OutputFileName.GetValue())\
                    .replace("$CurrentDate$", datetime.datetime.now().strftime("%s" % (TrimmerConfig.get('GlobalSettings', 'DateTemplate'))))\
                    .replace("$DateSunday$", time_of_record.strftime("%s" % (TrimmerConfig.get('GlobalSettings', 'DateTemplate'))))
        return s
    
    def OnEncode(self, evt):
        section = self.SectionSelect.GetClientData(self.SectionSelect.GetSelection())
             
        EncodeString = TrimmerConfig.get(section,'EncodeString').replace('\n',' ').replace('\r',' ')
            
        # Substitute other variables
        cmd = self.Substitute(EncodeString)   
        
        completion = self.Substitute(TrimmerConfig.get(section,'Completion', fallback='{}')).replace('\\', "\\\\")
        self.SubmitJobCallback("Encode %s" % TrimmerConfig.get(section,'Name') , cmd, completion)
        print(cmd)
        
    def OpenFile (self, MediaFileName, Play = True):
        # if a file is already running, then stop it.
        self.OnStop(None)

        self.MediaFileName=MediaFileName
        self.Media = self.Instance.media_new(str(self.MediaFileName))
        self.player.set_media(self.Media)
        # Report the title of the file chosen
        title = self.player.get_title()
        #  if an error was encountred while retriving the title, then use
        #  filename
        if title == -1:
            title = os.path.basename(MediaFileName)
        self.StatusBar.SetStatusText("%s - wxVLCplayer" % title)

        # set the window id where to render VLC's video output
        if platform.system() == 'Windows':
            self.player.set_hwnd(self.videopanel.GetHandle())
        elif platform.system() == 'Darwin':
            self.player.set_nsobject(self.videopanel.GetHandle())
        else:
            self.player.set_xwindow(self.videopanel.GetHandle())

        if Play:
            self.OnPlay(None)

        # set the volume slider to the current volume
        #self.player.audio_set_volume(0)
        self.volslider.SetValue(self.player.audio_get_volume() / 2)
        

        # Reset Video size
        (self.width, self.height) = (0,0)
    
    def OnOpen(self, evt):
        """Pop up a new dialow window to choose a file, then play the selected file.
        """
        # if a file is already running, then stop it.
        self.OnStop(None)

        # Create a file dialog opened in the current home directory, where
        # you can display all kind of files, having as title "Choose a file".
        dlg = wx.FileDialog(self, "Choose a file", os.path.expanduser('~'), "",
                            "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            dirname = dlg.GetDirectory()
            filename = dlg.GetFilename()
            # Creation
            self.OpenFile(os.path.join(dirname, filename))

        # finally destroy the dialog
        dlg.Destroy()
        
    def OnStartPlayFrom(self, evt):
        """
        """
        StartFrame = hms_to_ms (self.StartTime.GetValue())
        self.player.stop()
        if self.player.play() == -1:
            self.errorDialog("Unable to play.")
        else:
            self.timer.Start(milliseconds=100)
        if self.player.set_time(StartFrame) == -1:
            self.errorDialog("Failed to set time")

    def OnStartPlayTo(self, evt):
        """
        """
        StopFrame = hms_to_ms (self.StartTime.GetValue())
        StartFrame = StopFrame - 5000
        self.TimeToStop = StopFrame

        self.player.stop()
        if StartFrame < 0:
            StartFram = 0
        if self.player.play() == -1:
            self.errorDialog("Unable to play.")
        else:
            self.timer.Start(milliseconds=16)  
            
        if self.player.set_time(StartFrame) == -1:
            self.errorDialog("Failed to set time")
            
    def OnStartFill(self, evt):
        """
        """

        self.StartTime.SetValue(self.timeText.GetValue())
                
    def OnStopFill(self, evt):
        """
        """
        self.StopTime.SetValue(self.timeText.GetValue())

    def OnStopPlayTo(self, evt):
        """
        """
        StopFrame = hms_to_ms (self.StopTime.GetValue())
        StartFrame = StopFrame - 5000
        self.TimeToStop = StopFrame

        self.player.stop()
        if StartFrame < 0:
            StartFram = 0
        if self.player.play() == -1:
            self.errorDialog("Unable to play.")
        else:
            self.timer.Start(milliseconds=16)  
            
        if self.player.set_time(StartFrame) == -1:
            self.errorDialog("Failed to set time")
                
    def OnPlay(self, evt):
        """Toggle the status to Play/Pause.

        If no file is loaded, open the dialog window.
        """
        self.TimeToStop = None
        # check if there is a file to play, otherwise open a
        # wx.FileDialog to select a file
        if not self.player.get_media():
            self.OnOpen(None)
        else:
            # Try to launch the media, if this fails display an error message
            if self.player.play() == -1:
                self.errorDialog("Unable to play.")
            else:
                self.timer.Start(milliseconds=100)

    def OnPause(self, evt):
        """Pause the player.
        """
        self.player.pause()

    def OnStop(self, evt):
        """Stop the player.
        """
        self.player.stop()
        # reset the time slider
        self.timeslider.SetValue(0)
        self.timer.Stop()
        self.TimeToStop = None

    def OnNext(self, evt):
        """Next Fame.
        """
        self.player.next_frame()

    def OnTimer(self, evt):
        """Update the time slider according to the current movie time.
        """
        # since the self.player.get_length can change while playing,
        # re-set the timeslider to the correct range.
        length = self.player.get_length()
        self.timeslider.SetRange(-1, length)
        
        # Set Crop bar
        (width, height) = self.player.video_get_size()
        if (width, height) != (self.width, self.height):
            (self.width, self.height) = (width, height)
            print (width, height)
            self.cropslider.SetScrollbar((width-height*4/3)/2, height*4/3, width, 20)
            print (width/2, height*4/3, width, 20)
            
        self.VideoSize = (width, height)

        # update the time on the slider
        CurrentTime = self.player.get_time()
        self.timeslider.SetValue(CurrentTime)
        self.timeText.SetValue(ms_to_hms(CurrentTime))
        
        # See if we should stop
        if self.TimeToStop:
            if (CurrentTime >= self.TimeToStop):
                self.player.set_pause(True)
                self.TimeToStop = None

    def OnSetTime(self, evt):
        """Set the volume according to the volume sider.
        """
        slideTime = self.timeslider.GetValue()
        # vlc.MediaPlayer.audio_set_volume returns 0 if success, -1 otherwise
        if self.player.set_time(slideTime) == -1:
            self.errorDialog("Failed to set time")


    def OnToggleVolume(self, evt):
        """Mute/Unmute according to the audio button.
        """
        is_mute = self.player.audio_get_mute()

        self.player.audio_set_mute(not is_mute)
        # update the volume slider;
        # since vlc volume range is in [0, 200],
        # and our volume slider has range [0, 100], just divide by 2.
        self.volslider.SetValue(self.player.audio_get_volume() / 2)

    def OnSetVolume(self, evt):
        """Set the volume according to the volume sider.
        """
        volume = self.volslider.GetValue() * 2
        # vlc.MediaPlayer.audio_set_volume returns 0 if success, -1 otherwise
        if self.player.audio_set_volume(volume) == -1:
            self.errorDialog("Failed to set volume")

    def errorDialog(self, errormessage):
        """Display a simple error dialog.
        """
        edialog = wx.MessageDialog(self, errormessage, 'Error', wx.OK|
                                                                wx.ICON_ERROR)
        edialog.ShowModal()

    def GetTags(self):
        global Tags
        t = Tags
        t['video_width'] = str(self.VideoSize[0])
        t['video_height'] = str(self.VideoSize[1])
        # Get the additional inputs
        for i in self.AdditionalInputsSizer.GetChildren():
            t[i.GetWindow().GetName()]=i.GetWindow().GetStringValue()
        
        if "Vimeo_Title" in t:
            t["Vimeo_Title_For_Filename"] = t["Vimeo_Title"].replace("/","_").replace("\\","_").replace(":","_").replace(".","_")
        
        for l in self.Tags:
            t[l] = self.Tags[l].GetValue()
        return t

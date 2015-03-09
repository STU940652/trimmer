import wx
import os
import datetime
import time
import subprocess
import platform

from CheckListCtrl import CheckListCtrl
from Settings import *

def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB']:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0
    return "%3.1f %s" % (num, 'TB')

class FileCopy(wx.Panel):
    """The main window has to deal with events.
    """
    def __init__(self, parent, StatusBar, CopyDoneCallback):
        wx.Panel.__init__(self, parent)

        self.MediaFileName = ''
        self.FoundDir = False
        self.StartTime = None
        self.StatusBar = StatusBar
        self.CopyDoneCallback = CopyDoneCallback
        self.CopySubProcess = None
        self.DestFilename = ''
        self.DestSize = 0
        
        #Main Sizer
        Sizer=wx.BoxSizer(wx.VERTICAL)

        # Path to find files
        PathLabel = wx.StaticText(self, -1, "Source Directory")
        Sizer.Add(PathLabel)
        self.SourcePath=TrimmerConfig.get('FilePaths','SourcePath')
        self.PathName = wx.TextCtrl(self, value=self.SourcePath)
        self.PathButton = wx.Button(self, label='...', size=(20,-1))
        self.Bind(wx.EVT_TEXT, self.ChangeDirectoryText, self.PathName)
        self.Bind(wx.EVT_BUTTON, self.ChangeDirectory, self.PathButton)
        pathSizer = wx.BoxSizer(wx.HORIZONTAL)
        pathSizer.Add(self.PathName, 1, flag=wx.EXPAND)
        pathSizer.Add(self.PathButton)
        Sizer.Add(pathSizer, flag=wx.EXPAND|wx.ALL, border = 5)
        
        # File List
        self.FileList = CheckListCtrl(self)
        self.FileList.InsertColumn(0,'File Name')
        self.FileList.InsertColumn(1,'Size', format = wx.LIST_FORMAT_RIGHT)
        self.FileList.InsertColumn(2,'Date', width = 125)
        Sizer.Add(self.FileList, 1, flag=wx.EXPAND|wx.ALL, border = 5)
                
        # Filename
        PathLabel = wx.StaticText(self, -1, "Destination Filename")
        Sizer.Add(PathLabel)
        self.DestName = wx.TextCtrl(self, value=os.path.join(TrimmerConfig.get('FilePaths','DestPath'), 
                                    datetime.datetime.now().strftime("%s.mts" % (TrimmerConfig.get('GlobalSettings', 'NameTemplate')))))
        self.DestButton = wx.Button(self, label='...', size=(20,-1))
        self.Bind(wx.EVT_BUTTON, self.ChangeDestFile, self.DestButton)
        destSizer = wx.BoxSizer(wx.HORIZONTAL)
        destSizer.Add(self.DestName, 1, flag=wx.EXPAND)
        destSizer.Add(self.DestButton)
        Sizer.Add(destSizer, flag=wx.EXPAND|wx.ALL, border = 5)

        # Notification Text
        contrlSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.NotificationCheck = wx.CheckBox (self, label="Automatically start copying.")
        if TrimmerConfig.get('FilePaths','AutoStart').lower() == 'true':
            self.NotificationCheck.SetValue(True)
        contrlSizer.Add(self.NotificationCheck, 1, flag=wx.ALL, border = 5)

        # Cancel Button
        self.CancelButton = wx.Button (self, label='Cancel')      
        self.Bind(wx.EVT_BUTTON, self.CancelCopy, self.CancelButton)
        contrlSizer.Add(self.CancelButton, flag=wx.ALL|wx.ALIGN_RIGHT, border=5)
        self.CancelButton.Hide()
        
        # Start Button
        self.StartButton = wx.Button (self, label='Start')      
        self.Bind(wx.EVT_BUTTON, self.DoCopy, self.StartButton)
        contrlSizer.Add(self.StartButton, flag=wx.ALL|wx.ALIGN_RIGHT, border=5)
        Sizer.Add(contrlSizer, flag=wx.EXPAND|wx.ALL, border = 5)
        
        self.SetSizer(Sizer)
        
        # finally create the timer, which checks for the source files
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(1000)
        
    def CancelCopy (self, evt):
        if self.CopySubProcess:
            self.CopySubProcess.terminate()
            
    def DoCopy (self, evt=None):
        self.NotificationCheck.Disable()
        self.StartButton.Disable()
        self.DestName.Disable()
        self.DestFilename=self.DestName.GetValue()
        self.DestSize = 0
        self.StartTime = None
        if (os.path.exists(self.DestFilename)):
            d = wx.MessageDialog(self, "File %s exists.\nDo you want to overwrite?" % self.DestFilename, \
                caption = "Destination File Exists", style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
            if (d.ShowModal() != wx.ID_YES):
                # Bail out
                self.StatusBar.SetStatusText("")
                self.NotificationCheck.Enable()
                self.StartButton.Enable()
                self.DestName.Enable()
                return

        sources=list()
        for row in range(self.FileList.GetItemCount()):
            if self.FileList.IsChecked(row):
                sources.append('"'+os.path.join(self.PathName.GetValue(),self.FileList.GetItemText(row))+'"')
                si = os.stat(os.path.join(self.PathName.GetValue(),self.FileList.GetItemText(row)))
                self.DestSize += si.st_size
        if len(sources) > 0:
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW # Tell subprocess not to open terminal window
                c = 'cmd /c copy /b /y %s "%s"' % ('+'.join(sources), self.DestFilename)
                self.CopySubProcess = subprocess.Popen(c, startupinfo=startupinfo,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            else:
                #Mac, Linux
                c = "cat %s > '%s'" % (' '.join(sources), self.DestFilename)
                self.CopySubProcess = subprocess.Popen(c, shell = True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.CancelButton.Show(True)
            self.Layout()
            self.StatusBar.SetStatusText("Copying...")

    def OnTimer (self, evt):
        if self.CopySubProcess:
            # Copy is in progress.  Let's check the status
            if (self.CopySubProcess.poll() != None):
                # Copy is done.  Cleanup
                self.NotificationCheck.Enable()
                self.StartButton.Enable()        
                self.DestName.Enable()
                self.CancelButton.Hide()
                if (self.CopySubProcess.returncode != 0):
                    # Finished with errors
                    print(self.CopySubProcess.communicate())
                    self.StatusBar.SetStatusText("Error while copying.")
                    self.CopySubProcess = None
                else:
                    self.StatusBar.SetStatusText("Copying done.")
                    self.CopyDoneCallback(self.DestFilename)
                    self.CopySubProcess = None
            else:
                # Check to see how far we are
                if os.path.exists(self.DestFilename):
                    si = os.stat(self.DestFilename)
                    self.StatusBar.SetStatusText("Copying... %5.1f %%" % (100.0*si.st_size/self.DestSize))
        else:
            # No copy in progress.  Check for directory changes
            self.UpdateDirectory()
            
            if self.StartTime and (time.time() >= self.StartTime):
                self.StartTime = None
                if self.NotificationCheck.IsChecked() and self.NotificationCheck.IsEnabled():
                    self.DoCopy()
            
            if self.StartTime and self.NotificationCheck.IsChecked() and self.NotificationCheck.IsEnabled():
                self.NotificationCheck.SetLabel("Automatically copying in %i seconds" % (self.StartTime - time.time()))
                
            else:
                self.NotificationCheck.SetLabel("Automatically start copying.")
                self.StartTime = None

    def ChangeDirectory (self, evt):
        dd = wx.DirDialog(self, defaultPath = self.PathName.GetValue())
        if (dd.ShowModal() == wx.ID_OK):
            self.PathName.SetValue(dd.GetPath())
            
    def ChangeDestFile (self, evt):
        dd = wx.FileDialog(self, defaultFile = self.DestName.GetValue(), style=wx.FD_SAVE)
        if (dd.ShowModal() == wx.ID_OK):
            self.DestName.SetValue(dd.GetPath())
            
    def ChangeDirectoryText (self, evt=None):
        self.FoundDir = False
        self.SourcePath = self.PathName.GetValue()
        self.UpdateDirectory()
    
    def UpdateDirectory (self, evt=None):
        if os.path.isdir(self.SourcePath):
            if not self.FoundDir:
                file_000ok = False
                file_001ok = False
                #Fill in the directory stuff
                self.FileList.DeleteAllItems()
                self.FoundDir = True
                for filename in os.listdir(self.SourcePath):
                    si = os.stat(os.path.join(self.SourcePath,filename))
                    if si.st_size:
                        row=self.FileList.GetItemCount()
                        self.FileList.InsertStringItem(row, filename) 
                        self.FileList.SetItem(row, 1, sizeof_fmt(si.st_size)) #si.st_ctime
                        self.FileList.SetItem(row, 2, datetime.datetime.fromtimestamp(si.st_mtime).strftime('%m/%d/%Y %I:%M %p')) #si.st_ctime
                        if (filename == "00000.MTS") and (si.st_size > 4e+9):
                            file_000ok = True
                            self.FileList.CheckItem(row, True)
                        elif (filename == "00001.MTS") and (si.st_size < 4e+9):
                            file_001ok = True
                            self.FileList.CheckItem(row, True)
                        else:
                            #  Some other file exists in the directory.  No auto-copy
                            file_000ok = False
                            file_001ok = False
                if (file_000ok and file_001ok):
                    self.StartTime = time.time() + 5
                else:
                    self.StartTime = None
        else:
            self.FileList.DeleteAllItems()
            self.FoundDir = False
            self.StartTime = None


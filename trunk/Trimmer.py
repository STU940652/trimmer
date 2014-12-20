#! /usr/bin/python
# -*- coding: utf-8 -*-

#
# WX example for VLC Python bindings
# Copyright (C) 2009-2010 the VideoLAN team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
#
"""
A simple example for VLC python bindings using wxPython.

Author: Michele Orrù
Date: 23-11-2010
"""

# import standard libraries
import wx 
import sys
import os
import Queue
import subprocess

# import external libraries
from FileCopy import FileCopy
from CheckListCtrl import CheckListCtrl
from EncodeThread import EncodeThread
from Player import Player
from JobList import JobList
from Settings import *


class TrimmerMain (wx.Frame):
    def __init__ (self, title):
        minsize = (600,500)
        wx.Frame.__init__(self, None, -1, title,
                          pos=wx.DefaultPosition, size=minsize)
        # Menu Bar
        #   File Menu
        self.frame_menubar = wx.MenuBar()
        self.file_menu = wx.Menu()
        self.file_menu.Append(1, "&Open", "Open from file..")
        self.file_menu.AppendSeparator()
        self.file_menu.Append(2, "&View Logs", "View Log File Directory")
        self.file_menu.AppendSeparator()
        self.file_menu.Append(3, "&Close", "Quit")
        self.Bind(wx.EVT_MENU, self.OnOpen, id=1)
        self.Bind(wx.EVT_MENU, self.OnViewLogDir, id=2)
        self.Bind(wx.EVT_MENU, self.OnExit, id=3)
        self.frame_menubar.Append(self.file_menu, "File")
        self.SetMenuBar(self.frame_menubar)
        
        # Status Bar
        self.StatusBar = self.CreateStatusBar(2)
        
        # Start the Encode thread
        self.commandQueue = Queue.Queue()
        self.responseQueue = Queue.Queue()
        self.cancelQueue = Queue.Queue()
        self.EncodeThread = EncodeThread(self.commandQueue, self.responseQueue, self.cancelQueue)
        self.EncodeThread.start()
        self.Bind(wx.EVT_CLOSE, self.CloseEvent, self)

        # Make a Notebook (Tab thingy)
        self.tabs = wx.Notebook(self)
        
        # File Copy Tab
        self.copypanel = FileCopy(self.tabs, self.StatusBar, self.CopyDoneCallback)
        self.tabs.AddPage(self.copypanel,"Copy Files")
        
        # Setup the player panel
        self.playerpanel = Player(self.tabs, self.SubmitJobCallback, self.StatusBar)
        self.tabs.AddPage(self.playerpanel, "Trimmer")
        
        self.jobmessagepanel = JobList(self.tabs, self.responseQueue, self.CancelJobCallback)
        self.tabs.AddPage(self.jobmessagepanel, "Messages")
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tabs, 1, flag=wx.EXPAND)
        self.SetSizer(sizer)
        self.SetMinSize(minsize)
        
        self.JobCounter = 0
        
    def SubmitJobCallback (self, commandName, command):
        cName = "%2i: %s" % (self.JobCounter, str(commandName))
        self.commandQueue.put( (cName, command) )      
        self.jobmessagepanel.AddJob(cName)
        self.StatusBar.SetStatusText("Started job %s" % cName)
        self.JobCounter += 1
        self.tabs.SetSelection(2)
    
    def CancelJobCallback (self, commandName):
        self.cancelQueue.put(commandName)
    
    def CopyDoneCallback (self, DestFilename):
        self.tabs.SetSelection(1)
        self.playerpanel.OpenFile(DestFilename, Play = False)
        
    def CloseEvent (self, evt): 
        self.cancelQueue.put("exit")
        #m = wx.MessageDialog(self, "Waiting for encoding to complete.  See other window for progress.",  "Please Wait...")
        #m.Show()
        self.EncodeThread.join()
        self.Destroy()

    def OnViewLogDir(self, evt):
        subprocess.call('explorer "%s"' % TrimmerConfig.get('FilePaths', 'LogPath') )

    def OnOpen(self, evt):
        self.tabs.SetSelection(1)
        self.playerpanel.OnOpen(None)
        
    def OnExit(self, evt):
        """Closes the window.
        """
        self.Close()
		
if __name__ == "__main__":
    if not os.path.isdir(TrimmerConfig.get('FilePaths', 'LogPath')):
        os.makedirs(TrimmerConfig.get('FilePaths', 'LogPath'))
        
    try:
        log = open(os.path.join(TrimmerConfig.get('FilePaths', 'LogPath'), "stdout_log.txt"), "w")
        sys.stdout = log
        sys.stderr = log
    except:
        pass
    # Create a wx.App(), which handles the windowing system event loop
    app = wx.PySimpleApp()
    # Create the window containing our small media player
    player = TrimmerMain("Trimmer")
    # show the player window centred and run the application
    player.Show()
    app.MainLoop()

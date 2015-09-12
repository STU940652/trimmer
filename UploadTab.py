# Python imports
import wx 
import traceback
import json
import boto 
import boto.s3.connection
import os
import os.path
import datetime
import threading
import time

# Boto = Amazon S3
from boto.s3.key import Key 

# Selenium for Vimeo
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions

# Import other classes from this project
from Settings import *
from PasswordDialog import Credentials
from CmsManager import CmsManager
    
class UploadTab(wx.Panel):
    Tags = {}
    def __init__ (self, parent, GetTags):
        wx.Panel.__init__(self, parent)
        self.GetTags = GetTags
        
        #Main Sizer
        Sizer=wx.BoxSizer(wx.VERTICAL)
        
        # MP3 File dialog
        self.Mp3Enable = wx.CheckBox(self, -1, "Upload MP3 Audio (Amazon S3)")
        Sizer.Add(self.Mp3Enable, 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.Mp3Path = wx.TextCtrl(self)
        self.Mp3FileButton = wx.Button(self, label='...', size=(20,-1))
        self.Bind(wx.EVT_BUTTON, self.SelectMP3, self.Mp3FileButton)
        Mp3pathSizer = wx.BoxSizer(wx.HORIZONTAL)
        Mp3pathSizer.AddSpacer(25)
        Mp3pathSizer.Add(self.Mp3Path, 1, flag=wx.EXPAND)
        Mp3pathSizer.Add(self.Mp3FileButton)
        Sizer.Add(Mp3pathSizer, flag=wx.EXPAND|wx.ALL, border = 5)
        URLSizer = wx.BoxSizer(wx.HORIZONTAL)
        URLSizer.AddSpacer(25)
        URLSizer.Add(wx.StaticText(self, -1, "MP3 URL"))
        self.MP3URL = wx.TextCtrl(self, size=(200,-1))
        URLSizer.Add(self.MP3URL, 1, flag=wx.EXPAND)
        Sizer.Add(URLSizer, flag=wx.ALL, border = 5)

        Sizer.AddSpacer(20)
        
        # MP4 File dialog
        self.Mp4Enable = wx.CheckBox(self, -1, "Upload MP4 Video (Vimeo)")
        Sizer.Add(self.Mp4Enable, 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.Mp4Path = wx.TextCtrl(self)
        self.Mp4FileButton = wx.Button(self, label='...', size=(20,-1))
        self.Bind(wx.EVT_BUTTON, self.SelectMP4, self.Mp4FileButton)
        Mp4pathSizer = wx.BoxSizer(wx.HORIZONTAL)
        Mp4pathSizer.AddSpacer(25)
        Mp4pathSizer.Add(self.Mp4Path, 1, flag=wx.EXPAND)
        Mp4pathSizer.Add(self.Mp4FileButton)
        Sizer.Add(Mp4pathSizer, flag=wx.EXPAND|wx.ALL, border = 5)
        VimNumSizer = wx.BoxSizer(wx.HORIZONTAL)
        VimNumSizer.AddSpacer(25)
        VimNumSizer.Add(wx.StaticText(self, -1, "Vimeo Number"))
        self.VimNumber = wx.TextCtrl(self, size=(200,-1))
        VimNumSizer.Add(self.VimNumber, 1, flag=wx.EXPAND)
        Sizer.Add(VimNumSizer, flag=wx.ALL, border = 5)
        
        Sizer.AddSpacer(20)
        
        # Web page CMS
        self.CmsEnable = wx.CheckBox(self, -1, "Update Web Page")
        Sizer.Add(self.CmsEnable, 0, flag=wx.TOP|wx.LEFT, border = 10)

        # Upload Button
        self.StartButton = wx.Button (self, label='Upload')      
        self.Bind(wx.EVT_BUTTON, self.OnUpload, self.StartButton)
        Sizer.Add(self.StartButton, flag=wx.ALL|wx.ALIGN_RIGHT, border = 5)
        
        # Messages
        self.Messages = wx.TextCtrl (self, style=wx.TE_MULTILINE|wx.TE_READONLY)
        Sizer.Add(self.Messages, 1, flag=wx.ALL|wx.EXPAND, border = 5)
        
        self.SetSizer(Sizer)

    def SelectMP3 (self, evt):
        openFileDialog = wx.FileDialog(self, "Select MP3 Audio File", "", "",
                                       "MP3 (*.mp3)|*.mp3", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if (openFileDialog.ShowModal() == wx.ID_OK):
            self.Mp3Path.SetValue(openFileDialog.GetPath())
            
    def SelectMP4 (self, evt):
        openFileDialog = wx.FileDialog(self, "Select MP4 Video File", "", "",
                                       "MP4 (*.mp4)|*.mp4|All Files (*.*)", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if (openFileDialog.ShowModal() == wx.ID_OK):
            self.Mp4Path.SetValue(openFileDialog.GetPath())

    def OnCompletion (self, completion):
        print (completion)
        try:
            CompletionDict = json.loads(completion)
            
        except:
            #print (traceback.format_exc())
            return
            
        if "MP3" in CompletionDict:
            self.Mp3Path.SetValue(CompletionDict["MP3"])
            self.Mp3Enable.SetValue(True)
            self.CmsEnable.SetValue(True)

        if "MP4" in CompletionDict:
            self.Mp4Path.SetValue(CompletionDict["MP4"])
            self.Mp4Enable.SetValue(True)
            self.CmsEnable.SetValue(True)
    
    def OnUpload (self, evt):
        self.Tags.update(self.GetTags())
        self.UploadThread = threading.Thread(target=self.UploadFiles, \
                            args=(self.Mp3Enable.GetValue(), self.Mp4Enable.GetValue(), self.CmsEnable.GetValue(), \
                            self.Mp3Path.GetValue(), self.Mp4Path.GetValue()))
        self.UploadThread.start()
        if self.Mp3Enable.GetValue():
            self.Mp3Enable.Disable()
        if self.Mp4Enable.GetValue():
            self.Mp4Enable.Disable()
        if self.CmsEnable.GetValue():
            self.CmsEnable.Disable()
    
    ## This executes in a separate thread
    def UploadFiles (self, Mp3Enable, Mp4Enable, CmsEnable, Mp3Path, Mp4Path): 
        # TODO: wx stuff here needs to be handled by an event
        if Mp3Enable:
            ret = self.UploadMP3(Mp3Path)
            wx.CallAfter (self.Mp3Enable.Enable)
            if not ret:
                return 
            wx.CallAfter (self.Mp3Enable.SetValue, False)
        
        if Mp4Enable:
            ret = self.UploadMP4(Mp4Path)
            wx.CallAfter (self.Mp4Enable.Enable)
            if not ret:
                return
            wx.CallAfter (self.Mp4Enable.SetValue, False)
            
        if CmsEnable:
            c = CmsManager()
            c.SetMedia (self.Tags, self.ThreadSafeLog)
            wx.CallAfter (self.CmsEnable.Enable)
            wx.CallAfter (self.CmsEnable.SetValue, False)
        
    def UploadMP3 (self, Mp3Path):
        sourceFilename = os.path.abspath(Mp3Path)
        
        self.ThreadSafeLog ("Uploading %s to Amazon S3\n" %(sourceFilename))
        
        if sourceFilename != "":
            try:
                # Target filename
                self.Tags["mp3_url"] = '/'.join([time_of_record.strftime(TrimmerConfig.get('Upload', 'MP3BasePath', fallback='')), os.path.basename(sourceFilename)]).replace('\\','/')

                # connect to the bucket 
                conn = boto.connect_s3(Credentials["AWS_ACCESS_KEY_ID"], 
                                        Credentials["AWS_SECRET_ACCESS_KEY"],
                                        calling_format=boto.s3.connection.OrdinaryCallingFormat()) 
                bucket = conn.get_bucket(Credentials["BUCKET_NAME"]) 

                # create a key to keep track of our file in the storage  
                k = Key(bucket) 
                k.key = self.Tags["mp3_url"]
                self.ThreadSafeLog ("... to %s\n" %(self.Tags["mp3_url"]))                
                try:
                    wx.CallAfter (self.MP3URL.SetValue, self.Tags["mp3_url"])
                except:
                    self.ThreadSafeLog ('\n' + traceback.format_exc() + '\n')
                k.set_contents_from_filename(sourceFilename) 
                #k.set_acl('public-read')
                
                self.ThreadSafeLog ("Done uploading %s\n" %(sourceFilename))
            except:
                self.ThreadSafeLog ('\n' + traceback.format_exc() + '\n')
                return False
        return True
 
    def UploadMP4 (self, Mp4Path):
        sourceFilename = os.path.abspath(Mp4Path)
        self.ThreadSafeLog ("Uploading %s to Vimeo\n" %(sourceFilename))

        try:
            browser = webdriver.Chrome()
            # Visit URL
            browser.implicitly_wait(60) # seconds
            url = "http://www.vimeo.com/log_in"
            browser.get(url)
            login_form = browser.find_element_by_id('login_form')
            login_form.find_element_by_id('email').send_keys(Credentials["Vimeo_Username"])
            login_form.find_element_by_id('password').send_keys(Credentials["Vimeo_Password"])
            login_form.find_element_by_class_name('btn').click()
            browser.find_element_by_id('btn_upload').click()
            browser.find_element_by_link_text('legacy uploader').click()
            #browser.get("https://vimeo.com/upload?force_legacy=1") # This is a workaround for the Beta uploader
            browser.find_element_by_name('file_data').send_keys (sourceFilename)
            time.sleep(5)
            browser.find_element_by_id('submit_button').click()
            time.sleep(5)

            # Wait for upload 
            browser.implicitly_wait(60*60) # seconds.. wait up to one hour
            
            # Fill in some info
            self.ThreadSafeLog ("Entering video info\n")
            try:
                title = "%s - %s (%s)" % (self.Tags["Speaker"], self.Tags["Title"], self.Tags["Date"].replace("/","."))
                self.Tags["vimeo_title"] = title
                browser.find_element_by_id('title').clear()
                browser.find_element_by_id('title').send_keys(title)
                browser.find_element_by_id('description').clear()
                browser.find_element_by_id('description').send_keys(self.Tags["Summary"])
                browser.find_element_by_id('tags').clear()
                browser.find_element_by_id('tags').send_keys(self.Tags["Keywords"])
            except:
                self.ThreadSafeLog ('\n' + traceback.format_exc() + '\n')
            browser.find_element_by_id('tags').submit()
            
            # Wait until the 'Go to Video' link magically appears
            self.ThreadSafeLog ("Wait for upload to complete\n")
            still_going = True
            browser.implicitly_wait(0)
            while still_going:
                self.ThreadSafeLog (browser.title + '\n')
                try:
                    browser.find_element_by_partial_link_text('Go to Video')
                    still_going = False
                except selenium.common.exceptions.NoSuchElementException:
                    time.sleep(10)
                    
            browser.implicitly_wait(60*60)

            # This is the link for the video
            self.Tags["vimeo_number"] = browser.find_element_by_partial_link_text('Go to Video').get_attribute('href').rsplit("/",1)[1]
            self.ThreadSafeLog (self.Tags["vimeo_number"] + '\n')
            try:
                wx.CallAfter (self.VimNumber.SetValue, self.Tags["vimeo_number"])
            except:
                self.ThreadSafeLog ('\n' + traceback.format_exc() + '\n')

            self.ThreadSafeLog ("Done uploading %s\n" %(sourceFilename))
        except:
            self.ThreadSafeLog ('\n' + traceback.format_exc() + '\n')
            browser.quit()
            return False
            
        browser.quit()
        return True
          
    def ThreadSafeLog(self, s):
        wx.CallAfter (self.Messages.AppendText, s)
         
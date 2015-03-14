import wx 
import traceback
import json
import boto 
from boto.s3.key import Key 
import os
import os.path
import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from Settings import *
from PasswordDialog import Credentials
import threading
from Player import Tags
    
class UploadTab(wx.Panel):
    def __init__ (self, parent):
        wx.Panel.__init__(self, parent)
        
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
        
        Sizer.AddSpacer(20)
        
        # Web page CMS
        self.CmsEnable = wx.CheckBox(self, -1, "Update Web Page")
        Sizer.Add(self.CmsEnable, 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.CmsEnable.Enable(False)

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
        self.UploadThread = threading.Thread(target=self.UploadFiles)
        self.UploadThread.start()
    
    def UploadFiles (self):    
        if self.Mp3Enable.GetValue():
            self.UploadMP3()
        
        if self.Mp4Enable.GetValue():
            self.UploadMP4()
        
    def UploadMP3 (self):
        global Tags
        sourceFilename = os.path.abspath(self.Mp3Path.GetValue())
        
        self.Messages.AppendText("Uploading %s to Amazon S3\n" %(sourceFilename))
        
        if sourceFilename != "":
            try:
                # Target filename
                Tags["mp3_url"] = '/'.join([datetime.datetime.now().strftime(TrimmerConfig.get('Upload', 'MP3BasePath', fallback='')), os.path.basename(sourceFilename)]).replace('\\','/')

                # connect to the bucket 
                conn = boto.connect_s3(Credentials["AWS_ACCESS_KEY_ID"], 
                                        Credentials["AWS_SECRET_ACCESS_KEY"]) 
                bucket = conn.get_bucket(Credentials["BUCKET_NAME"]) 

                # create a key to keep track of our file in the storage  
                k = Key(bucket) 
                k.key = Tags["mp3_url"]
                self.Messages.AppendText("... to %s\n" %(Tags["mp3_url"]))                
                k.set_contents_from_filename(sourceFilename) 
                #k.set_acl('public-read')
                
                self.Mp3Enable.SetValue(False)
                self.Messages.AppendText("Done uploading %s\n" %(sourceFilename))
            except:
                self.Messages.AppendText('\n' + traceback.format_exc() + '\n')
                return
 
    def UploadMP4 (self):
        global Tags
        sourceFilename = os.path.abspath(self.Mp4Path.GetValue())
        self.Messages.AppendText("Uploading %s to Vimeo\n" %(sourceFilename))
        
        try:
            browser = webdriver.Chrome()
            # Visit URL
            browser.implicitly_wait(10) # seconds
            url = "http://www.vimeo.com/log_in"
            browser.get(url)
            login_form = browser.find_element_by_id('login_form')
            login_form.find_element_by_id('email').send_keys(Credentials["Vimeo_Username"])
            login_form.find_element_by_id('password').send_keys(Credentials["Vimeo_Password"])
            login_form.find_element_by_class_name('btn').click()
            #time.sleep(5)
            browser.find_element_by_id('btn_upload').click()
            #time.sleep(5)
            browser.find_element_by_name('file_data').send_keys (sourceFilename)
            time.sleep(5)
            browser.find_element_by_id('submit_button').click()
            time.sleep(5)

            # Fill in some info
            try:
                title = "%s - %s (%s)" % (Tags["speaker"], Tags["title"], Tags["date"].replace("/","."))
                browser.find_element_by_id('title').clear()
                browser.find_element_by_id('title').send_keys(title)
                browser.find_element_by_id('description').clear()
                browser.find_element_by_id('description').send_keys(Tags["summary"])
                browser.find_element_by_id('tags').clear()
                browser.find_element_by_id('tags').send_keys(Tags["keywords"])
            except:
                pass
            browser.find_element_by_id('tags').submit()
            #time.sleep(5)
            # Wait for upload 
            browser.implicitly_wait(30*60) # seconds

            #WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "myDynamicElement"))
            # This is the link for the video
            Tags["vimeo_number"] = browser.find_element_by_partial_link_text('Go to Video').get_attribute('href').rsplit("/",1)[1]
            self.Messages.AppendText (Tags["vimeo_number"] + '\n')

            self.Messages.AppendText("Done uploading %s\n" %(sourceFilename))
        except:
            self.Messages.AppendText('\n' + traceback.format_exc() + '\n')
            
        browser.close()
           
         
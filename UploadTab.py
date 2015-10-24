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

# Vimeo
import vimeo
import urllib.parse
import io

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
from PasswordDialog import SaveCredentials
from CmsManager import CmsManager
    
class MyVimeoClient(vimeo.VimeoClient):
    # Overload upload function to report progress
    def _perform_upload(self, filename, ticket):
        """Take an upload ticket and perform the actual upload."""

        assert ticket.status_code == 201, "Failed to create an upload ticket"

        ticket = ticket.json()

        # Perform the actual upload.
        target = ticket['upload_link']
        size = os.path.getsize(filename)
        last_byte = 0
        with io.open(filename, 'rb') as f:
            while last_byte < size:
                try:
                    self._make_pass(target, f, size, last_byte)
                except requests.exceptions.Timeout:
                    # If there is a timeout here, we are okay with it, since
                    # we'll check and resume.
                    pass
                last_byte = self._get_progress(target, size)
                print (100.0 * last_byte / size)

        # Perform the finalization and get the location.
        finalized_resp = self.delete(ticket['complete_uri'])

        assert finalized_resp.status_code == 201, "Failed to create the video."

        return finalized_resp.headers.get('Location', None)

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
        self.MP3URL = wx.TextCtrl(self, size=(400,-1))
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
            
        # Upload the Site-MP4 immediatly
        if "Site-MP4"  in CompletionDict:
            self.Tags.update(self.GetTags())
            self.SiteUploadThread = threading.Thread(target=self.UploadFiles, \
                                args=(False, True, False, \
                                "", CompletionDict["Site-MP4"], "SITE VIDEO: ", False))
            self.SiteUploadThread.start()
    
    def OnUpload (self, evt):
        self.Tags.update(self.GetTags())
        # Get the MP3 and Vimeo info is provided
        if self.MP3URL.GetValue() != "":
            self.Tags["mp3_url"] = self.MP3URL.GetValue()
        if self.VimNumber.GetValue() != "":
            self.Tags["vimeo_number"] = self.VimNumber.GetValue()
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
    def UploadFiles (self, Mp3Enable, Mp4Enable, CmsEnable, Mp3Path, Mp4Path, TitlePrefix="", UpdateVimeoLink = True): 
        if Mp3Enable:
            ret = self.UploadMP3(Mp3Path)
            wx.CallAfter (self.Mp3Enable.Enable)
            if not ret:
                return 
            wx.CallAfter (self.Mp3Enable.SetValue, False)
        
        if Mp4Enable:
            ret = self.UploadMP4(Mp4Path, TitlePrefix, UpdateVimeoLink)
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
 
    def UploadMP4 (self, Mp4Path, TitlePrefix = "", UpdateVimeoLink = True):
        sourceFilename = os.path.abspath(Mp4Path)
        self.ThreadSafeLog ("Uploading %s to Vimeo\n" %(sourceFilename))
        end_url = "http://sourceforge.net/p/trimmer/wiki/AuthEnd/"

        try:
            v = MyVimeoClient(
                key=Credentials["Vimeo_Client_Id"],
                secret=Credentials["Vimeo_Client_Secret"])
                
            # There seems to be a problem in the released api
            v.API_ROOT = v.API_ROOT.replace("http://api.vimeo.dev", "https://api.vimeo.com")

            code_from_url = ""
            token = Credentials["Vimeo_User_Token"].strip()

            if token == "":
                """This section is used to determine where to direct the user."""
                vimeo_authorization_url = v.auth_url(['upload', 'edit'], end_url, state = "INITIAL")

                # Your application should now redirect to vimeo_authorization_url.
                browser = webdriver.Chrome()
                # Visit URL
                browser.get(vimeo_authorization_url)
                self.ThreadSafeLog  (vimeo_authorization_url)
                
                # Wait until URL = end_url
                still_going = True
                while still_going:
                    time.sleep(0.5)
                    if end_url in browser.current_url:
                        authorized_url = browser.current_url
                        browser.quit()
                        still_going = False 

                authorized_params = urllib.parse.parse_qs(urllib.parse.urlparse(authorized_url).query)

                if authorized_params['state'] == ["INITIAL"]:
                    code_from_url = authorized_params['code'][0]
                    #print (code_from_url)

                """This section completes the authentication for the user."""
                # You should retrieve the "code" from the URL string Vimeo redirected to.  Here that's named CODE_FROM_URL
                try:
                    token, user, scope = v.exchange_code(code_from_url, end_url)
                    #print(token, user, scope)
                    Credentials["Vimeo_User_Token"] = token
                    SaveCredentials()
                    
                except vimeo.auth.GrantFailed:
                    # Handle the failure to get a token from the provided code and redirect.
                    self.ThreadSafeLog ('\n' + traceback.format_exc() + '\n')
                    return

                # Store the token, scope and any additional user data you require in your database so users do not have to re-authorize 
            else:
                v.token = token
                
            # Upload file
            video_uri = v.upload(sourceFilename)
            d = v.get(video_uri)
            self.ThreadSafeLog (TitlePrefix + " URL is " + str(d.json()["link"]) + '\n')
            
            if UpdateVimeoLink:
                self.Tags["vimeo_number"] = video_uri.split('/')[-1]
                try:
                    wx.CallAfter (self.VimNumber.SetValue, self.Tags["vimeo_number"])
                except:
                    self.ThreadSafeLog ('\n' + traceback.format_exc() + '\n')
            
            title = TitlePrefix + "%s - %s (%s)" % (self.Tags["Speaker"], self.Tags["Title"], self.Tags["Date"].replace("/","."))
            # Update Metadata
            m={}
            m["name"]=title
            m["description"]=self.Tags["Summary"]
            
            w = v.patch(video_uri, data=m)
            #print (w)
            
            for tag in self.Tags["Keywords"].split(','):
                w = v.put(video_uri + '/tags/' + tag)
                #print (tag, w)
        
            self.ThreadSafeLog ("Done uploading %s\n" %(sourceFilename))
        except:
            self.ThreadSafeLog ('\n' + traceback.format_exc() + '\n')
            return False

        return True
                  
    def ThreadSafeLog(self, s):
        wx.CallAfter (self.Messages.AppendText, s)
         
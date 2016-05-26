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

# Import other classes from this project
from Settings import *
from Credentials import Credentials
from PasswordDialog import SaveCredentials
from CmsManager import CmsManager
import GmailClient
    
class MyVimeoClient(vimeo.VimeoClient):
    pass
#   # Overload upload function to report progress
#   def _perform_upload(self, filename, ticket):
#       """Take an upload ticket and perform the actual upload."""
#
#       assert (ticket.status_code == 201), "Failed to create an upload ticket"
#
#       ticket = ticket.json()
#
#       # Perform the actual upload.
#       target = ticket['upload_link']
#       size = os.path.getsize(filename)
#       last_byte = 0
#       with io.open(filename, 'rb') as f:
#           while last_byte < size:
#               try:
#                   self._make_pass(target, f, size, last_byte)
#               except requests.exceptions.Timeout:
#                   # If there is a timeout here, we are okay with it, since
#                   # we'll check and resume.
#                   pass
#               last_byte = self._get_progress(target, size)
#               #print (100.0 * last_byte / size)
#
#       # Perform the finalization and get the location.
#       finalized_resp = self.delete(ticket['complete_uri'])
#
#       assert finalized_resp.status_code == 201, "Failed to create the video."
#
#       return finalized_resp.headers.get('Location', None)

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
        Mp3pathSizer.AddSpacer(20)
        Mp3pathSizer.Add(self.Mp3Path, 1, flag=wx.EXPAND)
        Mp3pathSizer.Add(self.Mp3FileButton)
        Sizer.Add(Mp3pathSizer, flag=wx.EXPAND|wx.ALL, border = 5)
        URLSizer = wx.BoxSizer(wx.HORIZONTAL)
        URLSizer.AddSpacer(20)
        URLSizer.Add(wx.StaticText(self, -1, "MP3 URL"))
        self.MP3URL = wx.TextCtrl(self, size=(400,-1))
        URLSizer.Add(self.MP3URL, 1, flag=wx.EXPAND)
        Sizer.Add(URLSizer, flag=wx.ALL, border = 5)

        Sizer.AddSpacer(10)
        
        # MP4 File dialog
        self.Mp4Enable = wx.CheckBox(self, -1, "Upload MP4 Video (Vimeo)")
        Sizer.Add(self.Mp4Enable, 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.Mp4Path = wx.TextCtrl(self)
        self.Mp4FileButton = wx.Button(self, label='...', size=(20,-1))
        self.Bind(wx.EVT_BUTTON, self.SelectMP4, self.Mp4FileButton)
        Mp4pathSizer = wx.BoxSizer(wx.HORIZONTAL)
        Mp4pathSizer.AddSpacer(20)
        Mp4pathSizer.Add(self.Mp4Path, 1, flag=wx.EXPAND)
        Mp4pathSizer.Add(self.Mp4FileButton)
        Sizer.Add(Mp4pathSizer, flag=wx.EXPAND|wx.ALL, border = 5)
        VimNumSizer = wx.BoxSizer(wx.HORIZONTAL)
        VimNumSizer.AddSpacer(20)
        VimNumSizer.Add(wx.StaticText(self, -1, "Vimeo Number"))
        self.VimNumber = wx.TextCtrl(self, size=(200,-1))
        VimNumSizer.Add(self.VimNumber, 1, flag=wx.EXPAND)
        Sizer.Add(VimNumSizer, flag=wx.ALL, border = 5)
        
        Sizer.AddSpacer(10)
        
        # Web page CMS
        self.CmsEnable = wx.CheckBox(self, -1, "Update Web Page")
        Sizer.Add(self.CmsEnable, 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.CmsPublish = wx.CheckBox(self, -1, "Publish Web Page")
        Sizer.Add(self.CmsPublish, 0, flag=wx.TOP|wx.LEFT, border = 10)

        Sizer.AddSpacer(10)
        
        # Update on completion
        self.UpdateOnCompletion = wx.CheckBox(self, -1, "Update On Completion")
        Sizer.Add(self.UpdateOnCompletion, 0, flag=wx.TOP|wx.LEFT, border = 10)

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
        update = False

        try:
            if completion.lower() != 'none':
                CompletionDict = json.loads(completion)
            else:
                return            
        except:
            print (traceback.format_exc())
            GmailClient.ExceptionEmail(traceback.format_exc())
            return
            
        if "MP3" in CompletionDict:
            self.Mp3Path.SetValue(CompletionDict["MP3"])
            self.Mp3Enable.SetValue(True)
            self.CmsEnable.SetValue(True)
            if self.UpdateOnCompletion.GetValue():
                update = True

        if "MP4" in CompletionDict:
            self.Mp4Path.SetValue(CompletionDict["MP4"])
            self.Mp4Enable.SetValue(True)
            self.CmsEnable.SetValue(True)
            if self.UpdateOnCompletion.GetValue():
                update = True
            
        if update:
            self.OnUpload(None)
            
        # Upload the Site-MP4 immediatly
        if "Site-MP4"  in CompletionDict:
            EmailMessage = None
            if "EmailMessage" in CompletionDict:
                EmailMessage = CompletionDict["EmailMessage"]
            self.Tags.update(self.GetTags())
            self.SiteUploadThread = threading.Thread(target=self.UploadFiles, \
                                args=(False, True, False, False,\
                                "", CompletionDict["Site-MP4"], "SITE VIDEO: ", False, EmailMessage))
            self.SiteUploadThread.start()
            
        # Replace existing public MP4
        if "Replace-MP4" in CompletionDict:
            if ("Vimeo_Number" in CompletionDict) and CompletionDict["Vimeo_Number"]:
                self.ThreadSafeLog ("Replacing Vimeo video %s\n" % CompletionDict["Vimeo_Number"])            
                # Ready to go
                self.UploadReplaceThread = threading.Thread(target=self.UploadFiles, \
                                args=(False, True, False, False,\
                                "", CompletionDict["Replace-MP4"], "", False, None, CompletionDict["Vimeo_Number"]))
                self.UploadReplaceThread.start()
            else:
                self.ThreadSafeLog ("Missing Vimeo Number.  Could not update\n")
    
    def OnUpload (self, evt):
        self.Tags.update(self.GetTags())
        # Get the MP3 and Vimeo info is provided
        if self.MP3URL.GetValue() != "":
            self.Tags["mp3_url"] = self.MP3URL.GetValue()
        if self.VimNumber.GetValue() != "":
            self.Tags["vimeo_number"] = self.VimNumber.GetValue()
        self.UploadThread = threading.Thread(target=self.UploadFiles, \
                            args=(self.Mp3Enable.GetValue(), self.Mp4Enable.GetValue(), self.CmsEnable.GetValue(), self.CmsPublish.GetValue(),\
                            self.Mp3Path.GetValue(), self.Mp4Path.GetValue()))
        self.UploadThread.start()
        if self.Mp3Enable.GetValue():
            self.Mp3Enable.Disable()
        if self.Mp4Enable.GetValue():
            self.Mp4Enable.Disable()
        if self.CmsEnable.GetValue():
            self.CmsEnable.Disable()
            self.CmsPublish.Disable()
    
    ## This executes in a separate thread
    def UploadFiles (self, Mp3Enable, Mp4Enable, CmsEnable, CmsPublish, Mp3Path, Mp4Path, TitlePrefix="", UpdateVimeoLink = True, EmailMessage = None,  ReplaceURI = None): 
        if Mp3Enable:
            ret = self.UploadMP3(Mp3Path)
            wx.CallAfter (self.Mp3Enable.Enable)
            if not ret:
                wx.CallAfter (self.Mp3Enable.Enable)
                wx.CallAfter (self.Mp4Enable.Enable)
                wx.CallAfter (self.CmsEnable.Enable)
                return 
            wx.CallAfter (self.Mp3Enable.SetValue, False)
        
        if Mp4Enable:
            ret = self.UploadMP4(Mp4Path, TitlePrefix, UpdateVimeoLink,  ReplaceURI)
            wx.CallAfter (self.Mp4Enable.Enable)
            if not ret:
                wx.CallAfter (self.Mp4Enable.Enable)
                wx.CallAfter (self.CmsEnable.Enable)
                return
            wx.CallAfter (self.Mp4Enable.SetValue, False)
            
        if CmsEnable:
            c = CmsManager()
            c.SetMedia (self.Tags, self.ThreadSafeLog, CmsPublish)
            wx.CallAfter (self.CmsEnable.Enable)
            wx.CallAfter (self.CmsPublish.Enable)
            wx.CallAfter (self.CmsEnable.SetValue, False)
            
        if EmailMessage and len(Credentials["Gmail_Token"]):
            try:
                message = "\n".join(EmailMessage["message"])
                for t in self.Tags:
                    message = message.replace('$'+str(t)+'$', str(self.Tags[t]))
                g = GmailClient.GmailClient()
                sender = "me"
                if "from" in EmailMessage:
                    sender = EmailMessage["from"]
                g.SendMessage(sender = sender, 
                              to = EmailMessage["to"], 
                              subject = EmailMessage["subject"], 
                              message_text = message)

            except:
                self.ThreadSafeLog ('\n' + traceback.format_exc() + '\n')
                GmailClient.ExceptionEmail(traceback.format_exc())
                
        
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
                GmailClient.ExceptionEmail(traceback.format_exc())
                return False
        return True
 
    def UploadMP4 (self, Mp4Path, TitlePrefix = "", UpdateVimeoLink = True, ReplaceURI = None):
        sourceFilename = os.path.abspath(Mp4Path)
        self.ThreadSafeLog ("Uploading %s to Vimeo\n" %(sourceFilename))

        try:
            v = MyVimeoClient(
                key=Credentials["Vimeo_Client_Id"],
                secret=Credentials["Vimeo_Client_Secret"])
                
            code_from_url = ""
            token = Credentials["Vimeo_User_Token"].strip()

            if token == "":
                self.ThreadSafeLog ('\nMP4 Upload failed - Vimeo authorization required\n')
                return
            else:
                v.token = token
                
            if ReplaceURI:
                # Fixup URI
                ReplaceURI = "/videos/" + ReplaceURI.split('/')[-1]                
                
                # Replace existing file
                self.ThreadSafeLog ("Replacing " + ReplaceURI + "\n")
                video_uri = v.replace(ReplaceURI, sourceFilename)
            
            else:
                # Upload file
                video_uri = v.upload(sourceFilename)
                d = v.get(video_uri)
                self.ThreadSafeLog (TitlePrefix + " URL is " + str(d.json()["link"]) + '\n')
                self.Tags["vimeo_link"] = str(d.json()["link"])
                
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
        
            self.ThreadSafeLog ("Done uploading %s\n\n" %(sourceFilename))
        except:
            self.ThreadSafeLog ('\n' + traceback.format_exc() + '\n')
            GmailClient.ExceptionEmail(traceback.format_exc())
            return False

        return True
                  
    def ThreadSafeLog(self, s):
        wx.CallAfter (self.Messages.AppendText, s)
         
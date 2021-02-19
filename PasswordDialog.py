import wx
import pickle
import codecs
from Settings import *
import traceback
import time
from Credentials import Credentials
from MailClient import MailClient

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

# YouTube
import google_auth_oauthlib.flow

def SaveCredentials ():
    global Credentials
    
    with open(os.path.join(TrimmerConfig.get('FilePaths', 'LogPath'),'Trimmer.pwl'), "wb") as f:
        f.write(codecs.encode(pickle.dumps(Credentials), "base64"))
    
class PasswordDialog(wx.Dialog):
    def __init__ (self):
        wx.Dialog.__init__(self, None, title="Update Passwords", style=wx.DEFAULT_DIALOG_STYLE)
        
        Sizer=wx.BoxSizer(wx.VERTICAL)
        
        # CMS
        Sizer.Add(wx.StaticText(self, -1, "CMS Username"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.CMS_Username = wx.TextCtrl(self, size=(400,-1), value=Credentials["CMS_Username"])
        Sizer.Add(self.CMS_Username, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)
        Sizer.Add(wx.StaticText(self, -1, "CMS Password"), 0, flag=wx.LEFT, border = 10)
        self.CMS_Password = wx.TextCtrl(self, style=wx.TE_PASSWORD, value=Credentials["CMS_Password"])
        Sizer.Add(self.CMS_Password, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)
        Sizer.Add(wx.StaticLine(self), 0, flag=wx.EXPAND)
        
        #Amazon S3 
        Sizer.Add(wx.StaticText(self, -1, "AWS_ACCESS_KEY_ID"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.AWS_ACCESS_KEY_ID = wx.TextCtrl(self, value=Credentials["AWS_ACCESS_KEY_ID"])
        Sizer.Add(self.AWS_ACCESS_KEY_ID, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)
        Sizer.Add(wx.StaticText(self, -1, "AWS_SECRET_ACCESS_KEY"), 0, flag=wx.LEFT, border = 10)
        self.AWS_SECRET_ACCESS_KEY = wx.TextCtrl(self, style=wx.TE_PASSWORD, value=Credentials["AWS_SECRET_ACCESS_KEY"])
        Sizer.Add(self.AWS_SECRET_ACCESS_KEY, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)
        Sizer.Add(wx.StaticText(self, -1, "BUCKET_NAME"), 0, flag=wx.LEFT, border = 10)
        self.BUCKET_NAME = wx.TextCtrl(self, value=Credentials["BUCKET_NAME"])
        Sizer.Add(self.BUCKET_NAME, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)
        Sizer.Add(wx.StaticLine(self), 0, flag=wx.EXPAND)
        
        # Vimeo
        Sizer.Add(wx.StaticText(self, -1, "Vimeo Client ID"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.Vimeo_Client_Id = wx.TextCtrl(self, value=Credentials["Vimeo_Client_Id"])
        Sizer.Add(self.Vimeo_Client_Id, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)

        Sizer.Add(wx.StaticText(self, -1, "Vimeo Client Secret"), 0, flag=wx.LEFT, border = 10)
        self.Vimeo_Client_Secret = wx.TextCtrl(self, style=wx.TE_PASSWORD, value=Credentials["Vimeo_Client_Secret"])
        Sizer.Add(self.Vimeo_Client_Secret, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)

        Sizer.Add(wx.StaticText(self, -1, "Vimeo User Token"), 0, flag=wx.LEFT, border = 10)
        
        rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.Vimeo_User_Token = wx.TextCtrl(self, value=Credentials["Vimeo_User_Token"])
        rowSizer.Add(self.Vimeo_User_Token, 1, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)
        self.VimeoAuthenticate = wx.Button (self, -1, "Authenticate")
        rowSizer.Add(self.VimeoAuthenticate, 0)
        self.Bind(wx.EVT_BUTTON, self.OnVimeoAuthenticate, self.VimeoAuthenticate)        
        Sizer.Add(rowSizer, flag=wx.EXPAND)

        Sizer.Add(wx.StaticLine(self), 0, flag=wx.EXPAND)
        
        # YouTube
        Sizer.Add(wx.StaticText(self, -1, "YouTube Client ID"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.YouTube_Client_Id = wx.TextCtrl(self, value=Credentials["YouTube_Client_Id"])
        Sizer.Add(self.YouTube_Client_Id, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)

        Sizer.Add(wx.StaticText(self, -1, "YouTube Client Secret"), 0, flag=wx.LEFT, border = 10)
        self.YouTube_Client_Secret = wx.TextCtrl(self, style=wx.TE_PASSWORD, value=Credentials["YouTube_Client_Secret"])
        Sizer.Add(self.YouTube_Client_Secret, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)

        Sizer.Add(wx.StaticText(self, -1, "YouTube User Token"), 0, flag=wx.LEFT, border = 10)
        
        rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.YouTube_User_Token = wx.TextCtrl(self, value=Credentials["YouTube_User_Token"])
        rowSizer.Add(self.YouTube_User_Token, 1, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)
        self.YouTubeAuthenticate = wx.Button (self, -1, "Authenticate")
        rowSizer.Add(self.YouTubeAuthenticate, 0)
        self.Bind(wx.EVT_BUTTON, self.OnYouTubeAuthenticate, self.YouTubeAuthenticate)        
        Sizer.Add(rowSizer, flag=wx.EXPAND)

        Sizer.Add(wx.StaticLine(self), 0, flag=wx.EXPAND)
        
        # Email
        Sizer.Add(wx.StaticText(self, -1, "SMTP Host:Port"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.Smtp_Host_Port = wx.TextCtrl(self, value=Credentials["SMTP_HOST_PORT"])
        Sizer.Add(self.Smtp_Host_Port, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)

        Sizer.Add(wx.StaticText(self, -1, "SMTP Username(email)"), 0, flag=wx.LEFT, border = 10)
        self.Smtp_Username = wx.TextCtrl(self, value=Credentials["SMTP_USERNAME"])
        Sizer.Add(self.Smtp_Username, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)


        Sizer.Add(wx.StaticText(self, -1, "SMTP Password"), 0, flag=wx.LEFT, border = 10)
        rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.Smtp_Password = wx.TextCtrl(self, value=Credentials["SMTP_PASSWORD"], style=wx.TE_PASSWORD)
        rowSizer.Add(self.Smtp_Password, 1, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)

        self.MailTest = wx.Button (self, -1, "Test")
        self.Bind(wx.EVT_BUTTON, self.OnMailTest, self.MailTest)
        rowSizer.Add(self.MailTest, 0)

        Sizer.Add(rowSizer, flag=wx.EXPAND)

        Sizer.Add(wx.StaticLine(self), 0, flag=wx.EXPAND)
        
        #Buttons
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.AddStretchSpacer()
        self.OK = wx.Button (self, -1, "OK")
        self.Bind(wx.EVT_BUTTON, self.OnOK, self.OK)
        buttonSizer.Add(self.OK, 0)
        self.CANCEL = wx.Button (self, -1, "Cancel")
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.CANCEL)
        buttonSizer.Add(self.CANCEL, 0)
        
        Sizer.Add(buttonSizer, 0, flag=wx.EXPAND)
        
        Sizer.Fit(self)
        self.SetSizer(Sizer)
        
    def OnOK (self, evt):
        global Credentials
        Credentials["CMS_Username"] = self.CMS_Username.GetValue()
        Credentials["CMS_Password"] = self.CMS_Password.GetValue()
        
        Credentials["AWS_ACCESS_KEY_ID"] = self.AWS_ACCESS_KEY_ID.GetValue()
        Credentials["AWS_SECRET_ACCESS_KEY"] = self.AWS_SECRET_ACCESS_KEY.GetValue()
        Credentials["BUCKET_NAME"] = self.BUCKET_NAME.GetValue()
        
        Credentials["Vimeo_Client_Id"] = self.Vimeo_Client_Id.GetValue()
        Credentials["Vimeo_Client_Secret"] = self.Vimeo_Client_Secret.GetValue()
        Credentials["Vimeo_User_Token"] = self.Vimeo_User_Token.GetValue()
        
        Credentials["YouTube_Client_Id"] = self.YouTube_Client_Id.GetValue()
        Credentials["YouTube_Client_Secret"] = self.YouTube_Client_Secret.GetValue()
        Credentials["YouTube_User_Token"] = self.YouTube_User_Token.GetValue()
        
        Credentials["SMTP_HOST_PORT"] = self.Smtp_Host_Port.GetValue()
        Credentials["SMTP_USERNAME"] =  self.Smtp_Username.GetValue()
        Credentials["SMTP_PASSWORD"] =  self.Smtp_Password.GetValue()
        
        SaveCredentials()
        
        self.Close()
        
    def OnCancel (self, evt):
        self.Close()
        
    def OnVimeoAuthenticate (self, evt):
        end_url = "http://sourceforge.net/p/trimmer/wiki/AuthEnd/"
        try:
            v = vimeo.VimeoClient(
                key=Credentials["Vimeo_Client_Id"],
                secret=Credentials["Vimeo_Client_Secret"])
                
            code_from_url = ""

            """This section is used to determine where to direct the user."""
            vimeo_authorization_url = v.auth_url(['upload', 'edit'], end_url, state = "INITIAL")

            # Your application should now redirect to vimeo_authorization_url.
            browser = webdriver.Chrome()
            # Visit URL
            browser.get(vimeo_authorization_url)
            
            # Wait until URL = end_url
            still_going = True
            while still_going:
                time.sleep(0.5)
                if end_url.split(":", 1)[-1] in browser.current_url:
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
                self.Vimeo_User_Token.SetValue(token)
                
            except vimeo.auth.GrantFailed:
                m = wx.MessageDialog(self, traceback.format_exc(), "Vimeo Authentication Error", wx.OK)
                m.ShowModal()

        except:
            m = wx.MessageDialog(self, traceback.format_exc(), "Vimeo Authentication Error", wx.OK)
            m.ShowModal()
            
    def OnYouTubeAuthenticate (self, evt):
        end_url = "http://sourceforge.net/p/trimmer/wiki/AuthEnd/"
        try:
            scopes = ["https://www.googleapis.com/auth/youtube.upload"]
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_config(
                client_config={"installed":
                    {
                        "client_id":    self.YouTube_Client_Id.GetValue(),
                        "project_id":   "trimmer-1137",
                        "auth_uri":     "https://accounts.google.com/o/oauth2/auth",
                        "token_uri":    "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
                        "client_secret": self.YouTube_Client_Secret.GetValue(),
                        "redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]
                    }},
                scopes=scopes)            
            credentials = flow.run_local_server(port=8085)
            
            self.YouTube_User_Token.SetValue(credentials.refresh_token)

        except:
            m = wx.MessageDialog(self, traceback.format_exc(), "YouTube Authentication Error", wx.OK)
            m.ShowModal()
                       
    def OnMailTest (self, evt):
        try:
            g = MailClient()
            g.SendMessage(sender = "me", to = self.Smtp_Username.GetValue(), subject="Test Message", message_text="This is a Trimmer test message.")
            m = wx.MessageDialog(self, "Test email sent.", "Test Email", wx.OK)
            m.ShowModal()
        except:
            m = wx.MessageDialog(self, traceback.format_exc(), "Test Email Error", wx.OK)
            m.ShowModal()
        
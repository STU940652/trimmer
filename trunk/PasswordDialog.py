import wx
import pickle
import codecs
from Settings import *
import traceback
from Credentials import Credentials
from GmailClient import GmailClient

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
        Sizer.Add(wx.StaticText(self, -1, "CMS Password"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.CMS_Password = wx.TextCtrl(self, style=wx.TE_PASSWORD, value=Credentials["CMS_Password"])
        Sizer.Add(self.CMS_Password, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)
        Sizer.Add(wx.StaticLine(self), 0, flag=wx.EXPAND)
        
        #Amazon S3 
        Sizer.Add(wx.StaticText(self, -1, "AWS_ACCESS_KEY_ID"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.AWS_ACCESS_KEY_ID = wx.TextCtrl(self, value=Credentials["AWS_ACCESS_KEY_ID"])
        Sizer.Add(self.AWS_ACCESS_KEY_ID, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)
        Sizer.Add(wx.StaticText(self, -1, "AWS_SECRET_ACCESS_KEY"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.AWS_SECRET_ACCESS_KEY = wx.TextCtrl(self, style=wx.TE_PASSWORD, value=Credentials["AWS_SECRET_ACCESS_KEY"])
        Sizer.Add(self.AWS_SECRET_ACCESS_KEY, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)
        Sizer.Add(wx.StaticText(self, -1, "BUCKET_NAME"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.BUCKET_NAME = wx.TextCtrl(self, value=Credentials["BUCKET_NAME"])
        Sizer.Add(self.BUCKET_NAME, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)
        Sizer.Add(wx.StaticLine(self), 0, flag=wx.EXPAND)
        
        # Vimeo
        Sizer.Add(wx.StaticText(self, -1, "Vimeo Client ID"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.Vimeo_Client_Id = wx.TextCtrl(self, value=Credentials["Vimeo_Client_Id"])
        Sizer.Add(self.Vimeo_Client_Id, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)

        Sizer.Add(wx.StaticText(self, -1, "Vimeo Client Secret"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.Vimeo_Client_Secret = wx.TextCtrl(self, style=wx.TE_PASSWORD, value=Credentials["Vimeo_Client_Secret"])
        Sizer.Add(self.Vimeo_Client_Secret, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)

        Sizer.Add(wx.StaticText(self, -1, "Vimeo User Token"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.Vimeo_User_Token = wx.TextCtrl(self, value=Credentials["Vimeo_User_Token"])
        Sizer.Add(self.Vimeo_User_Token, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)

        Sizer.Add(wx.StaticLine(self), 0, flag=wx.EXPAND)
        
        # Gmail
        Sizer.Add(wx.StaticText(self, -1, "Gmail User Token"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.Gmail_Token = wx.TextCtrl(self, value=Credentials["Gmail_Token"])
        rowSizer.Add(self.Gmail_Token, 1, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)
        self.GmailAuthenticate = wx.Button (self, -1, "Authenticate")
        self.Bind(wx.EVT_BUTTON, self.OnGmailAuthenticate, self.GmailAuthenticate)
        rowSizer.Add(self.GmailAuthenticate, 0)
        self.GmailTest = wx.Button (self, -1, "Test")
        self.Bind(wx.EVT_BUTTON, self.OnGmailTest, self.GmailTest)
        rowSizer.Add(self.GmailTest, 0)

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
        Credentials["Gmail_Token"] = self.Gmail_Token.GetValue()
        
        SaveCredentials()
        
        self.Close()
        
    def OnCancel (self, evt):
        self.Close()
        
    def OnGmailAuthenticate (self, evt):
        g = GmailClient()
        g.authenticate()
        if g.credentials:
            self.Gmail_Token.SetValue(g.credentials.to_json()) 
            
    def OnGmailTest (self, evt):
        try:
            g = GmailClient()
            g.SendMessage(sender = "me", to = g.credentials.id_token['email'], subject="Test Message", message_text="This is a Trimmer test message.")
            m = wx.MessageDialog(self, "Test email sent.", "Test Email", wx.OK)
            m.ShowModal()
        except:
            m = wx.MessageDialog(self, traceback.format_exc(), "Test Email Error", wx.OK)
            m.ShowModal()
        
import wx
import pickle
import codecs
from Settings import *
import traceback

Credentials = {}

# LoadCredentials ():
try:
    with open(os.path.join(TrimmerConfig.get('FilePaths', 'LogPath'),'Trimmer.pwl'), "rb") as f:

        Credentials = pickle.loads(codecs.decode(f.read(), "base64"))
        
        
except:
    print (traceback.format_exc())
    Credentials["CMS_Username"] = ""
    Credentials["CMS_Password"] = ""
    Credentials["AWS_ACCESS_KEY_ID"] = ""
    Credentials["AWS_SECRET_ACCESS_KEY"] = ""
    Credentials["BUCKET_NAME"] = ""
    Credentials["Vimeo_Username"] = ""
    Credentials["Vimeo_Password"] = ""

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
        Sizer.Add(wx.StaticText(self, -1, "Vimeo Username"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.Vimeo_Username = wx.TextCtrl(self, value=Credentials["Vimeo_Username"])
        Sizer.Add(self.Vimeo_Username, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)
        Sizer.Add(wx.StaticText(self, -1, "Vimeo Password"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.Vimeo_Password = wx.TextCtrl(self, style=wx.TE_PASSWORD, value=Credentials["Vimeo_Password"])
        Sizer.Add(self.Vimeo_Password, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)
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
        Credentials["Vimeo_Username"] = self.Vimeo_Username.GetValue()
        Credentials["Vimeo_Password"] = self.Vimeo_Password.GetValue()

        with open(os.path.join(TrimmerConfig.get('FilePaths', 'LogPath'),'Trimmer.pwl'), "wb") as f:
            f.write(codecs.encode(pickle.dumps(Credentials), "base64"))
        
        self.Close()
        
    def OnCancel (self, evt):
        self.Close()
        
        
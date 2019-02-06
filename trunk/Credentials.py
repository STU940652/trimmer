import os.path
from Settings import *
import traceback
import pickle
import codecs

Credentials = {}
Credentials["CMS_Username"] = ""
Credentials["CMS_Password"] = ""
Credentials["AWS_ACCESS_KEY_ID"] = ""
Credentials["AWS_SECRET_ACCESS_KEY"] = ""
Credentials["BUCKET_NAME"] = ""
Credentials["Vimeo_Client_Id"] = ""
Credentials["Vimeo_Client_Secret"] = ""
Credentials["Vimeo_User_Token"] = ""
Credentials["SMTP_HOST_PORT"] = ""
Credentials["SMTP_USERNAME"] = ""
Credentials["SMTP_PASSWORD"] = ""

# LoadCredentials ():
try:
    with open(os.path.join(TrimmerConfig.get('FilePaths', 'LogPath'),'Trimmer.pwl'), "rb") as f:

        newCredentials = pickle.loads(codecs.decode(f.read(), "base64"))
        Credentials.update(newCredentials)
        
        
except:
    print (traceback.format_exc())


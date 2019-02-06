"""Send an email message from the user's account.
"""

import os
import traceback
import smtplib

from email.mime.text import MIMEText

from Credentials import Credentials
from Settings import *


class MailClient():
    def SendMessage(self, sender, to, subject, message_text):
        """Create a message for an email.
        
        Args:
        sender: Email address of the sender.
        to: Email address of the receiver.
        subject: The subject of the email message.
        message_text: The text of the email message.
        """
        msg = MIMEText(message_text)
        msg['Subject'] = subject

        try:
            s = smtplib.SMTP(Credentials["SMTP_HOST_PORT"])
            s.starttls()
            s.login(Credentials["SMTP_USERNAME"], Credentials["SMTP_PASSWORD"])
            s.sendmail(sender, to, msg.as_string())
            s.quit()
        
        except:
            return False
            
        return True

def ExceptionEmail (s):
    if not len( Credentials["AWS_ACCESS_KEY_ID"]):
        return
    to = TrimmerConfig.get('GlobalSettings', 'ExceptionEmail', fallback='')
    if not len(to):
        return
        
    id = "%s@%s: " % (os.getenv('USERNAME',"unknown"), os.getenv('COMPUTERNAME',"unknown"))
    try:
        g = MailClient()
        g.SendMessage(sender = "me", 
                      to = to, 
                      subject = "Trimmer Exception", 
                      message_text = id + "Trimmer threw an exception:\n\n" + s)
    except:
        print (traceback.format_exc())

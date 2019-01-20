"""Send an email message from the user's account.
"""

import os
import traceback

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
        
        # Create a new SES resource and specify a region.
        client = boto.ses.connection.SESConnection(
            aws_access_key_id=Credentials["AWS_ACCESS_KEY_ID"], 
            aws_secret_access_key=Credentials["AWS_SECRET_ACCESS_KEY"])

        # Try to send the email.
        try:
            #Provide the contents of the email.
            response = client.send_email(
                to_addresses=to,
                subject=subject,
                body=message_text,
                source=sender
            )
        
        except:
            response = None
            
        return response

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

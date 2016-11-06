"""Send an email message from the user's account.
"""

import base64
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
import os
import urllib.parse

from apiclient import errors

import logging
import oauth2client.client
from apiclient.discovery import build
import httplib2
import json

# Selenium for Authorization
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions
import traceback
import time

from Credentials import Credentials
from Settings import *

# Path to client_secrets.json which should contain a JSON document such as:
#   {
#     "web": {
#       "client_id": "[[YOUR_CLIENT_ID]]",
#       "client_secret": "[[YOUR_CLIENT_SECRET]]",
#       "redirect_uris": [],
#       "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#       "token_uri": "https://accounts.google.com/o/oauth2/token"
#     }
#   }
CLIENTSECRETS_LOCATION = 'client_secrets.json'
REDIRECT_URI = 'https://sourceforge.net/p/trimmer/wiki/AuthEnd/'
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
    # Add other requested scopes.
]

class GetCredentialsException(Exception):
  """Error raised when an error occurred while retrieving credentials.

  Attributes:
    authorization_url: Authorization URL to redirect the user to in order to
                       request offline access.
  """

  def __init__(self, authorization_url):
    """Construct a GetCredentialsException."""
    self.authorization_url = authorization_url


class CodeExchangeException(GetCredentialsException):
  """Error raised when a code exchange has failed."""


class NoRefreshTokenException(GetCredentialsException):
  """Error raised when no refresh token has been found."""


class NoUserIdException(Exception):
  """Error raised when no user ID could be retrieved."""

class GmailClient():
    credentials = None
    
    def __init__(self):
        self.credentials = self.get_stored_credentials("")
        
    def authenticate(self):
        # See if we have a stored token
        if self.credentials == None:
            # No stored token, so let's get one
            
            # Get the Authorization URL
            authurl = self.get_authorization_url(email_address="", state="SUCCESS")
            
            for thisDriver in [webdriver.Chrome, webdriver.Firefox]:
                try:
                    browser = thisDriver()
                except:
                    #print(traceback.format_exc())
                    continue
                break

            # Visit URL
            browser.get(authurl)
            
            # Wait until URL = end_url
            still_going = True
            while still_going:
                time.sleep(1.0)
                if browser.current_url.startswith((REDIRECT_URI,REDIRECT_URI.replace("https://","http://"))):
                    authorized_url = browser.current_url
                    browser.quit()
                    still_going = False 

            authorized_params = urllib.parse.parse_qs(urllib.parse.urlparse(authorized_url).query)

            if authorized_params['state'] == ["SUCCESS"]:
                authorization_code = authorized_params['code'][0]
            
            # Exchange authorization code for a token
            self.credentials = self.get_credentials(authorization_code = authorization_code, state = "FAIL")
       
        pass

    def get_stored_credentials(self, user_id):
        """Retrieved stored credentials for the provided user ID.

        Args:
        user_id: User's ID.
        Returns:
        Stored oauth2client.client.OAuth2Credentials if found, None otherwise.
        Raises:
        NotImplemented: This function has not been implemented.
        """
        
        c = Credentials["Gmail_Token"]
        if not len(c):
            c = None
        else:
            c = oauth2client.client.AccessTokenCredentials.new_from_json(c)
        
        return c


    def store_credentials(self, user_id, credentials):
        """Store OAuth 2.0 credentials in the application's database.

        This function stores the provided OAuth 2.0 credentials using the user ID as
        key.

        Args:
        user_id: User's ID.
        credentials: OAuth 2.0 credentials to store.
        Raises:
        NotImplemented: This function has not been implemented.
        """
        print (user_id, credentials.to_json())


    def exchange_code(self, authorization_code):
      """Exchange an authorization code for OAuth 2.0 credentials.

      Args:
        authorization_code: Authorization code to exchange for OAuth 2.0
                            credentials.
      Returns:
        oauth2client.client.OAuth2Credentials instance.
      Raises:
        CodeExchangeException: an error occurred.
      """
      flow = oauth2client.client.flow_from_clientsecrets(CLIENTSECRETS_LOCATION, scope=' '.join(SCOPES), redirect_uri=REDIRECT_URI)
      try:
        self.credentials = flow.step2_exchange(authorization_code)
        return self.credentials
      except oauth2client.client.FlowExchangeError as error:
        logging.error('An error occurred: %s', error)
        raise CodeExchangeException(None)


    def get_user_info(self):
      """Send a request to the UserInfo API to retrieve the user's information.

      Args:
        credentials: oauth2client.client.OAuth2Credentials instance to authorize the
                     request.
      Returns:
        User information as a dict.
      """
      user_info_service = build(
          serviceName='oauth2', version='v2',
          http=self.credentials.authorize(httplib2.Http()))
      user_info = None
      try:
        user_info = user_info_service.userinfo().get().execute()
      except errors.HttpError as e:
        logging.error('An error occurred: %s', e)
      if user_info and user_info.get('id'):
        return user_info
      else:
        raise NoUserIdException()


    def get_authorization_url(self, email_address, state):
      """Retrieve the authorization URL.

      Args:
        email_address: User's e-mail address.
        state: State for the authorization URL.
      Returns:
        Authorization URL to redirect the user to.
      """
      flow = oauth2client.client.flow_from_clientsecrets(CLIENTSECRETS_LOCATION, scope=' '.join(SCOPES), redirect_uri=REDIRECT_URI)
      flow.params['access_type'] = 'offline'
      flow.params['approval_prompt'] = 'force'
      flow.params['user_id'] = email_address
      flow.params['state'] = state
      return flow.step1_get_authorize_url()


    def get_credentials(self, authorization_code, state):
      """Retrieve credentials using the provided authorization code.

      This function exchanges the authorization code for an access token and queries
      the UserInfo API to retrieve the user's e-mail address.
      If a refresh token has been retrieved along with an access token, it is stored
      in the application database using the user's e-mail address as key.
      If no refresh token has been retrieved, the function checks in the application
      database for one and returns it if found or raises a NoRefreshTokenException
      with the authorization URL to redirect the user to.

      Args:
        authorization_code: Authorization code to use to retrieve an access token.
        state: State to set to the authorization URL in case of error.
      Returns:
        oauth2client.client.OAuth2Credentials instance containing an access and
        refresh token.
      Raises:
        CodeExchangeError: Could not exchange the authorization code.
        NoRefreshTokenException: No refresh token could be retrieved from the
                                 available sources.
      """
      email_address = ''
      try:
        credentials = self.exchange_code(authorization_code)
        user_info = self.get_user_info()
        email_address = user_info.get('email')
        user_id = user_info.get('id')
        if credentials.refresh_token is not None:
          self.store_credentials(user_id, credentials)
          self.credentials = credentials
          return credentials
        else:
          credentials = self.get_stored_credentials(user_id)
          if credentials and credentials.refresh_token is not None:
            self.credentials = credentials
            return credentials
      except CodeExchangeException as error:
        logging.error('An error occurred during code exchange.')
        # Drive apps should try to retrieve the user and credentials for the current
        # session.
        # If none is available, redirect the user to the authorization URL.
        error.authorization_url = self.get_authorization_url(email_address, state)
        raise error
      except NoUserIdException:
        logging.error('No user ID could be retrieved.')
      # No refresh token has been retrieved.
      authorization_url = self.get_authorization_url(email_address, state)
      raise NoRefreshTokenException(authorization_url)

    def SendMIMEMessage(self, message, user_id = "me"):
      """Send an email message.

      Args:
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        message: Message to be sent.

      Returns:
        Sent Message.
      """
      
      #Build a Gmail service object.
      http = httplib2.Http()
      http = self.credentials.authorize(http)
      service =  build('gmail', 'v1', http=http)

      try:
        message = (service.users().messages().send(userId=user_id, body=message)
                   .execute())
        #print ('Message Id: %s' % message['id'])
        return message
      except errors.HttpError as error:
        print ('An error occurred: %s' % error)


    def SendMessage(self, sender, to, subject, message_text):
      """Create a message for an email.

      Args:
        sender: Email address of the sender.
        to: Email address of the receiver.
        subject: The subject of the email message.
        message_text: The text of the email message.

      Returns:
        An object containing a base64url encoded email object.
      """
      message = MIMEText(message_text)
      message['to'] = to
      message['from'] = sender
      message['subject'] = subject
      m = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
      return self.SendMIMEMessage(m)


    def CreateMessageWithAttachment(
        self, sender, to, subject, message_text, file_dir, filename):
      """Create a message for an email.

      Args:
        sender: Email address of the sender.
        to: Email address of the receiver.
        subject: The subject of the email message.
        message_text: The text of the email message.
        file_dir: The directory containing the file to be attached.
        filename: The name of the file to be attached.

      Returns:
        An object containing a base64url encoded email object.
      """
      message = MIMEMultipart()
      message['to'] = to
      message['from'] = sender
      message['subject'] = subject

      msg = MIMEText(message_text)
      message.attach(msg)

      path = os.path.join(file_dir, filename)
      content_type, encoding = mimetypes.guess_type(path)

      if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
      main_type, sub_type = content_type.split('/', 1)
      if main_type == 'text':
        fp = open(path, 'rb')
        msg = MIMEText(fp.read(), _subtype=sub_type)
        fp.close()
      elif main_type == 'image':
        fp = open(path, 'rb')
        msg = MIMEImage(fp.read(), _subtype=sub_type)
        fp.close()
      elif main_type == 'audio':
        fp = open(path, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=sub_type)
        fp.close()
      else:
        fp = open(path, 'rb')
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        
        ## From https://github.com/google/google-api-python-client/issues/93
        # Encode the payload using Base64.  This line is from here:
        # https://docs.python.org/3/library/email-examples.html
        encoders.encode_base64(msg)
        
        fp.close()

      msg.add_header('Content-Disposition', 'attachment', filename=filename)
      message.attach(msg)

      m = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
      return self.SendMIMEMessage(m)

def ExceptionEmail (s):
    if not len( Credentials["Gmail_Token"]):
        return
    to = TrimmerConfig.get('GlobalSettings', 'ExceptionEmail', fallback='')
    if not len(to):
        return
        
    id = "%s@%s: " % (os.getenv('USERNAME',"unknown"), os.getenv('COMPUTERNAME',"unknown"))
    try:
        g = GmailClient()
        g.SendMessage(sender = "me", 
                      to = to, 
                      subject = "Trimmer Exception", 
                      message_text = id + "Trimmer threw an exception:\n\n" + s)
    except:
        print (traceback.format_exc())
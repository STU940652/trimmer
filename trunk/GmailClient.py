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
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.client import AccessTokenCredentials
from apiclient.discovery import build
import httplib2
import json



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


def get_stored_credentials(user_id):
    """Retrieved stored credentials for the provided user ID.

    Args:
    user_id: User's ID.
    Returns:
    Stored oauth2client.client.OAuth2Credentials if found, None otherwise.
    Raises:
    NotImplemented: This function has not been implemented.
    """
    
    #credentials = AccessTokenCredentials('<an access token>',
    #    'my-user-agent/1.0')
    #http = httplib2.Http()
    #http = credentials.authorize(http) 
    c = None
    c = AccessTokenCredentials.from_json('{"id_token": {"iss": "accounts.google.com", "sub": "102006997547213390571", "at_hash": "2s_ng0xmYjhioGhr7EljFw", "email_verified": true, "azp": "728576164301-fsn0sd54ssvbed55r7bb4jpa7tpfa2v1.apps.googleusercontent.com", "email": "andyndeanna@gmail.com", "aud": "728576164301-fsn0sd54ssvbed55r7bb4jpa7tpfa2v1.apps.googleusercontent.com", "iat": 1448856368, "exp": 1448859968}, "token_info_uri": "https://www.googleapis.com/oauth2/v2/tokeninfo", "token_expiry": "2015-11-30T05:06:06Z", "access_token": "ya29.PAKGNPdgb05HCq6xglXvk-P8sNRfzilBiY_QyuB0T_eqeGgKrzkLYasay1pm6qnqTMOK", "token_uri": "https://accounts.google.com/o/oauth2/token", "revoke_uri": "https://accounts.google.com/o/oauth2/revoke", "_class": "OAuth2Credentials", "refresh_token": "1/QVvBD1TVUv1c7nD6BkFBWuf2v14ZLHkQ1eT7o-5QL11IgOrJDtdun6zK6XiATCKT", "client_id": "728576164301-fsn0sd54ssvbed55r7bb4jpa7tpfa2v1.apps.googleusercontent.com", "invalid": false, "_module": "oauth2client.client", "scopes": ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/userinfo.email"], "client_secret": "g0VVhi6_bfQYzWFVjPQ84kOM", "user_agent": null, "token_response": {"token_type": "Bearer", "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImFlMTRhYzI1ZjQwMzVhY2Q5ZDIxZWY3MjAxZGM4ODNjMDkwZWI4NDMifQ.eyJpc3MiOiJhY2NvdW50cy5nb29nbGUuY29tIiwiYXRfaGFzaCI6IjJzX25nMHhtWWpoaW9HaHI3RWxqRnciLCJhdWQiOiI3Mjg1NzYxNjQzMDEtZnNuMHNkNTRzc3ZiZWQ1NXI3YmI0anBhN3RwZmEydjEuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJzdWIiOiIxMDIwMDY5OTc1NDcyMTMzOTA1NzEiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiYXpwIjoiNzI4NTc2MTY0MzAxLWZzbjBzZDU0c3N2YmVkNTVyN2JiNGpwYTd0cGZhMnYxLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwiZW1haWwiOiJhbmR5bmRlYW5uYUBnbWFpbC5jb20iLCJpYXQiOjE0NDg4NTYzNjgsImV4cCI6MTQ0ODg1OTk2OH0.p8IRd3YE1QGAw-bxh4wl32PK4RX_zVTGPD77mnKazX7MWgTqZw_1K4agcbja2ZRkberUFBYd86nfTHafjDXAwtZ1hP5sqzEoWgsGKcLEJu--_wwRVAN2L_QnJjbY487DRqcJ7Xh03Qi-_crAN2PIVQSc4LtBJdkVyuSDgrXrhesU-CSUs0oSg4ljfx9zAyCGHuzzqVQMgYEm787eA1Ix_9dePFqR5xD_dQm1xDNmiJ_Ih1AXJ3WrzGFEJ6XsT2EdMaW46M_01lJkSF-vSWkdUw4J5s0bUpAeJ9IsHaZ1gYW7mI3toukQsp_jmU1FSQSLt8xDeQSTeXHEZpFiB4iUig", "access_token": "ya29.PAKGNPdgb05HCq6xglXvk-P8sNRfzilBiY_QyuB0T_eqeGgKrzkLYasay1pm6qnqTMOK", "refresh_token": "1/QVvBD1TVUv1c7nD6BkFBWuf2v14ZLHkQ1eT7o-5QL11IgOrJDtdun6zK6XiATCKT", "expires_in": 3600}}')
    
    return c


def store_credentials(user_id, credentials):
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


def exchange_code(authorization_code):
  """Exchange an authorization code for OAuth 2.0 credentials.

  Args:
    authorization_code: Authorization code to exchange for OAuth 2.0
                        credentials.
  Returns:
    oauth2client.client.OAuth2Credentials instance.
  Raises:
    CodeExchangeException: an error occurred.
  """
  flow = flow_from_clientsecrets(CLIENTSECRETS_LOCATION, scope=' '.join(SCOPES), redirect_uri=REDIRECT_URI)
  try:
    credentials = flow.step2_exchange(authorization_code)
    return credentials
  except FlowExchangeError as error:
    logging.error('An error occurred: %s', error)
    raise CodeExchangeException(None)


def get_user_info(credentials):
  """Send a request to the UserInfo API to retrieve the user's information.

  Args:
    credentials: oauth2client.client.OAuth2Credentials instance to authorize the
                 request.
  Returns:
    User information as a dict.
  """
  user_info_service = build(
      serviceName='oauth2', version='v2',
      http=credentials.authorize(httplib2.Http()))
  user_info = None
  try:
    user_info = user_info_service.userinfo().get().execute()
  except errors.HttpError as e:
    logging.error('An error occurred: %s', e)
  if user_info and user_info.get('id'):
    return user_info
  else:
    raise NoUserIdException()


def get_authorization_url(email_address, state):
  """Retrieve the authorization URL.

  Args:
    email_address: User's e-mail address.
    state: State for the authorization URL.
  Returns:
    Authorization URL to redirect the user to.
  """
  flow = flow_from_clientsecrets(CLIENTSECRETS_LOCATION, scope=' '.join(SCOPES), redirect_uri=REDIRECT_URI)
  flow.params['access_type'] = 'offline'
  #flow.params['approval_prompt'] = 'force'
  flow.params['user_id'] = email_address
  flow.params['state'] = state
  return flow.step1_get_authorize_url()


def get_credentials(authorization_code, state):
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
    credentials = exchange_code(authorization_code)
    user_info = get_user_info(credentials)
    email_address = user_info.get('email')
    user_id = user_info.get('id')
    if credentials.refresh_token is not None:
      store_credentials(user_id, credentials)
      return credentials
    else:
      credentials = get_stored_credentials(user_id)
      if credentials and credentials.refresh_token is not None:
        return credentials
  except CodeExchangeException as error:
    logging.error('An error occurred during code exchange.')
    # Drive apps should try to retrieve the user and credentials for the current
    # session.
    # If none is available, redirect the user to the authorization URL.
    error.authorization_url = get_authorization_url(email_address, state)
    raise error
  except NoUserIdException:
    logging.error('No user ID could be retrieved.')
  # No refresh token has been retrieved.
  authorization_url = get_authorization_url(email_address, state)
  raise NoRefreshTokenException(authorization_url)





def SendMessage(service, user_id, message):
  """Send an email message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

  Returns:
    Sent Message.
  """
  try:
    message = (service.users().messages().send(userId=user_id, body=message)
               .execute())
    print ('Message Id: %s' % message['id'])
    return message
  except errors.HttpError as error:
    print ('An error occurred: %s' % error)


def CreateMessage(sender, to, subject, message_text):
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
  return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}


def CreateMessageWithAttachment(
    sender, to, subject, message_text, file_dir, filename):
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

  return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def build_service(credentials):
  """Build a Gmail service object.

  Args:
    credentials: OAuth 2.0 credentials.

  Returns:
    Gmail service object.
  """
  http = httplib2.Http()
  http = credentials.authorize(http)
  return build('gmail', 'v1', http=http)
  
  
# https://developers.google.com/identity/protocols/OAuth2InstalledApp
#https://accounts.google.com/o/oauth2/auth
if False:
    d = {}
    d["response_type"]="code"
    d["client_id"]=""
    d["redirect_uri"]=""
    d["scope"]=" ".join(SCOPES)
    d["access_type"]="offline"
    d["state"]="SUCCESS"
    print ('https://accounts.google.com/o/oauth2/auth?' + urllib.parse.urlencode(d))

else:
    authorization_code = ""
    m = CreateMessage('', '', "Test Message", "This is the text of the test message")
    credentials = get_stored_credentials("")
    if credentials == None:
        credentials = get_credentials(authorization_code = authorization_code, state = "FAIL")
    service = build_service(credentials)
    SendMessage (service, "me", m)
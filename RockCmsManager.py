import time
import threading
import html
import traceback
import wx
import sys
import re
import requests
import datetime
from Credentials import Credentials
from Settings import *

class CmsManager ():
    def __init__ (self):
        self.IsLoggedIn = False
        self.EventInfo = {}
        self.cookies = None

    def Login(self):
        if not self.IsLoggedIn:
            try:
                # Login
                r = requests.post('https://rock.calvarysc.org/api/Auth/Login', data={"Username": Credentials["CMS_Username"], "Password": Credentials["CMS_Password"]})
                if r.ok:
                    # We have succeeded to log in
                    self.IsLoggedIn = True
                    self.cookies = r.cookies
                    return True
                    
                # Login Failed
                print("CMS Login failed", r.ok, r.status_code, r.reason)
                return False

            except:
                print (traceback.format_exc())
                return False
            
    def Logout (self):
        self.cookies = None
        self.IsLoggedIn = False
    
    def GetEventInfo (self, event = None, include_published = False):
        self.EventInfo = {}
        if not self.IsLoggedIn:
            if not self.Login():
                return None
        try:  

            # Find Message Content Channel     
            r = requests.get('https://rock.calvarysc.org/api/ContentChannels', headers={'Accept': 'application/json'}, params={'$filter': "Name eq 'Messages'"}, cookies=self.cookies)
            if not r.ok:
                print(r.ok, r.status_code, r.reason)
                return []

            message_content_channel_type_id = None
            for c in r.json():
                message_content_channel_type_id = c['ContentChannelTypeId']


            # Get Messages
            r = requests.get('https://rock.calvarysc.org/api/ContentChannelItems', 
                headers={'Accept': 'application/json'}, 
                params={
                    '$filter': f"ContentChannelTypeId eq {message_content_channel_type_id}",
                    '$top': 10,
                    #'$orderby': 'Id desc',
                    '$orderby': 'StartDateTime desc',
                }, 
                cookies=self.cookies
            )
            if not r.ok:
                print(r.ok, r.status_code, r.reason)
                return []
                
            event_list=[]
            for c in r.json():
                if True: # TODO ("Draft" in a.text) or (include_published and "Published" in a.text):
                    event_list.append( (f"{str(datetime.datetime.fromisoformat(c['StartDateTime']).date())}: {c['Title']}", c['Id']) )

            # Go to first in list by default
            if len(event_list) == 0:
                # Nothing valid found
                return []
            self.EventInfo["event_list"] = event_list
                
            if event == None:
                # Go to first in list
                event = event_list[0][1]

            # Get Attributes of this message
            a = requests.get(f"https://rock.calvarysc.org/api/ContentChannelItems/{event}", 
                headers={'Accept': 'application/json'}, 
                params={
                    'loadAttributes': 'simple',
                }, 
                cookies=self.cookies
            )
            if not a.ok:
                print(a.ok, a.status_code, a.reason)
                return []
                
            attr = a.json()

            self.EventInfo["event_id"] = event
            self.EventInfo["title"] = attr['Title']
            self.EventInfo["date"] = str(datetime.datetime.fromisoformat(attr['StartDateTime']).date()) 
            self.EventInfo["summary"] = attr['Content']
            self.EventInfo["speaker"] = attr["AttributeValues"]["Speaker"]["Value"]
            self.EventInfo["comment"] = attr["AttributeValues"]["Passage"]["Value"]

            # Get Vimeo Number for replace
            self.EventInfo["Existing_MP4"] = attr["AttributeValues"]["VideoLink"]["Value"].rsplit('/')[-1]
            # Get Audio link for replace
            self.EventInfo["Existing_MP3"] = attr["AttributeValues"]["AudioLink"]["Value"].replace("http://media.calvarysc.org/","")
            
            self.EventInfo["keywords"] = '' # TODO This was the Vimeo link for RSS
            # TODO attr["AttributeValues"]["VideoEmbed"]["Value"]


            # Get Sermon Series
            # TODO Filter for Sermon Series
            a = requests.get(f"https://rock.calvarysc.org/api/ContentChannelItems/GetParents/{c['Id']}", 
                headers={'Accept': 'application/json'}, 
                params={}, 
                cookies=self.cookies
            )
            attr = a.json()
            if not a.ok:
                print(a.ok, a.status_code, a.reason)
                return []

            self.EventInfo["series"] = attr[0]["Title"]

            return self.EventInfo
            
        except:
            print (traceback.format_exc())
            return None
        return []
        
    def SetMedia (self, Tags, MessageCallback, CmsPublish, CompletionDict={}):    
        if not self.IsLoggedIn:
            MessageCallback("Logging-in to Rock.\n")
            if not self.Login():
                MessageCallback("Rock Log-in failed.\n")
                return False
                
            MessageCallback("Rock Log-in OK.\n")

        MessageCallback("Updating website.\n")
        
        try:
            self.driver.get(Tags["event_id"])
            
            # Enter the Vimeo Video link
            if "vimeo_number" in Tags:
                vimeo_video_link = self.driver.find_element_by_name("custom_vimeovideolink")
                if vimeo_video_link.get_attribute("value") == "":
                    vimeo_video_link.send_keys("player.vimeo.com/video/" + Tags["vimeo_number"])
                    vimeo_video_link.submit()
                    pass
                else:
                    MessageCallback ("Skipping Vimeo Video link because it is not blank\n")
                    
            # Put Vimeo link in Keywords field for RSS feed
            try:            
                vimeo_prefix = "https://vimeo.com/"
                keywords_list = [x.strip() for x in Tags["Keywords"].split(',') if x.strip() and not re.match(r'^https?://vimeo.com/', x.strip().lower())]
                keywords_list.append(vimeo_prefix + Tags["vimeo_number"])

                [n for n in self.driver.find_elements_by_xpath("//div[@class='sectionNavigationSteps-name']") if n.text == 'Content'][0].click()
                keywords_field = self.driver.find_element_by_id("audio") # Yes, it is called "audio"
                keywords_field.clear()
                keywords_field.send_keys(", ".join(keywords_list))
                keywords_field.submit()
            except:
                MessageCallback('\n' + traceback.format_exc() + '\n')
            
            # Go to media tab
            [n for n in self.driver.find_elements_by_xpath("//div[@class='sectionNavigationSteps-name']") if n.text == 'Media'][0].click()

            # Audio
            if "mp3_url" in Tags:
                MessageCallback("...adding Audio\n")
                media_form=self.driver.find_element_by_id('mediaForm')
                media_form.find_element_by_id('name').send_keys("Sermon Audio: %s: %s: %s: %s" % (Tags["Speaker"], Tags["Series"], Tags["Title"], Tags["Date"]))
                media_form.find_element_by_id('description').send_keys(Tags["Summary"].replace('\n','').replace('\r',''))
                media_form.find_element_by_id('tags').send_keys(Tags["Keywords"])
                
                media_form.find_element_by_id("tabExternalLink").click()
                time.sleep(1)
                media_form.find_element_by_id("urlFile").send_keys("https://s3.amazonaws.com/media.calvarysc.org/" + Tags["mp3_url"])
                media_form.submit()

            # Video
            if "vimeo_number" in Tags:
                MessageCallback("...adding Video\n")
                media_form=self.driver.find_element_by_id('mediaForm')
                media_form.find_element_by_id('name').send_keys("Sermon Video: %s: %s: %s: %s" % (Tags["Speaker"], Tags["Series"], Tags["Title"], Tags["Date"]))
                media_form.find_element_by_id('description').send_keys(Tags["Summary"].replace('\n','').replace('\r',''))
                media_form.find_element_by_id('tags').send_keys(Tags["Keywords"])

                media_form.find_element_by_id("tabEmbedCode").click()
                time.sleep(1)
                if "vimeo_title" not in Tags:
                    Tags["vimeo_title"] = "%s - %s (%s)" % (Tags["Speaker"], Tags["Title"], Tags["Date"].replace("/","."))
                media_form.find_element_by_id("embedCode").send_keys(
                    '<iframe src="https://player.vimeo.com/video/%s"' % (Tags["vimeo_number"]) +
                        ' width="%d"' % (int(Tags['video_width'])) +
                        ' height="%d"' % (int(Tags['video_height'])) +
                        ' frameborder="0"' +
                        ' webkitallowfullscreen' +
                        ' mozallowfullscreen' +
                        ' allowfullscreen>' +
                    '</iframe>' +
                    '<p><a href="https://vimeo.com/%s">%s</a> ' % (Tags["vimeo_number"], html.escape(Tags["vimeo_title"])) +
                    'from <a href="https://vimeo.com/calvarysc">Calvary Church</a> on <a href="https://vimeo.com">Vimeo</a>.</p>')
                media_form.submit()
            
            # Publish it
            if CmsPublish:
                self.PublishWebsite(Tags, MessageCallback, Tags["event_id"], CompletionDict)

            MessageCallback("\nDone updating website.\n")
            
        except:
            MessageCallback('\n' + traceback.format_exc() + '\n')
            self.driver.save_screenshot(os.path.join(TrimmerConfig.get('FilePaths', 'LogPath'), 'screenshot.png'))
            return False
            
        finally:
            # self.Close() 
            pass
        
        return True
    
    def PublishWebsite (self, Tags, MessageCallback, EventId, CompletionDict={}):    
        if not self.IsLoggedIn:
            MessageCallback("Logging-in to CMS.\n")
            if not self.Login():
                MessageCallback("CMS Log-in failed.\n")
                return False
                
            MessageCallback("CMS Log-in OK.\n")

        MessageCallback("Publishing website.\n")
        
        try:
            # First get the list of sermons to remove from the Homepage list
            self.driver.get("https://my.ekklesia360.com/Sermon/list")

            l=self.driver.find_element_by_id('listOutput')
            homepage=[]
            for a in l.find_elements_by_tag_name('tr'):
                if ("Published" in a.text) and ("Homepage" in a.text):
                    try:
                        link = a.find_elements_by_tag_name('a')[0].get_attribute("href")
                        if link != EventId:
                            homepage.append(link) 
                    except TypeError:
                        pass
                        
            # Go to the sermon of interest
            self.driver.get(EventId)
            
            # Go to publish tab
            [n for n in self.driver.find_elements_by_xpath("//div[@class='sectionNavigationSteps-name']") if n.text == 'Publish'][0].click()

            if ('CMS_Groups' in CompletionDict):
                groupDropdowns = self.driver.find_element_by_id('groupDropdowns')
                for group in CompletionDict['CMS_Groups'].split(','):
                    # See if this is added to the group
                    if (group not in groupDropdowns.text):
                        # .. if not, add to the group
                        try:
                            groupDropdowns.find_element_by_link_text('Add another group').click()
                            time.sleep(2.0) # Wait to take effect
                            s = groupDropdowns.find_element_by_id('recordListGroup1')
                            Select(s).select_by_visible_text(group)
                            MessageCallback("Added to group \"%s\"\n" % group)
                        except:
                            MessageCallback("Failed to add to group \"%s\"\n" % group)
           
            # Click Publish button
            form = self.driver.find_element_by_id ('publishForm')
            buttons = form.find_elements_by_name('action')
            for button in buttons:
                if button.get_attribute("value") == 'Publish as Featured':
                    time.sleep(5.0) # Pause 5 seconds for the groups to populate
                    button.click()
                    time.sleep(2.0) # I think there is some AJAXish stuff that has to happen here.
                    MessageCallback("Published\n")
                    break
            
            # Do we need to remove homepage from others?
            if ('CMS_Groups' in CompletionDict) and ("Homepage" in CompletionDict['CMS_Groups'].split(',')):
                for this_sermon in homepage:
                    # Go to the sermon of interest
                    self.driver.get(this_sermon)
                    
                    # Go to publish tab
                    [n for n in self.driver.find_elements_by_xpath("//div[@class='sectionNavigationSteps-name']") if n.text == 'Publish'][0].click()
                    time.sleep(5.0) # Pause 5 seconds for the groups to populate
                    
                    # Delete homepage tag
                    b = self.driver.find_element_by_id ('groupDropdowns')
                    for c in b.find_elements_by_tag_name('div'):
                        if "Homepage" in c.text:
                            c.find_element_by_link_text('Remove').click()
                            time.sleep(2.0) # Wait to take effect
                            break
                    
                    # Publish-not-as-featured
                    form = self.driver.find_element_by_id ('publishForm')
                    buttons = form.find_elements_by_name('action')
                    for button in buttons:
                        if button.get_attribute("value") == 'Publish':
                            time.sleep(5.0) # Pause 5 seconds for the groups to populate
                            button.click() 
                            time.sleep(2.0) # Wait to take effect
                            break

            # Everything worked.  Close the browser
            self.driver.quit()
            
        except:
            MessageCallback('\n' + traceback.format_exc() + '\n')
            self.driver.save_screenshot(os.path.join(TrimmerConfig.get('FilePaths', 'LogPath'), 'screenshot.png'))
            return False
            
        finally:
            # self.Close() 
            pass
        
        return True 

        
    def Close( self):
        self.__exit__ (None, None, None)
    
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_value, traceback):           
        self.IsLoggedIn = False
        self.EventInfo = {}
        self.cookies = None
        
        return False

class ImportFromCMSThread(threading.Thread):
    def __init__(self, parent, callback, event = None, include_published = False):
        threading.Thread.__init__(self)
        self.callback = callback
        self.parent = parent
        self.event = event
        self.include_published = include_published
        
    def run (self):
        with CmsManager() as c:
            info = c.GetEventInfo(self.event, self.include_published)
            
        if self.callback and self.parent:
            # This we are in a non-GUI thread, so need to use CallAfter
            wx.CallAfter(self.callback, self.parent, info)
        

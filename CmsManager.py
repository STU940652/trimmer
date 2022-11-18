from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import time
import threading
import html
import traceback
import wx
import sys
import re
from Credentials import Credentials
from Settings import *

class CmsManager ():
    drivers = [webdriver.Chrome, webdriver.Firefox]
    def __init__ (self):
        self.IsLoggedIn = False
        self.EventInfo = {}
        self.driver = None

    def Login(self):
        if not self.IsLoggedIn:
            try:
                if self.driver == None:
                    for thisDriver in self.drivers:
                        try:
                            #if (thisDriver == webdriver.Chrome) and sys.platform.startswith('darwin'):
                            #    self.driver = thisDriver('/usr/local/bin/chromedriver')
                            #else:
                                self.driver = thisDriver()
                        except:
                            #print(traceback.format_exc())
                            continue
                        break
                        
                # Login
                self.driver.implicitly_wait(10) # seconds
                self.driver.get("http://my.ekklesia360.com/Login")
                self.driver.switch_to_frame('_monkIdXdm')
                b = self.driver.find_element_by_id('button')
                b.click()
                time.sleep(1)
                self.driver.switch_to_window(self.driver.window_handles[1])
                b = self.driver.find_element_by_id('user_email')
                b.send_keys(Credentials["CMS_Username"])
                b = self.driver.find_element_by_id('user_password')
                b.send_keys(Credentials["CMS_Password"])
                b = self.driver.find_element_by_name('button')
                b.click()

                # We are now logged in
                self.driver.switch_to_window(self.driver.window_handles[0])
                
                # Wait for dashboard to build
                time.sleep(5)
                
                # We have succeeded to log in
                self.IsLoggedIn = True
                return True
            except:
                print (traceback.format_exc())
                self.driver.save_screenshot(os.path.join(TrimmerConfig.get('FilePaths', 'LogPath'), 'screenshot.png'))
                return False
            
    def Logout (self):
        self.driver.get("https://my.ekklesia360.com/Logout/")
        self.IsLoggedIn = False
    
    def GetEventInfo (self, event = None, include_published = False):
        self.EventInfo = {}
        if not self.IsLoggedIn:
            if not self.Login():
                return None
        try:        
            self.driver.get("https://my.ekklesia360.com/Sermon/list")

            l=self.driver.find_element_by_id('listOutput')
            event_list=[]
            for a in l.find_elements_by_tag_name('tr'):
                if ("Draft" in a.text) or (include_published and "Published" in a.text):
                    try:
                        b = []
                        for c in a.find_elements_by_tag_name('td')[1:4]:
                            b.append(c.text.strip())
                        event_list.append( (": ".join(b), a.find_elements_by_tag_name('a')[0].get_attribute("href")) )
                            
                    except TypeError:
                        pass
                        
            # Go to first in list by default
            if len(event_list) == 0:
                # Nothing valid found
                return []
            self.EventInfo["event_list"] = event_list
                
            if event == None:
                # Go to first in list
                self.driver.get(event_list[0][1])
                time.sleep(1)
                
            else:
                # Go to the requested event
                self.driver.get(event)
                time.sleep(1)

            self.EventInfo["event_url"] = self.driver.current_url
            self.EventInfo["title"] = self.driver.find_element_by_id("title").get_attribute("value")

            l = self.driver.find_element_by_id("series_list")
            for i in l.find_elements_by_tag_name('option'):
                if i.get_attribute("selected"):
                    self.EventInfo["series"] = i.text
               
            self.EventInfo["date"] = self.driver.find_element_by_id("sermondate").get_attribute("value")

            self.EventInfo["speaker"] = self.driver.find_element_by_id("selection").find_elements_by_tag_name('span')[0].text
            
            # Get passage info
            self.EventInfo["comment"] = ""
            l = self.driver.find_element_by_id("books0")
            for i in l.find_elements_by_tag_name('option'):
                if i.get_attribute("selected"):
                    self.EventInfo["comment"] = i.text
                    break
            passage1chapter = self.driver.find_element_by_name("fromchapter0").get_attribute("value")
            self.EventInfo["comment"] += " " + passage1chapter
            self.EventInfo["comment"] += ":" + self.driver.find_element_by_name("fromverse0").get_attribute("value")
            passage1chapter2 = self.driver.find_element_by_name("tochapter0").get_attribute("value")
            if passage1chapter2 != "":
                self.EventInfo["comment"] += "-"
                if passage1chapter != passage1chapter2:
                    self.EventInfo["comment"] += passage1chapter2 + ":"
                self.EventInfo["comment"] += self.driver.find_element_by_name("toverse0").get_attribute("value")
                
            # Get Vimeo Number for replace
            if include_published:
                self.EventInfo["Existing_MP4"] = self.driver.find_element_by_name("custom_vimeovideolink").get_attribute("value").rsplit('/')[-1]

                
            # More Content Info
            [n for n in self.driver.find_elements_by_xpath("//div[@class='sectionNavigationSteps-name']") if n.text == 'Content'][0].click()
            self.EventInfo["summary"] = self.driver.find_element_by_id("summary").text
            self.EventInfo["keywords"] = self.driver.find_element_by_id("audio").get_attribute("value")
            
            # Get Audio link for replace
            if include_published:
                [n for n in self.driver.find_elements_by_xpath("//div[@class='sectionNavigationSteps-name']") if n.text == 'Media'][0].click()
                self.driver.get(self.driver.find_element_by_id("selectSermonAudioEdit").get_attribute("href"))
                self.EventInfo["Existing_MP3"] = self.driver.find_element_by_id("urlFile").get_attribute("value").replace("http://media.calvarysc.org/","")

            return self.EventInfo
            
        except:
            print (traceback.format_exc())
            self.driver.save_screenshot(os.path.join(TrimmerConfig.get('FilePaths', 'LogPath'), 'screenshot.png'))
            return None
        return []
        
    def SetMedia (self, Tags, MessageCallback, CmsPublish, CompletionDict={}):    
        if not self.IsLoggedIn:
            MessageCallback("Logging-in to CMS.\n")
            if not self.Login():
                MessageCallback("CMS Log-in failed.\n")
                return False
                
            MessageCallback("CMS Log-in OK.\n")

        MessageCallback("Updating website.\n")
        
        try:
            self.driver.get(Tags["event_url"])
            
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
                self.PublishWebsite(Tags, MessageCallback, Tags["event_url"], CompletionDict)

            MessageCallback("\nDone updating website.\n")
            
        except:
            MessageCallback('\n' + traceback.format_exc() + '\n')
            self.driver.save_screenshot(os.path.join(TrimmerConfig.get('FilePaths', 'LogPath'), 'screenshot.png'))
            return False
            
        finally:
            # self.Close() 
            pass
        
        return True
    
    def PublishWebsite (self, Tags, MessageCallback, EventURL, CompletionDict={}):    
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
                        if link != EventURL:
                            homepage.append(link) 
                    except TypeError:
                        pass
                        
            # Go to the sermon of interest
            self.driver.get(EventURL)
            
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
        if self.driver != None:
            try:
                self.Logout()
            except:
                pass
            self.driver.quit()
            
        self.IsLoggedIn = False
        self.EventInfo = {}
        self.driver = None
        
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
        

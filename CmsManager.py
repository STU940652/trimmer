from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import threading
from PasswordDialog import Credentials

class CmsManager ():
    def __init__ (self):
        self.IsLoggedIn = False
        self.EventInfo = {}
        self.driver = None

    def Login(self):
        if not self.IsLoggedIn:
            if self.driver == None:
                #self.driver = webdriver.PhantomJS()
                self.driver = webdriver.Chrome()
            self.driver.implicitly_wait(10) # seconds
            self.driver.get("http://my.ekklesia360.com/Login")
            self.driver.switch_to_frame('_monkIdXdm')
            b = self.driver.find_element_by_id('button')
            b.click()
            self.driver.switch_to_window(self.driver.window_handles[1])
            b = self.driver.find_element_by_id('user_email')
            b.send_keys(Credentials["CMS_Username"])
            b = self.driver.find_element_by_id('user_password')
            b.send_keys(Credentials["CMS_Password"])
            b = self.driver.find_element_by_name('button')
            b.click()

            # We are now logged in
            self.driver.switch_to_window(self.driver.window_handles[0])
            
            # We have succeeded to log in
            self.IsLoggedIn = True
            return True
            
    def GetEventInfo (self):
        self.EventInfo = {}
        if not self.IsLoggedIn:
            if not self.Login():
                return self.EventInfo
                
        self.driver.get("https://my.ekklesia360.com/Sermon/list")

        l=self.driver.find_element_by_id('listOutput')
        l.find_elements_by_class_name ('title')[1].find_elements_by_tag_name('a')[0].click()
        time.sleep(1)

        self.EventInfo["title"] = self.driver.find_element_by_id("title").get_attribute("value")

        l = self.driver.find_element_by_id("series_list")
        for i in l.find_elements_by_tag_name('option'):
            if i.get_attribute("selected"):
                self.EventInfo["series"] = i.text
           
        self.EventInfo["date"] = self.driver.find_element_by_id("sermondate").get_attribute("value")

        self.EventInfo["speaker"] = self.driver.find_element_by_id("selection").find_elements_by_tag_name('span')[0].text
        
        # Get passage info
        self.EventInfo["comment"] = ""
        l = self.driver.find_element_by_id("passage")
        for i in l.find_elements_by_tag_name('option'):
            if i.get_attribute("selected"):
                self.EventInfo["comment"] = i.text
                break
        passage1chapter = self.driver.find_element_by_name("passage1chapter").get_attribute("value")
        self.EventInfo["comment"] += " " + passage1chapter
        self.EventInfo["comment"] += ":" + self.driver.find_element_by_name("passage1verse").get_attribute("value")
        passage1chapter2 = self.driver.find_element_by_name("passage1chapter2").get_attribute("value")
        if passage1chapter2 != "":
            self.EventInfo["comment"] += "-"
            if passage1chapter != passage1chapter2:
                self.EventInfo["comment"] += passage1chapter2 + ":"
            self.EventInfo["comment"] += self.driver.find_element_by_name("passage1verse2").get_attribute("value")
        
        # More Content Info
        self.driver.find_element_by_link_text('Content').click()
        self.EventInfo["summary"] = self.driver.find_element_by_id("summary").text
        self.EventInfo["keywords"] = self.driver.find_element_by_id("audio").get_attribute("value")
        
        return self.EventInfo

    def SetVimeoVideo (self, Tags, MessageCallback):
        if not self.IsLoggedIn:
            if not self.Login():
                return False

        self.driver.get("https://my.ekklesia360.com/Sermon/list")

        l=self.driver.find_element_by_id('listOutput')
        l.find_elements_by_class_name ('title')[1].find_elements_by_tag_name('a')[0].click()
        
        # Enter the Vimeo Video link
        if "vimeo_number" in Tags:
            vimeo_video_link = self.driver.find_element_by_name("custom_vimeovideolink")
            if vimeo_video_link.get_attribute("value") == "":
                vimeo_video_link.send_keys("player.vimeo.com/video/" + Tags["vimeo_number"])
                vimeo_video_link.submit()
                pass
            else:
                print ("Skipping Vimeo Video link because it is not blank")
        
        # Go to media tab
        self.driver.find_element_by_link_text('Media').click()
        
        # Audio
        if "mp3_url" in Tags:
            media_form=self.driver.find_element_by_id('mediaForm')
            media_form.find_element_by_id('name').send_keys("Sermon Audio: %s: %s: %s: %s" % (Tags["speaker"], Tags["series"], Tags["title"], Tags["date"]))
            media_form.find_element_by_id('description').send_keys(Tags["summary"])
            media_form.find_element_by_id('tags').send_keys(Tags["keywords"])
            
            media_form.find_element_by_id("tabExternalLink").click()
            media_form.find_element_by_id("urlFile").send_keys("http://media.calvarysc.org/" + Tags["mp3_url"])
            media_form.submit()

        # Video
        if "vimeo_number" in Tags:
            media_form=self.driver.find_element_by_id('mediaForm')
            media_form.find_element_by_id('name').send_keys("Sermon Video: %s: %s: %s: %s" % (Tags["speaker"], Tags["series"], Tags["title"], Tags["date"]))
            media_form.find_element_by_id('description').send_keys(Tags["summary"])
            media_form.find_element_by_id('tags').send_keys(Tags["keywords"])

            media_form.find_element_by_id("tabEmbedCode").click()
            media_form.find_element_by_id("embedCode").send_keys("embed this" + Tags["vimeo_number"])
            media_form.submit()
        
        return True
    
    def Close( self):
        self.__exit__ (None, None, None)
    
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_value, traceback):
        if self.driver != None:
            self.driver.close()
            
        self.IsLoggedIn = False
        self.EventInfo = {}
        self.driver = None
        
        return False

class ImportFromCMSThread(threading.Thread):
    def __init__(self, parent, callback):
        threading.Thread.__init__(self)
        self.callback = callback
        self.parent = parent
        
    def run (self):
        with CmsManager() as c:
            info = c.GetEventInfo()
            
        if self.callback and self.parent:
            self.callback(self.parent, info)
        
            
        
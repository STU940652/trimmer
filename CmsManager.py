from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from credentials import *

class CmsManager ():
    def __init__ (self):
        self.IsLoggedIn = False
        self.EventInfo = {}
        self.driver = None

    def Login(self):
        if not self.IsLoggedIn:
            if self.driver == None:
                #self.driver = webdriver.PhantomJS()
                self.driver = webdriver.Firefox()
            self.driver.get("http://my.ekklesia360.com/Login")
            self.driver.switch_to_frame('_monkIdXdm')
            b = self.driver.find_element_by_id('button')
            b.click()
            time.sleep(5)
            self.driver.switch_to_window(self.driver.window_handles[1])
            b = self.driver.find_element_by_id('user_email')
            b.send_keys(cms_username)
            b = self.driver.find_element_by_id('user_password')
            b.send_keys(cms_password)
            b = self.driver.find_element_by_name('button')
            b.click()
            time.sleep(5)

            # We are now logged in
            self.driver.switch_to_window(self.driver.window_handles[0])
            
            # We have succeeded to log in
            return True
            
    def GetEventInfo (self):
        self.EventInfo = {}
        if not self.IsLoggedIn:
            if not self.Login():
                return self.EventInfo
                
        self.driver.get("https://my.ekklesia360.com/Sermon/list")

        l=self.driver.find_element_by_id('listOutput')
        l.find_elements_by_class_name ('title')[1].find_elements_by_tag_name('a')[0].click()
        time.sleep(5)

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
        passage1chaper = self.driver.find_element_by_name("passage1chapter").get_attribute("value")
        self.EventInfo["comment"] += " " + passage1chaper
        self.EventInfo["comment"] += ":" + self.driver.find_element_by_name("passage1verse").get_attribute("value")
        passage1chapter2 = self.driver.find_element_by_name("passage1chapter2").get_attribute("value")
        if passage1chapter2 != "":
            self.EventInfo["comment"] += "-"
            if passage1chapter != passage1chapter2:
                self.EventInfo["comment"] += passage1chapter2 + ":"
            self.EventInfo["comment"] += self.driver.find_element_by_name("passage1verse2").get_attribute("value")
        
        return self.EventInfo

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

            
        

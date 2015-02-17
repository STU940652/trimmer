import threading
import time
import subprocess
import traceback
import os

from Settings import *

class EncodeThread (threading.Thread):

        def __init__ (self, commandQueue, responseQueue, cancelQueue):
            threading.Thread.__init__(self)
            self.commandQueue = commandQueue
            self.responseQueue = responseQueue
            self.cancelQueue = cancelQueue
            self.cancelList=[]
            
        def run (self):
            sp = None
            cName = ""
            c=""
            o=""
            while (True):
                if sp == None:
                    # Check for a new command
                    if not self.commandQueue.empty():
                        cName, command, completion = self.commandQueue.get()
                        if cName in self.cancelList:
                            # Cancel job and move on
                            self.responseQueue.put( (cName, "Canceled", None) )
                        else:
                            # ok to start this job
                            try:
                                os.environ["FFREPORT"]= "file='" + os.path.join(TrimmerConfig.get('FilePaths', 'LogPath'), "ffmpeg-%s-%s.log'" % \
                                    (cName.rsplit(":",1)[-1].strip(), time.strftime("%Y%m%d-%H%M%S")))
                                sp = subprocess.Popen(command, 
                                                        #shell=True, 
                                                        bufsize=0, 
                                                        universal_newlines=True, 
                                                        creationflags=0x08000000, # CREATE_NO_WINDOW
                                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                            except:
                                sp = None
                                self.responseQueue.put ( (cName, "Exception: " + traceback.format_exc(), None) )
                                print(traceback.format_exc())
                if (sp != None) and (sp.poll() == None):
                    # Get any output
                    c = sp.stdout.read(1)
                    if len(c) > 0:
                        if (ord(c) == 0x0D) or (ord(c) == 0x0A):                        
                            self.responseQueue.put ( (cName, o, None) )
                            o=""
                        else:
                            o += c
                else:
                    time.sleep(0.5)
                    
                if (sp != None) and (sp.poll() != None):
                    o = sp.stdout.read()
                    self.responseQueue.put ( (cName, o, None) )
                    if sp.returncode == 0:
                        self.responseQueue.put( (cName, "Finished successfully", completion) )
                    else:
                        self.responseQueue.put( (cName, "Error: %d" % sp.returncode, None) )
                    sp = None
                        
                if not self.cancelQueue.empty():
                    cancelName = self.cancelQueue.get()
                    if cancelName == "exit":
                        break
                    if cancelName == cName:
                        sp.terminate()
                        sp = None
                        self.responseQueue.put( (cName, "Canceled", None) )
                    else:
                        # Save job name for when it comes up
                        self.cancelList.append(cancelName)
                        
                
            if sp != None:
                sp.terminate()
                sp.wait()


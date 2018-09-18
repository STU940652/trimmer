import threading
import time
import subprocess
import traceback
import os
import platform
import re

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
                        cName, command, completion, out_file_name = self.commandQueue.get()
                        if cName in self.cancelList:
                            # Cancel job and move on
                            self.responseQueue.put( (cName, "Canceled", None) )
                            
                        else:
                            fn_prefix = ""
                            fn_suffix = ""
                            n = 0

                            if out_file_name:
                                for file_name_match in re.finditer(r'"([^"\n]*)\$OutFileName\$([^"\n]*)"', command):
                                    if file_name_match:
                                        fn_prefix = file_name_match.group(1)
                                        fn_suffix = file_name_match.group(2)
                                    full_out_file_name = fn_prefix + out_file_name + ('_'+str(n) if n else '') + fn_suffix
                                    
                                    while os.path.isfile(full_out_file_name):
                                        if n == 10:
                                            # Give up
                                            break
                                            
                                        # Get a unique filename
                                        n += 1
                                        full_out_file_name = fn_prefix + out_file_name + ('_'+str(n) if n else '') + fn_suffix
                                        if not os.path.isfile(full_out_file_name):
                                            break
                                            
                                out_file_name = out_file_name + ('_'+str(n) if n else '')
                                        
                            # Do filename replacement
                            command = command.replace("$OutFileName$", out_file_name)
                            completion = completion.replace("$OutFileName$", out_file_name)
                                  
                            # Ok to start this job
                            try:
                                os.environ["FFREPORT"]= "file='" + os.path.join(TrimmerConfig.get('FilePaths', 'LogPath'), "ffmpeg-%s-%s.log'" % \
                                    (cName.rsplit(":",1)[-1].strip(), time.strftime("%Y%m%d-%H%M%S")))
                                if platform.system() == 'Windows':    
                                    sp = subprocess.Popen(command,  
                                                        bufsize=0, 
                                                        universal_newlines=True, 
                                                        creationflags=0x08000000, # CREATE_NO_WINDOW
                                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
                                else:    
                                    sp = subprocess.Popen(command, 
                                                        shell=True, 
                                                        bufsize=0, 
                                                        universal_newlines=True, 
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


TRIMMER README
==============

Trimmer is released under LGPL 2.1.  It is currently hosted at
http://trimmer.sourceforge.net where you can find the most 
complete documentation.


DEPENDENCIES
============
  Running the binary
    - VLC

  Running the Python
    - Python 3.x
    - wxPython
    - Boto (Amazon S3 client)
    - Selenium (automated web client)
    - Vimeo client (pip install PyVimeo)
    - Google API (pip install google-api-python-client)
    - one of the following web browsers:
        - PhantomJS (headless - put the exe in this directory, or your path)
        - Chrome (need Chrome Driver)
        - Firefox    

  Building the binary
    - cx_freeze 2.x
	
PIP
===
pip install --trusted_host -U --pre -f http://wxpython.org/Phoenix/snapshot-builds/ wxPython_Phoenix
pip install boto
pip install selenium
pip install PyVimeo


#Textonmsg ZNC Module
This ZNC module uses the Twilio API to allow users to have themselves be texted whenever they recieve a private message on IRC.

###Requirements
* All normal ZNC requirements
* A Twilio account to send the texts

###Setting up the module
1. Download ZNC, making sure that the version you get has the modpython module included (github version is preferred)

2. Install all normal znc requirements, as well as python3 and swig
     * If you are using a linux system, you will also have to install python3-pip

3. If you are going to use a virtualenv, make sure that you ahve created and entered it before you move on

4. Use the command `pip3 install twilio` to get twilio so that you can send texts

5. Compile ZNC normally, except for replacing the `./configure` command with `./configure --enable python`

6. Once you have begun the server, find the znc directory (most likely ~/.znc) and create a "modules" directory within it

7. Put the textonmsg.py file in this directory

8. Next, go to the local.py.example file and follow its instructions

9. Find the modpython directory in the ZNC modules library (most likely /usr/local/lib/znc/modpython) and put the new local.py file in this directory

10. Log in to your ZNC server as an admin and load the global "modpython" module

And your done! Your users can now load the textonmsg module just like any other network module, and use it as they please.

------

##Warning!
This module is by no means a complete product, and may have any number of bugs. If you find any, please submit them as issues to this repository.

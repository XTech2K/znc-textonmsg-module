import znc
from twilio.rest import TwilioRestClient

class textonmsg(znc.Module):
    description = 'Texts you if you recieve a private message while offline.'
    
    def OnLoad(self, args, message):
        self.nv['connected'] = 'yes'
        return True
    
    def OnClientLogin(self):
        self.nv['connected'] = 'yes'
    
    def OnClientDisconnect(self):
        self.nv['connected'] = 'no'

    def OnPrivMsg(self, nick, message):
        if self.nv['connected'] == 'no':
            pass
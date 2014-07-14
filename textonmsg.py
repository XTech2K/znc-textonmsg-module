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
            twilio = TwilioRestClient('AC941b51c0ef6f66eccec551177afb1a64','15abf8da2e7b716f209c9657079301fb')
            message = twilio.messages.create(
                                             body=message.s,
                                             to='+14342841361',
                                             from_='+14342605039'
            )
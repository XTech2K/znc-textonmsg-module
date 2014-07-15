activate_this = '../../../../Users/xander/.virtualenvs/py3irc/bin/activate_this.py'
exec(open(activate_this).read(), dict(__file__=activate_this))
import znc
from twilio.rest import TwilioRestClient
import json

class textonmsg(znc.Module):
    description = 'Texts you if you recieve a private message while offline.'
    
    def OnLoad(self, args, message):
        self.nv['number'] = args.
        self.nv['connected'] = 'yes'
        self.nv['blocked'] = '{}'
        return True
    
    def OnClientLogin(self):
        self.nv['connected'] = 'yes'
    
    def OnClientDisconnect(self):
        self.nv['connected'] = 'no'

    def OnPrivMsg(self, nick, message):
        blocked = json.loads(self.nv['blocked']).keys()
        blocked = list(blocked)
        nick = nick.GetNick()
        if self.nv['connected'] == 'no' and not nick in blocked:
            twilio = TwilioRestClient('AC941b51c0ef6f66eccec551177afb1a64',
                                      '15abf8da2e7b716f209c9657079301fb')
            number = self.nv['number']
            message = 'You have recieved a message from '+nick+': "'+message.s+'"'
            twilio.messages.create(
                                   body=message,
                                   to='+1'+number,
                                   from_='+14342605039'
                                   )
        
    def block(self, username):
        blocked = json.loads(self.nv['blocked'])
        if username in blocked.keys():
            self.PutModule(username+' is already blocked')
            return
        blocked[username] = ''
        self.PutModule(username+' is now blocked.')
        self.nv['blocked'] = json.dumps(blocked, separators=(',',':'))

    def unblock(self, username):
        blocked = json.loads(self.nv['blocked'])
        if not username in blocked.keys():
            self.PutModule(username+' was not blocked to begin with.')
            return
        del(blocked[username])
        self.PutModule(username+' is no longer blocked')
        self.nv['blocked'] = json.dumps(blocked, separators=(',',':'))

    def listblocked(self):
        blocked = json.loads(self.nv['blocked'])
        nicks_list = blocked.keys()
        self.PutModule('Blocked users:')
        self.PutModule('\n'.join(nicks_list)+'\n\n')

    def help(self):
        self.PutModule('Available commands are:')
        self.PutModule('block <username>   - '
                       'stops getting texts when messaged by specified user')
        self.PutModule('unblock <username> - '
                       'removes block from specified user')
        self.PutModule('listblocked        - '
                       'returns a list of blocked users')
        self.PutModule('number <phone #>   - '
                       'sets 10-digit phone number to receive texts')

    def OnModCommand(self, command):
        command = command.split(' ')
        if command[0].lower() == 'block':
            if len(command) != 2:
                self.PutModule('invalid number of arguments given;')
                self.PutModule('please present command and 1 argument.')
                return
            self.block(command[1])
            return
        if command[0].lower() == 'unblock':
            if len(command) != 2:
                self.PutModule('invalid number of arguments given;')
                self.PutModule('please present command and 1 argument.')
                return
            self.unblock(command[1])
        if command[0].lower() == 'listblocked':
            if len(command) > 1:
                self.PutModule('"listblocked" does not accept arguments.')
                return
            self.listblocked()
        if command[0].lower() == 'help':
            self.help()
        self.PutModule('Not a valid command')
        self.PutModule('Type "help" to receive a list of valid commands')
#!/usr/bin/env python3

activate_this = '../../../..' \
                '/Users/xander/.virtualenvs/py3irc/bin/activate_this.py'
exec(open(activate_this).read(), dict(__file__=activate_this))
import znc
from twilio.rest import TwilioRestClient
import json
from local import TWILIO_SID, TWILIO_TOKEN

class textonmsg(znc.Module):
    description = 'Texts you if you receive a private message while offline.'
    
    def OnLoad(self, args, message):
        self.nv['number'] = self.number_check(args)
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
        number = self.nv['number']
        if self.nv['connected'] == 'no' and \
                not nick in blocked and number != '':
            twilio = TwilioRestClient(TWILIO_SID, TWILIO_TOKEN)
            message = 'You have received a message from '\
                      +nick+': "'+message.s+'"'
            twilio.messages.create(
                                   body=message,
                                   to='+1'+number,
                                   from_='+14342605039'
                                  )

    def number_check_fail(self):
        self.PutModule('Warning: not a valid number')
        self.PutModule('Please enter a 10-digit phone number')
        self.PutModule('Type "/msg textonmsg number <phone #>" to enter')

    def number_check(self, number):
        if number == '':
            self.PutModule('Warning: no number was entered\n')
            self.PutModule('The module will not work until you enter a number')
            self.PutModule('Type "/msg textonmsg number <phone #>" to enter')
        remove = '-_()[]'
        for x in remove:
            number = number.replace(x,'')
        for x in number:
            if not x in '1234567890':
                self.number_check_fail()
                number = ''
                break
        if len(number) != 10:
            self.number_check_fail()
            number = ''
        if number != '':
            self.PutModule('New number set: "'+number+'"')
        return number
        
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
        self.PutModule('\n'.join(nicks_list))

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
        elif command[0].lower() == 'unblock':
            if len(command) != 2:
                self.PutModule('invalid number of arguments given;')
                self.PutModule('please present command and 1 argument.')
                return
            self.unblock(command[1])
        elif command[0].lower() == 'listblocked':
            if len(command) > 1:
                self.PutModule('"listblocked" does not accept arguments.')
                return
            self.listblocked()
        elif command[0].lower() == 'number':
            if len(command) != 2:
                self.PutModule('invalid number of arguments given;')
                self.PutModule('please present command and 1 argument.')
                return
            self.nv['number'] = self.number_check(command[1])
        elif command[0].lower() == 'shownum':
            number = self.nv['number']
            if number == '':
                self.PutModule('Currently, no number is set')
                self.PutModule('The module will not work until you enter a number')
                self.PutModule('Type "/msg textonmsg number <phone #>" to enter')
                return
            self.PutModule('Current number: '+number)
        elif command[0].lower() == 'help':
            self.help()
        else:
            self.PutModule('Not a valid command')
            self.PutModule('Type "help" to receive a list of valid commands')
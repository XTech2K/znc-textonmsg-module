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

    #CamelCase method name means that it is a built-in ZNC event handler
    def OnLoad(self, args, message):
        """Initially sets variables on module load"""
        self.nv['number'] = self.numberCheck(args)
        self.nv['connected'] = 'yes'
        self.nv['blocked'] = '{}'
        self.nv['received'] = '{}'
        return True

    def OnClientLogin(self):
        self.nv['connected'] = 'yes'

    def OnClientDisconnect(self):
        self.nv['connected'] = 'no'
        self.nv['received'] = '{}'

    def OnPrivMsg(self, nick, message):
        """Sends text via Twilio when client is offline and receives message"""
        blocked = json.loads(self.nv['blocked']).keys()
        blocked = list(blocked)
        received_dict = json.loads(self.nv['received'])
        nick = nick.GetNick()
        try:
            received_num = received_dict[nick]
            if received_num < int(self.nv['msg_limit']):
                received = False
            else:
                received = True
        except KeyError:
            received_dict[nick] = 0
            received = False
        number = self.nv['number']
        if self.nv['connected'] == 'no' and \
                not nick in blocked and number != '' and not received:
            twilio = TwilioRestClient(TWILIO_SID, TWILIO_TOKEN)
            message = 'You have received a message from '\
                      +nick+': "'+message.s+'"'
            twilio.messages.create(
                                   body=message,
                                   to='+1'+number,
                                   from_='+14342605039'
                                  )
            received_dict[nick] += 1
            self.nv['received'] = json.dumps(received_dict, separators=(',',':'))

    #mixedCase method name means that it is a normal method
    def numberCheckFail(self):
        self.PutModule('Warning: not a valid number')
        self.PutModule('Please enter a 10-digit phone number')
        self.PutModule('Type "/msg *textonmsg number <phone #>" to enter')

    def numberCheck(self, number):
        """Checks entered phone number to ensure that it is valid"""
        if number == '':
            self.PutModule('Warning: no number was entered\n')
            self.PutModule('The module will not work until you enter a number')
            self.PutModule('Type "/msg *textonmsg number <phone #>" to enter')
        remove = '-_()[]'
        for x in remove:
            number = number.replace(x,'')
        for x in number:
            if not x in '1234567890':
                self.numberCheckFail()
                number = ''
                break
        if len(number) != 10:
            self.numberCheckFail()
            number = ''
        if number != '':
            self.PutModule('New number set: "'+number+'"')
        return number

    def showNum(self):
        number = self.nv['number']
        if number == '':
            self.PutModule('Currently, no number is set')
            self.PutModule('The module will not work until you enter a number')
            self.PutModule('Type "/msg *textonmsg number <phone #>" to enter')
            return
        self.PutModule('Current number: '+number)

    def block(self, username):
        """Blocks specified username"""
        blocked = json.loads(self.nv['blocked'])
        if username in blocked.keys():
            self.PutModule(username+' is already blocked')
            return
        blocked[username] = ''
        self.PutModule(username+' is now blocked.')
        self.nv['blocked'] = json.dumps(blocked, separators=(',',':'))

    def unblock(self, username):
        """Removes block from specified user"""
        blocked = json.loads(self.nv['blocked'])
        if not username in blocked.keys():
            self.PutModule(username+' was not blocked to begin with.')
            return
        del(blocked[username])
        self.PutModule(username+' is no longer blocked')
        self.nv['blocked'] = json.dumps(blocked, separators=(',',':'))

    def listBlocked(self):
        """Gives a list of users that are blocked"""
        blocked = json.loads(self.nv['blocked'])
        nicks_list = blocked.keys()
        self.PutModule('Blocked users:')
        self.PutModule('\n'.join(nicks_list))

    def setLimit(self, limit):
        try:
            limit = int(limit)
        except ValueError:
            self.PutModule('Argument was not a number')
            self.PutModule('Please enter a number')
            self.Putmodule('Limit was set to default value of 3')
            return 3
        self.PutModule('Message limit set to '+str(limit))
        return str(limit)


    def help(self):
        """Lists all commands"""
        self.PutModule('Available commands are:')
        self.PutModule('block <username>   - '
                       'stops getting texts when messaged by specified user')
        self.PutModule('unblock <username> - '
                       'removes block from specified user')
        self.PutModule('listblocked        - '
                       'returns a list of blocked users')
        self.PutModule('number <phone #>   - '
                       'sets 10-digit phone number to receive texts')
        self.PutModule('shownum            - '
                       'shows the current connected phone number')
        self.PutModule('limit              - '
                       'sets a new max messages per user to send as texts'
                       '(current: '+self.nv['msg_limit']+')')

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
            self.listBlocked()
        elif command[0].lower() == 'number':
            if len(command) != 2:
                self.PutModule('invalid number of arguments given;')
                self.PutModule('please present command and 1 argument.')
                return
            self.nv['number'] = self.numberCheck(command[1])
        elif command[0].lower() == 'shownum':
            if len(command) > 1:
                self.PutModule('"shownum" does not accept arguments.')
                return
            self.showNum()
        elif command[0].lower() == 'limit':
            if len(command) != 2:
                self.PutModule('invalid number of arguments given;')
                self.PutModule('please present command and 1 argument.')
                return
            self.nv['msg_limit'] = self.setLimit(command[1])
        elif command[0].lower() == 'help':
            self.help()
        else:
            self.PutModule('Not a valid command')
            self.PutModule('Type "/msg *textonmsg help" to receive '
                           'a list of valid commands')
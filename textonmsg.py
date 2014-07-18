#!/usr/bin/env python3

import znc
# Make sure that you install twilio outside of any virtual environment
from twilio.rest import TwilioRestClient
import json
from time import time
from local import TWILIO_SID, TWILIO_TOKEN


class IdleTimer(znc.Timer):
    def RunJob(self):
        if 0 < self.idle_time < time() - self.last_activity:
            self.GetModule().setIdle()


class textonmsg(znc.Module):
    description = 'Texts you if you receive a private message while offline.'

    timer = None
    connected = None
    idle = None
    away = None
    received = None

    def setTimer(self):
        textonmsg.timer = self.CreateTimer(IdleTimer,
                                           interval=5,
                                           cycles=0,
                                           description='checks for idle client'
        )
        textonmsg.timer.idle_time = float(self.nv['idle_time']) * 60
        textonmsg.timer.last_activity = time()

    def ping(self):
        self.PutStatus('ping')
        textonmsg.received = {}
        textonmsg.away = False
        if textonmsg.idle:
            textonmsg.idle = False
            self.setTimer()
        else:
            textonmsg.timer.last_activity = time()

    def setIdle(self):
        textonmsg.timer.Stop()
        textonmsg.idle = True
        self.PutStatus('you are now idle and will receive texts when you are PM\'ed')

    def setNV(self, var, default):
        try:
            self.nv[var]
        except:
            self.nv[var] = default

    # CamelCase method name means that it is a built-in ZNC event handler
    def OnLoad(self, args, message):
        """Initially sets variables on module load"""
        # TODO add introduction statements
        if args != '':
            self.nv['number'] = self.numberCheck(args)
        else:
            self.setNV('number', '')
            self.showNum()
        self.setNV('blocked', '{}')
        self.setNV('idle_time', '0')
        self.setTimer()
        textonmsg.received = {}
        textonmsg.connected = True
        textonmsg.idle = False
        textonmsg.away = False
        return True

    def OnClientLogin(self):
        textonmsg.connected = True
        self.ping()

    def OnClientDisconnect(self):
        textonmsg.connected = False

    def isOnline(self):
        if textonmsg.connected and not textonmsg.away and not textonmsg.idle:
            return True
        return False

    def OnPrivMsg(self, nick, message):
        """Sends text via Twilio when client is offline and receives message"""
        blocked = json.loads(self.nv['blocked']).keys()
        blocked = list(blocked)
        nick = nick.GetNick()
        try:
            received_num = textonmsg.received[nick]
            # TODO fix potential int error
            if received_num < int(self.nv['msg_limit']):
                limit = False
            else:
                limit = True
        except KeyError:
            textonmsg.received[nick] = 0
            limit = False
        number = self.nv['number']
        if not (self.isOnline() or nick in blocked or number == '' or limit):
            twilio = TwilioRestClient(TWILIO_SID, TWILIO_TOKEN)
            message = 'You have received a message from ' \
                      + nick + ': "' + message.s + '"'
            twilio.messages.create(
                body=message,
                to='+1' + number,
                from_='+14342605039'
            )
            textonmsg.received[nick] += 1

    def OnUserMsg(self, target, message):
        self.ping()

    # mixedCase method name means that it is a normal method
    def numberCheckFail(self):
        # TODO make message more clear
        self.PutModule('Warning: not a valid number')
        self.PutModule('Please enter a 10-digit phone number')
        self.PutModule('Type "/msg *textonmsg number <phone #>" to enter')
        return ''

    def numberCheck(self, number):
        """Checks entered phone number to ensure that it is valid"""
        remove = '-_()[]'
        for x in remove:
            number = number.replace(x, '')
        for x in number:
            if not x in '1234567890':
                return self.numberCheckFail()
        if len(number) != 10:
            return self.numberCheckFail()
        self.PutModule('New number set: "' + number + '"')
        return number

    def showNum(self):
        number = self.nv['number']
        if number == '':
            self.PutModule('Currently, no number is set')
            self.PutModule('The module will not work until you enter a number')
            self.PutModule('Type "/msg *textonmsg number <phone #>" to enter')
            return
        self.PutModule('Current number: ' + number)

    def block(self, username):
        """Blocks specified username"""
        blocked = json.loads(self.nv['blocked'])
        if username in blocked.keys():
            self.PutModule(username + ' is already blocked')
            return
        blocked[username] = ''
        self.PutModule(username + ' is now blocked.')
        self.nv['blocked'] = json.dumps(blocked, separators=(',', ':'))

    def unblock(self, username):
        """Removes block from specified user"""
        blocked = json.loads(self.nv['blocked'])
        if not username in blocked.keys():
            self.PutModule(username + ' was not blocked to begin with.')
            return
        del (blocked[username])
        self.PutModule(username + ' is no longer blocked')
        self.nv['blocked'] = json.dumps(blocked, separators=(',', ':'))

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
        self.PutModule('Message limit set to ' + str(limit))
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
        self.PutModule('limit <new limit>  - '
                       'sets a new max messages per user to send as texts'
                       '(current: ' + self.nv['msg_limit'] + ')')
        self.PutModule('away               - sets you to away')
        self.PutModule('idle <idle time>   - '
                       'sets the number of minutes before you are set to idle '
                       '(set to 0 to turn off this functionality)')
        self.PutModule('ping               - '
                       'resets idle timer and ends away status')

    def checkArg(self, command):
        if len(command) != 2:
            self.PutModule('invalid number of arguments given;')
            self.PutModule('please present command and 1 argument.')
            return False
        return True

    def checkNoArg(self, command):
        if len(command) > 1:
            self.PutModule('"away" does not accept arguments.')
            return False
        return True

    def setIdleTime(self, idle_time):
        try:
            float(idle_time)
            self.nv['idle_time'] = idle_time
            self.ping()
            textonmsg.timer.Stop()
            self.setTimer()
        except ValueError:
            self.PutModule('Not a valid number')
            self.PutModule('Please try again')

    def OnModCommand(self, command):
        command = command.split(' ')
        if command[0].lower() == 'block':
            if self.checkArg(command):
                self.block(command[1])
        elif command[0].lower() == 'unblock':
            if self.checkArg(command):
                self.unblock(command[1])
        elif command[0].lower() == 'listblocked':
            if self.checkNoArg(command):
                self.listBlocked()
        elif command[0].lower() == 'number':
            if self.checkArg(command):
                self.nv['number'] = self.numberCheck(command[1])
        elif command[0].lower() == 'shownum':
            if self.checkNoArg(command):
                self.showNum()
        elif command[0].lower() == 'limit':
            if self.checkArg(command):
                self.nv['msg_limit'] = self.setLimit(command[1])
        elif command[0].lower() == 'away':
            if self.checkNoArg(command):
                textonmsg.away = True
                self.PutModule('You are now away, and will receive texts when PM\'ed')
        elif command[0].lower() == 'idle':
            if self.checkArg(command):
                self.setIdleTime(command[1])
        elif command[0].lower() == 'ping':
            if self.checkNoArg(command):
                self.ping()
        elif command[0].lower() == 'help':
            self.help()
        else:
            self.PutModule('Not a valid command')
            self.PutModule('Type "/msg *textonmsg help" to receive '
                           'a list of valid commands')
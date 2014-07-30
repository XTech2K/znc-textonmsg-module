#!/usr/bin/env python3

import znc
# Make sure that you install twilio outside of any virtual environment
from twilio.rest import TwilioRestClient
import json
import re
from time import time
from local import TWILIO_SID, TWILIO_TOKEN, INTRODUCTION


class IdleTimer(znc.Timer):
    def RunJob(self):
        """Checks to see if enough time has passed to set idle status"""
        if 0 < self.idle_time < time() - self.last_activity:
            self.GetModule().set_idle()


class textonmsg(znc.Module):  # Note: name must be lowercase; ignore convention
    description = 'Texts you if you receive a private message while offline'

    timer = None
    connected = None
    idle = None
    away = None
    received = None

    # snake_case method name means that it is a normal method
    def send_text(self, nick, message):
        """Sends text via Twilio when client is offline and receives message"""
        blocked = json.loads(self.nv['blocked']).keys()
        blocked = list(blocked)
        nick = nick.GetNick()
        if self.nv['msg_limit'] != '0':
            try:
                received_num = textonmsg.received[nick]
                if received_num < int(self.nv['msg_limit']):
                    limit = False
                else:
                    limit = True
            except KeyError:
                textonmsg.received[nick] = 0
                limit = False
        else:
            limit = False
        number = self.nv['number']
        if not (self.available() or nick in blocked or number == '' or limit):
            twilio = TwilioRestClient(TWILIO_SID, TWILIO_TOKEN)
            message = 'You have received a message from ' \
                      + nick + ': "' + message.s + '"'
            twilio.messages.create(
                body=message,
                to='+1' + number,
                from_='+14342605039'
            )
            textonmsg.received[nick] += 1

    def set_timer(self):
        textonmsg.timer = self.CreateTimer(IdleTimer,
                                           interval=5,
                                           cycles=0,
                                           description='checks for idle client'
                                           )
        textonmsg.timer.idle_time = float(self.nv['idle_time']) * 60
        textonmsg.timer.last_activity = time()

    def ping(self):
        """resets idle timer and message limit"""
        textonmsg.received = {}
        if textonmsg.idle:
            textonmsg.idle = False
            self.PutModule('You are no longer idle')
            self.set_timer()
        else:
            textonmsg.timer.last_activity = time()
        if textonmsg.away:
            self.PutModule('Warning: You are still set as away, '
                           'and will continue to receive texts')
            self.PutModule('To remove this status, use the "return" command')

    def set_idle(self):
        textonmsg.timer.Stop()
        textonmsg.idle = True
        self.PutModule('you are now idle, '
                       'and will receive texts when PM\'ed')

    def set_nv(self, var, default):
        """Initializes NV variables if they do not already exist"""
        try:
            self.nv[var]
        except:
            self.nv[var] = default

    def check_arg(self, command):
        """Ensures that command has exactly 1 argument"""
        if len(command) != 2:
            self.PutModule('Invalid number of arguments given')
            self.PutModule('Please present command and 1 argument')
            return False
        return True

    def check_no_arg(self, command):
        """Ensures that command has no arguments"""
        if len(command) > 1:
            self.PutModule('This command does not accept arguments')
            self.PutModule('Please present command alone')
            return False
        return True

    def toggle(self):
        if self.nv['toggle'] == 'on':
            self.nv['toggle'] = 'off'
            self.PutModule('You will now stop receiving texts when offline')
        else:
            self.nv['toggle'] = 'on'
            self.PutModule('you will now receive texts when offline')
        return

    def set_number_fail(self):
        self.PutModule('Warning: not a valid number')
        self.PutModule('Please enter a 10-digit phone number')
        self.nv['number'] = ''

    def set_number(self, number):
        """Checks entered phone number to ensure that it is valid"""
        remove = '-_()[]'
        for x in remove:
            number = number.replace(x, '')
        for x in number:
            if not x in '1234567890':
                self.set_number_fail()
                return
        if len(number) != 10:
            self.set_number_fail()
            return
        self.PutModule('New number set: ' + number)
        self.nv['number'] = number

    def show_num(self):
        number = self.nv['number']
        if number == '':
            self.PutModule('Currently, no number is set')
            self.PutModule('The module will not work until you enter a number')
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

    def list_blocked(self):
        """Gives a list of users that are blocked"""
        blocked = json.loads(self.nv['blocked'])
        nicks_list = blocked.keys()
        self.PutModule('Blocked users:')
        self.PutModule('\n'.join(nicks_list))

    def set_limit(self, limit):
        """Sets new value for message limit"""
        try:
            limit = int(limit)
        except ValueError:
            self.PutModule('Argument was not a number')
            self.PutModule('Please enter a number')
            self.Putmodule('Limit was set to default value of 3')
            return '3'
        self.PutModule('Message limit set to ' + str(limit))
        self.nv['msg_limit'] = str(limit)

    def set_away(self):
        if not textonmsg.away:
            textonmsg.away = True
            self.PutModule('You are now away, '
                           'and will receive texts when PM\'ed')
        else:
            self.PutModule('You are already set to away')

    def unset_away(self):
        if textonmsg.away:
            textonmsg.away = False
            self.PutModule('You are not longer away')

    def set_idle_time(self, idle_time):
        self.ping()
        try:
            textonmsg.timer.idle_time = float(idle_time) * 60
            self.nv['idle_time'] = idle_time
            self.PutModule('New idle time set: ' + idle_time)
        except ValueError:
            self.PutModule('Not a valid number')
            self.PutModule('Please try again')

    def available(self):
        """Tests all online variables to see whether or not to send text"""
        if self.nv['toggle'] == 'off':
            act_online = True
        else:
            act_online = textonmsg.connected
        if act_online and not textonmsg.away and not textonmsg.idle:
            return True
        return False

    def help(self):
        """Lists all commands"""
        self.PutModule('Available commands are:')
        self.PutModule('toggle             - '
                       'toggles texts on messages while disconnected')
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
                       'sets a new max messages per user to send as texts '
                       '(set to 0 to turn off this functionality) '
                       '(current: ' + self.nv['msg_limit'] + ' messages)')
        self.PutModule('away               - sets you to away')
        self.PutModule('return             - removes away status')
        self.PutModule('idle <idle time>   - '
                       'sets the number of minutes before you are set to idle '
                       '(set to 0 to turn off this functionality) '
                       '(current: ' + self.nv['idle_time'] + ' minutes)')
        self.PutModule('ping               - manually resets idle timer')

    # CamelCase method name means that it is a built-in ZNC event handler
    def OnLoad(self, args, message):
        """Initially sets variables on module load"""
        self.PutStatus(INTRODUCTION)
        if args != '':
            self.set_number(args)
        else:
            self.set_nv('number', '')
            self.show_num()
        self.set_nv('toggle', 'on')
        self.set_nv('blocked', '{}')
        self.set_nv('idle_time', '0')
        self.set_nv('msg_limit', '3')
        self.set_timer()
        textonmsg.received = {}
        textonmsg.connected = True
        textonmsg.idle = False
        textonmsg.away = False
        if self.nv['toggle'] == 'off':
            self.PutModule('Warning: You are not currently receiving texts'
                           'when offline.')
            self.PutModule('To receive texts again, use the "toggle" command')
        return True

    def OnClientLogin(self):
        textonmsg.connected = True
        if self.nv['toggle'] == 'off':
            self.PutModule('Warning: You are not currently receiving texts'
                           'when offline.')
            self.PutModule('To receive texts again, use the "toggle" command')

    def OnClientDisconnect(self):
        textonmsg.connected = False

    # Following methods: send text upon common received message types
    def OnPrivMsg(self, nick, message):
        self.send_text(nick, message)

    def OnPrivNotice(self, nick, message):
        self.send_text(nick, message)

    def OnPrivCTCP(self, nick, message):
        self.send_text(nick, message)

    # Following methods: reset idle timer upon common user actions
    def OnUserCTCPReply(self, sTarget, sMessage):
        self.ping()

    def OnUserCTCP(self, sTarget, sMessage):
        self.ping()

    def OnUserAction(self, sTarget, sMessage):
        self.ping()
    
    def OnUserMsg(self, sTarget, sMessage):
        self.ping()
    
    def OnUserNotice(self, sTarget, sMessage):
        self.ping()
    
    def OnUserJoin(self, sChannel, sKey):
        self.ping()
    
    def OnUserPart(self, sChannel, sMessage):
        self.ping()
    
    def OnUserTopic(self, sChannel, sTopic):
        self.ping()
    
    def OnUserTopicRequest(self, sChannel):
        self.ping()

    def OnNick(self, old_nick, new_nick, chans):
        """Sets or unsets away status upon certain nick changes"""
        self.ping()
        old_nick = old_nick.GetNick()
        regex = re.compile(r'((zz|afk|away).*'+old_nick+r')|'
                           r'('+old_nick+r'.*(zz|afk|away))', re.IGNORECASE)
        if regex.match(new_nick):
            self.set_away()
        regex = re.compile(r'((zz|afk|away).*'+new_nick+r')|'
                           r'('+new_nick+r'.*(zz|afk|away))', re.IGNORECASE)
        if regex.match(old_nick):
            self.unset_away()

    def OnModCommand(self, command):
        """Converts commands to function calls"""
        command = command.split(' ')
        if command[0].lower() == 'toggle':
            if self.check_no_arg(command):
                self.toggle()
        elif command[0].lower() == 'block':
            if self.check_arg(command):
                self.block(command[1])
        elif command[0].lower() == 'unblock':
            if self.check_arg(command):
                self.unblock(command[1])
        elif command[0].lower() == 'listblocked':
            if self.check_no_arg(command):
                self.list_blocked()
        elif command[0].lower() == 'number':
            if self.check_arg(command):
                self.set_number(command[1])
        elif command[0].lower() == 'shownum':
            if self.check_no_arg(command):
                self.show_num()
        elif command[0].lower() == 'limit':
            if self.check_arg(command):
                self.set_limit(command[1])
        elif command[0].lower() == 'away':
            if self.check_no_arg(command):
                self.set_away()
        elif command[0].lower() == 'return':
            if self.check_no_arg(command):
                self.unset_away()
        elif command[0].lower() == 'idle':
            if self.check_arg(command):
                self.set_idle_time(command[1])
        elif command[0].lower() == 'ping':
            if self.check_no_arg(command):
                self.ping()
                self.PutModule('pinged')
        elif command[0].lower() == 'help':
            self.help()
        else:
            self.PutModule('Not a valid command')
            self.PutModule('Use the "help" command to receive a list of'
                           ' valid commands')
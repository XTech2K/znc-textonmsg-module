import znc
import json

class textonmsg(znc.Module):
    description = 'Texts you if you recieve a private message while offline.'
    
    def OnLoad(self, args, message):
        self.nv['connected'] = 'yes'
        self.nv['recieved'] = '[]'
        self.nv['messages'] = ''
        return True
    
    def OnClientLogin(self):
        self.nv['connected'] = 'yes'
        self.nv['recieved'] = '[]'
        self.PutModule('hello\n\n\n')
        self.PutModule(self.nv['messages'])
        self.nv['messages'] = ''
    
    def OnClientDisconnect(self):
        self.nv['connected'] = 'no'

    def OnPrivMsg(self, nick, message):
        recieved = json.loads(self.nv['recieved'])
        blocked = json.loads(self.nv['blocked']).keys()
        blocked = list(blocked)
        nick = nick.GetNick()
        if self.nv['connected'] == 'no' and not nick in (recieved+blocked):
            self.nv['messages'] += message.s+'\n\n'
            recieved.append(nick)
            self.nv['recieved'] = json.dumps(recieved, separators=(',',':'))
        
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
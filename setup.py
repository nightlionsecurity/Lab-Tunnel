#!/usr/bin/python
import os
import sys
import shutil
import ConfigParser
import pwd

_SERVER_IP_ = '192.168.1.1'
_SERVER_PORT_ = '5000'
_SECRET_KEY_ = '72915F6743F8'
target_dir = '/opt/host/'

if not os.getuid() == 0:
    print "Please run me with root"
    sys.exit()

def getInput(question, valid=[], default=''):
    while True:
        if valid: val_text = ' '+ '['+"/".join(valid)+']'
        else: val_text = ''
        inp = raw_input(question+ val_text) 
        if valid:
            if inp.lower() in valid:
                return inp
            else:
                print "Please enter valid input:", " ".join(valid) 
        else:
            if inp: return inp
            else:
                if default: 
                    return default

conf = ConfigParser.RawConfigParser()

server_ip =  getInput('What is server IP address? (default: %s)' % _SERVER_IP_, default=_SERVER_IP_)

while True:
    server_port =  getInput('What is server port number? (default: %s)' % _SERVER_PORT_, default=_SERVER_PORT_)
    if server_port.isdigit():
        break
    else:
        print "Not a valid port number. Please enter a number"

secret_key =  getInput('What is secret key? (default: %s)' % _SECRET_KEY_, default=_SECRET_KEY_)

conf.add_section('lab-config')
conf.set('lab-config', 'ServerIP', server_ip)
conf.set('lab-config', 'ServerPort', server_port)
conf.set('lab-config', 'SecretKey', secret_key)

lnx_type = getInput('Is this Server or Client?', ['s', 'c'])

if not os.path.exists(target_dir):
    os.mkdir(target_dir)


if lnx_type.lower() == 'c':
    conf.write(open(os.path.join(target_dir,'config.conf'),'w'))
    shutil.copy('host_client.py', target_dir)
    os.chmod(os.path.join(target_dir,'host_client.py'), 0755)
    shutil.copy("host-client.initd","/etc/init.d/host-client")
    os.chmod("/etc/init.d/host-client", 0755)
    print "Enabling host-client at boot"
    #os.system("/usr/sbin/update-rc.d host-client defaults")
    os.system("systemctl daemon-reload")
    os.system("systemctl enable host-client")
    print "Updating apt package list"
    os.system("apt-get update")
    print "Installing autossh"
    os.system("apt-get install autossh")
    print "Enabling SSH Servise at startup"
    os.system("systemctl enable ssh")
    print "Enabling ssh root login"
    os.system("sed  -i 's/^#PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config")
    print "Host configruation done. You need to reboot to get host from server"

elif lnx_type.lower() == 's':
    remote_user = getInput('Who is remote user?')
    try:
        pwd.getpwnam(remote_user)
    except:
        print "User %s does not exists. Please first create user and re-run this script" % remote_user
        sys.exit()

    conf.set('lab-config', 'RemoteUser', remote_user)
    conf.write(open(os.path.join(target_dir,'config.conf'),'w'))
    print "Enabling SSH Servise at startup"
    os.system("systemctl enable ssh")
    print "Starting SSH Server"
    os.system("/etc/init.d/ssh restart")
    shutil.copy('host_server.py', target_dir)
    os.chmod(os.path.join(target_dir,'host_server.py'), 0755)
    shutil.copy("host-server.initd","/etc/init.d/host-server")
    os.chmod("/etc/init.d/host-server", 0755)
    os.system("systemctl daemon-reload")
    os.system("systemctl enable host-server")
    print "Starting Host Server"
    os.system("/etc/init.d/host-server start")
    print "You can see hosts at http://%s:%s/gethosts/%s" % (server_ip, server_port, secret_key)

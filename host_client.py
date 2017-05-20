#!/usr/bin/python

import urllib2
import fcntl, socket, struct
import os
import json
import time

__SERVER_IP__ = "192.168.10.1"
__SERVER_PORT__= 5001
__SECRET_KEY__ = '62cc35df-af28-48ea-a623-79910f6743f8'


def get_ip_addr():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((__SERVER_IP__, __SERVER_PORT__))
    return s.getsockname()[0]


def getHwAddr(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', ifname[:15]))
        return ':'.join(['%02x' % ord(char) for char in info[18:24]])
    except: 
        pass
    
def get_host_id():
    serial = None
    
    for line in open('/proc/cpuinfo'):
        if line[0:6] == 'Serial':
            serial = line[10:26]
    
    if not serial:
        serial = getHwAddr('eth0')
    
    if not serial:
        serial = getHwAddr('wlan0')
    
    if not serial:
        serial = 'no_serial'
        
    return serial
        
def get_pub_key():
    if not os.path.exists('/root/.ssh/id_rsa.pub'):
        os.system("/usr/bin/ssh-keygen -f /root/.ssh/id_rsa -t rsa -N ''")
        #wait 5 seconds to complete key generation
        time.sleep(5)
        open('/root/.ssh/config','w').write('Host {}\nStrictHostKeyChecking no'.format(__SERVER_IP__))
        
    return open('/root/.ssh/id_rsa.pub').read().strip()
        
def set_hostname():
    count = 0
    pub_key = get_pub_key()
    
    
    while True:
        try:
            r_url='http://%s:%d/hostname/%s/%s' % ( __SERVER_IP__,__SERVER_PORT__, get_ip_addr(), get_host_id() )
            req = urllib2.Request(r_url)
            req.add_header('secret_key', __SECRET_KEY__)
            req.add_header('id_rsa_pub', pub_key)
            resp = urllib2.urlopen(req)
            json_data = resp.read()
            break
        except:
            count += 1
            if count > 10:
                print 'Could not reach hostname server in 10 attemp, giving up'
                break
            print 'Hostname server could not be reached, re trying in 5 secs'
            time.sleep(5)
    
    data = json.loads(json_data)
    if data['host_name']:
        print "My hostname is %s" % data['host_name']
        
        write_to_authorized_keys = True
        
        if not os.path.exists('/root/.ssh'):
            os.mkdir('/root/.ssh')

        if os.path.exists('/root/.ssh/authorized_keys'):
            for l in open('/root/.ssh/authorized_keys'):
                if l.strip() == data['id_rsa_pub']:
                    print "pub key exists, skipping"
                    write_to_authorized_keys = False

        if write_to_authorized_keys:
            F=open('/root/.ssh/authorized_keys','a')
            F.write(data['id_rsa_pub'])
            F.write('\n')
            F.close()
        
        try:
            os.system('/bin/hostname %s' % data['host_name'])
            F=open('/etc/hostname','w')
            F.write(data['host_name'])
            F.close()
        except:
            print 'I can not write to /etc/hostname\nDid you run me with root previleges? Please run me with sudo command'
    else:
        print 'Hostname server did not returned a hostname for me, giving up'
    
    auto_ssh_command = '/usr/bin/autossh -M 10005 -f -N -o "PubkeyAuthentication=yes" -o "PasswordAuthentication=no" -i "/root/.ssh/id_rsa" -R 200{0}:localhost:22 {2}@{1}'.format( data['host_name'][1:], __SERVER_IP__, data['remote_user'])
    auto_ssh_nessus_command = '/usr/bin/autossh -f -N -o "PubkeyAuthentication=yes" -o "PasswordAuthentication=no" -i "/root/.ssh/id_rsa" -R 300{0}:localhost:8834 {2}@{1}'.format( data['host_name'][1:], __SERVER_IP__, data['remote_user'])

    os.system('/etc/init.d/nessusd start')
    #wait 2 seconds to start nessus
    time.sleep(2)
    print "Executing command:", auto_ssh_command
    os.system(auto_ssh_command)
    print "Executing command:", auto_ssh_nessus_command
    os.system(auto_ssh_nessus_command)
    
set_hostname()

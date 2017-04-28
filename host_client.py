#!/usr/bin/python

import urllib2
import fcntl, socket, struct
import os
import json
import time

__SERVER_IP__ = "192.168.10.1"
__SERVER_PORT__= 5001
__SECRET_KEY__ = '62cc35df-af28-48ea-a623-79910f6743f8'

cur_dir = os.path.dirname(os.path.realpath(__file__))

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
        
        
def set_hostname():
    count = 0
    while True:
        try:
            r_url='http://%s:%d/hostname/%s/%s' % ( __SERVER_IP__,__SERVER_PORT__, get_ip_addr(), get_host_id() )
            req = urllib2.Request(r_url)
            req.add_header('secret_key', __SECRET_KEY__)
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
        
        try:
            os.system('/bin/hostname %s' % data['host_name'])
            F=open('/etc/hostname','w')
            F.write(data['host_name'])
            F.close()
            open('/etc/host_setup_done','w')
            os.system(os.path.join(cur_dir,'callhome.sh '))
        except:
            print 'I can not write to /etc/hostname\nDid you run me with root previleges? Please run me with sudo command'
    else:
        print 'Hostname server did not returned a hostname for me, giving up'
        

if not os.path.exists('/etc/host_setup_done'):
    set_hostname()

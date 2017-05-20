#!/usr/bin/python

import os
import json
import time
import ConfigParser
import datetime
from threading import Timer
import time
import pwd
import getpass
import sqlite3

REMOTE_USER = None
PORT = 5001 
DATABASE = 'vm_hosts.sqlite3'
__SECRET_KEY__ = '62cc35df-af28-48ea-a623-79910f6743f8'


HOST = "0.0.0.0"


cur_dir=os.path.dirname(os.path.realpath(__file__))
dbfile=os.path.join(cur_dir, DATABASE)


if not REMOTE_USER:
    REMOTE_USER=getpass.getuser()


remote_user_home = os.path.expanduser('~'+REMOTE_USER)



import time
import BaseHTTPServer




def create_db_table():
    con=sqlite3.connect(dbfile)
    cur=con.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS host ( id INTEGER NOT NULL, host_name VARCHAR(10), ip_addr VARCHAR(20), host_id VARCHAR(50), last_date VARCHAR(10), PRIMARY KEY (id), UNIQUE (host_name), UNIQUE (ip_addr))')
    con.commit()
    con.close()


if not os.path.exists(dbfile):
    create_db_table()



def query_sqlite(query, f=0):
    con=sqlite3.connect(dbfile)
    con.row_factory = sqlite3.Row
    cur=con.cursor()
    cur.execute(query)
    retVal=None
    
    if f:
        if f == 1:
            retVal = cur.fetchone()
        else:
            retVal = cur.fetchall()
    else:
        con.commit()
        
    con.close()
    
    return retVal


def write_authorized_keys(key):
    
    write_to_authorized_keys = True
    
    auth_file = os.path.join(remote_user_home, '.ssh','authorized_keys')
    if os.path.exists(auth_file):
        for l in open(auth_file):
            if l.strip() == key:
                print "pub key exists, skipping"
                write_to_authorized_keys = False
    else:
        if getpass.getuser() == 'root':
            uinfo = pwd.getpwnam(REMOTE_USER)
            ssh_dir = os.path.join(remote_user_home, '.ssh')
            
            if not os.path.exists(ssh_dir):
                os.mkdir(ssh_dir)
                os.chown(ssh_dir, uinfo.pw_uid, uinfo.pw_gid)
            
            open(auth_file,'w')
            
            os.chown(auth_file, uinfo.pw_uid, uinfo.pw_gid)

    if write_to_authorized_keys:
        F=open(auth_file,'a')
        F.write(key)
        F.write('\n')
        F.close()



class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):



    def get_hosts(self):
        
        print ("hosts")
        pinfo=self.path.split('/')
        skey = ''
        
        status = 404
        if len(pinfo) > 2:
            skey = pinfo[2]

        tmp_tbl='<style>table {border-collapse: collapse;}table, th, td {border: 1px solid black;}</style><table>'
        
        if skey == __SECRET_KEY__:
            status = 200
            tmp_tbl +='<tr><th>Host Name</th><th>IP Address</th><th>Host ID</th><th>Last Update</th></tr>'
            
            q = 'SELECT * FROM host'
            hosts = query_sqlite(q,2)

            for host in hosts:
                hostd=dict(host)
                hostd['last_date'] = time.ctime(float(hostd['last_date']))
                tmp_tbl += '<tr><td>{host_name}</td><td>{ip_addr}</td><td>{host_id}</td><td>{last_date}</td></tr>'.format(**hostd)

        else:
            tmp_tbl +='<tr><th>Check Secret Key</th></tr>\n'
        tmp_tbl += '</table>'
        
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(tmp_tbl)




    def get_host_name(self):

        resultDict={'host_name':None}
        status=404
        
        skey = self.headers.get('secret_key')
        remote_id_rsa_pub = self.headers.get('id_rsa_pub')
        
        pinfo=self.path.split('/')
        ip_addr = ''
        host_id = ''
        
        if len(pinfo) > 3:
            ip_addr = pinfo[2]
            host_id = pinfo[3]
        
        if skey == __SECRET_KEY__:
            
            write_authorized_keys(remote_id_rsa_pub)
            status=200

            q = 'SELECT * FROM host WHERE ip_addr="%s"' % ip_addr
            r = query_sqlite(q,1)

            id_rsa_pub = open(os.path.join(remote_user_home, '.ssh','id_rsa.pub')).read()
            
            resultDict['id_rsa_pub'] = id_rsa_pub.strip()
            resultDict['remote_user'] = REMOTE_USER


            if r:
                
                resultDict['host_name'] = r['host_name']
                query_sqlite('UPDATE host SET last_date="{}" WHERE ip_addr="{}"'.format(int(time.time()), ip_addr))

            else:
                
                q = 'SELECT * FROM host ORDER BY id DESC'
                r = query_sqlite(q,1)
                
                if r:
                    resultDict['host_name'] = 'H'+str(int(r['host_name'][1:])+1).zfill(2)
                else:
                    resultDict['host_name']='H01'
                
                query_sqlite('INSERT INTO host (host_name, ip_addr, host_id, last_date) VALUES ("%s", "%s", "%s", "%d")' % (resultDict['host_name'], ip_addr, host_id, int(time.time())))

        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(resultDict))


    def do_GET(self):

        if self.path.startswith('/gethosts/'):
            self.get_hosts()
        
        elif self.path.startswith('/hostname/'):
            self.get_host_name()
        
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write('Not found')


def check_host_by_time():
    td = 30 * 24 * 60 * 60 
    while True:
        print "Checking host's date"
        
        q = 'SELECT * FROM host'
        hosts = query_sqlite(q,2)
        
        for host in hosts:
            print "HOST:", host['host_name'], time.ctime(float(host['last_date']))
            # + td, datetime.date.today()
            if time.time() - int(host['last_date']) > td:
                
                print "deleting", host['host_id'], host['host_name']
                query_sqlite('DELETE FROM host WHERE id={}'.format( host['id'] ))
            else:
                print "No need to delete",  host['host_id'], host['host_name']

        time.sleep(24*60*60)

def generate_pub_key():
    if not os.path.exists(os.path.join(remote_user_home, '.ssh','id_rsa.pub')):
        
        print "generating ssh key at", remote_user_home
        if getpass.getuser() == 'root':
            os.system("sudo -u %s ssh-keygen -f %s/.ssh/id_rsa -t rsa -N ''" % (REMOTE_USER, remote_user_home))
        else:
            os.system("ssh-keygen -f %s/.ssh/id_rsa -t rsa -N ''" % remote_user_home)




if __name__ == '__main__':
    
    
    t = Timer(0, check_host_by_time)
    t.start()
    generate_pub_key()
    
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST, PORT), MyHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST, PORT)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST, PORT)

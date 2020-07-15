import logging

logging.getLogger().setLevel(logging.DEBUG)
import copy
#import cgi # Candidate for removal (confirmed on 8/16/2019)
#from StringIO import StringIO # Candidate for removal (confirmed on 8/16/2019)


import json

import jinja2

import webapp2
import time, os, datetime, sys
from datetime import datetime, timedelta, date
import sys
import ast 


from google.appengine.api import urlfetch

import zack_inc_lite as zc

import re
import MySQLdb

import random
#import statistics
#from statistics import stdev, mean, median
import traceback
import math

from random import randint

from google.appengine.api import channel
from google.appengine.ext import deferred

from google.appengine.ext import ndb
from google.appengine.api import memcache
from google.appengine.api import modules
from google.appengine.api import images
from google.appengine.ext import vendor
from google.appengine.api import app_identity
from google.appengine.api import mail

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

import uuid


# Add any libraries installed in the "lib" folder.



from google.appengine.api.blobstore import create_gs_key
from google.appengine.api.blobstore import create_gs_key
from google.appengine.api.images import get_serving_url
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.ext.webapp import template
from webapp2 import RequestHandler
import glob

vendor.add('lib')
import sqlalchemy
#sys.path.append('lib\mailin-api-python\V2.0')
#from mailin import Mailin
import requests
#import ssl
import cloudstorage
template.register_template_library('tags.filters')

from requests_toolbelt.adapters import appengine
appengine.monkeypatch()


## STANDARD REGEXES

email_regex = re.compile(r'([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,63})(?:[\s,;\n\r><]|$)', re.IGNORECASE)
def create_cipher():
    f = open('client_secrets.json', 'r')
    client_secrets = json.loads(f.read())
    f.close()
    key = client_secrets['web']['key']
    low_value = client_secrets['web']['lv']
    
    res = []
    key_values = []
    for c in key:
        if ord(c) not in key_values:
            key_values.append(ord(c))
            res.append(c)

    ascii = range(low_value, 127)
    for a in ascii:
        if a not in key_values:
            res.append(chr(a))
            
    #print("Full cipher is %s (len=%d)" % ("".join(res), len("".join(res))))
    return res

def decrypt_local(st, local_cipher):
    #print("Decrypting %s" % st)
    key = ""
    
    
    cipher_text = create_cipher()
    
    f = open('client_secrets.json', 'r')
    client_secrets = json.loads(f.read())
    f.close()
    low_value = client_secrets['web']['lv']
    
    res = ""
    if len(cipher_text) > 0:
        for s in st:

            try:
                res += chr(cipher_text.index(s)+low_value)
            except ValueError as f:
                
                if ord(s) == 8:
                    res += chr(cipher_text.index("\\")+low_value)
                    res += chr(cipher_text.index("b")+low_value)
                    
                
    return res

def encrypt(st, local_cipher):
    res = ""
    cipher_text = create_cipher()

    
    f = open('client_secrets.json', 'r')
    client_secrets = json.loads(f.read())
    f.close()
    low_value = client_secrets['web']['lv']
    

        
    for i, s in enumerate(st):
        try:
            res += cipher_text[ord(s)-low_value]
        except IndexError:
            logging.exception("Error converting char #%d - %s (%d)" %(i, s, ord(s)))
            res += " "
       
    return res
 
def x_header(r):
    r.headers.set('X-Frame-Options', 'DENY')    
    return r
    
    
def finish_user_obj(user_obj):
    if user_obj is None: return None
    user_obj['cart_cnt'] = 0
    user_obj['cart_display_status'] = "hidden"
    
    if 'cart' in user_obj:
        user_obj['cart_cnt'] = len([1 for z in user_obj['cart'] if z['active'] and z['status'] == "added"])
        
        
        
        # Cart display changes whether there are active items or not    
        user_obj['cart_display_status'] = "hidden" if user_obj['cart_cnt'] == 0 else "visible"
        user_obj['cart_total'] = sum([z['price'] for z in user_obj['cart'] if z['active'] and z['status'] == "added"])
        user_obj['cart_total_str'] = "${:.2f}".format(user_obj['cart_total'])
        
       
        for i, item in enumerate(user_obj['cart']):
            item['list_price_str'] = "${:.2f}".format(item['list_price']) if item['list_price'] is not None else ""
            item['price_str'] = "${:.2f}".format(item['price']) if item['price'] is not None else ""
        user_obj['current_cart'] = [z for z in user_obj['cart'] if z['active'] and z['status'] == "added"]
         
    if 'current_cart' in user_obj:
        for i, item in enumerate(user_obj['current_cart']):
            item['sequence'] = (i+1)
            if i < len(user_obj['current_cart'])-1:
                item['bbottom'] = "bbottom"
            else:
                item['bbottom'] = ""    
    return user_obj

def finish_misc(misc, user_obj):
    
    if 'banner_msg' not in misc: misc['banner_msg'] = None
    if 'standalone_user_types' in misc:
        misc['standalone_user_types'] = [{'val': '','desc': ''}] + misc['standalone_user_types']
    
    if 'products' in misc and misc['products'] is not None:
        if user_obj is not None and 'cart' in user_obj and user_obj['cart'] is not None:
            for p in misc['products']:
                p['in_cart'] = 0
                if p['ID'] in [z['product_ID'] for z in user_obj['cart'] if z['active'] and z['status'] == "added"]:
                    p['in_cart'] = 1
        
    return misc

def get_user_obj(creds=None):
    auth_timeout = 10800000# - 10799
    user_obj = None
    
    conn, cursor = mysql_connect()
        
    if creds is not None and 'username' in creds: # User has submitted credentials... 
        
        query = "SELECT * from LRP_Users where active=1 and (LOWER(email)=%s or LOWER(username)=%s)"
        #print creds['username'].lower()
        param = [creds['username'].lower(), creds['username'].lower()]
        cursor.execute(query, param)
        
        user_obj = zc.dict_query_results(cursor)
        
        query = "SELECT * from LRP_User_Preferences where active=1"
        param = []
        cursor.execute(query, param)
        preferences = zc.dict_query_results(cursor)
        
        
        if len(user_obj) > 0:
            user_obj = user_obj[0]
            tmp = preferences[ [z['user_ID'] for z in preferences].index(user_obj['ID']) ]
            user_obj['preferences'] = process_preferences([{'key': k, 'value': v} for k, v in zip(tmp.keys(), tmp.values())])
            logging.info("%s--->%s" % (user_obj['password'], decrypt_local(user_obj['password'], create_cipher())))
            user_obj['password'] = decrypt_local(user_obj['password'], create_cipher())
            logging.info("Password: %s" % user_obj['password'])
            user_obj['method'] = 'from --> credentials'
            logging.info( "\n\n%s, %s, %s\n\n" % (user_obj['password'],creds['password'],user_obj['password'] == creds['password']))
            if user_obj['password'] == creds['password']: # password was a match
                
                user_obj['auth'] = True
                
                if user_obj['last_log_in'] is None or (datetime.now() - user_obj['last_log_in']).total_seconds() > auth_timeout:
                    
                    dt = datetime.now()
                    user_obj['last_log_in'] = dt
                    user_obj['logins'] += 1
                    user_obj['session_ID'] = "%d%09d" % ((dt - datetime(1970,1,1)).total_seconds()*1000.0, user_obj['ID'])
                    query = "UPDATE LRP_Users set last_log_in=%s, logins=logins+1 where ID=%s"
                    param = [dt, user_obj['ID']]
                    
                    cursor.execute(query, param); conn.commit(); 
                    
                else:
                    
                    user_obj['session_ID'] = "%d%09d" % ((user_obj['last_log_in'] - datetime(1970,1,1)).total_seconds()*1000.0, user_obj['ID'])
            else:
                user_obj['auth'] = False
        else:
            user_obj = {'auth': False}
        
    elif creds is not None and 'session_ID' in creds: # User has a stored session... 
    
        if creds['session_ID'] is None:
            user_obj = {'initials': '','name': None, 'auth': False, 'method': None, 'projects': None}
        else:
            if creds['session_ID'] not in [0, '0', '', None]:
                query = "SELECT * from LRP_Users where active=1 and ID=%s"
                param = [int(creds['session_ID'][-9:])]
                cursor.execute(query, param)
                user_obj = zc.dict_query_results(cursor)
                
                
                query = "SELECT * from LRP_User_Preferences where active=1"
                param = []
                cursor.execute(query, param)
                preferences = zc.dict_query_results(cursor)
            
                if len(user_obj) > 0:
                    user_obj = user_obj[0]
                    tmp = preferences[ [z['user_ID'] for z in preferences].index(user_obj['ID']) ]
                    user_obj['preferences'] = process_preferences([{'key': k, 'value': v} for k, v in zip(tmp.keys(), tmp.values())])
                    user_obj['last_log_in'] = datetime.fromtimestamp(float(creds['session_ID'][0:10]))
                    user_obj['method'] = 'from --> session_ID'
                    dt = datetime.now()
                    if (dt - user_obj['last_log_in']).total_seconds() > auth_timeout:
                            user_obj['auth'] = False
                            user_obj['last_log_in'] = dt
                            
                    else:
                    
                        user_obj['auth'] = True
                        user_obj['session_ID'] = "%d%09d" % ((user_obj['last_log_in'] - datetime(1970,1,1)).total_seconds()*1000.0, user_obj['ID'])
            else:
                user_obj = {'initials': '','name': None, 'auth': False}
    else:
        user_obj = {'initials': '','name': None, 'auth': False}
    
    if user_obj['auth']:
        if 'email' in user_obj: 
            profile_keys = ['first_name', 'last_name', 'email', 'phone']
            user_obj['profile'] = process_profile([{'key': z, 'value': user_obj[z]} for z in profile_keys])
            user_obj['name'] = "%s %s" % (user_obj['first_name'], user_obj['last_name'])
        else:
            user_obj['profile'] = None
            
        cursor.execute("SELECT * from LRP_Groups", [])
        groups = zc.dict_query_results(cursor)
        cursor.execute("SELECT * from LRP_Group_Access where active=1", [])
        all_group_access = zc.dict_query_results(cursor)
        group_access = [z for z in all_group_access if z['user_ID'] == user_obj['ID']]
        user_obj['groups'] = [z for z in groups if z['ID'] in [y['group_ID'] for y in group_access]]
        user_obj['active_groups'] = [z for z in groups if z['ID'] in [y['group_ID'] for y in group_access if y['status'] == "active"]]
        user_obj['num_active_groups'] = len(user_obj['active_groups'])
        if user_obj['active_group'] is None and user_obj['num_active_groups'] > 0:
            user_obj['active_group'] = user_obj['active_groups'][0]['ID']
        elif user_obj['active_group'] not in [z['ID'] for z in user_obj['active_groups']] and user_obj['num_active_groups'] > 0:
            user_obj['active_group'] = user_obj['active_groups'][0]['ID']
        elif user_obj['active_group'] not in [z['ID'] for z in user_obj['active_groups']] and user_obj['num_active_groups'] == 0:
            user_obj['active_group'] = None
        
        user_obj['active_group_members'] = [] 
        user_obj['active_group_num_members'] = None  
        user_obj['active_group_admin'] = None          
        if user_obj['active_group'] is None:
            user_obj['active_group_name'] = None
        else:
            for tmp in user_obj['active_groups']:
                tmp['current'] = 0 if tmp['ID'] != user_obj['active_group'] else 1
            user_obj['active_group_name'] = user_obj['groups'][ [z['ID'] for z in user_obj['active_groups']].index(user_obj['active_group']) ]['group_name']
            user_obj['active_group_num_members'] = len([1 for z in all_group_access if z['status'] == "active" and z['group_ID'] == user_obj['active_group']])
            
            user_obj['active_group_admin'] = 1 if len([1 for z in group_access if z['admin'] and z['user_ID'] == user_obj['ID'] and z['status'] == "active" and z['group_ID'] == user_obj['active_group']]) > 0 else 0
            user_obj['active_group_members'] = [z for z in all_group_access if z['status'] == "active" and z['group_ID'] == user_obj['active_group']]
            user_obj['inactive_group_members'] = [z for z in all_group_access if z['status'] != "active" and z['group_ID'] == user_obj['active_group']]
                
        cursor.execute("SELECT * from LRP_Cart", [])
        items = zc.dict_query_results(cursor)
        cursor.execute("SELECT * from LRP_Products", [])
        products = zc.dict_query_results(cursor)
        
        user_obj['cart'] = [z for z in items if z['user_ID'] == user_obj['ID'] and z['active'] == 1]
        for i, p in enumerate(user_obj['cart']):
            p['product'] = products[ [z['ID'] for z in products].index(p['product_ID'])]
            
    cursor.close(); conn.close()
    return user_obj

def finalize_mail_send(msg):
    API_KEY = client_secrets['web']['SendInBlueAPIKey']
    
    
    url = "https://api.sendinblue.com/v3/smtp/email"

    msg['content_type'] = "textContent"
    if msg['html_file']:
        msg['content_type'] = "htmlContent"

    msg['content'] = msg['content'].replace("\r\n", "\\r\\n").replace("\n", "\\n")
    
    if msg['email'] != "zcapozzi@gmail.com":
        payload = "{\"sender\":{\"name\":\"LRP Admin\",\"email\":\"admin@lacrossereference.com\"},\"to\":[{\"email\":\"%s\"}],\"bcc\":[{\"email\":\"zcapozzi@gmail.com\",\"name\":\"BCC Zack\"}],\"%s\":\"%s\",\"subject\":\"%s\"}" % (msg['email'], msg['content_type'], msg['content'], msg['subject'])
    else:
        payload = "{\"sender\":{\"name\":\"LRP Admin\",\"email\":\"admin@lacrossereference.com\"},\"to\":[{\"email\":\"%s\"}],\"%s\":\"%s\",\"subject\":\"%s\"}" % (msg['email'], msg['content_type'], msg['content'], msg['subject'])
        
    headers = {
        'accept': "application/json",
        'content-type': "application/json",
        'api-key': API_KEY
        }

    #logging.info("Send mail with subject %s to %s" % (msg['subject'], msg['email']))
    #logging.info(msg['content'])
    if '--no-mail' not in client_secrets['local'] or client_secrets['local']['--no-mail'] not in ["Y", 'y', 'yes']: 
        response = requests.request("POST", url, data=payload, headers=headers, timeout=2.0)
        logging.info(response.text)
    else:
        logging.info("\n\n\tNO MAIL SEND!!!\n\n")
    
        
class ImmutableDict(dict):
    def __setitem__(self, key, value):
        raise Exception("Attempted to alter the dictionary")
    def __hash__(self):
        return hash(tuple(sorted(self.items())))

CLOUDSQL_PROJECT = 'capozziinc'
CLOUDSQL_INSTANCE = 'us-east1:lrpdb'
    
f = open('client_secrets.json', 'r')
client_secrets = json.loads(f.read())
f.close()
cloud_dbpass = client_secrets['web']['DBPASS']
cloud_dbhost = client_secrets['web']['DBHOST']
cloud_dbuser = client_secrets['web']['DBUSER']
cloud_dbname = client_secrets['web']['DBNAME']
cloud_dbport = client_secrets['web']['DBPORT']


SQLALCHEMY_DATABASE_URI='mysql+mysqldb://'+cloud_dbuser+':'+cloud_dbpass+'@/'+cloud_dbname+'?unix_socket=/cloudsql/'+CLOUDSQL_PROJECT+':'+CLOUDSQL_INSTANCE



#print "SQLALCHEMY: %s" % SQLALCHEMY_DATABASE_URI
db = sqlalchemy.create_engine(
    # Equivalent URL:
    # mysql+pymysql://<db_user>:<db_pass>@/<db_name>?unix_socket=/cloudsql/<cloud_sql_instance_name>
	SQLALCHEMY_DATABASE_URI,

    # ... Specify additional properties here.
    # ...
    pool_size=20,
    max_overflow=10
)



def mysql_connect():

    f = open('client_secrets.json', 'r')
    client_secrets = json.loads(f.read())
    f.close()

    
    CLOUDSQL_PROJECT = 'capozziinc'
    CLOUDSQL_INSTANCE = 'us-east1:lrpdb'


    #conn = db.connect() #MySQLdb.connect(unix_socket='/cloudsql/{}:{}'.format(CLOUDSQL_PROJECT, CLOUDSQL_INSTANCE), user=cloud_dbuser, host=cloud_dbhost, passwd=cloud_dbpass, db=cloud_dbname)
    if os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/'):
        
        cloud_dbpass = client_secrets['web']['DBPASS']
        cloud_dbhost = client_secrets['web']['DBHOST']
        cloud_dbuser = client_secrets['web']['DBUSER']
        cloud_dbname = client_secrets['web']['DBNAME']
        cloud_dbport = client_secrets['web']['DBPORT']
        conn=db.raw_connection()
        #conn = MySQLdb.connect(unix_socket='/cloudsql/{}:{}'.format(CLOUDSQL_PROJECT, CLOUDSQL_INSTANCE), user=cloud_dbuser, host=cloud_dbhost, passwd=cloud_dbpass, db=cloud_dbname)
    else:
    
        cloud_dbpass = client_secrets['local']['DBPASS']
        cloud_dbhost = client_secrets['local']['DBHOST']
        cloud_dbuser = client_secrets['local']['DBUSER']
        cloud_dbname = client_secrets['local']['DBNAME']
        cloud_dbport = client_secrets['local']['DBPORT']
        #conn = MySQLdb.connect(unix_socket='/cloudsql/{}:{}'.format(CLOUDSQL_PROJECT, CLOUDSQL_INSTANCE), user=cloud_dbuser, host=cloud_dbhost, passwd=cloud_dbpass, db=cloud_dbname)
        conn = MySQLdb.connect(user=cloud_dbuser, host=cloud_dbhost, passwd=cloud_dbpass, db=cloud_dbname)
        
        
    cursor = conn.cursor()
    return conn, cursor

from webapp2_extras import sessions

class QueryHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    msg = None; error = None; 
    
    def post(self):
        misc = {'error': None, 'msg': None}
        session_ID = self.session.get('session_ID')
        if True or session_ID not in [None, 0]:
            user_obj = None #get_user_obj({'session_ID': session_ID})
            if True or ('ID' in user_obj and user_obj['ID'] == 1):
                
                req = dict_request(self.request)
                queries = req['query'].split("\n")
                misc['query'] = queries[0]
                misc = self.process_queries(misc, queries)
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", "query.html")
                self.response.out.write(template.render(path, tv))
            
            else:
                    
                target_template = get_template(user_obj)
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
    def process_queries(self, misc, queries, table=None):
        field_type = {
                     0: 'DECIMAL',
                     1: 'TINY',
                     2: 'SHORT',
                     3: 'LONG',
                     4: 'FLOAT',
                     5: 'DOUBLE',
                     6: 'NULL',
                     7: 'TIMESTAMP',
                     8: 'LONGLONG',
                     9: 'INT24',
                     10: 'DATE',
                     11: 'TIME',
                     12: 'DATETIME',
                     13: 'YEAR',
                     14: 'NEWDATE',
                     15: 'VARCHAR',
                     16: 'BIT',
                     246: 'NEWDECIMAL',
                     247: 'INTERVAL',
                     248: 'SET',
                     249: 'TINY_BLOB',
                     250: 'MEDIUM_BLOB',
                     251: 'LONG_BLOB',
                     252: 'BLOB',
                     253: 'VAR_STRING',
                     254: 'STRING',
                     255: 'GEOMETRY' }
                

        misc['insert_query'] = ""; insert_comma = ""; insert_ID_exists = False
        misc['update_query'] = ""; misc['alter_query'] = ""
        reverse_sort = False
        for ie, query in enumerate(queries):
            query = query.replace("UDPATE ", "UPDATE ")
            query = query.replace("\t", ",")
            now_query = False
            if ", now" in query:
                now_query = True
                now_dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                query = query.replace(", now",  ", '%s'" % now_dt)
            queries[ie] = query
            misc['query'] = query
   
        misc['columns'] = []
        misc['types'] = []
        misc['data'] = []
        mysql_conn, cursor = mysql_connect()
        misc['error'] = None
        cnt = 0
        try:
            for query in queries:
                #logging.info ("\nQuery: %s\n" % query)
                cursor.execute(query)

                if now_query:
                    query = query.replace(", '%s'" % now_dt, ", now")
                res = cursor.fetchall()
                misc['data'] = []
                num_fields = []
                misc['columns'] = []
                types_ = []

                if cursor is not None and res is not None:
                    if cursor.description is not None:
                        num_fields = len(cursor.description)
                        misc['columns'] = [i[0] for i in cursor.description]
                        for c in misc['columns']:
                            misc['insert_query'] += "%s%s" % (insert_comma, c); insert_comma = ", "
                            if c == "ID":
                                insert_ID_exists = True
                        types_ = [i[1] for i in cursor.description]
                        for t in types_:
                            #logging.info("Convert %d to %s" % (t, field_type[t]))
                            misc['types'].append(field_type[t])
                        if query == "SHOW TABLES":
                            for i, row in enumerate(res):
                                row_  = []
                                for r in row:
                                    logging.info(r)
                                    r_ = "<a href='/query?table=%s'>%s</a>" % (r, r)
                                    row_.append(r_)


                                misc['data'].append(row_)

                        else:
                            for i, row in enumerate(res):
                                row_  = []
                                for r in row:
                                    try:
                                        f_ = float(r)
                                        row_.append("{:,}".format(r))
                                    except Exception ,e:

                                        if r is None or isinstance(r, datetime) or isinstance(r, date):
                                            r_ = r
                                        else:
                                            try:
                                                r_ = r.decode("utf-8")
                                            except Exception as e:
                                                r_ = r.decode('latin-1')
                                                print(r_)



                                        row_.append(r_)


                                misc['data'].append(row_)




                if res is not None:
                    misc['cnt'] = len(res)
                else:
                    misc['cnt'] = 0
        except Exception, e:
            
            try:
                misc['error'] = e[1]
            except IndexError:
                misc['error'] = e

        if query.upper().startswith("TRUNCATE") or query.upper().startswith("ALTER") or query.upper().startswith("INSERT") or query.upper().startswith("UPDATE") or query.upper().startswith("DELETE"):
            mysql_conn.commit()
            regex = re.compile(r'(TRUNCATE TABLE|ALTER TABLE |INSERT INTO |UPDATE |DELETE FROM )([a-zA-Z_\.]+)')
            m = regex.search(query)
            if m is not None:
                table = m.group(2)
                if reverse_sort:
                    new_query = "SELECT * from %s order by ID desc limit 100" % table
                else:
                    new_query = "SELECT * from %s limit 100" % table
                misc['columns'] = []
                misc['types'] = []
                misc['data'] = []
                try:
                    cursor.execute(new_query)
                    res = cursor.fetchall()
                    misc['data'] = []
                    num_fields = []
                    misc['columns'] = []
                    types_ = []

                    if cursor is not None and res is not None:
                        if cursor.description is not None:
                            num_fields = len(cursor.description)
                            misc['columns'] = [i[0] for i in cursor.description]

                            types_ = [i[1] for i in cursor.description]
                            for t in types_:
                                logging.info("Convert %d to %s" % (t, field_type[t]))
                                misc['types'].append(field_type[t])
                            for i, row in enumerate(res):
                                misc['data'].append(row)




                    if res is not None:
                        misc['cnt'] = len(res)
                    else:
                        misc['cnt'] = 0
                except Exception, e:
                    try:
                        error = e[1]
                    except IndexError:
                        error = e
        if table != "" and insert_ID_exists:
            misc['insert_query'] += ") VALUES ((SELECT count(1)+1 from %s fds))" % table
        else:
            misc['insert_query'] += ") VALUES ()"
        cursor.close(); mysql_conn.close()
        return misc
        
    def get(self):
        misc = {'error': None, 'msg': None}
        session_ID = self.session.get('session_ID')
        if True or session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if True or user_obj['ID'] == 1:
                
                table = ""
 
                queries = ["SHOW TABLES"]
                
                
                table = None
                if self.request.get('table') != "":
                    table = self.request.get('table')
                    if table in ['LaxRef_Games', 'LaxRef_Game_Streams', 'LaxRef_Active_Live_WP_Games']:
                        queries = ["SELECT * from %s order by ID desc limit 100" % table]
                        reverse_sort = True
                    else:
                        queries = ["SELECT * from %s limit 100" % table]
                    misc['insert_query'] = "INSERT INTO %s (" % table
                    misc['alter_query'] = "ALTER TABLE %s" % table
                    misc['update_query'] = "UPDATE %s set =" % table

                
                
                misc = self.process_queries(misc, queries, table)
                logging.info(misc['error'])
        
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'query': "SELECT * from LRP_Users", 'columns': [], 'types': [], 'data': [], 'error': "", 'cnt': 0}; path = os.path.join("templates", "query.html"); self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}; path = os.path.join("templates", "index.html"); self.response.out.write(template.render(path, tv))
        else:
            user_obj = process_non_auth(self)
            
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", 'index.html'); self.response.out.write(template.render(path, tv))

def process_preferences(preferences):
    for i,p in enumerate(preferences):
        if p['key'] == "receive_newsletter":
            p['element'] = "select"
            p['dtop_display'] = "Receive LR Pro Newsletter"
            p['mob_display'] = "Receive Newsletter"
            p['options'] = [{'display': "Yes", 'value': 1, 'selected': ' selected' if p['value'] in [1, None] else ''}, {'display': "No", 'value': 0, 'selected': ' selected' if p['value'] not in [1, None] else ''}]
            
    return preferences

def process_profile(profile):
    for i,p in enumerate(profile):
        if p['key'] in ["first_name", "last_name", 'email', 'phone']:
            p['element'] = "text"
            p['dtop_display'] = " ".join(p['key'].split("_")).title()
            p['mob_display'] = " ".join(p['key'].split("_")).title()
            if p['value'] in ["null", None]:
                p['value'] = ""
    return profile

def get_template(user_obj):
    if user_obj['activated'] != 1:
        target_template = "activation_reminder.html"
    elif user_obj['user_type'] == "individual":
        target_template = "individual_home.html"
    elif user_obj['user_type'] == "team":
        target_template = "team_home.html"
    elif user_obj['user_type'] == "media":
        target_template = "media_home.html"
    elif user_obj['user_type'] == "master":
        target_template = "master_home.html"
    else:
        target_template = "index.html"
        
    #logging.info("Target Template: %s" % target_template)
    return target_template

def get_relevant_preferences(user_obj):
    if user_obj['user_type'] == "individual":
        return ["receive_newsletter"]
    elif user_obj['user_type'] == "team":
        return ["receive_newsletter"]
    elif user_obj['user_type'] == "media":
        return ["receive_newsletter"]
    elif user_obj['user_type'] == "master":
        return ["receive_newsletter"]
    else:
        return ["receive_newsletter"]

class IndexHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        misc = {'error': None, 'msg': None}
        if self.request.get("username") != "":
            user_obj = get_user_obj({'username': self.request.get("username"), 'password': self.request.get("password")})
            if user_obj['auth']:
                self.session['session_ID'] = user_obj['session_ID']
                user_obj['user_cookie'] = self.session['cart_cookie']
                
                target_template = get_template(user_obj)
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"  }
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
            else:
                target_template = "login.html"
                misc['error'] = "We could not find your username/password combination."
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
        else:
            tv = {'user_obj': None, 'misc': {}, 'layout': 'layout_no_auth.html'}; path = os.path.join("templates", "index.html")
            self.response.out.write(template.render(path, tv))
    
    def get(self):
        if False:
            mail.send_mail(sender="admin@lacrossereference.com",
                       to="zcapozzi@gmail.com",
                       subject="Your account has been approved",
                       body="""Dear Albert:

    Your example.com account has been approved.  You can now visit
    http://www.example.com/ and sign in using your Google Account to
    access new features.

    Please let us know if you have any questions.

    The example.com Team
    """)
        target_template = "index.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [0, None]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
             
                target_template = get_template(user_obj)
                
                    
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html" }
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
            else:
                user_obj = process_non_auth(self)        
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
class LoginHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        tv = {'user_obj': None, 'misc': {}}
        path = os.path.join("templates", "index.html")
        self.response.out.write(template.render(path, tv))
    
    def get(self):
        
        target_template = "login.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", "index.html")
                self.response.out.write(template.render(path, tv))
            else:
                user_obj = process_non_auth(self)
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

def dict_request(req):            
    d = {}
    for r in req.POST.items():
        d[str(r[0])] = r[1]
        if isinstance(r[1], str) or isinstance(r[1], unicode):
            d[str(r[0])] = d[str(r[0])].strip()
        
    return d
    
class CreateHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "index.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None
        misc['create_group_user_display'] = "visible"; misc['create_group_user_tag_display'] = "tag-on"
        misc['create_standalone_user_display'] = "hidden"; misc['create_standalone_user_tag_display'] = "tag-off"
        
        misc['standalone_user_types'] = [{'val': 'team', 'desc': 'Team'}, {'val': None, 'desc': 'Lurker'}, {'val': 'media', 'desc': 'Media'}, {'val': 'individual', 'desc': 'Individual'}]
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth'] and user_obj['is_admin']:
                req = dict_request(self.request)
                queries = []; params = []
                
                # GET USEFUL INFO FROM THE DB
                if req['action'].startswith("create"):
                    conn, cursor = mysql_connect()
                    cursor.execute("SELECT * from LRP_Users")
                    users = zc.dict_query_results(cursor)
                    cursor.execute("SELECT * from LRP_Groups")
                    groups = zc.dict_query_results(cursor)
                    cursor.execute("SELECT * from LRP_Group_Access")
                    access = zc.dict_query_results(cursor)
                    cursor.close(); conn.close()
                    
                # CREATE A STANDALONE USER
                if req['action'] == "create_standalone_user":
                    misc['create_group_user_display'] = "hidden";  misc['create_standalone_user_display'] = "visible"
                    misc['create_group_user_tag_display'] = "tag-off";  misc['create_standalone_user_tag_display'] = "tag-on"
                    
                    map_fields = ["standalone_email", "standalone_user_type", "standalone_username", "standalone_first_name", "standalone_last_name", "standalone_phone", "standalone_password", "standalone_is_admin"]
                    for m in map_fields:
                        misc[m] = None
                        if m in req:
                            misc[m] = req[m]
                    
                    for o in misc['standalone_user_types']:
                        o['selected'] = ""
                        if o['val'] == req['standalone_user_type'] or o['val'] is None and req['standalone_user_type'] == "None":
                            o['selected'] = " selected"
                    
                    misc['standalone_is_admin_checked'] = " checked" if misc['standalone_is_admin'] in ["on", 1, True] else ""
                    is_admin = 1 if misc['standalone_is_admin'] in ["on", 1, True] else 0
                    go_on = True
                    if req['standalone_email'].upper() in [z['email'].upper() for z in users]:
                        misc['error'] = "Email is already associated with an account."
                        go_on = False
                    elif req['standalone_email'] == "":
                        misc['error'] = "All accounts need an associated email address."
                        go_on = False
                    elif req['standalone_username'] == "":
                        misc['error'] = "All accounts need an associated username."
                        go_on = False
                    elif req['standalone_username'].upper() in [z['username'].upper() for z in users]:
                        misc['error'] = "Username is already associated with an account."
                        go_on = False
                    elif req['standalone_first_name'] in ["", None] or req['standalone_last_name'] in ["", None]:
                        misc['error'] = "Please enter a first and last name."
                        go_on = False
                        
                    if go_on:
                        ab_group = min(47, int(random.random()*48.))
                        
                        query = ("INSERT INTO LRP_Users (ID,email,active,logins,user_type,password,username,AB_group,first_name,last_name,phone,date_created,track_GA,is_admin, activated) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Users fds), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
                        param = [req['standalone_email'], 1, 0, req['standalone_user_type'], req['standalone_password'], req['standalone_username'], ab_group, req['standalone_first_name'], req['standalone_last_name'], req['standalone_phone'], datetime.now(), 1, is_admin, 1]
                        #logging.info(query)
                        #logging.info(param)
                        queries.append(query)
                        params.append(param)
                        
                        queries.append("INSERT INTO LRP_User_Preferences (ID, user_ID, active) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_User_Preferences fds), (SELECT max(ID) from  LRP_Users fdsa), %s)")
                        params.append([1])
                        
                ex_queries(queries,params)
                
                target_template = "create.html"
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
            else:
                
                target_template = get_template(user_obj)
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
    
    def get(self):
        
        target_template = "index.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None
        misc['create_group_user_display'] = "visible"; misc['create_group_user_tag_display'] = "tag-on"
        misc['create_standalone_user_display'] = "hidden"; misc['create_standalone_user_tag_display'] = "tag-off"
        
        misc['standalone_user_types'] = [{'val': 'team', 'desc': 'Team'}, {'val': None, 'desc': 'Lurker'}, {'val': 'media', 'desc': 'Media'}, {'val': 'individual', 'desc': 'Individual'}]
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth'] and user_obj['is_admin']:
                target_template = "create.html"
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
            else:
                
                target_template = get_template(user_obj)
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
class AdminHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "index.html"
        misc = {'error': None, 'msg': None}; user_obj = None
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
        path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
    
    def get(self):
        
        target_template = "admin.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth'] and user_obj['is_admin']:
      
                conn, cursor = mysql_connect()
                cursor.execute("SELECT * from LRP_Users")
                misc['users'] = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Groups")
                misc['groups'] = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Group_Access")
                misc['access'] = zc.dict_query_results(cursor)
                cursor.close(); conn.close()
                
                for u in misc['groups']:   
                    tmp = [z for z in misc['access'] if z['group_ID'] ==  u['ID']]
                    u['num_users'] = len(tmp)
                    #u['num_active_users'] = len([1 for z in tmp if z['status'] == "active"])
                    
                for u in misc['users']:
                    u['decrypted_password'] = decrypt_local(u['password'], create_cipher())
                    u['current_group_obj'] = None
                    if u['active_group'] is not None:
                        u['current_group_obj'] = misc['groups'][ [z['ID'] for z in misc['groups']].index(u['active_group']) ]
                misc['display_users'] = sorted(misc['users'], key=lambda x:x['ID'],  reverse=True)[0:15]
                misc['display_groups'] = sorted(misc['groups'], key=lambda x:x['ID'],  reverse=True)[0:15]
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
            else:
                
                target_template = get_template(user_obj)
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
class ActivateHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
    
        misc = {'error': None, 'code_error': None, 'msg': None}; user_obj = None
        queries = []; params = []
        
        target_template = "activated.html"
        
        
        misc['user_ID'] = int(self.request.get('user_ID').strip())
        misc['username'] = self.request.get('username').strip()
        misc['password'] = self.request.get('password').strip()
        misc['phone'] = self.request.get('phone').strip()
        
        conn, cursor = mysql_connect()
        cursor.execute("SELECT * from LRP_Users where ID!=%s", [misc['user_ID']])
        existing_users = zc.dict_query_results(cursor)
        cursor.close(); conn.close()
        
        if "" == misc['username']:
            misc['error'] = "You must enter a valid value for username."
        elif sum([1 for z in misc['username'].lower() if 97 <= ord(z) <= 122 or 48 <= ord(z) <= 57]) != len(misc['username']):
            misc['username'] = ""
            misc['error'] = "Usernames can only include numbers and letters."
        elif "" == misc['password']:
            misc['error'] = "You must enter a valid value for password."
        elif len(misc['password']) < 8:
            misc['error'] = "Passwords must be at least 8 characters and include at least one of: UpperCase, Letter, Number"
            misc['password'] = ""
        elif len([1 for z in misc['password'] if 48 <= ord(z) <= 57]) == 0 or len([1 for z in misc['password'] if 97 <= ord(z) <= 122]) == 0 or len([1 for z in misc['password'] if 65 <= ord(z) <= 90]) == 0:
            misc['error'] = "Passwords must be at least 8 characters and include at least one of: UpperCase, LowerCase, Number"
            misc['password'] = ""
        elif misc['username'].lower() in [z['username'].lower() for z in existing_users if z['active'] == 1]:
            misc['username'] = ""
            misc['error'] = "Username is not available."
            
        
        
        if misc['error'] is None:
            
       
            query = "UPDATE LRP_Users set username=%s, password=%s, activated=%s, phone=%s where ID=%s"
            param = [misc['username'], encrypt(misc['password'], create_cipher()), 1, misc['phone'], misc['user_ID']]
            session_ID = "%d%09d" % ((datetime.now() - datetime(1970,1,1)).total_seconds()*1000.0, misc['user_ID'])
            self.session['session_ID'] = session_ID
            
            queries.append(query); params.append(param)
            
            ex_queries(queries, params)
            
            user_obj = get_user_obj({'session_ID': session_ID})      
            
            layout = "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"       
        else:
            layout = "layout_no_auth.html"   
            target_template = "finalize_activation.html"         
            

        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
        path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
    
    def get(self):
        
       
        misc = {'error': None, 'code_error': None, 'msg': None}; user_obj = None
        queries = []; params = []
        
        
        
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
            
                user_obj = logout(self, user_obj)
                
        misc['activation_code'] = self.request.get('c')        
        
        
        conn, cursor = mysql_connect()
        cursor.execute("SELECT * from LRP_Users where activation_code=%s", [misc['activation_code']])
        users = zc.dict_query_results(cursor)
        cursor.close(); conn.close()
        
        if len(users) == 0:
            misc['code_error'] = "Your activation code did not match our records."
            target_template = "finalize_activation.html"
        else:
            user = users[0]
            misc['user_ID'] = user['ID']
            if user['activation_type'] == "full":
                target_template = "finalize_activation.html"
            elif user['activation_type'] == "final":
                target_template = "activated.html"
                conn, cursor = mysql_connect()
                cursor.execute("UPDATE LRP_Users set activated=1 where ID=%s", [misc['user_ID']])
                conn.commit(); cursor.close(); conn.close()
            else:
                target_template = "activated.html"
                conn, cursor = mysql_connect()
                cursor.execute("UPDATE LRP_Users set activated=1 where ID=%s", [misc['user_ID']])
                conn.commit(); cursor.close(); conn.close()
                
            self.session['session_ID'] = "%d%09d" % ((datetime.now() - datetime(1970,1,1)).total_seconds()*1000.0, user['ID'])
            
        layout = "layout_main.html" #if user_obj['user_type'] is not None else "layout_lurker.html"       
        if misc['error'] is not None or misc['code_error'] is not None:
            layout = "layout_no_auth.html"
            
        user_obj = process_non_auth(self)
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
        path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        
def logout(self, user_obj):
    user_obj['auth'] = False
    self.session['session_ID'] = 0               
    
    conn, cursor = mysql_connect()
    cursor.execute("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)", [9, user_obj['ID'], datetime.now()]); conn.commit()
    cursor.close(); conn.close()
    return user_obj    
    
class LogoutHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        tv = {'user_obj': None, 'misc': {}}
        path = os.path.join("templates", "index.html")
        self.response.out.write(template.render(path, tv))
    
    def get(self):
        
        target_template = "index.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            
            user_obj = logout(self, user_obj)
                
            tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

def ex_queries(queries, params, desc=None):
    if len(queries) > 0:
        if desc is not None:
            logging.info("  %d queries to upload (%s)..." % (len(queries), desc))
        conn, cursor = mysql_connect();
        cursor.execute("START TRANSACTION")
        for i, (q, p) in enumerate(zip(queries, params)):
            logging.info(q)
            logging.info(p)
            cursor.execute(q, p)
        if '--no-commit' not in client_secrets['local'] or client_secrets['local']['--no-commit'] not in ["Y", 'y', 'yes']: 
            cursor.execute("COMMIT")
        else:
            logging.info("\n\n\tNO COMMIT!!!\n\n")
        cursor.close(); conn.close()
            
class RegisterHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "register_start.html"
        misc = {'error': None}; user_obj = None; queries = []; params = []
        
        conn, cursor = mysql_connect()
        cursor.execute("SELECT * from LRP_Users")
        existing_users = zc.dict_query_results(cursor)
        misc['products'] = get_products(cursor, "Data Subscriptions")
        cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
        next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
        cursor.execute("SELECT * from LRP_Email_Templates where active=1")
        email_templates = zc.dict_query_results(cursor)
        cursor.close(); conn.close()
        next_ID = len(existing_users) + 1
        
        misc['process_step'] = self.request.get('process_step').strip()
        misc['username'] = self.request.get('username').strip()
        misc['password'] = self.request.get('password').strip()
        misc['email'] = self.request.get('email').strip()
        misc['phone'] = self.request.get('phone').strip()
        
        email_match = email_regex.search(misc['email'])
        
        if "" == misc['username']:
            misc['error'] = "You must enter a valid value for username."
        elif sum([1 for z in misc['username'].lower() if 97 <= ord(z) <= 122 or 48 <= ord(z) <= 57]) != len(misc['username']):
            misc['username'] = ""
            misc['error'] = "Usernames can only include numbers and letters."
        elif "" == misc['password']:
            misc['error'] = "You must enter a valid value for password."
        elif len(misc['password']) < 8:
            misc['error'] = "Passwords must be at least 8 characters and include at least one of: UpperCase, Letter, Number"
            misc['password'] = ""
        elif len([1 for z in misc['password'] if 48 <= ord(z) <= 57]) == 0 or len([1 for z in misc['password'] if 97 <= ord(z) <= 122]) == 0 or len([1 for z in misc['password'] if 65 <= ord(z) <= 90]) == 0:
            misc['error'] = "Passwords must be at least 8 characters and include at least one of: UpperCase, LowerCase, Number"
            misc['password'] = ""
        elif "" == misc['email']:
            misc['error'] = "You must enter a valid value for email."
        elif email_match is None:
            misc['error'] = "You must enter a valid value for email."
        elif misc['username'].lower() in [z['username'].lower() for z in existing_users if z['active'] == 1]:
            misc['username'] = ""
            misc['error'] = "Username is not available."
        elif misc['email'].lower() in [z['email'].lower() for z in existing_users if z['active'] == 1]:
            misc['email'] = ""
            misc['error'] = "Email is already associated with an account."
            
        
        
        if misc['error'] is None:
            
            target_template = "register_start.html"
            
            tmp1 = create_temporary_password()
            tmp2 = create_temporary_password()
            activation_code = "%s%s" % (tmp1, tmp2)
            random.seed(time.time() + 110935)
            
            dt = datetime.now()
            
            query = "INSERT INTO LRP_Users (ID, active, logins, email, username, password, AB_group, date_created, activation_code, activated, activation_type) VALUES  (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            param = [next_ID, 1, 0, misc['email'], misc['username'], encrypt(misc['password'], create_cipher()), min(47, int(random.random()*48.)), dt, activation_code, 0, 'final']
            queries.append(query); params.append(param)

            user_obj = {'date_created': dt, 'auth': False, 'last_log_in': None, 'logins': 0, 'user_type': None, 'ID': next_ID, 'email': misc['email'], 'password': misc['password'], 'phone': misc['phone'], 'username': misc['username']}
            user_obj['session_ID'] = "%d%09d" % ((datetime.now() - datetime(1970,1,1)).total_seconds()*1000.0, user_obj['ID'])
            self.session['session_ID'] = user_obj['session_ID']
            
            
            
            query = "INSERT INTO LRP_User_Preferences (ID, user_ID, active) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_User_Preferences fds), %s, %s)"
            param = [next_ID, 1]
            queries.append(query); params.append(param)
            ex_queries(queries, params)
                        
            msg = email_templates[ [z['template_desc'] for z in email_templates].index('Activate Account') ]
            msg['email'] = misc['email']
            msg['subject'] = "Your LacrosseReference PRO account is ready"
            
            msg['content'] = get_file(msg['bucket'], msg['fname'])
            msg['content'] = msg['content'].replace("[activation_link]", "https://pro.lacrossereference.com/activate?c=%s" % (url_escape(activation_code)))
            
            finalize_mail_send(msg)
            
            misc['msg'] = "An account activation link has been sent to the email account specified."
            misc['username'] = ""
            misc['password'] = ""
            misc['email'] = ""
            misc['phone'] = ""
            
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
        path = os.path.join("templates", target_template)
        self.response.out.write(template.render(path, tv))

    
        
        
    
    def get(self):
        
        target_template = "register_start.html"
        
        misc = {'username': '', 'password': '', 'email': '', 'phone': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                target_template = "index.html"
                misc['msg'] = "You are already registered and logged in."
            
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
      
def get_products(cursor, category=None):
    
    if category is None:
        cursor.execute("SELECT * from LRP_Products", [])
    else:
        cursor.execute("SELECT * from LRP_Products where product_category=%s", [category])
    products = zc.dict_query_results(cursor)
    cursor.execute("SELECT * from LRP_Offers where active=1", [])
    offers = zc.dict_query_results(cursor)
    
    for i, p in enumerate(products):
        p['offers'] = [z for z in offers if z['product_ID'] == p['ID'] and z['active']]
        
        if p['request_quote']:
                
            p['price_str'] = ""
            p['action'] = "REQUEST QUOTE"
        else:
            
            p['price_str'] = "$%d / yr" % (p['price'])
            p['action'] = "ADD TO CART"
    return products
    
class RegisterConfigHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "register_config.html"
        misc = {'error': None, 'current_items': None}; user_obj = None; queries = []; params = []
        
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
                
                if self.request.get("action") == "add_item_to_cart":
                    misc['product_ID'] = int(self.request.get("product_ID"))
                    
                    if misc['error'] is None:
                        
                        tup = (user_obj['ID'], misc['product_ID'])
                        if tup not in [(z['user_ID'], z['product_ID']) for z in user_obj['cart'] if z['status'] in ["added"]]:
                            
                            tmp_product = misc['products'][ [z['ID'] for z in misc['products']].index(misc['product_ID'])]
                            
                            price = tmp_product['price']
                            list_price = price
                            
                            query = "INSERT INTO LRP_Cart (ID, user_ID, product_ID, status, date_added, price, discount_tag, list_price, active) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Cart fds), %s, %s, %s, %s, %s, %s, %s, %s)"
                            param = [user_obj['ID'], misc['product_ID'], 'added', datetime.now(), price, None, list_price, 1]
                            queries.append(query); params.append(param)
                            
                            ex_queries(queries, params)
                            
                            
                            
                            user_obj['cart'].append({'ID': next_cart_ID, 'user_ID': user_obj['ID'], 'product_ID': misc['product_ID'], 'date_added': datetime.now(), 'status': 'added', 'active': 1, 'price': price, 'list_price': list_price, 'product': tmp_product})
                        else:
                            misc['error'] = "Product has been added already."
                        target_template = "cart.html"
                    
             
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
            else:
                target_template = "index.html"
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
    def get(self):
        
        target_template = "index.html"
        
        misc = {'username': '', 'password': '', 'email': '', 'phone': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
    
                
        conn, cursor = mysql_connect()
        misc['products'] = get_products(cursor, "Data Subscriptions")
        cursor.close(); conn.close()
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                
                target_template = get_template(user_obj)
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
def pd(d):
    logging.info("\n\n%s\n\n" % zc.print_dict(d))

def create_cart_cookie():
    random.seed(time.time())
    user_cookie = "%d" % time.time()
    for ij in range(5):
        random.seed(time.time())
        user_cookie += create_temporary_password()
        time.sleep(.05)
    return user_cookie
    
class CartHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "cart.html"
        misc = {'error': None}; user_obj = None; queries = []; params = []
        
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                layout = "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"
            else:
                user_obj = process_non_auth(self)
                layout = "layout_no_auth.html"
        else: 
            user_obj = process_non_auth(self)
            layout = "layout_no_auth.html"
        
        conn, cursor = mysql_connect()
        misc['products'] = get_products(cursor, "Data Subscriptions")
        cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
        next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
        cursor.close(); conn.close()

        
        if self.request.get("action") == "remove_item_from_cart":
            misc['cart_ID'] = int(self.request.get("cart_ID"))
            if 'ID' in user_obj:
                queries.append("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)")
                params.append([3, user_obj['ID'], datetime.now()])
        
            if misc['error'] is None:
                
                if misc['cart_ID'] in [z['ID'] for z in user_obj['cart']]:
                    
                    query = "UPDATE LRP_Cart set status='removed' where ID=%s"
                    param = [misc['cart_ID']]
                    queries.append(query); params.append(param)
                    
                    misc['msg'] = "Item has been removed"
                else:
                    misc['error'] = "Cart could not be updated."
                target_template = "cart.html"
            
        elif self.request.get("action") == "enter_discount":
            queries.append("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)")
            params.append([4, user_obj['ID'], datetime.now()])
            
            misc['cart_ID'] = int(self.request.get("cart_ID"))
            misc['product_ID'] = int(self.request.get("product_ID"))
            misc['discount_tag'] = self.request.get("discount_tag").strip().upper()
            
            
            tmp_product = misc['products'][ [z['ID'] for z in misc['products']].index(misc['product_ID']) ]
            pd(tmp_product)
            
            if misc['discount_tag'] in [ z['discount_tag'].upper() for z in tmp_product['offers'] if z['product_ID'] == misc['product_ID'] and z['good_until'] is not None and z['good_until'] < datetime.now()]: # It has expired
                misc['error'] = "Offer has already expired."
            elif misc['discount_tag'] in [ z['discount_tag'].upper() for z in tmp_product['offers'] if z['product_ID'] != misc['product_ID']]: # It is for a different product
                misc['error'] = "Unknown discount code/product combination."
            elif misc['discount_tag'] in [ z['discount_tag'].upper() for z in tmp_product['offers'] if z['specific_to_user_ID'] not in [None, user_obj['ID']]]: # It's specific to a different user
                misc['error'] = "Unknown discount code/product combination."
            elif misc['discount_tag'] not in [ z['discount_tag'].upper() for z in tmp_product['offers']]: # not in the active list at all
                misc['error'] = "Unknown discount code/product combination."
            else:
                offer = [z for z in tmp_product['offers'] if z['active'] and (z['good_until'] is None or z['good_until'] >= datetime.now()) and z['specific_to_user_ID'] in [None, user_obj['ID']] and z['product_ID'] == misc['product_ID'] and misc['discount_tag'] == z['discount_tag'].upper()]
                if len(offer) == 0:
                    misc['error'] = "Unknown discount code/product combination."
                else:
                    offer = offer[0]
                
            if misc['error'] is None:
                
                if misc['cart_ID'] in [z['ID'] for z in user_obj['cart']]:
                    
                    query = "UPDATE LRP_Cart set discount_tag=%s, price=%s where ID=%s"
                    param = [misc['discount_tag'].upper(), offer['offer_price'], misc['cart_ID']]
                    queries.append(query); params.append(param)
                    
                    misc['msg'] = "Discount code has been applied."
                else:
                    misc['error'] = "Discount code could not be applied."
                target_template = "cart.html"
            
     
        ex_queries(queries, params)
        if user_obj['auth']:
            user_obj = get_user_obj({'session_ID': session_ID})
        else:
            user_obj = process_non_auth(self)
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
        path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        
    def get(self):
        
        target_template = "cart.html"
        
        misc = {'username': '', 'password': '', 'email': '', 'phone': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                
                conn, cursor = mysql_connect()
                cursor.execute("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)", [2, user_obj['ID'], datetime.now()]); conn.commit()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
        
                misc['current_items'] = [z for z in misc['products'] if z['ID'] in [y['product_ID'] for y in user_obj['cart'] if y['active'] and y['status'] == "added"]]
                
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_lurker.html'}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
            
                user_obj = process_non_auth(self)
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
class SubscriptionHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = ".html"
        misc = {'error': None}; user_obj = None; queries = []; params = []
        
        conn, cursor = mysql_connect()
        
        cursor.close(); conn.close()
        
        #misc[''] = self.request.get('').strip()
        
        if misc['error'] is None:
            
            target_template = ".html"
            
            #queries.append(query); params.append(param)
            #ex_queries(queries, params)
                    
        
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
        path = os.path.join("templates", target_template)
        self.response.out.write(template.render(path, tv))

    def get(self):
        
        target_template = "index.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                target_template = "subscription.html"
                
                conn, cursor = mysql_connect()
                cursor.execute("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)", [7, user_obj['ID'], datetime.now()]); conn.commit()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
class UploadHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        misc = {'error': None, 'msg': 'N/A'}; user_obj = None; queries = []; params = []
        
        bucket_name = self.request.get("bucket")
        
        field_storage = self.request.POST.get("file", None)
        input_data = field_storage.file.read()
                            
        full_file_list = self.request.POST.getall('file')
        my_file = full_file_list[0]
        
        fname = str(my_file).split("u'")[-1][:-2]
        
        options = {'retry_params': cloudstorage.RetryParams(backoff_factor=1.1)}
        
        
        #bucket_name = "svc_data_extraction/SVC_MDV_Models"
        tmp_path = "%s/%s" % (bucket_name, fname)
        path = "/capozziinc.appspot.com/%s" % (tmp_path)
        logging.info("Attempting an upload to %s (%d chars)" % (path, len(input_data)))
        if os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/'):
                
            #conn, cursor = mysql_connect()
            #conn.commit(); cursor.close(); conn.close()
                
            
            f_ = cloudstorage.open(path, 'w')
            try:
                f_.write(input_data)   
            except UnicodeDecodeError:
                try:
                    f_.write(input_data.encode('utf-8'))   
                except UnicodeDecodeError:
                    try:
                        f_.write(input_data.encode('latin-1'))   
                    except UnicodeDecodeError:
                        misc['msg'] = ("Could not upload file using either utf-8 or latin-1")
            f_.close()
            misc['msg'] = "Success"
        else:
            misc['msg'] = "LocalHost-NoUpload"
        ex_queries(queries, params)
        
        self.response.out.write(misc['msg'])
        
    def get(self):
        
        target_template = "index.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                target_template = "password.html"
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
class PasswordHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "password.html"
        misc = {'error': None}; user_obj = None; queries = []; params = []
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                user_obj['password'] = decrypt_local(user_obj['password'], create_cipher())
        
                
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
        
                misc['password'] = self.request.get('password').strip()
                misc['new_password'] = self.request.get('new_password').strip()
                misc['repeat_password'] = self.request.get('repeat_password').strip()
                
                if misc['password'] != user_obj['password']:
                    misc['error'] = "Current password did not match."
                elif misc['new_password'] != misc['repeat_password']:
                    misc['error'] = "New password duplicate did not match original."
                elif "" in [misc['new_password'], misc['new_password'], misc['repeat_password']]:
                    misc['error'] = "All three values must be entered."
                elif len(misc['new_password']) < 8:
                    misc['error'] = "Passwords must be at least 8 characters and include at least one of: UpperCase, Letter, Number"
                elif len([1 for z in misc['new_password'] if 48 <= ord(z) <= 57]) == 0 or len([1 for z in misc['new_password'] if 97 <= ord(z) <= 122]) == 0 or len([1 for z in misc['new_password'] if 65 <= ord(z) <= 90]) == 0:
                    misc['error'] = "Passwords must be at least 8 characters and include at least one of: UpperCase, LowerCase, Number"
        
                
                if misc['error'] is None:
                    
                    queries.append("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)")
                    params.append([10, user_obj['ID'], datetime.now()])
                    
                    query = "UPDATE LRP_Users set password=%s where ID=%s"
                    param = [encrypt(misc['new_password'], create_cipher()), user_obj['ID']]
                    queries.append(query); params.append(param)
                    logging.info("Query %s w/ %s" % (query, param))
                    ex_queries(queries, params)
                    misc['msg'] = "Password has been changed."
                    
                else:
                    
                    queries.append("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)")
                    params.append([11, user_obj['ID'], datetime.now()])
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
        
            else:
                target_template = "index.html"
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

    def get(self):
        
        target_template = "index.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                target_template = "password.html"
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
class ReviewQuoteHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        self.price_type_options = []
        self.price_type_options.append({'desc': 'Annual', 'value': 'annual'})
        self.price_type_options.append({'desc': 'One-Time', 'value': 'one-time'})
        self.price_type_options.append({'desc': 'Monthly', 'value': 'monthly'})
        
        self.trial_options = []
        self.trial_options.append({'desc': 'Yes', 'value': 1})
        self.trial_options.append({'desc': 'No', 'value': 0})
        
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "review_quote.html"
        misc = {'error': None}; user_obj = None; queries = []; params = []
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth'] and user_obj['is_admin']:
                
                misc = dict_request(self.request); misc['error'] = None
                pd(misc)
                misc['request_ID'] = int(misc['request_ID'])
                misc['product_ID'] = int(misc['product_ID'])
                misc['trial'] = int(misc['trial'])
                misc['trial_str'] = "Yes" if misc['trial'] else "No"
                
                if misc['trial']:
                    try:
                        trial_end_dt = datetime.strptime(misc['trial_end_str'].replace(" ", "").replace("/", "-").strip(), "%Y-%m-%d")
                        misc['trial_end_formatted'] = datetime.strptime(misc['trial_end_str'].replace(" ", "").replace("/", "-").strip(), "%Y-%m-%d").strftime("%b %d, %Y")
                        if trial_end_dt < datetime.now():
                            misc['error'] = "Trial End date can't be in the past."
                    except Exception:
                        #logging.info(traceback.format_exc())
                        misc['error'] = "Trial End date must be YYYY-MM-DD."
            
                misc['msg_body_html'] = misc['msg_body'].replace("\n", "<BR>")
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT * from LRP_Product_Requests where status='active'", [])
                misc['product_requests'] = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Groups where active=1 order by group_name asc", [])
                groups = zc.dict_query_results(cursor)
                cursor.close(); conn.close()
                
                misc['product_name'] = misc['products'][ [z['ID'] for z in misc['products']].index(misc['product_ID']) ]['product_name']
                
                
                misc['context'] = ""
                if misc['request_ID'] != -1:
                    request = misc['product_requests'][ [z['ID'] for z in misc['product_requests']].index(misc['request_ID']) ]
                    misc['context'] = request['email']
                    misc['request_team_ID'] = request['team_ID']
                    if misc['request_team_ID'] is not None:
                        misc['context'] += " (team: %s)" % (groups[ [z['team_ID'] for z in groups].index(misc['request_team_ID'])]['group_name'])
                
                
                for p in misc['product_requests']:
                    p['selected'] = " selected" if p['ID'] == misc['request_ID'] else ""
                
                misc['price_type_options'] = self.price_type_options
                for p in misc['price_type_options']:
                    p['selected'] = " selected" if p['value'] == misc['price_type'] else ""
                
                misc['trial_options'] = self.trial_options
                for p in misc['trial_options']:
                    p['selected'] = " selected" if p['value'] == misc['trial'] else ""
                
                for p in misc['products']:
                    p['selected'] = " selected" if p['ID'] == misc['product_ID'] else ""
                
      
                misc['price_str'] = "%.2f" % float(misc['price'])
                if misc['action'] == "edit_quote":
                    target_template = "create_quote.html"
                elif misc['action'] == "send_quote":
                    cur_dt = "%d" % time.time()
                    misc['hash'] = ""
                    for ij in range(10):
                        misc['hash'] += "%s%s" % (cur_dt[ij], create_temporary_password())
                    
                    logging.info("Send the template to the user and record the quote in the DB with hash: %s." % misc['hash'])
                    
                    misc['msg_body_div'] = "<div style=''><span style='display:contents;'>{}</span></div>".format(misc['msg_body'])
                    
                    quote_content = []
                    quote_content.append({'label': '%s Price' % misc['price_type'].title(), 'value': "$%s" % misc['price_str']}) 
                    quote_content.append({'label': 'Number of Users', 'value': "50"}) 
                    if misc['trial']:
                        quote_content.append({'label': 'Trial Period Ends', 'value': misc['trial_end_formatted']}) 
                    
                    
                    misc['msg_quote_div'] = "".join(["<div style='display:flex; background-color:{};'><div style='width:49%;  margin-left:1%;'><span style='display:contents;'>{}</span></div><div style=''><span style='display:contents;'>{}</span></div></div>".format("#EEE" if i % 2 == 0 else "#FFF", z['label'],  z['value']) for i, z in enumerate(quote_content)])
                    misc['msg_html'] = "\n\n".join([misc['msg_body_div'], misc['msg_quote_div']])
                    misc['msg_html_safe'] = misc['msg_html'].replace("\n", "<BR>")
                    
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj),}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
        
            else:
                target_template = "index.html"
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

    def get(self):
        
        target_template = "index.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth'] and user_obj['is_admin']:
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                target_template = "index.html"; user_obj = process_non_auth(self)
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"; user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
class CreateQuoteHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        self.price_type_options = []
        self.price_type_options.append({'desc': 'Annual', 'value': 'annual'})
        self.price_type_options.append({'desc': 'One-Time', 'value': 'one-time'})
        self.price_type_options.append({'desc': 'Monthly', 'value': 'monthly'})
        
        self.trial_options = []
        self.trial_options.append({'desc': 'Yes', 'value': 1})
        self.trial_options.append({'desc': 'No', 'value': 0})
        
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "create_quote.html"
        misc = {'error': None}; user_obj = None; queries = []; params = []
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth'] and user_obj['is_admin']:
                trial_end_dt = None
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT * from LRP_Product_Requests where status='active'", [])
                misc['product_requests'] = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Groups where active=1 order by group_name asc", [])
                groups = zc.dict_query_results(cursor)
                cursor.close(); conn.close()
                
                
                misc['request_ID'] = int(self.request.get('request_ID'))
                misc['context'] = ""
                if misc['request_ID'] != -1:
                    request = misc['product_requests'][ [z['ID'] for z in misc['product_requests']].index(misc['request_ID']) ]
                    misc['context'] = request['email']
                    misc['request_team_ID'] = request['team_ID']
                    if misc['request_team_ID'] is not None:
                        misc['context'] += " (team: %s)" % (groups[ [z['team_ID'] for z in groups].index(misc['request_team_ID'])]['group_name'])
                for p in misc['product_requests']:
                    p['selected'] = " selected" if p['ID'] == misc['request_ID'] else ""
                    
                misc['email'] = self.request.get('email').strip()
                misc['trial'] = int(self.request.get('trial'))
                misc['product_ID'] = int(self.request.get('product_ID'))
                misc['product_name'] = misc['products'][ [z['ID'] for z in misc['products']].index(misc['product_ID']) ]['product_name']
                misc['msg_body'] = self.request.get('msg_body').strip()
                misc['msg_body_html'] = misc['msg_body'].replace("\n", "<BR>")
                misc['price_str'] = self.request.get('price')
                misc['trial_end_str'] = self.request.get('trial_end')
                misc['price_type'] = self.request.get('price_type')
                misc['trial_str'] = "Yes" if misc['trial'] else "No"
                
                
                misc['price_type_options'] = self.price_type_options
                
                for p in misc['price_type_options']:
                    p['selected'] = " selected" if p['value'] == misc['price_type'] else ""
                
                for p in misc['products']:
                    p['selected'] = " selected" if p['ID'] == misc['product_ID'] else ""
                
                misc['trial_options'] = self.trial_options
                for p in misc['trial_options']:
                    p['selected'] = " selected" if p['value'] == misc['trial'] else ""
                
                
                if misc['email'] in [None, ''] and misc['request_ID'] in [-1, "-1", "", None]:
                    misc['error'] = "You must specify a recipient or a quote request."
                elif misc['msg_body'] in [None, '']:
                    misc['error'] = "The content of the email is empty."
                elif misc['email'] not in ['', None] and email_regex.search(misc['email']) is None:
                    misc['error'] = "The email address you entered is invalid."
                elif misc['product_ID'] in [-1, "-1", "", None]:
                    misc['error'] = "You must specify which product this relates to."
                misc['trial_end_formatted'] = "N/A"
                if misc['error'] is None:
                    try:
                       misc['price'] = float(misc['price_str'].replace("$", "").replace(",", "").strip())
                    except Exception:
                        misc['error'] = "Price must be a valid number."
                    if misc['trial']:
                        try:
                            trial_end_dt = datetime.strptime(misc['trial_end_str'].replace(" ", "").replace("/", "-").strip(), "%Y-%m-%d")
                            misc['trial_end_formatted'] = datetime.strptime(misc['trial_end_str'].replace(" ", "").replace("/", "-").strip(), "%Y-%m-%d").strftime("%b %d, %Y")
                            if trial_end_dt < datetime.now():
                                misc['error'] = "Trial End date can't be in the past."
                        except Exception:
                            #logging.info(traceback.format_exc())
                            misc['error'] = "Trial End date must be YYYY-MM-DD."
                
                if misc['error'] in ['', None]:
                    target_template = "review_quote.html"
                    
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj),}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
        
            else:
                target_template = "index.html"
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

    def get(self):
        
        target_template = "create_quote.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth'] and user_obj['is_admin']:
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT * from LRP_Product_Requests where status='active'", [])
                misc['product_requests'] = zc.dict_query_results(cursor)
                cursor.close(); conn.close()
                
                misc['price_type_options'] = self.price_type_options
                misc['trial_options'] = self.trial_options
                
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                target_template = "index.html"; user_obj = process_non_auth(self)
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"; user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
class ViewQuoteHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "view_quote.html"
        misc = {'error': None}; user_obj = None; queries = []; params = []
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                user_obj['password'] = decrypt_local(user_obj['password'], create_cipher())
        
                
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
        
                misc['password'] = self.request.get('password').strip()
                misc['new_password'] = self.request.get('new_password').strip()
                misc['repeat_password'] = self.request.get('repeat_password').strip()
                
                if misc['password'] != user_obj['password']:
                    misc['error'] = "Current password did not match."
                elif misc['new_password'] != misc['repeat_password']:
                    misc['error'] = "New password duplicate did not match original."
                elif "" in [misc['new_password'], misc['new_password'], misc['repeat_password']]:
                    misc['error'] = "All three values must be entered."
                elif len(misc['new_password']) < 8:
                    misc['error'] = "Passwords must be at least 8 characters and include at least one of: UpperCase, Letter, Number"
                elif len([1 for z in misc['new_password'] if 48 <= ord(z) <= 57]) == 0 or len([1 for z in misc['new_password'] if 97 <= ord(z) <= 122]) == 0 or len([1 for z in misc['new_password'] if 65 <= ord(z) <= 90]) == 0:
                    misc['error'] = "Passwords must be at least 8 characters and include at least one of: UpperCase, LowerCase, Number"
        
                
                if misc['error'] is None:
                    
                    queries.append("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)")
                    params.append([10, user_obj['ID'], datetime.now()])
                    
                    query = "UPDATE LRP_Users set password=%s where ID=%s"
                    param = [encrypt(misc['new_password'], create_cipher()), user_obj['ID']]
                    queries.append(query); params.append(param)
                    logging.info("Query %s w/ %s" % (query, param))
                    ex_queries(queries, params)
                    misc['msg'] = "Password has been changed."
                    
                else:
                    
                    queries.append("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)")
                    params.append([11, user_obj['ID'], datetime.now()])
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
        
            else:
                target_template = "index.html"
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

    def get(self):
        
        target_template = "view_quote.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
class SwitchGroupsHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "switch_groups.html"
        misc = {'error': None}; user_obj = None; queries = []; params = []
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
        
                switch_to_group_ID = int(self.request.get('switch_to_group_ID').strip())
                
                if switch_to_group_ID in [z['ID'] for z in user_obj['active_groups']]:
                    
                
                    conn, cursor = mysql_connect()
                    cursor.execute("UPDATE LRP_Users set active_group=%s", [switch_to_group_ID])
                    cursor.execute("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)", [13, user_obj['ID'], datetime.now()])
                    conn.commit()
                    cursor.close(); conn.close()
                    user_obj = get_user_obj({'session_ID': session_ID})
                    
                    
                    target_template = "team_home.html"
                    tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                    path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
                else:
                    
                    target_template = "index.html"
                    tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                    path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
                    
                            
                
                
                
        
            else:
                target_template = "index.html"
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

    def get(self):
        
        target_template = "switch_groups.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                target_template = "switch_groups.html"
                
                if user_obj['active_group'] is None:
                    target_template = "lurker_home.html"
                elif user_obj['num_active_groups'] ==  1:
                    target_template = get_template(user_obj)
                    
                conn, cursor = mysql_connect()
                cursor.execute("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)", [8, user_obj['ID'], datetime.now()]); conn.commit()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
class PreferencesHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "preferences.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None; queries = []; params = []
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
            
                
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
                
                relevants = get_relevant_preferences(user_obj)
                keys = []; vals = []
                for r in relevants:
                    keys.append(r)
                    vals.append(self.request.get(r))
                    
                
                queries.append("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)")
                params.append([12, user_obj['ID'], datetime.now()])
                query = "UPDATE LRP_User_Preferences set %s" % ", ".join(["%s=%%s" % (z) for z in keys])
                query += " where user_ID=%s"
                param = vals + [user_obj['ID']]
                logging.info("Query %s w/ %s" % (query, param))
                queries.append(query); params.append(param)
                ex_queries(queries, params)
                
                
                user_obj = get_user_obj({'session_ID': session_ID})
                user_obj['relevant_preferences'] = [z for z in user_obj['preferences'] if z['key'] in relevants]
                
                
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                target_template = "index.html"
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        
    def get(self):
        
        target_template = "preferences.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None; queries = []; params = []
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                relevants = get_relevant_preferences(user_obj)
                
                conn, cursor = mysql_connect()
                cursor.execute("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)", [5, user_obj['ID'], datetime.now()]); conn.commit()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
                
                user_obj['relevant_preferences'] = [z for z in user_obj['preferences'] if z['key'] in relevants]
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                target_template = "index.html"
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
class ProfileHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "profile.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None; queries = []; params = []
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
            
                
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
                
                keys = []; vals = []
                update_keys = ['first_name', 'last_name', 'email', 'phone']
                for r in update_keys:
                    keys.append(r)
                    vals.append(self.request.get(r))
                
                email_match = email_regex.search(self.request.get('email'))
                
                if email_match is None:
                    misc['error'] = "The email address was invalid."
        
                if misc['error'] is None:
                    misc['msg'] = "Profile has been updated"
                    query = "UPDATE LRP_Users set %s" % ", ".join(["%s=%%s" % (z) for z in keys])
                    query += " where ID=%s"
                    param = vals + [user_obj['ID']]
                    queries.append(query); params.append(param)
                    ex_queries(queries, params)
                
                
                user_obj = get_user_obj({'session_ID': session_ID})
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                target_template = "index.html"
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        
    def get(self):
        
        target_template = "profile.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None; queries = []; params = []
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
            
                conn, cursor = mysql_connect()
                cursor.execute("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)", [6, user_obj['ID'], datetime.now()]); conn.commit()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
                
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                target_template = "index.html"
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

def get_file(bucket, fname, specs = {}):       
    if bucket is None:
        server_path = "/capozziinc.appspot.com/%s" % (fname)
        local_path = os.path.join("LocalDocs" , fname)
    else:
        server_path = "/capozziinc.appspot.com/%s/%s" % (bucket, fname)
        local_path = os.path.join("LocalDocs", bucket , fname)
        
    if os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/'):
        
        data = cloudstorage.open(server_path).read()
        
    else:
        data = open(local_path, 'rb').read()
    
    if 'json' in specs:
        data = json.loads(data)
    
    return data

def create_temporary_password(seq = ""):
    random.seed(time.time() + 9324158)
    chars = range(35, 37) + range(38, 39) + range(48,58) + range(65, 91) + range(97, 123)
    tmp_len = 17;
    tmp_password = "%s%s" % (seq, int(datetime.now().second))
    while len(tmp_password) < tmp_len:
        c = None
        while c not in chars:
            
            c = int(random.random()*123)
        tmp_password += chr(c)
    time.sleep(.02)
    return tmp_password
                
class ForgotHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "forgot.html"
        misc = {'error': None}; user_obj = None; queries = []; params = []
        
        
        misc['username'] = self.request.get('username').strip().lower()
        
        conn, cursor = mysql_connect()
        cursor.execute("SELECT * from LRP_Users")
        users = zc.dict_query_results(cursor)
        cursor.execute("SELECT * from LRP_Email_Templates where template_desc='Password Reset'")
        msg = zc.dict_query_results(cursor)[0]
        cursor.close(); conn.close()
        
        
        if "" == misc['username']:
            misc['error'] = "You must enter a valid value for username/email."
        elif misc['username'] not in [z['username'].strip().lower() for z in users] and misc['username'] not in [z['email'].strip().lower() for z in users]:
            misc['error'] = "Could not find an account associated with your entry."
        
        if misc['error'] is None:
            
            
            
            user = None
            if misc['username'] in [z['username'].strip().lower() for z in users]:
                user = users[ [z['username'].strip().lower() for z in users].index(misc['username']) ]
            elif misc['username'] in [z['email'].strip().lower() for z in users]:
                user = users[ [z['email'].strip().lower() for z in users].index(misc['username']) ]
            
            misc['msg'] = "Password has been reset; check your inbox for a password reset message."
            
            tmp_password = create_temporary_password()
            msg['email'] = user['email']
            msg['subject'] = "Password Reset"
            
            query = "UPDATE LRP_Users set password=%s where ID=%s"
            param = [encrypt(tmp_password, create_cipher()), user['ID']]
            queries.append(query); params.append(param)
            
            
            msg['content'] = get_file(msg['bucket'], msg['fname'])
            msg['content'] = msg['content'].replace("[password]", tmp_password)
            msg['content'] = msg['content'].replace("[username]", user['username'])
            msg['content'] = msg['content'].replace("\r\n", "\\n")
            msg['content'] = msg['content'].replace("\n", "\\n")
            
            finalize_mail_send(msg)
            
            ex_queries(queries, params)
                    
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
        path = os.path.join("templates", target_template)
        self.response.out.write(template.render(path, tv))

    
        
        
    
    def get(self):
        
        target_template = "forgot.html"
        
        misc = {'username': '', 'password': '', 'email': '', 'phone': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                target_template = "index.html"
                misc['msg'] = "You are already registered and logged in."
            
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

def process_non_auth(self):
    # If we ever have issues with this, it's possible that because we aren't returning the self object, the actual cookie is not getting set
    user_cookie = self.session.get('cart_cookie')
    if user_cookie in [None, '']:
        user_cookie = create_cart_cookie()
        self.session['cart_cookie'] = user_cookie
    user_obj = {'user_cookie': user_cookie, 'auth': 0}
    
    conn, cursor = mysql_connect()
    cursor.execute("SELECT * from LRP_Cart", [])
    items = zc.dict_query_results(cursor)
    cursor.execute("SELECT * from LRP_Products", [])
    products = zc.dict_query_results(cursor)
    cursor.close(); conn.close()
    
    user_obj['cart'] = [z for z in items if z['user_cookie'] == user_cookie and z['active'] == 1]
    for i, p in enumerate(user_obj['cart']):
        p['product'] = products[ [z['ID'] for z in products].index(p['product_ID'])]
        
    return user_obj    
    
class ProductSummaryHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        self.url_regex = re.compile(r'product\-summary\-?(.+)',re.IGNORECASE)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self, orig_url):
    
        url_match = self.url_regex.search(orig_url)
        product_tag = url_match.group(1)
        
        misc = {'error': None, 'product_tag': product_tag,  'team_ID': None}; user_obj = None; queries = []; params = []
        
        
        misc['email'] = self.request.get('email').strip().lower()
        misc['request_type'] = self.request.get('request_type')
        misc['AB_group'] = self.request.get('AB_group')
        if product_tag == "team":
            misc['team_ID'] = int(self.request.get('team_select'))
        
        
        email_match = email_regex.search(misc['email'])
        if email_match is None:
            misc['error'] = "You must enter a valid email."
        
        """
        conn, cursor = mysql_connect()
        cursor.execute("SELECT * from LRP_Users")
        users = zc.dict_query_results(cursor)
        cursor.execute("SELECT * from LRP_Email_Templates where template_desc='Password Reset'")
        msg = zc.dict_query_results(cursor)[0]
        cursor.close(); conn.close()
        """
        
        if misc['product_tag'] == "team":
            if misc['team_ID'] in ["-1", -1,  None, '']:
                misc['error'] = "You must select a team."

        if misc['error'] is None:
            misc['msg'] = "Request received."
            query = "INSERT INTO LRP_Product_Requests (ID, datestamp, email, team_ID, product_tag, status, active, request_type, request_comments) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Product_Requests fds), %s, %s, %s, %s, %s, %s, %s, %s)"
            param = [datetime.now(), misc['email'], misc['team_ID'], misc['product_tag'], 'active', 1, misc['request_type'], None]
            queries.append(query); params.append(param)
            ex_queries(queries, params)
        
          

        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:       
                layout = "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"
            else:
                layout = 'layout_no_auth.html'
        else:
            layout = 'layout_no_auth.html'
            
        conn, cursor = mysql_connect()
        cursor.execute("SELECT * from LRP_Groups where active=1 order by group_name asc", [])
        misc['groups'] = zc.dict_query_results(cursor)
        cursor.close(); conn.close()
        for g in misc['groups']:
            g['selected'] = " selected" if misc['team_ID'] == g['team_ID'] else ""
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
        path = os.path.join("templates", "product_summary_%s%s.html" % (product_tag, misc['AB_group'])); self.response.out.write(template.render(path, tv))

    
        
    def get(self, orig_url):
        
        misc = {'user_ID': None, 'email': "", "AB_group": None, 'hash': create_temporary_password()}; user_obj = None
        random.seed(time.time()); misc['AB_group'] = "A" if random.random() < .5 else "B"
        if self.request.get('v') != "": misc['AB_group'] = self.request.get('v')
        url_match = self.url_regex.search(orig_url)
        product_tag = url_match.group(1)
        
        
        
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                misc['user_ID'] = user_obj['ID']
                misc['email'] = user_obj['email']
                misc['AB_group'] = "A" if user_obj['AB_group'] < 24 else "B"
                if self.request.get('v') != "": misc['AB_group'] = self.request.get('v')
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}

            else:
                user_obj = process_non_auth(self)
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
        
        conn, cursor = mysql_connect()
        cursor.execute("SELECT * from LRP_Groups where active=1 order by group_name asc", [])
        misc['groups'] = zc.dict_query_results(cursor)
        
        if datetime.now().strftime("%Y%m%d") == "20200709" or os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/'):
        
            cursor.execute("INSERT INTO LRP_Product_Views (datestamp, product_tag, AB_group, user_ID, active) VALUES (%s, %s, %s, %s, %s)", [datetime.now(), product_tag, misc['AB_group'], misc['user_ID'], 1])
            conn.commit()
        
        cursor.close(); conn.close()
        path = os.path.join("templates", "product_summary_%s%s.html" % (product_tag, misc['AB_group'])); self.response.out.write(template.render(path, tv))
            
def url_escape(url):
    url = (url
    .replace(" ", "%20")
    .replace("!", "%21")
    .replace('"', "%22")
    .replace("#", "%23")
    .replace("$", "%24")
    .replace("%", "%25")
    .replace("&", "%26")
    .replace("'", "%27")
    .replace("(", "%28")
    .replace(")", "%29")
    .replace("*", "%2A")
    )
    return url

class EditGroupHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "edit_group.html"
        
        misc = {'emails': "", 'error': None, 'msg': None}; user_obj = None; queries = []; params = []
        misc['add_members_msg'] = None
        misc['add_members_error'] = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
        
                misc['group_ID'] = int(self.request.get('group_ID'))
                
                req = dict_request(self.request)
                req['admin'] = self.request.get_all('admin')
                req['remove'] = self.request.get_all('remove')
                req['reactivate'] = self.request.get_all('reactivate')
                
                if 'action' in req:
                    if req['action'] == "manage_members":
                        conn, cursor = mysql_connect()
                        cursor.execute("SELECT * from LRP_Group_Access where group_ID=%s", [misc['group_ID']])
                        access = zc.dict_query_results(cursor)
                        cursor.close(); conn.close()
                        
                        req['admin'] = [int(z) for z in req['admin']]
                        req['remove'] = [int(z) for z in req['remove']]
                        req['reactivate'] = [int(z) for z in req['reactivate']]
                        
                        for a in access:
                            # Reactivate
                            if a['status'] == "inactive" and a['user_ID'] in req['reactivate']:
                                queries.append("UPDATE LRP_Group_Access set status='active' where group_ID=%s and user_ID=%s")
                                params.append([misc['group_ID'], a['user_ID']])
                                
                            if a['status'] == "active" and a['user_ID'] in req['remove'] and a['user_ID'] != user_obj['ID']:
                                queries.append("UPDATE LRP_Group_Access set status='inactive' where group_ID=%s and user_ID=%s")
                                params.append([misc['group_ID'], a['user_ID']])
                            if a['status'] == "active" and a['admin'] == 0 and a['user_ID'] in req['admin']:
                                logging.info("A) status=%s, admin=%s" % (a['status'], a['admin']))
                                queries.append("UPDATE LRP_Group_Access set admin=1 where group_ID=%s and user_ID=%s")
                                params.append([misc['group_ID'], a['user_ID']])
                            elif a['status'] == "active" and a['admin'] == 1 and a['user_ID'] not in req['admin'] and a['user_ID'] != user_obj['ID']:
                                logging.info("B) status=%s, admin=%s" % (a['status'], a['admin']))
                                queries.append("UPDATE LRP_Group_Access set admin=0 where group_ID=%s and user_ID=%s")
                                params.append([misc['group_ID'], a['user_ID']])
                        ex_queries(queries, params)
        
                    elif req['action'] == "add_members":
                        conn, cursor = mysql_connect()
                        cursor.execute("SELECT * from LRP_Users")
                        users = zc.dict_query_results(cursor)
                        cursor.execute("SELECT * from LRP_Group_Access")
                        access = zc.dict_query_results(cursor)
                        cursor.close(); conn.close()
                        
                        next_user_ID = max([z['ID'] + 1 for z in users]) if len(users) > 0 else 1
                    
                        
                        matches = [{'seq': i, 'email': z.strip().lower()} for i, z in enumerate(list(set(re.findall(email_regex, req['emails']))))]
                        if len(matches) == 0:
                            misc['add_members_error'] = "No email addresses were detected in your entry."
                        for m in matches:
                            m['user_exists'] = 1 if m['email'] in [z['email'].strip().lower() for z in users] else 0
                            m['user_ID'] = None; m['access_exists'] = 0; m['access_active'] = 0
                            if m['user_exists']:
                            
                                tmp_user = users[ [z['email'].strip().lower() for z in users].index(m['email']) ] 
                                m['user_ID'] = tmp_user['ID'] 
                                m['access_exists'] = 1 if m['user_ID'] in [z['user_ID'] for z in access if z['group_ID'] == misc['group_ID']] else 0
                                m['access_active'] = 1 if m['user_ID'] in [z['user_ID'] for z in access if z['status'] == "active" and z['group_ID'] == misc['group_ID']] else 0
                            else:
                                random.seed(time.time() + m['seq'] + 9518)
                                m['ab_group'] = min(47, int(random.random()*48.))
                                m['tmp_password'] = create_temporary_password(m['seq'])
                                m['username'] = m['email'].split("@")[0]
                                if m['username'] in [z['username'] for z in users]:
                                    orig = m['username']; seq = 1
                                    while "%s%s" % (orig,seq) in [z['username'] for z in users]:
                                        seq += 1
                                    m['username'] = "%s%s" % (orig,seq)
                            if not m['user_exists']:
                                tmp1 = create_temporary_password()
                                tmp2 = create_temporary_password()
                                m['activation_code'] = "%s%s" % (tmp1, tmp2)
                                
                        misc['users_created'] = len([1 for z in matches if not z['user_exists']])
                        misc['users_added'] = len([1 for z in matches if z['user_exists'] and not z['access_exists']])
                        misc['users_readded'] = len([1 for z in matches if z['user_exists'] and z['access_exists'] and not z['access_active']])
                        misc['users_confirmed'] = len([1 for z in matches if z['user_exists'] and z['access_exists'] and z['access_active']])
                        all_added = misc['users_created'] + misc['users_added'] + misc['users_readded']
                        misc['add_members_msg'] = ""
                        if all_added > 0:
                            misc['add_members_msg'] += " %d users were added to the group." % all_added
                        if misc['users_confirmed'] > 0:
                            misc['add_members_msg'] += "  There were %d users who were already active members of the group." % misc['users_confirmed']
                        misc['add_members_msg'] = misc['add_members_msg'].replace(" 1 users were added"," 1 user was added")  .replace("were 1 users who were already active members","was 1 user that was already an active member")   
                        for m in matches:
                            if m['user_exists']:
                                if m['access_exists']:
                                    queries.append("UPDATE LRP_Group_Access set status='active' where user_ID=%s and group_ID=%s")
                                    params.append([m['user_ID'], misc['group_ID']])
                                    
                                else:
                                    queries.append("INSERT INTO LRP_Group_Access (ID, user_ID, group_ID, status, active, admin) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Group_Access fds), %s, %s, %s, %s, %s)")
                                    params.append([m['user_ID'], misc['group_ID'], 'active', 1, 0])
                                    
                                    queries.append("UPDATE LRP_Users set active_group=%s where ID=%s")
                                    params.append([misc['group_ID'], m['user_ID']])
                            else:
                                
                                queries.append("INSERT INTO LRP_Users (ID, email, active, logins, user_type, password, username, AB_group, date_created, track_GA, active_group, is_admin, activation_code, activated, activation_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
                                params.append([next_user_ID, m['email'], 1, 0, 'team', m['tmp_password'], m['username'], m['ab_group'], datetime.now(), 1, misc['group_ID'], 0, m['activation_code'], 0, 'full'])
                                
                                queries.append("INSERT INTO LRP_Group_Access (ID, user_ID, group_ID, status, active, admin) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Group_Access fds), %s, %s, %s, %s, %s)")
                                params.append([next_user_ID, misc['group_ID'], 'active', 1, 0])
                                
                                queries.append("INSERT INTO LRP_User_Preferences (ID, user_ID, active) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_User_Preferences fds), %s, %s)")
                                params.append([next_user_ID, 1])
                                
                                next_user_ID += 1
                        ex_queries(queries, params)
                    
                        conn, cursor = mysql_connect()
                        cursor.execute("SELECT * from LRP_Email_Templates where active=1")
                        email_templates = zc.dict_query_results(cursor)
                        cursor.close(); conn.close()
                        
                        for m in matches:
                            if not m['user_exists']:
                                msg = email_templates[ [z['template_desc'] for z in email_templates].index('Activate Account') ]
                                msg['email'] = m['email']
                                msg['subject'] = "Your LacrosseReference PRO account is ready"
                                
                                msg['content'] = get_file(msg['bucket'], msg['fname'])
                                msg['content'] = msg['content'].replace("[activation_link]", "https://pro.lacrossereference.com/activate?c=%s" % (url_escape(m['activation_code'])))
                                
                                finalize_mail_send(msg)
                            
                            
                            if not m['access_active']:
                                msg = email_templates[ [z['template_desc'] for z in email_templates].index('Added User to Group') ]
                                msg['email'] = m['email']
                                msg['subject'] = "You've been added to %s" % (user_obj['active_group_name'])
                                
                                msg['content'] = get_file(msg['bucket'], msg['fname'])
                                msg['content'] = msg['content'].replace("[group_name]", user_obj['active_group_name'])
                                
                                finalize_mail_send(msg)
                        
                        
                        if misc['add_members_error'] is None:
                            pass
                        else:
                            misc['emails'] = req['emails']
                
                
                conn, cursor = mysql_connect()
                cursor.execute("SELECT * from LRP_Users")
                users = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Group_Access")
                access = zc.dict_query_results(cursor)
                cursor.close(); conn.close()
            
                user_obj = get_user_obj({'session_ID': session_ID})
            
                for u in user_obj['active_group_members']:
                    user = users[ [z['ID'] for z in users].index(u['user_ID']) ]
                    u['username'] = user['username']
                    u['admin_checked'] = " checked" if u['admin']==1 else ""
                user_obj['active_group_members'] = sorted(user_obj['active_group_members'], key=lambda x:x['username'])    
                
                if len(user_obj['inactive_group_members']) == 0:
                    user_obj['inactive_group_members'] = None
                else:
                    for u in user_obj['inactive_group_members']:
                        user = users[ [z['ID'] for z in users].index(u['user_ID']) ]
                        u['username'] = user['username']
                    user_obj['inactive_group_members'] = sorted(user_obj['inactive_group_members'], key=lambda x:x['username'])
                
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))

            
            else:
                target_template = "index.html"
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        
        
    
    def get(self):
        
        target_template = "index.html"
        
        default_get(self)

class ResendHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "activation_reminder.html"
        
        misc = {'emails': "", 'error': None, 'msg': None}; user_obj = None; queries = []; params = []
    
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                misc['user_ID'] = int(self.request.get('ID'))
                conn, cursor = mysql_connect()
                cursor.execute("SELECT * from LRP_Email_Templates where active=1")
                email_templates = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Users where ID=%s",[misc['user_ID']])
                user = zc.dict_query_results(cursor)[0]
                cursor.close(); conn.close()
                
                
                
                random.seed(time.time() + 110935)
                tmp1 = create_temporary_password()
                tmp2 = create_temporary_password()
                activation_code = "%s%s" % (tmp1, tmp2)
                
               
                
                query = "UPDATE LRP_Users set activation_code=%s where ID=%s"
                param = [activation_code, misc['user_ID']]
                queries.append(query); params.append(param)
                ex_queries(queries, params)

                msg = email_templates[ [z['template_desc'] for z in email_templates].index('Activate Account') ]
                msg['email'] = user['email']
                msg['subject'] = "Your LacrosseReference PRO account is ready (Resend)"
                
                msg['content'] = get_file(msg['bucket'], msg['fname'])
                msg['content'] = msg['content'].replace("[activation_link]", "https://pro.lacrossereference.com/activate?c=%s" % (url_escape(activation_code)))
                
                finalize_mail_send(msg)
                
                misc['msg'] = "Activation email has been resent to %s" % user['email']
                
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))

            
            else:
                target_template = "index.html"
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        
        
    
    def get(self):
        
        target_template = "index.html"
        
        default_get(self)

def default_get(self):
    misc = {'username': '', 'password': '', 'email': '', 'phone': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
    session_ID = self.session.get('session_ID')
    if session_ID not in [None, 0]:
        user_obj = get_user_obj({'session_ID': session_ID})
        if user_obj['auth']:
            target_template = "index.html"
            
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else:
            tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
    else: 
        user_obj = process_non_auth(self)
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
        path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        
                

class TeamsHomeHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        tv = {'user_obj': None, 'misc': {}}
        path = os.path.join("templates", "teams_home.html")
        self.response.out.write(template.render(path, tv))
    
    def get(self):
        misc = {'error': None, 'msg': None}; user_obj = None
        #conn, cursor = mysql_connect()
        
        #cursor.close(); conn.close()
        tv = {'user_obj': user_obj, 'misc': misc}
        path = os.path.join("templates", "teams_home.html")
        self.response.out.write(template.render(path, tv))

def build_preferences_html(user_obj, misc):
    html = ""
    
    if user_obj['user_type'] == "team":
        pref = []
        pref.append({'tag': 'receive_newsletter', 'display': 'Receive Newsletter'})
        for i, p in enumerate(pref):
            html += "<div class='col-12 flex'>"
            if 'mob_display' in p:
                html += "<div class='col-9-6'><span class='font-15 light dtop'>%s</span><span class='font-15 light mob'>%s</span></div>" % (p['dtop_display'], p['mob_display'])
            else:
                html += "<div class='col-9-6'><span class='font-15 light'>%s</span></div>" % p['display']
            
            display_value = user_obj['preferences'][ [z['key'] for z in user_obj['preferences']].index(p['tag'])]['value']
            if p['tag'] == "receive_newsletter":
                display_value = "Yes" if display_value in [None,1] else "No"
            html += "<div class='col-3-6'><span class='font-15'>%s</span></div>" % display_value
            html += "</div>"
                
    return html
    
class AccountHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        tv = {'user_obj': None, 'misc': {}}
        path = os.path.join("templates", "index.html")
        self.response.out.write(template.render(path, tv))
    
            
    def get(self):
        misc = {'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                target_template = "account.html"
                
                conn, cursor = mysql_connect()
                cursor.execute("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)", [1, user_obj['ID'], datetime.now()]); conn.commit()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
                
                profile_keys = ['email', 'username', 'name', 'phone']
                for p in profile_keys:
                    if user_obj[p] is None:
                        user_obj['%s_str' % p] = ""
                    else:
                        user_obj['%s_str' % p] = user_obj[p]
                
                misc['preferences_html'] = build_preferences_html(user_obj, misc)
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                target_template = "index.html"
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
        
            target_template = "index.html"
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        
   
config = {}
if os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/'):
    
    config['webapp2_extras.sessions'] = {
        'secret_key': 'my-super-secret-key',
                    
        'cookie_args': {  'httponly': True, 'secure': True },
    }
else:
    config['webapp2_extras.sessions'] = {
        'secret_key': 'my-super-secret-key',
    }

def handle_404(request, response, exception):
    logging.exception(exception)
    user_obj = process_non_auth(self)
    misc = {'error': None, 'msg': None}
    tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_lurker.html"}
    response.set_status(404)
    path = os.path.join("templates", 'error_404.html'); response.out.write(template.render(path, tv))
    
def handle_500(request, response, exception):
    logging.exception(exception)
    user_obj = get_user_obj()
    misc = {'error': None, 'msg': None}
    if not os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/'):
        misc['error'] = traceback.format_exc()
        txt = misc['error'].split("File")[-1]
        regexes = []
        regexes.append({'regex': re.compile(r'\"(.*?.py)\", (line [0-9]+?), in ([^\s]+?)\s([\s\S]+)', re.IGNORECASE)})
        for r in regexes:
        
            match = r['regex'].search(txt)
            if match:
                sections = []
                sections.append("<div class='col-12' style='padding-bottom: 30px;'><span class='font-15' style='display:contents;'>%s</span></div>" % ("%s - %s" % (match.group(1).split("\\")[-1], match.group(2))))
                sections.append("<div class='col-12' style='padding-bottom: 30px;'><span class='font-15' style='display:contents;'>%s</span></div>" % (match.group(3)))
                sections.append("<div class='col-12' style='padding-bottom: 30px;'><span class='font-24' style='display:contents;'>%s</span></div>" % (match.group(4)))
                sections.append("<div class='col-12' style='padding-top:50px;'><span class='font-12' style='display:contents;'>%s</span></div>" % ((misc['error'])))
                misc['error'] = "".join(sections)
                break
    tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_lurker.html"}
    response.set_status(500)
    path = os.path.join("templates", 'error_general.html'); response.out.write(template.render(path, tv))
    
app = webapp2.WSGIApplication([
    ('/', IndexHandler)
    ,('/forgot', ForgotHandler)
    ,('/account', AccountHandler)
    ,('/query', QueryHandler)
    ,('/login', LoginHandler)
    ,('/logout', LogoutHandler)
    
    ,('/register', RegisterHandler)
    ,('/register_config', RegisterConfigHandler)
    ,('/cart', CartHandler)
    
    ,('/preferences', PreferencesHandler)
    ,('/switch_groups', SwitchGroupsHandler)
    ,('/password', PasswordHandler)
    ,('/profile', ProfileHandler)
    ,('/subscription', SubscriptionHandler)
    
    
    ,('/activate', ActivateHandler)
    ,('/edit_group', EditGroupHandler)
    ,('/create', CreateHandler)
    ,('/admin', AdminHandler)
    ,('/upload', UploadHandler)
    ,('/resend', ResendHandler)
    ,('/view-quote', ViewQuoteHandler)
    ,('/create-quote', CreateQuoteHandler)
    ,('/review-quote', ReviewQuoteHandler)
    
    
    ,('/teamshome', TeamsHomeHandler)
    
    ,('/(product-summary.+)', ProductSummaryHandler)
    
], config=config)

app.error_handlers[500] = handle_500
app.error_handlers[404] = handle_404
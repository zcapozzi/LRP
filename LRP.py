import logging

logging.getLogger().setLevel(logging.DEBUG)
import copy
#import cgi # Candidate for removal (confirmed on 8/16/2019)
#from StringIO import StringIO # Candidate for removal (confirmed on 8/16/2019)


import json

import jinja2

import webapp2
import time, os, datetime, sys
from datetime import datetime, timedelta
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

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

import uuid

# Add any libraries installed in the "lib" folder.
vendor.add('lib')

from google.appengine.api.blobstore import create_gs_key
from google.appengine.api.blobstore import create_gs_key
from google.appengine.api.images import get_serving_url
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.ext.webapp import template
from webapp2 import RequestHandler
import glob
import sqlalchemy
   
template.register_template_library('tags.filters')

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
    
    return user_obj

def finish_misc(misc):
    
    return misc

def get_user_obj(creds=None):
    auth_timeout = 10800000# - 10799
    user_obj = None
    #logging.info(zc.print_dict(creds))
    conn, cursor = cloud_sql_connect()
        
    if creds is not None and 'username' in creds: # User has submitted credentials... 
        
        query = "SELECT * from LRP_Users where active=1 and (LOWER(email)=%s or LOWER(username)=%s)"
        #print creds['username'].lower()
        param = [creds['username'].lower(), creds['username'].lower()]
        cursor.execute(query, param)
        
        user_obj = zc.dict_query_results(cursor)
        logging.info( len(user_obj))
        
        if len(user_obj) > 0:
            user_obj = user_obj[0]
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
            
                if len(user_obj) > 0:
                    user_obj = user_obj[0]
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
    
    cursor.close(); conn.close()
    return user_obj

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



def cloud_sql_connect():

    f = open('client_secrets.json', 'r')
    client_secrets = json.loads(f.read())
    f.close()

    #zc.print_dict(client_secrets)
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
        misc = {}
        session_ID = self.session.get('session_ID')
        if True or session_ID is not None:
            user_obj = get_user_obj({'session_ID': session_ID})
            if True or ('ID' in user_obj and user_obj['ID'] == 1):
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
                query = self.request.get('query')
                
                columns = []
                types = []
                data = []
                mysql_conn,  cursor = cloud_sql_connect()
                
                
                error = None
                cnt = 0
                try:
                    cursor.execute(query)
                    res = cursor.fetchall()
                    data = []
                    num_fields = []
                    columns = []
                    types_ = []
                    
                    if cursor is not None and res is not None:
                        if cursor.description is not None:
                            num_fields = len(cursor.description)
                            columns = [i[0] for i in cursor.description]
                            types_ = [i[1] for i in cursor.description]
                            for t in types_:
                                #logging.info("Convert %d to %s" % (t, field_type[t]))
                                types.append(field_type[t])
                            for i, row in enumerate(res):
                                data.append(row)
                  
                            
                        
                        
                    if res is not None:
                        cnt = len(res)
                    else:
                        cnt = 0
                except Exception, e:
                    try:
                        error = traceback.format_exc()
                    except IndexError:
                        error = traceback.format_exc()

                if query.upper().startswith("ALTER") or query.upper().startswith("INSERT") or query.upper().startswith("UPDATE") or query.upper().startswith("DELETE"):

                        

                    mysql_conn.commit()
                
                cursor.close(); mysql_conn.close()
                 
                 
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc), 'query': query, 'columns': columns, 'types': types, 'data': data, 'error': error, 'cnt': cnt}
                path = os.path.join("templates", "query.html")
                self.response.out.write(template.render(path, tv))
            else:
                user_obj = get_user_obj()
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc)}; path = os.path.join("templates", "svc_mdv_home.html"); self.response.out.write(template.render(path, tv))
        else:
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc), 'query': "", 'columns': [], 'types': [], 'data': [], 'error': "", 'cnt': 0}; path = os.path.join("templates", "svc_mdv_home.html"); self.response.out.write(template.render(path, tv))
            
    def get(self):
            misc = {}
            session_ID = self.session.get('session_ID')
            if True or session_ID is not None:
                user_obj = get_user_obj({'session_ID': session_ID})
                if True or user_obj['ID'] == 1:
                
                    tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc), 'query': "SELECT * from LRP_Users", 'columns': [], 'types': [], 'data': [], 'error': "", 'cnt': 0}; path = os.path.join("templates", "query.html"); self.response.out.write(template.render(path, tv))
                else:
                    tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc)}; path = os.path.join("templates", "index.html"); self.response.out.write(template.render(path, tv))
            else:
                user_obj = get_user_obj()
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc)}
                path = os.path.join("templates", 'index.html'); self.response.out.write(template.render(path, tv))

def get_template(user_obj):
    if user_obj['user_type'] == "individual":
        target_template = "individual_home.html"
    elif user_obj['user_type'] == "team":
        target_template = "team_home.html"
    elif user_obj['user_type'] == "media":
        target_template = "media_home.html"
    elif user_obj['user_type'] == "master":
        target_template = "master_home.html"
    else:
        target_template = "lurker_home.html"
    return target_template

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
        misc = {}
        if self.request.get("username") != "":
            user_obj = get_user_obj({'username': self.request.get("username"), 'password': self.request.get("password")})
            if user_obj['auth']:
                self.session['session_ID'] = user_obj['session_ID']
                
                target_template = get_template(user_obj)
                
                    
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc)}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
            else:
                target_template = "login.html"
                misc['error'] = "We could not find your username/password combination."
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc)}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
        else:
            tv = {'user_obj': None, 'misc': {}}; path = os.path.join("templates", "index.html")
            self.response.out.write(template.render(path, tv))
    
    def get(self):

        target_template = "index.html"
        
        misc = {}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [0, None]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
            
                target_template = get_template(user_obj)
                    
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc)}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc)}
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
        
        misc = {}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID is not None:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc)}
                path = os.path.join("templates", "index.html")
                self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
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
        
        misc = {}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID is not None:
            user_obj = get_user_obj({'session_ID': session_ID})
            
            user_obj['auth'] = False
            self.session['session_ID'] = 0               
            tv = {'user_obj': None, 'misc': finish_misc(misc)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
        else: 
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

def ex_queries(queries, params, desc=None):
    if len(queries) > 0:
        if desc is not None:
            logging.info("  %d queries to upload (%s)..." % (len(queries), desc))
        conn, cursor = cloud_sql_connect();
        cursor.execute("START TRANSACTION")
        for i, (q, p) in enumerate(zip(queries, params)):
            cursor.execute(q, p)
        cursor.execute("COMMIT")
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
        
        conn, cursor = cloud_sql_connect()
        cursor.execute("SELECT * from LRP_Users")
        existing_users = zc.dict_query_results(cursor)
        cursor.close(); conn.close()
        next_ID = len(existing_users) + 1
        
        misc['process_step'] = self.request.get('process_step').strip()
        misc['username'] = self.request.get('username').strip()
        misc['password'] = self.request.get('password').strip()
        misc['email'] = self.request.get('email').strip()
        misc['phone'] = self.request.get('phone').strip()
        email_regex = re.compile(r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,63}$', re.IGNORECASE)
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
            
            target_template = "lurker_home.html"
            
            query = "INSERT INTO LRP_Users (ID, active, logins, email, username, password) VALUES  (%s, %s, %s, %s, %s, %s)"
            param = [next_ID, 1, 0, misc['email'], misc['username'], encrypt(misc['password'], create_cipher())]
            user_obj = {'auth': False, 'last_log_in': None, 'logins': 0, 'user_type': None, 'ID': next_ID, 'email': misc['email'], 'password': misc['password'], 'phone': misc['phone'], 'username': misc['username']}
            user_obj['session_ID'] = "%d%09d" % ((datetime.now() - datetime(1970,1,1)).total_seconds()*1000.0, user_obj['ID'])
            self.session['session_ID'] = user_obj['session_ID']
            
            logging.info(query)
            logging.info(param)
            queries.append(query); params.append(param)
            
            ex_queries(queries, params)
                    
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc)}
        path = os.path.join("templates", target_template)
        self.response.out.write(template.render(path, tv))

    
        
        
    
    def get(self):
        
        target_template = "register_start.html"
        
        misc = {'username': '', 'password': '', 'email': '', 'phone': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID is not None:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                target_template = "index.html"
                misc['msg'] = "You are already registered and logged in."
            
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': None, 'misc': finish_misc(misc)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc)}
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
        misc = {}; user_obj = None
        #conn, cursor = cloud_sql_connect()
        
        #cursor.close(); conn.close()
        tv = {'user_obj': user_obj, 'misc': misc}
        path = os.path.join("templates", "teams_home.html")
        self.response.out.write(template.render(path, tv))

   
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
    user_obj = {} # get_user_obj()
    misc = {}
    tv = {'user_obj': user_obj, 'misc': misc}
    response.set_status(404)
    path = os.path.join("templates", 'error_404.html'); response.out.write(template.render(path, tv))
    
def handle_500(request, response, exception):
    logging.exception(exception)
    misc = {}
    user_obj = {} # get_user_obj()
    tv = {'user_obj': user_obj, 'misc': misc}
    response.set_status(500)
    path = os.path.join("templates", 'error_general.html'); response.out.write(template.render(path, tv))
    
app = webapp2.WSGIApplication([
    ('/', IndexHandler)
    ,('/query', QueryHandler)
    ,('/login', LoginHandler)
    ,('/logout', LogoutHandler)
    ,('/register', RegisterHandler)
    
    
    ,('/teamshome', TeamsHomeHandler)
    
], config=config)
app.error_handlers[404] = handle_404
app.error_handlers[500] = handle_500
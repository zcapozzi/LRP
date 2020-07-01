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
        cursor.execute("SELECT * from LRP_Group_Access where active=1 and user_ID=%s", [user_obj['ID']])
        group_access = zc.dict_query_results(cursor)
        user_obj['groups'] = [z for z in groups if z['ID'] in [y['group_ID'] for y in group_access]]
        user_obj['active_groups'] = [z for z in groups if z['ID'] in [y['group_ID'] for y in group_access if y['status'] == "active"]]
        user_obj['num_active_groups'] = len(user_obj['active_groups'])
        if user_obj['active_group'] is None and user_obj['num_active_groups'] > 0:
            user_obj['active_group'] = user_obj['active_groups'][0]['ID']
        elif user_obj['active_group'] not in [z['ID'] for z in user_obj['active_groups']] and user_obj['num_active_groups'] > 0:
            user_obj['active_group'] = user_obj['active_groups'][0]['ID']
        elif user_obj['active_group'] not in [z['ID'] for z in user_obj['active_groups']] and user_obj['num_active_groups'] == 0:
            user_obj['active_group'] = None
        
            
        if user_obj['active_group'] is None:
            user_obj['active_group_name'] = None
        else:
            for tmp in user_obj['active_groups']:
                tmp['current'] = 0 if tmp['ID'] != user_obj['active_group'] else 1
            user_obj['active_group_name'] = user_obj['groups'][ [z['ID'] for z in user_obj['active_groups']].index(user_obj['active_group']) ]['group_name']
            
        cursor.execute("SELECT * from LRP_Cart", [])
        items = zc.dict_query_results(cursor)
        cursor.execute("SELECT * from LRP_Products", [])
        products = zc.dict_query_results(cursor)
        
        user_obj['cart'] = [z for z in items if z['user_ID'] == user_obj['ID'] and z['active'] == 1]
        for i, p in enumerate(user_obj['cart']):
            p['product'] = products[ [z['ID'] for z in products].index(p['product_ID'])]
            
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
        if True or session_ID is not None:
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
            user_obj = get_user_obj()
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
        if True or session_ID is not None:
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
            user_obj = get_user_obj()
            
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
    if user_obj['user_type'] == "individual":
        target_template = "individual_home.html"
    elif user_obj['user_type'] == "team":
        target_template = "team_home.html"
    elif user_obj['user_type'] == "media":
        target_template = "media_home.html"
    elif user_obj['user_type'] == "master":
        target_template = "master_home.html"
    else:
        target_template = "register_config.html"
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
                
                target_template = get_template(user_obj)
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
            else:
                target_template = "login.html"
                misc['error'] = "We could not find your username/password combination."
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
        else:
            tv = {'user_obj': None, 'misc': {}}; path = os.path.join("templates", "index.html")
            self.response.out.write(template.render(path, tv))
    
    def get(self):
        tmp = 10/0
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
                
                    
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
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
        if session_ID is not None:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", "index.html")
                self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = get_user_obj()
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
        if session_ID is not None:
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
                    logging.info(zc.print_dict(req))
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
                        
                        query = ("INSERT INTO LRP_Users (ID,email,active,logins,user_type,password,username,AB_group,first_name,last_name,phone,date_created,track_GA,is_admin) VALUES ((SELECT count(1)+1 from LRP_Users fds), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
                        param = [req['standalone_email'], 1, 0, req['standalone_user_type'], req['standalone_password'], req['standalone_username'], ab_group, req['standalone_first_name'], req['standalone_last_name'], req['standalone_phone'], datetime.now(), 1, is_admin]
                        #logging.info(query)
                        #logging.info(param)
                        queries.append(query)
                        params.append(param)
                        
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
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
    
    def get(self):
        
        target_template = "index.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None
        misc['create_group_user_display'] = "visible"; misc['create_group_user_tag_display'] = "tag-on"
        misc['create_standalone_user_display'] = "hidden"; misc['create_standalone_user_tag_display'] = "tag-off"
        
        misc['standalone_user_types'] = [{'val': 'team', 'desc': 'Team'}, {'val': None, 'desc': 'Lurker'}, {'val': 'media', 'desc': 'Media'}, {'val': 'individual', 'desc': 'Individual'}]
        session_ID = self.session.get('session_ID')
        if session_ID is not None:
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
            user_obj = get_user_obj()
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
        if session_ID is not None:
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
                
                for u in misc['users']:
                    u['current_group_obj'] = None
                    if u['active_group'] is not None:
                        u['current_group_obj'] = misc['groups'][ [z['ID'] for z in misc['groups']].index(u['active_group']) ]
                misc['display_users'] = sorted(misc['users'], key=lambda x:x['ID'],  reverse=True)[0:10]
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
            else:
                
                target_template = get_template(user_obj)
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
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
        
        misc = {'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID is not None:
            user_obj = get_user_obj({'session_ID': session_ID})
            
            user_obj['auth'] = False
            self.session['session_ID'] = 0               
            tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
        else: 
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

def ex_queries(queries, params, desc=None):
    if len(queries) > 0:
        if desc is not None:
            logging.info("  %d queries to upload (%s)..." % (len(queries), desc))
        conn, cursor = mysql_connect();
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
        
        conn, cursor = mysql_connect()
        cursor.execute("SELECT * from LRP_Users")
        existing_users = zc.dict_query_results(cursor)
        misc['products'] = get_products(cursor, "Data Subscriptions")
        cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
        next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
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
            
            target_template = "register_config.html"
            random.seed(time.time())
            dt = datetime.now()
            query = "INSERT INTO LRP_Users (ID, active, logins, email, username, password, AB_group, date_created) VALUES  (%s, %s, %s, %s, %s, %s, %s, %s)"
            param = [next_ID, 1, 0, misc['email'], misc['username'], encrypt(misc['password'], create_cipher()), min(47, int(random.random()*48.)), dt]
            user_obj = {'date_created': dt, 'auth': False, 'last_log_in': None, 'logins': 0, 'user_type': None, 'ID': next_ID, 'email': misc['email'], 'password': misc['password'], 'phone': misc['phone'], 'username': misc['username']}
            user_obj['session_ID'] = "%d%09d" % ((datetime.now() - datetime(1970,1,1)).total_seconds()*1000.0, user_obj['ID'])
            self.session['session_ID'] = user_obj['session_ID']
            
            logging.info(query)
            logging.info(param)
            queries.append(query); params.append(param)
            
            query = "INSERT INTO LRP_User_Preferences (ID, user_ID, active) VALUES ((SELECT count(1) + 1 from LRP_User_Preferences fds), %s, %s)"
            param = [next_ID, 1]
            queries.append(query); params.append(param)
            ex_queries(queries, params)
                    
            
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
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
            
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = get_user_obj()
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
        if session_ID is not None:
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
                            
                            query = "INSERT INTO LRP_Cart (ID, user_ID, product_ID, status, date_added, price, discount_tag, list_price, active) VALUES ((SELECT count(1)+1 from LRP_Cart fds), %s, %s, %s, %s, %s, %s, %s, %s)"
                            param = [user_obj['ID'], misc['product_ID'], 'added', datetime.now(), price, None, list_price, 1]
                            queries.append(query); params.append(param)
                            logging.info("Query %s w/ %s" % (query, param))
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
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
    def get(self):
        
        target_template = "index.html"
        
        misc = {'username': '', 'password': '', 'email': '', 'phone': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
    
                
        conn, cursor = mysql_connect()
        misc['products'] = get_products(cursor, "Data Subscriptions")
        cursor.close(); conn.close()
        
        session_ID = self.session.get('session_ID')
        if session_ID is not None:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                
                target_template = get_template(user_obj)
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
def pd(d):
    logging.info("\n\n%s\n\n" % zc.print_dict(d))
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
        if session_ID is not None:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()

                
                if self.request.get("action") == "remove_item_from_cart":
                    misc['cart_ID'] = int(self.request.get("cart_ID"))
                    
                    if misc['error'] is None:
                        
                        if misc['cart_ID'] in [z['ID'] for z in user_obj['cart']]:
                            
                            query = "UPDATE LRP_Cart set status='removed' where ID=%s"
                            param = [misc['cart_ID']]
                            queries.append(query); params.append(param)
                            
                            ex_queries(queries, params)
                            logging.info("Query %s w/  %s"% (query, param))
                            
                            user_obj = get_user_obj({'session_ID': session_ID})
                            misc['msg'] = "Item has been removed"
                        else:
                            misc['error'] = "Cart could not be updated."
                        target_template = "cart.html"
                    
                elif self.request.get("action") == "enter_discount":
                    misc['cart_ID'] = int(self.request.get("cart_ID"))
                    misc['product_ID'] = int(self.request.get("product_ID"))
                    misc['discount_tag'] = self.request.get("discount_tag").strip().upper()
                    
                    logging.info("Tag: %s" % misc['discount_tag'])
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
                            
                            ex_queries(queries, params)
                            logging.info("Query %s w/  %s"% (query, param))
                            
                            user_obj = get_user_obj({'session_ID': session_ID})
                            misc['msg'] = "Discount code has been applied."
                        else:
                            misc['error'] = "Discount code could not be applied."
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
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        
    def get(self):
        
        target_template = "cart.html"
        
        misc = {'username': '', 'password': '', 'email': '', 'phone': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID is not None:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
                next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
                cursor.close(); conn.close()
        
                misc['current_items'] = [z for z in misc['products'] if z['ID'] in [y['product_ID'] for y in user_obj['cart'] if y['active'] and y['status'] == "added"]]
                
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                target_template = "index.html"
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
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
        if session_ID is not None:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                target_template = "subscription.html"
                
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
            user_obj = get_user_obj()
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
        if session_ID is not None:
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
                    
                    query = "UPDATE LRP_Users set password=%s where ID=%s"
                    param = [encrypt(misc['new_password'], create_cipher()), user_obj['ID']]
                    queries.append(query); params.append(param)
                    logging.info("Query %s w/ %s" % (query, param))
                    ex_queries(queries, params)
                    misc['msg'] = "Password has been changed."
                            
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
        
            else:
                target_template = "index.html"
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

    def get(self):
        
        target_template = "index.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID is not None:
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
            user_obj = get_user_obj()
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
        if session_ID is not None:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
        
                switch_to_group_ID = int(self.request.get('switch_to_group_ID').strip())
                
                if switch_to_group_ID in [z['ID'] for z in user_obj['active_groups']]:
                    
                
                    conn, cursor = mysql_connect()
                    cursor.execute("UPDATE LRP_Users set active_group=%s", [switch_to_group_ID])
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
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

    def get(self):
        
        target_template = "switch_groups.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID is not None:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                target_template = "switch_groups.html"
                
                if user_obj['active_group'] is None:
                    target_template = "lurker_home.html"
                elif user_obj['num_active_groups'] ==  1:
                    target_template = get_template(user_obj)
                    
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
            user_obj = get_user_obj()
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
        if session_ID is not None:
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
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        
    def get(self):
        
        target_template = "preferences.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None; queries = []; params = []
        session_ID = self.session.get('session_ID')
        if session_ID is not None:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                relevants = get_relevant_preferences(user_obj)
                
                conn, cursor = mysql_connect()
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
            user_obj = get_user_obj()
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
        if session_ID is not None:
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
                
                email_regex = re.compile(r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,63}$', re.IGNORECASE)
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
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        
    def get(self):
        
        target_template = "profile.html"
        
        misc = {'error': None, 'msg': None}; user_obj = None; queries = []; params = []
        session_ID = self.session.get('session_ID')
        if session_ID is not None:
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
                target_template = "index.html"
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = get_user_obj()
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            
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
        target_template = "register_start.html"
        misc = {'error': None}; user_obj = None; queries = []; params = []
        
        conn, cursor = mysql_connect()
        
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
            random.seed(time.time())
            
            
            
            ex_queries(queries, params)
                    
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
        path = os.path.join("templates", target_template)
        self.response.out.write(template.render(path, tv))

    
        
        
    
    def get(self):
        
        target_template = "forgot.html"
        
        misc = {'username': '', 'password': '', 'email': '', 'phone': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID is not None:
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
            user_obj = get_user_obj()
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
        if session_ID is not None:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                target_template = "account.html"
                
                conn, cursor = mysql_connect()
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
            user_obj = get_user_obj()
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
    user_obj = get_user_obj()
    misc = {'error': None, 'msg': None}
    tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_lurker.html"}
    response.set_status(404)
    path = os.path.join("templates", 'error_404.html'); response.out.write(template.render(path, tv))
    
def handle_500(request, response, exception):
    logging.exception(exception)
    user_obj = get_user_obj()
    misc = {'error': None, 'msg': None}
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
    
    
    ,('/create', CreateHandler)
    ,('/admin', AdminHandler)
    
    
    ,('/teamshome', TeamsHomeHandler)
    
], config=config)

app.error_handlers[500] = handle_500
app.error_handlers[404] = handle_404
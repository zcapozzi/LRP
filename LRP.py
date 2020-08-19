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
import stripe
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

def decrypt(st, local_cipher=None):

    if st is None: return None
    if local_cipher is None: local_cipher = create_cipher()
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

def encrypt(st, local_cipher=None):
    if st is None: return None
    if local_cipher is None: local_cipher = create_cipher()
    
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
    
    try:
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
        
        tmp_keys = ['email']
        for k in tmp_keys:
            if k in user_obj:
                user_obj["%s_decrypted" % k] = decrypt(user_obj[k])
        if 'notifications' not in user_obj or user_obj['notifications'] is None or user_obj['notifications'] in ["", []]: 
            user_obj['notifications'] = {}
        else:
            for n in user_obj['notifications']:
                n['display_until'] = "" if 'display_until' not in n or n['display_until'] is None else n['display_until'].strftime("%Y-%m-%d")
                n['first_viewed'] = ""
        user_obj['notifications'] = json.dumps(user_obj['notifications'])
    except Exception:
        logging.error("finish_user_obj fail: %s" % traceback.format_exc())
    return user_obj

def finish_misc(misc, user_obj):
    try:
        if 'handler' not in misc: 
            misc['handler'] = ""
        elif misc['handler'] not in [None, '']:
            misc['handler'] = "?c=%s" % misc['handler']
            
        misc['copyright'] = "&#xA9; LacrosseReference %d" % datetime.now().year
        
        if 'banner_msg' not in misc: misc['banner_msg'] = None
        if 'standalone_user_types' in misc:
            misc['standalone_user_types'] = [{'val': '','desc': ''}] + misc['standalone_user_types']
        
        if 'products' in misc and misc['products'] is not None:
            if user_obj is not None and 'cart' in user_obj and user_obj['cart'] is not None:
                for p in misc['products']:
                    p['in_cart'] = 0
                    if p['ID'] in [z['product_ID'] for z in user_obj['cart'] if z['active'] and z['status'] == "added"]:
                        p['in_cart'] = 1
    
    except Exception:
        logging.error("finish_misc fail: %s" % traceback.format_exc())   
    return misc

def get_user_obj(creds=None):
    auth_timeout = 10800000# - 10799
    user_obj = None
    
    conn, cursor = mysql_connect(); queries = []; params = []
        
    if creds is not None and 'username' in creds: # User has submitted credentials... 
        
        query = "SELECT * from LRP_Users where active=1 and (LOWER(email)=%s or LOWER(username)=%s)"
        #print creds['username'].lower()
        dt = datetime.now()
        tmp_keys = ['username']
        for k in tmp_keys:
            creds["%s_encrypted" % k] =  encrypt(creds[k]).lower()
        param = [creds['username_encrypted'], creds['username_encrypted']]
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
            logging.info("%s--->%s" % (user_obj['password'], decrypt(user_obj['password'])))
            user_obj['password'] = decrypt(user_obj['password'])
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
    else:
        user_obj = {'initials': '','name': None, 'auth': False}
    
    if user_obj['auth']:
        if 'email' in user_obj: 
            profile_keys = ['first_name', 'last_name', 'email', 'phone']
            
            user_obj['profile'] = process_profile([{'key': z, 'value': decrypt(user_obj[z])} for z in profile_keys])
            
            if user_obj['first_name'] is None and user_obj['last_name'] is not None:
                user_obj['name'] = decrypt(user_obj['last_name'])
            elif user_obj['first_name'] is not None and user_obj['last_name'] is None:
                user_obj['name'] = decrypt(user_obj['first_name'])
            elif user_obj['first_name'] is not None and user_obj['last_name'] is not None:
                user_obj['name'] = "%s %s" % (decrypt(user_obj['first_name']), decrypt(user_obj['last_name']))
            else:
                user_obj['name'] = None
            
        else:
            user_obj['profile'] = None
            
        cursor.execute("SELECT * from LRP_Products where active", [])
        products = zc.dict_query_results(cursor)
        cursor.execute("SELECT * from LRP_Subscriptions where active", [])
        subscriptions = zc.dict_query_results(cursor)
        cursor.execute("SELECT * from LRP_Groups where active", [])
        groups = zc.dict_query_results(cursor)
        cursor.execute("SELECT * from LRP_Group_Access where active=1", [])
        all_group_access = zc.dict_query_results(cursor)
        group_access = [z for z in all_group_access if z['user_ID'] == user_obj['ID']]
        user_obj['groups'] = [z for z in groups if z['ID'] in [y['group_ID'] for y in group_access]]
        user_obj['group_IDs'] = [z['ID'] for z in user_obj['groups']]
        user_obj['active_groups'] = [z for z in groups if z['ID'] in [y['group_ID'] for y in group_access if y['status'] == "active"]]
        user_obj['active_group_IDs'] = [z['ID'] for z in user_obj['active_groups']]
        
        user_obj['num_active_groups'] = len(user_obj['active_groups'])
        if user_obj['active_group'] is None and user_obj['num_active_groups'] > 0:
            user_obj['active_group'] = user_obj['active_groups'][0]['ID']
        elif user_obj['active_group'] not in [z['ID'] for z in user_obj['active_groups']] and user_obj['num_active_groups'] > 0:
            user_obj['active_group'] = user_obj['active_groups'][0]['ID']
        elif user_obj['active_group'] not in [z['ID'] for z in user_obj['active_groups']] and user_obj['num_active_groups'] == 0:
            user_obj['active_group'] = None
        
        
        user_obj['all_subscriptions'] = [z for z in subscriptions if z['user_ID'] == user_obj['ID'] or z['group_ID'] in user_obj['group_IDs']]
        user_obj['active_subscriptions'] = [z for z in user_obj['all_subscriptions'] if z['status'] in ["non-renewing", "active"] and z['start_date'] <=  datetime.now() <= z['end_date']]
        user_obj['non_renewed_subscriptions'] = [z for z in user_obj['all_subscriptions'] if z['status'] == "non-renewing" and datetime.now() > z['end_date']]
        
        
        
        user_obj['active_group_members'] = [] 
        user_obj['active_group_num_members'] = "N/A"  
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
        if user_obj['active_group'] not in [-1, '', None] and user_obj['active_group'] in [z['group_ID'] for z in user_obj['active_subscriptions']]:
                
            
            user_obj['active_subscription'] = user_obj['active_subscriptions'][ [z['group_ID'] for z in user_obj['active_subscriptions']].index(user_obj['active_group']) ]
            
            user_obj['active_subscription']['end_date_str'] = None
            if user_obj['active_subscription']['end_date'] is not None:
                user_obj['active_subscription']['end_date_str'] = user_obj['active_subscription']['end_date'].strftime("%b %d, %Y").replace(" 0", " ")
            product = products[ [ z['ID'] for z in products ].index(user_obj['active_subscription']['product_ID']) ]
            user_obj['active_subscription']['is_quotable'] = 1 if product['status'] == "quotable" else 0
        elif len(user_obj['active_subscriptions']) > 0:
            
            user_obj['active_subscription'] = user_obj['active_subscriptions'][0]
            
            user_obj['active_subscription']['end_date_str'] = None
            if user_obj['active_subscription']['end_date'] is not None:
                user_obj['active_subscription']['end_date_str'] = user_obj['active_subscription']['end_date'].strftime("%b %d, %Y").replace(" 0", " ")
            product = products[ [ z['ID'] for z in products ].index(user_obj['active_subscription']['product_ID']) ]
            user_obj['active_subscription']['is_quotable'] = 1 if product['status'] == "quotable" else 0
        for sub in user_obj['active_subscriptions']:
            sub['days_left'] = (sub['end_date'] - datetime.now()).total_seconds() / (3600.*24.)
            sub['expiring'] = 1 if sub['days_left'] < 14 else 0
        
        cursor.execute("SELECT * from LRP_Notifications where (not show_once or not viewed) and (ISNULL(user_ID) or user_ID=%s)", [user_obj['ID']])
        user_obj['notifications'] = zc.dict_query_results(cursor)
        user_obj['notifications'] = [z for z in user_obj['notifications'] if z['display_until'] > datetime.now()]
        cursor.execute("SELECT * from LRP_Cart", [])
        items = zc.dict_query_results(cursor)
        cursor.execute("SELECT * from LRP_Products", [])
        products = zc.dict_query_results(cursor)
        
        user_obj['cart'] = [z for z in items if z['user_ID'] == user_obj['ID'] and z['active'] == 1]
        for i, p in enumerate(user_obj['cart']):
            p['product'] = products[ [z['ID'] for z in products].index(p['product_ID'])]
        
        
        for n in user_obj['notifications']:
            queries.append("UPDATE LRP_Notifications set first_viewed=IFNULL(first_viewed, %s), viewed=1 where ID=%s")
            params.append([datetime.now(), n['ID']])
            
        # Add auto-generated notifications as needed
        if len([z for z in user_obj['active_subscriptions'] if z['status'] != "non-renewing"]) == 0 and len(user_obj['non_renewed_subscriptions']) > 0:
            max_dt = max([z['end_date'] for z in user_obj['non_renewed_subscriptions']])
            max_dt_str = max_dt.strftime("%b %d, %Y").replace(" 0", " ")
            user_obj['notifications'].append({'nospan': 1, 'html': "<FORM id='banner_renew_form' class='no-padding' action='/cart' method=POST><input type=hidden name='action' value='renew_expired' /><span style='padding-left:10px;' class='font-12'> Your subscription(s) expired on %s. Click <a style='cursor:pointer; color: blue; text-decoration: underline; text-decoration-color: blue;' class='text-button' onclick='document.getElementById(\"banner_renew_form\").submit();'>here</a> to renew.</span></FORM>" % max_dt_str})
        if len([1 for z in user_obj['active_subscriptions'] if z['expiring']]) > 0:
            # This should be added as a show_once notification by cron job rather than every time
            """
            min_dt = min([z['end_date'] for z in user_obj['active_subscriptions'] if z['expiring']])
            min_dt_str = min_dt.strftime("%b %d, %Y").replace(" 0", " ")
            
            user_obj['notifications'].append({'nospan': 1, 'html': "<span style='padding-left:10px;' class='font-12'> Your subscription expires on %s. You can make changes to your subscription <a href='/subscription'>here</a>.</span></FORM>" % min_dt_str})
            """
            pass
        
    cursor.close(); conn.close()
    
    ex_queries(queries, params)
    
    return user_obj

def finalize_mail_send(msg):
    API_KEY = client_secrets['web']['SendInBlueAPIKey']
    res = None
    
    url = "https://api.sendinblue.com/v3/smtp/email"

    msg['content_type'] = "textContent"
    if ('html_file' in msg and msg['html_file']) or 'html' in msg:
        msg['content_type'] = "htmlContent"
        #msg['content'] = "".join([z.strip() for z in msg['content'].split("\n") if z.strip() != ""])
        msg['content'] = msg['content'].replace("\r\n", "<BR>").replace("\n", "<BR>")
    else:    
        msg['content'] = msg['content'].replace("\r\n", "\\r\\n").replace("\n", "\\n")
    
    
    db_payload = "{\"sender\":{\"name\":\"LRP Admin\",\"email\":\"admin@lacrossereference.com\"},\"to\":[{\"email\":\"%s\"}],\"%s\":\"%s\",\"subject\":\"%s\"}" % (msg['email'], msg['content_type'], "[removed-content]", msg['subject'])
    if False and msg['email'] not in ["zcapozzi@gmail.com", "zack@lacrossereference.com", "zack@looseleafguide.com", "zack@mainstreetdataguy.com", "bot@lacrossereference.com", "kyle@lacrossereference.com", "guide@looseleafguide.com", "zack@durhamcornholecompany.com"]:
        payload = "{\"sender\":{\"name\":\"LRP Admin\",\"email\":\"admin@lacrossereference.com\"},\"to\":[{\"email\":\"%s\"}],\"bcc\":[{\"email\":\"zcapozzi@gmail.com\",\"name\":\"BCC Zack\"}],\"%s\":\"%s\",\"subject\":\"%s\"}" % (msg['email'], msg['content_type'], msg['content'], msg['subject'])
    else:
        payload = "{\"sender\":{\"name\":\"LRP Admin\",\"email\":\"admin@lacrossereference.com\"},\"to\":[{\"email\":\"%s\"}],\"%s\":\"%s\",\"subject\":\"%s\"}" % (msg['email'], msg['content_type'], msg['content'], msg['subject'])
        
    logging.info(payload)
    headers = {
        'accept': "application/json",
        'content-type': "application/json",
        'api-key': API_KEY
        }

    #logging.info("Send mail with subject %s to %s" % (msg['subject'], msg['email']))
    #logging.info(msg['content'])
    
    email_hash = msg['email'].replace("@", "").replace(".", "").replace("-", "")
    dbrec = {'send_in_blue_ID': None, 'content_type': msg['content_type'], 'content': msg['content'], 'hash': "%s%d%s" % (email_hash, int(time.time()), create_temporary_password()),  'payload': db_payload, 'recipient': msg['email'], 'subject': msg['subject']}
    time.sleep(.01)
    send_mail = True    
    if client_secrets['local']['--no-mail'] in ["Y", 'y', 'yes']:
        send_mail = False
        dbrec['status'] = "not-sent"
        dbrec['success'] = 0
        
    if dbrec['recipient'].split("@")[1] in ['email.com', 'user.com']:
        res = "Success"
        dbrec['success'] = 1
        dbrec['status'] = "test"
        send_mail = False
    
    if send_mail:
        if 'send_date' not in msg:
            dbrec['send_date'] = datetime.now()
        if msg['email'] == "zcapozzi@gmail.com": logging.info(payload)
        response = requests.request("POST", url, data=payload, headers=headers, timeout=2.0)
        regexes = [{'r': '\"messageId\":\"<?(.+?)>?\"'}]
        for r in regexes:
            r['regex'] = re.compile(r['r'], re.IGNORECASE)
            match = r['regex'].search(response.text)
            if match:
                dbrec['send_in_blue_ID'] = match.group(1)
                break
        
        if 'messageId' not in response.text:
            res = "Mail send failed."
            logging.error(response.text)
            dbrec['success'] = 0
            dbrec['status'] = "failed"
        else:
            res = "Success"
            dbrec['status'] = "sent"
            dbrec['success'] = 1
    else:
        logging.info("\n\n\tNO MAIL SEND!!!\n\n")
        res = ""
        
        
    return res, dbrec
        
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
        misc = {'handler': 'query', 'error': None, 'msg': None}
        session_ID = self.session.get('session_ID')
        if True or session_ID not in [None, 0]:
            user_obj = None #get_user_obj({'session_ID': session_ID})
            if True or ('ID' in user_obj and user_obj['ID'] == 1):
                
                conn, cursor = mysql_connect()
                cursor.execute("SHOW TABLES", [])
                misc['tables'] = zc.dict_query_results(cursor)
                cursor.close(); conn.close()
                
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
        misc = {'handler': 'query', 'error': None, 'msg': None}
        session_ID = self.session.get('session_ID')
        if True or session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if True or user_obj['ID'] == 1:
            
                if self.request.get('encrypt') != "":
                    encrypt_user_info()
                
                conn, cursor = mysql_connect()
                cursor.execute("SHOW TABLES", [])
                misc['tables'] = zc.dict_query_results(cursor)
                cursor.close(); conn.close()
 
                
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
def encrypt_user_info():
    lg("Encrypting existing user information...")
    misc = {}
    conn, cursor = mysql_connect()
    cursor.execute("SELECT * from LRP_Users", [])
    misc['users'] = {'data': zc.dict_query_results(cursor), 'table': 'LRP_Users', 'keys': ["email", "username", "phone", "first_name", "last_name", "stripe_customer_id"]}
    cursor.execute("SELECT * from LRP_Quotes", [])
    misc['quotes'] = {'data': zc.dict_query_results(cursor), 'table': 'LRP_Quotes', 'keys': ["user_email"]}
    cursor.execute("SELECT * from LRP_Product_Requests", [])
    misc['requests'] = {'data': zc.dict_query_results(cursor), 'table': 'LRP_Product_Requests', 'keys': ["email"]}
    cursor.close(); conn.close()
    
    tmp = ['users', 'quotes', 'requests']
    
    queries = []; params = []
    fail = False
    for t in tmp:
        
        for k in misc[t]['keys']:
            for d in misc[t]['data']:
                if d[k] not in [None, "None"]:
                    d['%s_encrypted' % k] = encrypt(d[k])
                    d['%s_decrypted' % k] = decrypt(d['%s_encrypted' % k])
                    if d[k] != d['%s_decrypted' % k]:
                        lg("Error encrypting %s in %s ID=%d" % (d[k],  misc[t]['table'], d['ID']))
                        fail = True
                    else:
                        pass
                        #queries.append("UPDATE %s set %s=%%s where ID=%%s" % (misc[t]['table'], k))
                        #params.append([d['%s_encrypted' % k],  d['ID']])
        
    if  False and not fail:
        ex_queries(queries, params)
    
    
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

def transfer_cart_items(self, user_obj):
    queries = []; params = []
    conn, cursor = mysql_connect()
    cursor.execute("SELECT * from LRP_Cart where (user_ID=%s or user_cookie=%s) and status='added' and active=1", [user_obj['ID'], user_obj['user_cookie']])
    cart_items = zc.dict_query_results(cursor)
    cursor.close(); conn.close()
    
    
    for c in cart_items:
        if c['product_ID'] in [z['product_ID'] for z in user_obj['cart'] if z['status'] == "added"]:
            c['in_user_cart'] = 1
            if c['user_ID'] != user_obj['ID']:
                #user_item = user_obj['cart'][ [z['product_ID'] for z in user_obj['cart']].index(c['product_ID']) ]
                queries.append("UPDATE LRP_Cart set status='duplicate', user_cookie=NULL where ID=%s")
                params.append([c['ID']])
        
        else:
            c['in_user_cart'] = 0
            queries.append("UPDATE LRP_Cart set user_ID=%s, user_cookie=NULL where ID=%s")
            params.append([user_obj['ID'], c['ID']])
        

    ex_queries(queries, params)
    if len(queries) > 0:
        user_obj = get_user_obj({'session_ID': user_obj['session_ID']})
    return user_obj
def lg(s):
    logging.info("\n%s\n" % s)
    
def claim_quote(misc, user_obj):
    queries = []; params = []
    group_ID = misc['quote']['group_ID']
    if misc['quote']['trial']:
        # Allow them to get started automatically
        if group_ID is not None:
            if group_ID not in [z['ID'] for z in user_obj['active_groups']]:
                # Add them to the group
                queries.append("INSERT INTO LRP_Group_Access (ID, user_ID, group_ID, status, active, admin) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Group_Access fds), %s, %s, %s, %s, %s)")
                params.append([user_obj['ID'], group_ID, 'active', 1, 1])
                queries.append("UPDATE LRP_Users set active_group=%s where ID=%s")
                params.append([group_ID, user_obj['ID']])
                user_obj['active_group'] = group_ID
                
            elif group_ID != user_obj['active_group']:
                # Set the quoted group to be active
                queries.append("UPDATE LRP_Users set active_group=%s where ID=%s")
                params.append([group_ID, user_obj['ID']])
                user_obj['active_group'] = group_ID
        # Set up the subscription record as needed
        start_date = datetime.now()
        end_date = misc['quote']['trial_end']
            
        
        # Only create a new subscription if there is no existing active subscription for the same group/user and product where the proposed start date is prior to the current end date
        if group_ID is not None:
            tup = (misc['product_ID'], group_ID)
            if tup not in [(z['product_ID'], z['group_ID']) for z in user_obj['active_subscriptions'] if start_date <= z['end_date']]:
                queries.append("INSERT INTO LRP_Subscriptions (ID, active, start_date, end_date, group_ID, product_ID, quote_ID, status, trial) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Subscriptions fds), %s, %s, %s, %s, %s, %s, %s, %s)")
                params.append([1, start_date, end_date, group_ID, misc['product_ID'], misc['quote']['ID'], 'active', 1])
            
        else:
            tup = (misc['product_ID'], user_ID)
            if tup not in [(z['product_ID'], z['user_ID']) for z in user_obj['active_subscriptions'] if start_date <= z['end_date']]:
                queries.append("INSERT INTO LRP_Subscriptions (ID, active, start_date, end_date, user_ID, product_ID, quote_ID, status, trial) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Subscriptions fds), %s, %s, %s, %s, %s, %s, %s, %s)")
                params.append([1, start_date, end_date, user_obj['ID'], misc['product_ID'], misc['quote']['ID'], 'active', 1])
        
        # In case their user type needs to be upgraded
        if user_obj['user_type'] in [None, 'individual', 'media'] and misc['product_user_type'] == "team":
            queries.append("UPDATE LRP_Users set user_type=%s where ID=%s")
            params.append([misc['product_user_type'], user_obj['ID']])
            user_obj['user_type'] = misc['product_user_type']
            
        elif user_obj['user_type'] in [None, 'individual'] and misc['product_user_type'] in ["media", "team"]:
            queries.append("UPDATE LRP_Users set user_type=%s where ID=%s")
            params.append([misc['product_user_type'], user_obj['ID']])
            user_obj['user_type'] = misc['product_user_type']

        
        
    else:
        # Add the subscription to their cart
        if misc['product_ID'] not in [z['product_ID'] for z in user_obj['cart'] if z['status'] == 'added' and z['active']]:
            query = "INSERT INTO LRP_Cart (ID, user_ID, quote_ID, product_ID, status, date_added, price, discount_tag, list_price, active) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Cart fds), %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            param = [user_obj['ID'], misc['quote']['ID'], misc['product_ID'], 'added', datetime.now(), misc['quote']['price'], None, misc['list_price'], 1]
            queries.append(query); params.append(param)
    return misc, user_obj, queries, params
        
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
        misc = {'handler': 'index', 'error': None, 'msg': None}; queries = []; params = []
        if self.request.get("username") != "":
            user_obj = get_user_obj({'username': self.request.get("username"), 'password': self.request.get("password")})
            if user_obj['auth']:
                self.session['session_ID'] = user_obj['session_ID']
                user_obj['user_cookie'] = self.session['cart_cookie']
                
                target_template = get_template(user_obj)
                if self.request.get('from') not in ['', None]:
                    target_template = "%s.html" % self.request.get('from')
                
                misc['login_account_msg'] = "Login was successful"
                # If this is because someone is claiming a quote, process all that stuff
                if self.request.get('from') == "quote":
                    misc['quote_hash'] = self.request.get('quote_hash')
                    misc = display_quote(misc)
                    
                    # Make sure that the user is associated with the given quote hash
                    if 'quote' in misc and misc['quote'] is not None:
                        misc, user_obj, new_queries, new_params = claim_quote(misc, user_obj)
                        queries += new_queries; params += new_params
                    
                    else:
                        misc['login_account_msg'] = None
                        misc['login_account_error'] = "Login was successful, but account updates were not finalized."
                        logging.error("%s Email: %s" % (misc['login_account_error'], user_obj['email']))
                        
                    ex_queries(queries, params)
                    target_template = get_template(user_obj)
                    
                    # If there is not a free trial, then they are still just a lurker that should see their quote again.
                    if 'quote' in misc and misc['quote'] is not None and not misc['quote']['trial']:
                        target_template = "quote.html"
                    
                stripe.api_key = client_secrets['web']['StripeServerKey']
                misc['clientKey'] = client_secrets['web']['StripeClientKey']
                
                # Transfer any cart items held prior to log-in to the actual user's cart
                user_obj = transfer_cart_items(self, user_obj)
                
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"  }
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
            else:
                target_template = "login.html"
                if self.request.get('from') not in ['', None]:
                    target_template = "%s.html" % self.request.get('from')
                misc['login_tag_display'] = "tag-on"
                misc['login_display'] = "visible"
                misc['create_account_tag_display'] = "tag-off"
                misc['create_account_display'] = "hidden"
                
                misc['error'] = "We could not find your username/password combination."
                
                misc['login_account_error'] = misc['error']
                
                if self.request.get('from') == "quote":
                    misc['quote_hash'] = self.request.get('quote_hash')
                    misc = display_quote(misc)

                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
        else:
            tv = {'user_obj': None, 'misc': {}, 'layout': 'layout_no_auth.html'}; path = os.path.join("templates", "index.html")
            self.response.out.write(template.render(path, tv))
    
    def get(self):
        
        target_template = "index.html"
        
        misc = {'handler': 'index', 'error': None, 'msg': None}; user_obj = None
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
                
                user_obj['email_decrypted'] = decrypt(user_obj['email'])
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html" }
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
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
        
        misc = {'handler': 'login', 'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
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
        
        misc = {'handler': 'create', 'error': None, 'msg': None}; user_obj = None
        misc['create_group_user_display'] = "visible"; misc['create_group_user_tag_display'] = "tag-on"
        misc['create_standalone_user_display'] = "hidden"; misc['create_standalone_user_tag_display'] = "tag-off"
        
        misc['standalone_user_types'] = [{'val': 'team', 'desc': 'Team'}, {'val': None, 'desc': 'Lurker'}, {'val': 'media', 'desc': 'Media'}, {'val': 'individual', 'desc': 'Individual'}]
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth'] and user_obj['is_admin']:
                req = dict_request(self.request)
                queries = []; params = []
                
                misc['team_ID'] = int(req['team_select'])
                misc['group_ID'] = None
                # GET USEFUL INFO FROM THE DB
                if req['action'].startswith("create"):
                    conn, cursor = mysql_connect()
                    cursor.execute("SELECT * from LRP_Users")
                    users = zc.dict_query_results(cursor)
                    cursor.execute("SELECT * from LRP_Groups order by group_name asc")
                    misc['groups'] = zc.dict_query_results(cursor)
                    cursor.execute("SELECT * from LRP_Group_Access")
                    access = zc.dict_query_results(cursor)
                    cursor.close(); conn.close()
                    
                    for g in misc['groups']:
                        g['selected'] = " selected" if misc['team_ID'] == g['team_ID'] else ""
                        if misc['team_ID'] == g['team_ID']:
                            misc['group_ID'] = g['ID']
                # CREATE A STANDALONE USER
                if req['action'] == "create_standalone_user":
                    misc['create_group_user_display'] = "hidden";  misc['create_standalone_user_display'] = "visible"
                    misc['create_group_user_tag_display'] = "tag-off";  misc['create_standalone_user_tag_display'] = "tag-on"
                    
                    map_fields = ["standalone_email", "standalone_user_type", "standalone_username", "standalone_first_name", "standalone_last_name", "standalone_phone", "standalone_password", "standalone_is_admin", "standalone_subscription", "standalone_trial"]
                    for m in map_fields:
                        misc[m] = None
                        if m in req:
                            misc[m] = req[m]
                    
                    for o in misc['standalone_user_types']:
                        o['selected'] = ""
                        if o['val'] == req['standalone_user_type'] or o['val'] is None and req['standalone_user_type'] == "None":
                            o['selected'] = " selected"
                    
                    misc['standalone_is_admin_checked'] = " checked" if misc['standalone_is_admin'] in ["on", 1, True] else ""
                    misc['standalone_subscription_checked'] = " checked" if misc['standalone_subscription'] in ["on", 1, True] else ""
                    misc['standalone_trial_checked'] = " checked" if misc['standalone_trial'] in ["on", 1, True] else ""
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
                    elif misc['team_ID'] == -1 and  misc['standalone_subscription'] in ["on", 1, True]:
                        misc['error'] = "Please select the team to go with the subscription"
                        go_on = False
                    elif misc['team_ID'] > -1 and  misc['standalone_trial'] not in ["on", 1, True] and misc['standalone_subscription'] not in ["on", 1, True]:
                        misc['error'] = "To set the user as a non-lurker, specify whether it's a trial or a paid subscription."
                        go_on = False
                    elif req['standalone_user_type'] not in ['',"None"] and misc['team_ID'] == -1:
                        misc['error'] = "If there isn't a subscription, the user must be set to Lurker"
                        go_on = False
                    elif req['standalone_user_type'] in ['',"None"] and misc['team_ID'] > -1:
                        misc['error'] = "The user can't be a Lurker if they have a subscription."
                        go_on = False
                    
                    
                    pd(misc)    
                    if req['standalone_first_name'] == "": req['standalone_first_name'] = None
                    if req['standalone_last_name'] == "": req['standalone_last_name'] = None
                    tmp_keys = ['standalone_email', 'standalone_password', 'standalone_username', 'standalone_first_name', 'standalone_last_name', 'standalone_phone']
                    for k in tmp_keys:
                        req["%s_encrypted" % k] =  encrypt(req[k])
                    
                    if go_on:
                        product_ID = None
                        if req['standalone_user_type'] == "individual":
                            product_ID = 1
                        elif req['standalone_user_type'] == "media":
                            product_ID = 2
                        elif req['standalone_user_type'] == "team":
                            product_ID = 3
                        ab_group = min(47, int(random.random()*48.))
                        
                        if req['standalone_user_type'] == "": req['standalone_user_type'] = None
                        query = ("INSERT INTO LRP_Users (ID, email, active, logins, user_type, password, username, AB_group, first_name, last_name, phone, date_created, track_GA, is_admin, activated) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Users fds), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
                        param = [req['standalone_email_encrypted'], 1, 0, req['standalone_user_type'], req['standalone_password_encrypted'], req['standalone_username_encrypted'], ab_group, req['standalone_first_name_encrypted'], req['standalone_last_name_encrypted'], req['standalone_phone_encrypted'], datetime.now(), 1, is_admin, 1]
                        
                        queries.append(query)
                        params.append(param)
                        misc['msg'] ="User %s has been created. Reminder that no email went out." % (req['standalone_username'])
                        
                        queries.append("INSERT INTO LRP_User_Preferences (ID, user_ID, active) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_User_Preferences fds), (SELECT max(ID) from  LRP_Users fdsa), %s)")
                        params.append([1])
                        
                        if misc['standalone_subscription'] in ["on", 1, True]:
                                
                            start_date = datetime.now(); end_date = start_date + timedelta(days=365)
                            queries.append("INSERT INTO LRP_Subscriptions (ID, user_ID, active, start_date, end_date, group_ID, product_ID, status, trial, price_paid) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Subscriptions fds), (SELECT max(ID) from  LRP_Users fdsa), %s, %s, %s, %s, %s, %s, %s, %s)")
                            params.append([1, start_date, end_date, misc['group_ID'], product_ID, 'active', 0, 0.])
                            
                        if misc['standalone_trial'] in ["on", 1, True]:
                                
                            start_date = datetime.now(); end_date = start_date + timedelta(days=30)
                            queries.append("INSERT INTO LRP_Subscriptions (ID, user_ID, active, start_date, end_date, group_ID, product_ID, status, trial) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Subscriptions fds), (SELECT max(ID) from  LRP_Users fdsa), %s, %s, %s, %s, %s, %s, %s)")
                            params.append([1, start_date, end_date, misc['group_ID'], product_ID, 'active', 1])
                            
                        
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
        
        misc = {'handler': 'create', 'error': None, 'msg': None}; user_obj = None
        misc['create_group_user_display'] = "visible"; misc['create_group_user_tag_display'] = "tag-on"
        misc['create_standalone_user_display'] = "hidden"; misc['create_standalone_user_tag_display'] = "tag-off"
        
        misc['standalone_user_types'] = [{'val': 'team', 'desc': 'Team'}, {'val': None, 'desc': 'Lurker'}, {'val': 'media', 'desc': 'Media'}, {'val': 'individual', 'desc': 'Individual'}]
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth'] and user_obj['is_admin']:
                target_template = "create.html"
                
                conn, cursor = mysql_connect()
                cursor.execute("SELECT * from LRP_Users")
                misc['users'] = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Groups order by group_name asc")
                misc['groups'] = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Group_Access")
                misc['access'] = zc.dict_query_results(cursor)
                cursor.close(); conn.close()
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
                path = os.path.join("templates", target_template)
                self.response.out.write(template.render(path, tv))
            else:
                
                target_template = get_template(user_obj)
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
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
        misc = {'handler': 'admin', 'error': None, 'msg': None}; user_obj = None
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
        path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
    
    def get(self):
        
        target_template = "admin.html"
        
        misc = {'handler': 'admin', 'error': None, 'msg': None}; user_obj = None
        local = not os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/')
        session_ID = self.session.get('session_ID')
        if local or session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if local or (user_obj['auth'] and user_obj['is_admin']):
      
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
                    u['activation_code'] = url_escape(u['activation_code'])
                    u['last_log_in'] = "" if u['last_log_in'] is None else u['last_log_in'].strftime("%b %d, %Y")
                    u['date_created'] = "" if u['date_created'] is None else u['date_created'].strftime("%b %d, %Y")
                    u['password_decrypted'] = decrypt(u['password'])
                    u['username_decrypted'] = decrypt(u['username'])
                    u['email_decrypted'] = decrypt(u['email'])
                    u['first_name_decrypted'] = decrypt(u['first_name'])
                    u['last_name_decrypted'] = decrypt(u['last_name'])
                    u['current_group_obj'] = None
                    if u['active_group'] is not None:
                        u['current_group_obj'] = misc['groups'][ [z['ID'] for z in misc['groups']].index(u['active_group']) ]
                misc['display_users'] = sorted(misc['users'], key=lambda x:x['ID'],  reverse=True)[0:15]
                misc['display_groups'] = sorted(misc['groups'], key=lambda x:x['ID'],  reverse=True)[0:15]
                
                if self.request.get("c") not in [None, '']:
                    target_template = self.request.get("c") + ".html"
                    misc['users_json'] = json.dumps(misc['users'])
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
            
class TermsHandler(webapp2.RequestHandler):
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
        default_get(self)
    
    def get(self):
        
       
        misc = {'handler': 'terms', 'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                user_obj['user_cookie'] = None
                layout = "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"
            else:
                user_obj = process_non_auth(self); user_obj['ID'] = None
                layout = "layout_no_auth.html"
        else: 
            user_obj = process_non_auth(self); user_obj['ID'] = None
            layout = "layout_no_auth.html"
        
        misc['terms'] = []
        section = {'title': 'Introduction and Acceptance of Agreement'}
        section['content'] = "By accessing and using this service, you accept and agree to be bound by the terms and provision of this agreement. In addition, when using these particular services, you shall be subject to any posted guidelines or rules applicable to such services. Any participation in this service will constitute acceptance of this agreement. If you do not agree to abide by the above, please do not use this service."
        section['plain'] = "I'm not going to be a jerk. I hope you won't either. If you were planning to be a jerk, please do it somewhere else."
        misc['terms'].append(section)
        section = {'title': 'Privacy Practices'}
        section['content'] = "Certain registration information and other information about you may be collected by LacrosseReference through your use of this website. Our <a href='/privacy'>Privacy Policy</a> details what we capture and how we use it."
        section['plain'] = "I will never sell or share any user information with anyone else for any reason. I only collect information needed to make the site work smoothly and to facilitate payment."
        misc['terms'].append(section)
        section = {'title': 'Limitation of Liability or Disclaimers'}
        section['content'] = "This site and its components are offered for informational purposes only; this site shall not be responsible or liable for the accuracy, usefulness or availability of any information transmitted or made available via the site, and shall not be responsible or liable for any error or omissions in that information."
        section['plain'] = "I have always done my best to make sure that the information and calculations I publish are correct. But I'm not perfect. If I notice an error or if someone points it out to me, I'll do my best to fix it ASAP."
        misc['terms'].append(section)
        section = {'title': 'Intellectual Property Rights'}
        section['content'] = "The Site and its original content, features, and functionality are owned by LacrosseReference and are protected by international copyright, trademark, patent, trade secret, and other intellectual property or proprietary rights laws."
        section['plain'] = "I'm happy to have you share the information and insights presented on the site, but do not copy and republish my work without attribution."
        misc['terms'].append(section)
        section = {'title': 'Advertising and Endorsements'}
        section['content'] = "I am not accepting any advertisers nor am I soliciting any endorsements of the LacrosseReference PRO service. This entire project is about creating a product that is valuable to the users, so the only monetary inducements should be from the users themselves."
        section['plain'] = "I actually wrote this one, so nothing to add here."
        misc['terms'].append(section)
        section = {'title': 'Payment Terms'}
        sub_sections = []
        sub_sections.append({'sub_title': "Billing", 'content': "You may purchase a Paid Subscription by paying a subscription fee in advance on an annual basis or some other recurring interval disclosed to you prior to your purchase<BR><BR>I may change the price for the Paid Subscriptions, including recurring subscription fees, from time to time and will communicate any price changes to you in advance and, if applicable, how to accept those changes. Price changes will take effect at the start of the next subscription period following the date of the price change. Subject to applicable law, you accept the new price by continuing to use the LacrosseReference PRO Service after the price change takes effect. If you do not agree with a price change, you have the right to reject the change by unsubscribing from the Paid Subscription prior to the price change going into effect."})

        sub_sections.append({'sub_title': "Renewal / Cancellation", 'content': "Your payment to LacrosseReference will automatically renew at the end of the applicable subscription period, unless you cancel your Paid Subscription before the end of the then-current subscription period by clicking <a href='subscription'>here</a> (logged-in users only). The cancellation will take effect the day after the last day of the current subscription period, and your account will be limited to non-paid features. A full refund will be granted, no questions asked, at any time.<BR><BR>If you have purchased a reduced-price Paid Subscription using a discount code, your renewal price will be automatically raised to the prevailing price when your subscription period ends."})
        for s in sub_sections:
            s['html'] = "<span class='font-15 bold contents'>{}</span><BR><BR><span class='font-15 contents'>{}</span>".format(s['sub_title'], s['content'])
        section['content'] = "<BR><BR>".join([z['html'] for z in sub_sections])
        section['plain'] = "To make things easier on both of us, your account will auto-renew each year, which means we will automatically charge your credit card or payment account when the time comes.<BR><BR>But if you would like a refund for a subscription prior to the end of the subscription period, just ask. Refunds for current subscriptions (as opposed to prior years) will be granted no questions asked."
        misc['terms'].append(section)
        section = {'title': 'Termination'}
        section['content'] = "We may terminate your access to the Site, without cause or notice, which may result in the forfeiture and destruction of all information associated with your account. All provisions of this Agreement that, by their nature, should survive termination shall survive termination, including, without limitation, ownership provisions, warranty disclaimers, indemnity, and limitations of liability."
        section['plain'] = "Again, don't be a jerk. If you are a jerk, I'll refund your money and deactivate your account. Life's too short to deal with jerks."
        misc['terms'].append(section)
        section = {'title': 'Notification of Changes'}
        section['content'] = "I reserve the right to change these conditions from time to time if needed and your continued use of the site will signify your acceptance of any adjustment to these terms. If there are any changes to the <a href='/privacy'>privacy policy</a>, I will announce that these changes have been made on the home page and on other key pages on the site. If there are any changes in how I use my customers' information, notification by email will be made to those affected by the change. Any changes to the <a href='/privacy'>privacy policy</a> will be posted on the site 30 days prior to these changes taking place."
        section['plain'] = "I'm not sure what would change, but if anything important does, I'll let you know. But I'm not going to start selling/sharing user data or anything, so if there are changes, they'll be minor."
        misc['terms'].append(section)
        section = {'title': 'Contact Information'}
        section['content'] = "To contact me with any questions,  suggestions, recommendations, complaints, etc, use this <a href='/contact'>contact form</a>."
        section['plain'] = None
        misc['terms'].append(section)
        
        for i, s in enumerate(misc['terms']):
            s['seq'] = i+1
        
            
        
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
        path = os.path.join("templates", "terms.html"); self.response.out.write(template.render(path, tv))
        
class PrivacyHandler(webapp2.RequestHandler):
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
        default_get(self)
    
    def get(self):
        
       
        misc = {'handler': 'privacy', 'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                user_obj['user_cookie'] = None
                layout = "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"
            else:
                user_obj = process_non_auth(self); user_obj['ID'] = None
                layout = "layout_no_auth.html"
        else: 
            user_obj = process_non_auth(self); user_obj['ID'] = None
            layout = "layout_no_auth.html"
        
        misc['terms'] = []
        section = {'title': 'Personal Information'}
        section['content'] = "To create your account, I have to store some basic information. I have tried to collect only what is needed. An email address is the only thing I require because obviously, the site would not work otherwise. Your name and phone number can be stored, but they aren't required. If you update your account information, having those pieces of information will make it easier should I need to contact you or vice versa, but you are under no obligation to share them.<BR><BR>Your use of this site is completely confidential. I may share summary statistics about number of users, but I would never share any information about the individuals or teams that subscribe to the site."
        misc['terms'].append(section)
        section = {'title': 'Payment Information'}
        section['content'] = "Credit card and other payment account information is stored (not in plain-text) in our database to enable easy renewals. This information is encrypted and only used to process payments."
        misc['terms'].append(section)
        section = {'title': 'Usage Information'}
        section['content'] = "I keep track of some usage information as a way to understand how users use the site. This is basic stuff like the number of times a user takes a certain action or views a certain report/visualization/etc. These actions are tagged with a timestamp, but I do not capture anything about the device or the device's location."
        misc['terms'].append(section)
        section = {'title': 'Contact Policy'}
        section['content'] = "I may reach out to users via email from time to time as a way to understand how they like using the service, but I will never call you unless you ask me to."
        misc['terms'].append(section)
        section = {'title': 'Deletion Policy'}
        section['content'] = "I am happy to totally delete your information from the site if you decide that you want to cancel the account. I will make sure that the information is purged within 7 days of receiving the request (barring unforeseen circumstances)."
        misc['terms'].append(section)
        section = {'title': 'Contact me with any Questions'}
        section['content'] = "I am more than happy to answer any questions related to this privacy policy. To get in touch, use this <a href='/contact'>contact form</a>."
        section['plain'] = None
        misc['terms'].append(section)
        
        
        for i, s in enumerate(misc['terms']):
            s['seq'] = i+1
        
            
        
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
        path = os.path.join("templates", "privacy.html"); self.response.out.write(template.render(path, tv))
        
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
    
        misc = {'handler': 'activate', 'error': None, 'code_error': None, 'msg': None}; user_obj = None
        queries = []; params = []
        
        target_template = "activated.html"
        
        
        misc['user_ID'] = int(self.request.get('user_ID').strip())
        misc['username'] = self.request.get('username').strip()
        misc['password'] = self.request.get('password').strip()
        misc['phone'] = self.request.get('phone').strip()
        
        conn, cursor = mysql_connect()
        cursor.execute("SELECT * from LRP_Users where ID!=%s", [misc['user_ID']])
        existing_users = zc.dict_query_results(cursor)
        cursor.execute("SELECT b.group_type 'group_type' from LRP_Group_Access a, LRP_Groups b where a.group_ID=b.ID and b.active and a.user_ID=%s and a.active group by b.group_type", [misc['user_ID']])
        access = zc.dict_query_results(cursor)
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
            
            tmp_keys = ['username', 'phone', 'password']
            for k in tmp_keys:
                misc["%s_encrypted" % k] =  encrypt(misc[k])
                
            misc['user_type'] = None
            if 'team' in [z['group_type'] for z in access]:
                misc['user_type'] = "team"
            elif 'media' in [z['group_type'] for z in access]:
                misc['user_type'] = "media"
            elif 'basic' in [z['group_type'] for z in access]:
                misc['user_type'] = "individual"
            
                
            query = "UPDATE LRP_Users set username=%s, user_type=%s, password=%s, activated=%s, phone=%s where ID=%s"
            param = [misc['username_encrypted'], misc['user_type'], misc['password_encrypted'], 1, misc['phone_encrypted'], misc['user_ID']]
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
        
       
        misc = {'handler': 'activate', 'error': None, 'code_error': None, 'msg': None}; user_obj = None
        queries = []; params = []
        
        
        
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
            
                user_obj = logout(self, user_obj)
                
        misc['activation_code'] = self.request.get('c') 

        lg(misc['activation_code'])
        
        
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
        
        misc = {'handler': 'logout', 'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            
            user_obj = logout(self, user_obj)
            user_obj = process_non_auth(self)
                
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
        
def create_mail_record(dbrec, cursor=None):
    lg("Create mail record")
    if client_secrets['local']['--no-mail'] in ["Y", 'y', 'yes'] or dbrec['recipient'].split("@")[1] in ['email.com', 'user.com']:
        # Don't store it because it's a test email or we are in test mode
        pass
    else:
    
        if 'send_in_blue_ID' not in dbrec: dbrec['send_in_blue_ID'] = None
        
        # Save it to the database
        create_conn = True if cursor is None else False
        
        if create_conn:
            conn, cursor = mysql_connect()

        query = "INSERT INTO LRP_Emails(send_date, active, recipient, subject, hash, email_type, status, send_in_blue_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        param = [dbrec['send_date'], 1, encrypt(dbrec['recipient']), encrypt(dbrec['subject']), dbrec['hash'], dbrec['content_type'], dbrec['status'], dbrec['send_in_blue_ID']]
        
        cursor.execute(query, param)
            
        if create_conn:
            conn.commit()
            cursor.close(); conn.close()
        
        # Save it to the storage buckets
        options = {'retry_params': cloudstorage.RetryParams(backoff_factor=1.1)}
        server_path = "/capozziinc.appspot.com/SentEmailRecords/%s" % (dbrec['hash'])
        
        if os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/'): 
            f_ = cloudstorage.open(server_path, 'w')
            try:
                f_.write(dbrec['content'])   
            except UnicodeDecodeError:
                try:
                    f_.write(dbrec['content'].encode('utf-8'))   
                except UnicodeDecodeError:
                    try:
                        f_.write(dbrec['content'].encode('latin-1'))   
                    except UnicodeDecodeError:
                        logging.error("Could not upload email message (hash=%s) using either utf-8 or latin-1" % dbrec['hash'])
            f_.close()
        
                    
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
        misc = {'handler': 'register', 'error': None, 'msg': None}; user_obj = None; queries = []; params = []
        
        
        stripe.api_key = client_secrets['web']['StripeServerKey']
        misc['clientKey'] = client_secrets['web']['StripeClientKey']
                
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
        
        misc['login_tag_display'] = "tag-off"
        misc['login_display'] = "hidden"
        misc['create_account_tag_display'] = "tag-on"
        misc['create_account_display'] = "visible"
        
        
        
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
        elif misc['username'].lower() in [decrypt(z['username'].lower()) for z in existing_users if z['active'] == 1]:
            misc['username'] = ""
            misc['error'] = "Username is not available."
        elif misc['email'].lower() in [decrypt(z['email'].lower()) for z in existing_users if z['active'] == 1]:
            misc['email'] = ""
            misc['error'] = "Email is already associated with an account."
            
        
        
        if misc['error'] is None:
            
            target_template = "register_start.html"
            if self.request.get('from') not in ['', None]:
                target_template = "%s.html" % self.request.get('from')
                
            if os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/') or not (misc['username'].startswith("newuser")):
       
                tmp1 = create_temporary_password()
                tmp2 = create_temporary_password()
                activation_code = "%s%s" % (tmp1, tmp2)
            else:
                activation_code = "%s%s" % (misc['username'], datetime.now().strftime("%Y%m%d"))
            random.seed(time.time() + 110935)
            
            dt = datetime.now()
            tmp_keys = ['username', 'email', 'password']
            for k in tmp_keys:
                misc["%s_encrypted" % k] =  encrypt(misc[k])
                
            query = "INSERT INTO LRP_Users (ID, active, logins, email, username, password, AB_group, date_created, activation_code, activated, activation_type) VALUES  (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            param = [next_ID, 1, 0, misc['email_encrypted'], misc['username_encrypted'], misc['password_encrypted'], min(47, int(random.random()*48.)), dt, activation_code, 0, 'final']
            queries.append(query); params.append(param)

            user_obj = {'cart': [], 'date_created': dt, 'user_cookie': self.session.get('cart_cookie'), 'auth': False, 'activated': 0, 'last_log_in': None, 'logins': 0, 'user_type': None, 'ID': next_ID, 'email': misc['email'], 'password': misc['password'], 'phone': misc['phone'], 'username': misc['username'], 'active_groups': [], 'active_group': None}
            user_obj['session_ID'] = "%d%09d" % ((datetime.now() - datetime(1970,1,1)).total_seconds()*1000.0, user_obj['ID'])
            self.session['session_ID'] = user_obj['session_ID']
            
            if self.request.get('from') == "quote":
                misc['quote_hash'] = self.request.get('quote_hash')
                misc = display_quote(misc)    
                
                # Make sure that the user is associated with the given quote hash
                if 'quote' in misc and misc['quote'] is not None:
                    misc, user_obj, new_queries, new_params = claim_quote(misc, user_obj)
                    queries += new_queries; params += new_params
            
            query = "INSERT INTO LRP_User_Preferences (ID, user_ID, active) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_User_Preferences fds), %s, %s)"
            param = [next_ID, 1]
            queries.append(query); params.append(param)
            
            
                    
                    
            ex_queries(queries, params)
            
            # Transfer any cart items held prior to log-in to the actual user's cart
            user_obj = transfer_cart_items(self, user_obj)
            
            msg = email_templates[ [z['template_desc'] for z in email_templates].index('Activate Account') ]
            msg['email'] = misc['email']
            msg['subject'] = "Your LacrosseReference PRO account is ready"
            
            msg['content'] = get_file(msg['bucket'], msg['fname'])
            msg['content'] = msg['content'].replace("[activation_link]", "https://pro.lacrossereference.com/activate?c=%s" % (url_escape(activation_code)))
            
            mail_res, dbrec = finalize_mail_send(msg)
            if mail_res != "": create_mail_record(dbrec)
            
            misc['msg'] = "An account activation link has been sent to the email account specified."
            misc['username'] = ""
            misc['password'] = ""
            misc['email'] = ""
            misc['phone'] = ""
            
            
            misc['create_account_tag_display'] = "tag-off"
            misc['create_account_display'] = "hidden"
            user_obj = get_user_obj({'session_ID': user_obj['session_ID']})
            layout = "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"
            
        else:
            layout = 'layout_no_auth.html'
            user_obj = process_non_auth(self)
            if self.request.get('from') not in ['', None]:
                target_template = "%s.html" % self.request.get('from')
                
            if self.request.get('from') == "quote":
                misc['quote_hash'] = self.request.get('quote_hash')
                misc = display_quote(misc)    
                # Make sure that the user is associated with the given quote hash
                pass    
        misc['create_account_error'] = misc['error']
        misc['create_account_msg'] = misc['msg']
        if target_template == "checkout.html":
            misc['error'] = None; misc['msg'] = None
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
        path = os.path.join("templates", target_template)
        self.response.out.write(template.render(path, tv))

    
        
        
    
    def get(self):
        
        target_template = "register_start.html"
        
        misc = {'handler': 'register', 'username': '', 'password': '', 'email': '', 'phone': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
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
        p['tag'] = p['product_name'].lower().strip()
        
        if p['call_to_action'] == "ADD TO CART" and p['status'] == "pre-register":
            p['call_to_action'] = "GET NOTIFIED"
        
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
        misc = {'handler': 'registerConfig', 'error': None, 'current_items': None}; user_obj = None; queries = []; params = []
        
        
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
        
        misc = {'handler': 'registerConfig', 'username': '', 'password': '', 'email': '', 'phone': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
    
                
        conn, cursor = mysql_connect()
        misc['products'] = get_products(cursor, "Data Subscriptions")
        cursor.close(); conn.close()
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                
                target_template = get_template(user_obj)
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj), 'layout': "layout_no_auth.html"}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_no_auth.html"}
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
        misc = {'handler': 'cart', 'error': None}; user_obj = None; queries = []; params = []
        
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                user_obj['user_cookie'] = None
                layout = "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"
            else:
                user_obj = process_non_auth(self); user_obj['ID'] = None
                layout = "layout_no_auth.html"
        else: 
            user_obj = process_non_auth(self); user_obj['ID'] = None
            layout = "layout_no_auth.html"
        
        conn, cursor = mysql_connect()
        misc['products'] = get_products(cursor, "Data Subscriptions")
        cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
        next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
        cursor.close(); conn.close()

        lg("Action: %s" % self.request.get("action"))
        if self.request.get("action") == "remove_item_from_cart":
            misc['cart_ID'] = int(self.request.get("cart_ID"))
            if 'ID' in user_obj and user_obj['ID'] is not None:
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
            if 'ID' in user_obj and user_obj['ID'] is not None:
                queries.append("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)")
                params.append([4, user_obj['ID'], datetime.now()])
            
            misc['cart_ID'] = int(self.request.get("cart_ID"))
            misc['product_ID'] = int(self.request.get("product_ID"))
            misc['discount_tag'] = self.request.get("discount_tag").strip().upper()
            
            
            tmp_product = misc['products'][ [z['ID'] for z in misc['products']].index(misc['product_ID']) ]
            
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
            
        elif self.request.get("action") == "renew_expired":
            if 'ID' in user_obj and user_obj['ID'] is not None:
                queries.append("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)")
                params.append([10, user_obj['ID'], datetime.now()])
            for sub in user_obj['non_renewed_subscriptions']:
                sub['product'] = misc['products'][ [z['ID'] for z in misc['products']].index(sub['product_ID']) ]
            
            for sub in user_obj['non_renewed_subscriptions']:
                if sub['product_ID'] not in [z['product_ID'] for z in user_obj['cart'] if z['status'] == "added"]:
                    query = "INSERT INTO LRP_Cart (ID, user_ID, product_ID, status, date_added, price, list_price, active) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Cart fds),%s, %s, %s, %s, %s, %s, %s)"
                    param = [user_obj['ID'], sub['product_ID'], 'added', datetime.now(), sub['product']['price'], sub['product']['price'], 1]
                
                    queries.append(query); params.append(param)
            
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
        
        misc = {'handler': 'cart', 'username': '', 'password': '', 'email': '', 'phone': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
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
        target_template = "subscription.html"
        misc = {'handler': 'subscription', 'error': None}; user_obj = None; queries = []; params = []
        
        
        stripe.api_key = client_secrets['web']['StripeServerKey']
        misc['clientKey'] = client_secrets['web']['StripeClientKey']
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                user_obj['email_decrypted'] = decrypt(user_obj['email'])
                
                misc['confirmed'] = self.request.get("confirmed")
            
                conn, cursor = mysql_connect()
                #cursor.execute("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)", [7, user_obj['ID'], datetime.now()]); conn.commit()
                cursor.execute("SELECT * from LRP_Quotes where active=1", [])
                quotes = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Products", [])
                products = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Groups where active", [])
                groups = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Group_Access where active", [])
                access = zc.dict_query_results(cursor)
                cursor.execute("SELECT ID, email from LRP_Users where active", [])
                users = zc.dict_query_results(cursor)
                
                cursor.close(); conn.close()
                
                misc['action'] = self.request.get("action")
                
                sub = user_obj['active_subscription']
                sub['stripe_payment_intent_decrypted'] = decrypt(sub['stripe_payment_intent'])
                pd(sub)
                
                if misc['error'] is None:
                    if misc['action'] == "disable_autorenew" and misc['confirmed'] == "no":
                        # This is where we are confirming that everything we entered was correct
                        misc['confirmed'] = "yes"
                        
                    elif misc['action'] == "set_renewing" and misc['confirmed'] == "no":
                        # This is where we are confirming that everything we entered was correct
                        misc['confirmed'] = "yes"
                      
                    elif misc['action'] == "request_refund" and misc['confirmed'] == "no":
                        # This is where we are confirming that everything we entered was correct
                        misc['confirmed'] = "yes"
                        
                        
                        
                      
                    elif misc['action'] == "disable_autorenew" and misc['confirmed'] == "yes":
                        # This is where we are actually processing the disabling
                        if self.request.get("understand") == "":
                            misc['error'] = "Please confirm by checking the confirmation box"
                        else:
                            queries.append("UPDATE LRP_Subscriptions set status=%s where ID=%s")
                            params.append(["non-renewing", sub['ID']])
                            
                            queries.append("INSERT INTO LRP_Cancellations (ID, active, datestamp, refund, user_ID, group_ID, subscription_ID) VALUES ((SELECT IFNULL(max(ID),0) + 1 from LRP_Cancellations fd), %s, %s, %s, %s, %s, %s)")
                            params.append([1, datetime.now(), 0, user_obj['ID'], sub['group_ID'], sub['ID']])
                                      
                            misc['msg'] = "Thank you. Your subscription is still active, but it won't auto-renew when the period ends."
                            
                            misc['confirmed'] = "no"
                        
                    elif misc['action'] == "set_renewing" and misc['confirmed'] == "yes":
                        # This is where we are actually processing the disabling
                        if self.request.get("understand") == "":
                            misc['error'] = "Please confirm by checking the confirmation box"
                        else:
                            queries.append("UPDATE LRP_Subscriptions set status=%s where ID=%s")
                            params.append(["active", sub['ID']])
                            
                            misc['msg'] = "Thank you. Your subscription is now set to auto-renew when the period ends."
                            
                            misc['confirmed'] = "no"
                        
                    elif misc['action'] == "request_refund" and misc['confirmed'] == "yes":
                        if self.request.get("understand") == "":
                            misc['error'] = "Please confirm by checking the confirmation box"
                        else:
                            # This is where we are actually processing the refund
                            
                            #pd(sub)
                            
                            payment_went_through = False
                            try:
                                refund = stripe.Refund.create(
                                  amount=int(sub['price_paid']*100.),
                                  payment_intent=sub['stripe_payment_intent_decrypted']
                                )
                                r = generate_stripe_response(refund)
                                payment_went_through = True
                                
                            except stripe.error.InvalidRequestError as e:
                                if 'already been refunded' in str(e):
                                    misc['error'] = "This subscription has already been refunded. If this in error, please <a href='https://pro.lacrossereference.com/contact'>contact us</a>."
                                lg(str(e))
                               
                            except Exception as e:
                                misc['error']= "Refund could not be processed automatically. We will handle it manually within 48 hours"
                                lg(str(e))
                            
                            if payment_went_through:
                                if 'success' not in r[0]:
                                    misc['msg'] = None
                                    logging.error(str(r))
                                    misc['error']= "Refund could not be processed automatically. We will handle it manually within 48 hours"
                                else:
                                    queries.append("UPDATE LRP_Subscriptions set status=%s where ID=%s")
                                    params.append(["cancelled", sub['ID']])
                                    
                                    queries.append("INSERT INTO LRP_Cancellations (ID, active, datestamp, refund, user_ID, group_ID, subscription_ID) VALUES ((SELECT IFNULL(max(ID),0) + 1 from LRP_Cancellations fd), %s, %s, %s, %s, %s, %s)")
                                    params.append([1, datetime.now(), 1, user_obj['ID'], sub['group_ID'], sub['ID']])
                                    
                                    if sub['group_ID'] is not None:
                                        group_access = [z['user_ID'] for z in access if z['group_ID'] == sub['group_ID'] and z['status'] == "active" and z['active']]
                                        queries.append("UPDATE LRP_Group_Access set status='inactive' where group_ID=%s")
                                        params.append([sub['group_ID']])
                                        
                                        for u in group_access:
                                            queries.append("UPDATE LRP_Users set user_type=NULL where ID=%s")
                                            params.append([u])    
                                    
                                    else:
                                        queries.append("UPDATE LRP_Users set user_type=NULL where ID=%s")
                                        params.append([user_obj['ID']])
                                        
                                    msg = {'email': user_obj['email_decrypted'], 'subject': "Refund Processed for LacrosseReference PRO", 'content': "Hello,\n\nWe have processed your refund. Please <a href='https://pro.lacrossereference.com/contact'>contact us</a> if, for some reason, the refund hasn't shown up within 1 business day.\n\nThank you for being a valued customer.\n\n-Zack (founder of LacrosseReference)"}
                                    mail_res, dbrec = finalize_mail_send(msg)
                                    if mail_res != "": create_mail_record(dbrec)
                                    target_template = "index.html"
                                    misc['msg'] = "Refund has been processed and sent to %s" % user_obj['email_decrypted']
                                    user_obj = get_user_obj({'session_ID': session_ID})
                                    user_obj['email_decrypted'] = decrypt(user_obj['email'])
                                    
                            misc['confirmed'] = "no"
                          
                        
                    elif misc['action'] == "convert":
                        
                        # Convert a trial subscription to a paid subscription
                        sub = user_obj['active_subscription']
                        
                        product = products[ [z['ID'] for z in products].index(sub['product_ID']) ]
                        if sub['quote_ID'] is not None:
                            quote = quotes[ [z['ID'] for z in quotes].index(sub['quote_ID']) ]
                            new_price = quote['price']
                        else:
                            new_price = product['price']
                            
                        #pd(sub)
                        #pd(quote)
                        #pd(product)
                        if sub['product_ID'] not in [z['product_ID'] for z in user_obj['cart'] if z['status'] == "added" and z['active']]:
                            query = "INSERT INTO LRP_Cart (ID, user_ID, quote_ID, product_ID, status, date_added, price, discount_tag, list_price, active, trial_subscription_ID) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Cart fds), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                            param = [user_obj['ID'], sub['quote_ID'], sub['product_ID'], 'added', datetime.now(), new_price, None, product['price'], 1, sub['ID']]
                            queries.append(query); params.append(param)
                            misc['msg'] = "Your new subscription has been added to your cart."
                            misc['confirmed'] = "no"
                        else:
                            misc['error'] = "This product is already in your cart."
                        
                      
                   
            
                
                 
            
                #queries.append(query); params.append(param)
                ex_queries(queries, params)
                user_obj = get_user_obj({'session_ID': session_ID})
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
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
        
        misc = {'handler': 'subscription', 'error': None, 'confirmed': 'no', 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                target_template = "subscription.html"
                
                conn, cursor = mysql_connect()
                #cursor.execute("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, datestamp)  VALUES (%s, %s, %s)", [7, user_obj['ID'], datetime.now()]); conn.commit()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.close(); conn.close()
                
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
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
        misc = {'handler': 'upload', 'error': None, 'msg': 'N/A'}; user_obj = None; queries = []; params = []
        
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
        
        misc = {'handler': 'upload', 'error': None, 'msg': None}; user_obj = None
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
        misc = {'handler': 'password', 'error': None}; user_obj = None; queries = []; params = []
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                user_obj['password'] = decrypt(user_obj['password'])
        
                
                
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
                    
                    misc['new_password_encrypted'] = encrypt(misc['new_password'])
                    query = "UPDATE LRP_Users set password=%s where ID=%s"
                    param = [misc['new_password_encrypted'], user_obj['ID']]
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
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            target_template = "index.html"
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

    def get(self):
        
        target_template = "index.html"
        
        misc = {'handler': 'password', 'error': None, 'msg': None}; user_obj = None
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

def calc_discount(misc, product):
    misc['list_price'] = product['price']
    misc['list_price_str'] = "${:,.0f}".format(product['price'])
    if product['price'] > misc['price']:
        misc['discount'] = product['price'] - misc['price']
        misc['discount_pct'] = None if product['price'] == 0 else -((misc['price']/product['price'])-1.)
        if misc['discount_pct'] is not None:
            misc['discount_pct_str'] = "%d%%" % (100. * misc['discount_pct'])
    else:
        misc['discount'] = None
        misc['discount_pct'] = None
        misc['discount_pct_str'] = None
    return misc

def create_receipt_msg(misc):
    
    msg = {'html': 1, 'email': misc['receipt_email'], 'subject': "Payment Receipt for LacrosseReference PRO"}
    msg['msg_body'] = "Hi,\n\nI have processed your payment; your receipt is included below. I wanted to say thank you for spending your hard-earned time and money on a LacrosseReference PRO product. I feel a responsibility to my users to create products that they ultimately feel are worth the cost. If you ever feel like my products are not living up to that standard, <a href='https://pro.lacrossereference.com/contact'>please let me know</a>.\n\nThanks again.\n\n- Zack (founder of LacrosseReference)"
    msg['msg_body'].replace("\r\n", "<BR>").replace("\n", "<BR>")
    msg['msg_body_div'] = "<div style=''><span style='display:contents;'>{}</span></div>".format(msg['msg_body'])
                    
    for item in misc['active_cart']:
        item['display_product_name'] = item['product']['product_name']
        if not ("LRP" in item['display_product_name'] or "LacrosseReference" in item['display_product_name']):
            item['display_product_name'] = "LacrosseReference PRO: %s" % item['display_product_name']
        days_left = int((misc['end_date'] - datetime.now()).total_seconds() / (24.*3600.) + .001)
        item['term'] = None   
        if days_left == 365:
            item['term'] = "1 Year"   
        elif days_left in [30, 31]:
            item['term'] = "1 Month"  
        elif days_left in [7]:
            item['term'] = "1 Week"   
    
    quote_content = []
    if len(misc['active_cart']) == 1:
        multiples = False
    else:
        multiples = True
        
    for item in misc['active_cart']:
        if multiples:
            quote_content.append({'label': item['display_product_name']})   
        else:
            quote_content.append({'label': 'Product', 'value': item['display_product_name']})   
        quote_content.append({'label': 'Price', 'value': "${:,.2f}".format(item['price'])})
        if item['term'] is not None:
            quote_content.append({'label': 'Subscription Term', 'value': item['term']})
        quote_content.append({'label': 'Subscription Ends', 'value': misc['end_date_formatted']})

        
    for i, z in enumerate(quote_content):
        
        if 'value' in z:
            z['html'] = "<div style='display:flex; background-color:{};'><div style='width:49%;  margin-left:1%;'><span style='display:contents;'>{}</span></div><div style=''><span style='display:contents;'>{}</span></div></div>".format("#EEE" if not multiples and i % 2 == 0 else "#FFF", z['label'],  z['value'])
        else:
            z['html'] = "<div style='display:flex; background-color:{};'><div style='width:98%;  margin-left:1%;'><span style='display:contents; font-weight:700;'>{}</span></div></div>".format("#EEE" if multiples else "#FFF", z['label'])
    msg['msg_quote_div'] = "".join([z['html'] for i, z in enumerate(quote_content)])
    
    msg['msg_html'] = "\n\n".join([msg['msg_body_div'], msg['msg_quote_div']])
    
    msg['msg_html'] += "\n<div style='display:block'><div style='width:98%; margin-left:1%;'><span style='display:contents;'>Your subscription is valid through the date above. Products automatically renew for the same term on the next day unless otherwise indicated. To modify your subscription (i.e. to disable auto-renewal) login to your <a href='https://pro.lacrossereference.com/account'>account</a> and edit your subscription via the 'Account' page.</span></div></div>"
    
    msg['msg_html'] += "\n<div style='display:block'><div style='width:98%; margin-left:1%;'><span style='display:contents;'>NOTE: This message confirms that during the checkout process you agreed to the Terms in LacrosseReference's <a href='https://pro.lacrossereference.com/terms'>Universal Terms of Service Agreement</a>, <a href='https://pro.lacrossereference.com/privacy'>Privacy Policy</a>, and any other applicable agreements. Your use of these products is governed by the terms of these agreements and policies. If you wish to cancel, we proudly offer a full refund guarantee. This message also confirms that during the checkout process you agreed to enroll your products in our automatic renewal service. This keeps your products up and running, automatically charging then-current renewal fees to your payment method on file, with no further action on your part.</span></div></div>"
    
    msg['msg_html'] += "\n<div style='display:block'><div style='width:98%; margin-left:1%;'><span style='display:contents;'>Please do not reply to this email. Emails sent to this address will not be answered.</span></div></div>"

    address = ""
    msg['msg_html'] += "\n<div style='display:block'><div style='width:98%%; margin-left:1%%;'><span style='display:contents;'>Copyright &#xA9; %d LacrosseReference, LLC. %sAll rights reserved.</span></div></div>" % (datetime.now().year, address)

    msg['msg_html'] = "<HTML>%s</HTML>" % msg['msg_html']
    
    msg['msg_html_safe'] = msg['msg_html'].replace("\n", "<BR>")

    msg['content'] = msg['msg_html_safe']
            
    return msg
    
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
        misc = {'handler': 'reviewQuote', 'error': None}; user_obj = None; queries = []; params = []
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth'] and user_obj['is_admin']:
                
                misc = dict_request(self.request); misc['error'] = None
                misc['handler'] = "reviewQuote"
                misc['price'] = float(misc['price'])
                
                if misc['request_ID'] not in [-1, '', None]:
                    misc['request_ID'] = int(misc['request_ID'])
                else:
                    misc['request_ID'] = None
                    
                misc['product_ID'] = int(misc['product_ID'])
                misc['group_ID'] = int(misc['group_ID'])
                misc['trial'] = int(misc['trial'])
                misc['trial_str'] = "Yes" if misc['trial'] else "No"
                misc['email_decrypted'] = misc['email'].strip().lower()
                
                trial_end_dt = None; valid_until_dt = None
                if misc['trial']:
                    try:
                        trial_end_dt = datetime.strptime(misc['trial_end_str'].replace(" ", "").replace("/", "-").strip(), "%Y-%m-%d")
                        misc['trial_end_formatted'] = datetime.strptime(misc['trial_end_str'].replace(" ", "").replace("/", "-").strip(), "%Y-%m-%d").strftime("%b %d, %Y")
                        if not misc['email_decrypted'].startswith("newuser202") and trial_end_dt < datetime.now():
                            misc['error'] = "Trial End date can't be in the past."
                    except Exception:
                        #logging.info(traceback.format_exc())
                        misc['error'] = "Trial End date must be YYYY-MM-DD."
                try:
                    valid_until_dt = datetime.strptime(misc['valid_until_str'].replace(" ", "").replace("/", "-").strip(), "%Y-%m-%d")
                    misc['valid_until_formatted'] = datetime.strptime(misc['valid_until_str'].replace(" ", "").replace("/", "-").strip(), "%Y-%m-%d").strftime("%b %d, %Y")
                    if not misc['email_decrypted'].startswith("newuser202") and valid_until_dt < datetime.now():
                        misc['error'] = "Valid Until date can't be in the past."
                except Exception:
                    #logging.info(traceback.format_exc())
                    misc['error'] = "Valid Until date must be YYYY-MM-DD."
            
            
                if '[quote-hash-link]' not in misc['msg_body']:
                    misc['error'] = "The message body must contain the tag [quote-hash-link]"
                    
                misc['msg_body_html'] = misc['msg_body'].replace("\r\n", "<BR>").replace("\n", "<BR>")
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT * from LRP_Product_Requests where status='active'", [])
                misc['product_requests'] = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Groups where active=1 order by group_name asc", [])
                groups = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Users where active=1", [])
                users = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Quotes where active=1", [])
                quotes = zc.dict_query_results(cursor)
                cursor.close(); conn.close()
                
                for z in quotes:
                    z['tup'] = (z['request_ID'], z['period'], z['group_ID'], z['user_email'], z['product_ID'])
                product = None
              
                
                user = None; misc['user_ID'] = None
                if 'email' in misc and misc['email'] is not None and misc['email'] in [z['email'] for z in users]:
                    user = users[ [z['email'] for z in users].index(misc['email'])]
                    misc['user_ID'] = user['ID']
                misc['product_name'] = misc['products'][ [z['ID'] for z in misc['products']].index(misc['product_ID']) ]['product_name']
                
                
                misc['context'] = ""
                if misc['request_ID'] not in  ['', None, -1]:
                    request = misc['product_requests'][ [z['ID'] for z in misc['product_requests']].index(misc['request_ID']) ]
                    misc['context'] = decrypt(request['email'])
                    misc['request_team_ID'] = request['team_ID']
                    if misc['request_team_ID'] is not None:
                        misc['context'] += " (team: %s)" % (groups[ [z['team_ID'] for z in groups].index(misc['request_team_ID'])]['group_name'])
                elif misc['email'] not in [None, ''] and misc['group_ID'] not in [None, -1, '']:
                    misc['request_team_ID'] = None
                    misc['context'] = misc['email_decrypted']
                    gr = groups[ [z['ID'] for z in groups].index(misc['group_ID'])]
                    misc['context'] += " (team: %s)" % (gr['group_name'])
                    misc['group_ID'] = gr['ID']        
                else:
                    misc['error'] = "You must select a product request or specify team/email"    
                
                for p in misc['product_requests']:
                    p['selected'] = " selected" if p['ID'] == misc['request_ID'] else ""
                    p['email_decrypted'] = decrypt(p['email'])
                    if p['ID'] == misc['request_ID']:
                        misc['email'] = p['email_decrypted']
                        misc['email_decrypted'] = p['email_decrypted']
                        
                misc['price_type_options'] = self.price_type_options
                for p in misc['price_type_options']:
                    p['selected'] = " selected" if p['value'] == misc['price_type'] else ""
                
                misc['trial_options'] = self.trial_options
                for p in misc['trial_options']:
                    p['selected'] = " selected" if p['value'] == misc['trial'] else ""
                
                for p in misc['products']:
                    p['selected'] = " selected" if p['ID'] == misc['product_ID'] else ""
                    product = p
                    
                
                misc['discount_pct_str'] = None; misc['discount_pct'] = None; misc['discount'] = None; misc['list_price_str'] = None
                if product is not None:
                    misc = calc_discount(misc, product)
                        
                misc['price_str'] = "${:,.0f}".format(misc['price'])
                if misc['action'] == "edit_quote":
                    target_template = "create_quote.html"
                elif misc['action'] in ['resend_quote', "send_quote"]:
                    misc['period'] = None
                    if misc['price_type'] in ["monthly", "annual"]:
                        misc['period'] = datetime.now().strftime("%Y")
                    
                    misc['tup'] = (misc['request_ID'], misc['period'], misc['group_ID'], misc['email'], misc['product_ID'])
                
                
                    if os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/') or not (misc['email'].startswith("newuser")):
                        cur_dt = "%d" % time.time()
                        misc['hash'] = ""
                        for ij in range(10):
                            misc['hash'] += "%s%s" % (cur_dt[ij], create_temporary_password())
                    else:
                        misc['hash'] = "%s%s" % (misc['email'].split("@")[0], datetime.now().strftime("%Y%m%d"))
                    #logging.info("Send the template to the user and record the quote in the DB with hash: %s." % misc['hash'])
                    
                    misc['msg_body_div'] = "<div style=''><span style='display:contents;'>{}</span></div>".format(misc['msg_body'])
                    
                    quote_content = []
                    quote_content.append({'label': '%s Price' % misc['price_type'].title(), 'value': misc['price_str']}) 
                    quote_content.append({'label': 'Number of Users', 'value': "50"}) 
                    if misc['trial']:
                        quote_content.append({'label': 'Free Trial Period Ends', 'value': misc['trial_end_formatted']}) 
                    if product is not None:
                        quote_content.append({'label': 'List Price', 'value': "%s (%s off)" % (misc['list_price_str'],misc['discount_pct_str'])}) 
                    quote_content.append({'label': 'Valid until', 'value': misc['valid_until_formatted']}) 
                    
                    misc['msg_quote_div'] = "".join(["<div style='display:flex; background-color:{};'><div style='width:49%;  margin-left:1%;'><span style='display:contents;'>{}</span></div><div style=''><span style='display:contents;'>{}</span></div></div>".format("#EEE" if i % 2 == 0 else "#FFF", z['label'],  z['value']) for i, z in enumerate(quote_content)])
                    
                    misc['msg_html'] = "\n\n".join([misc['msg_body_div'], misc['msg_quote_div']])
                    misc['msg_html'] = "<HTML>%s</HTML>" % misc['msg_html']
                    
                    link_text = "Set-up your account"
                    if misc['trial']:
                        link_text = "Set-up your trial"
                    
                    misc['msg_html_safe'] = misc['msg_html'].replace("[quote-hash-link]", "<a href='%s'>%s</a>" % (url_escape("https://pro.lacrossereference.com/quote?c=%s" % misc['hash']), link_text)).replace("\n", "<BR>")
                    
                    #logging.info("\n\n%s\n\n" % str([z['tup'] for z in quotes]))
                    if misc['action'] in ["send_quote"] :
                        if misc['tup'] in [z['tup'] for z in quotes]:
                            misc['error'] = "This quote appears to exist in the database already."
                            misc['show_resend_email'] = 1
                            
                            
                    if misc['error'] in ['', None]:
                    
                        with_link = misc['msg_html'].replace("[quote-hash-link]", "<a href='%s'>%s</a>" % (url_escape("https://pro.lacrossereference.com/quote?c=%s" % misc['hash']), link_text))
                        msg = {'html': 1, 'email': misc['email_decrypted'], 'subject': "Your requested quote from LacrosseReference PRO is ready", 'content': with_link}
                        
                        mail_res, dbrec = finalize_mail_send(msg)
                        if mail_res != "": create_mail_record(dbrec)
                        
                        if mail_res == "Success" or not ('--no-mail' not in client_secrets['local'] or client_secrets['local']['--no-mail'] not in ["Y", 'y', 'yes']):
                        
                                
                            if misc['action'] == "send_quote": # If we are resending the quote, we don't need to add it to the DB
                            
                                tmp_keys = ['email']
                                for k in tmp_keys:
                                    misc["%s_encrypted" % k] =  encrypt(misc[k])
                        
                                query = "INSERT INTO LRP_Quotes (ID, active, datestamp, period, product_ID, group_ID, user_ID, user_cookie, user_email, quote_type, price, price_type, request_ID, trial, trial_end, valid_until, hash) VALUES ((SELECT IFNULL(max(ID),0) + 1 from LRP_Quotes fd), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                                param = [1, datetime.now(), misc['period'], misc['product_ID'], misc['group_ID'], misc['user_ID'], None, misc['email_encrypted'], None, misc['price'], misc['price_type'], misc['request_ID'], misc['trial'], trial_end_dt, valid_until_dt, misc['hash']]
                                queries.append(query); params.append(param)
                                misc['msg'] = "Quote has been added to the database and emailed to %s." % misc['email']
                                
                            if misc['action'] == "resend_quote":
                                
                                misc['msg'] = "Quote has been emailed to %s." % misc['email']
                        else:
                            misc['error'] = "Mail Send Failed: %s" % mail_res
                        
                ex_queries(queries, params)
                misc['groups'] = groups
                for g in misc['groups']:
                    g['selected'] = " selected" if g['ID'] == misc['group_ID'] else ""
                    
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
        
        misc = {'handler': 'reviewQuote', 'error': None, 'msg': None}; user_obj = None
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
class CreateRefundHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "admin_subscriptions.html"
        misc = {'handler': 'createRefund', 'error': None}; user_obj = None; queries = []; params = []
        
        stripe.api_key = client_secrets['web']['StripeServerKey']
        misc['clientKey'] = client_secrets['web']['StripeClientKey']
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth'] and user_obj['is_admin']:
        
                misc['subscription_ID'] = int(self.request.get('subscription_ID'))
                misc['action'] = self.request.get('action')
                misc['confirmed'] = self.request.get('confirmed')
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT * from LRP_Subscriptions where active", [])
                misc['subscriptions'] = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Groups where active", [])
                groups = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Group_Access where active", [])
                access = zc.dict_query_results(cursor)
                cursor.execute("SELECT ID, email from LRP_Users where active", [])
                users = zc.dict_query_results(cursor)
                cursor.close(); conn.close()
                
                
                
                for u in users:
                    u['email_decrypted'] = decrypt(u['email'])
                    
                for p in misc['products']:
                    for o in p['offers']:
                        o['date_created'] = "" if o['date_created'] in ["", None] else o['date_created'].strftime("%b %d, %Y").replace(" 0", " ")
                
                
                for sub in misc['subscriptions']:
                    sub['stripe_payment_intent_decrypted'] = decrypt(sub['stripe_payment_intent'])
                    if sub['user_ID'] is not None:
                        sub['user'] = users[ [z['ID'] for z in users].index(sub['user_ID']) ]
                        sub['group'] = None
                        sub['email'] = decrypt(sub['user']['email'])
                        
                    elif sub['group_ID'] is not None:
                        sub['group'] = groups[ [z['ID'] for z in groups].index(sub['group_ID']) ]
                        sub['user'] = None
                        group_access = [z['user_ID'] for z in access if z['admin'] and z['group_ID'] == sub['group_ID'] and z['status'] == "active" and z['active']]
                        sub['emails'] = [z for z in users if z['ID'] in group_access]
                        sub['email'] =  None if len(sub['emails']) != 1 else sub['emails'][0]['email_decrypted']
                        for e in sub['emails']:
                            e['selected'] = ""
                            if self.request.get("selected_email") == e['email_decrypted']: 
                                e['selected'] = " selected" 
                                sub['email'] = e['email_decrypted']
                            
                    sub['display'] = "visible" if misc['subscription_ID'] == sub['ID'] else "hidden"
                    sub['refund_msg'] = self.request.get('refund_msg') if misc['subscription_ID'] == sub['ID'] else ""
                    sub['refund_amount'] = self.request.get('refund_amount') if misc['subscription_ID'] == sub['ID'] else sub['price_paid']
                    sub['start_date_str'] = sub['start_date'].strftime("%b %d, %Y").replace(" 0", " ")
                    sub['end_date_str'] = sub['end_date'].strftime("%b %d, %Y").replace(" 0", " ")
                    sub['start_date'] = None
                    sub['end_date'] = None
                    if sub['user_ID'] is None: sub['user_ID'] = ""
                    if sub['group_ID'] is None: sub['group_ID'] = ""
                    sub['product'] = misc['products'] [ [z['ID'] for z in misc['products']].index(sub['product_ID']) ]
                    
                    sub['product']['date_created'] = ""
                
                misc['subscriptions_json'] = json.dumps(misc['subscriptions'])
                
                
                    
                sub = misc['subscriptions'][ [z['ID'] for z in misc['subscriptions']].index(misc['subscription_ID'])]
                if sub['refund_msg'] in [None,'']:
                    misc['error'] = "Please enter a message to be sent to the user."
                refund_amount_val = None
                if sub['email'] is None:
                    misc['error'] = "Please select the recipient of the refund notification."
                try:
                    refund_amount_val = float(sub['refund_amount'].strip())
                except Exception:
                    misc['error'] = "The refund amount was not valid number."
                if misc['error'] in ['', None]:
                    
                  
                        
                    if misc['action'] == "create_refund" and misc['confirmed'] == "no":
                        # This is where we are confirming that everything we entered was correct
                        misc['confirmed'] = "yes"
                        
                    elif misc['action'] == "create_refund" and misc['confirmed'] == "yes":
                        # This is where we are actually processing the refund
                        misc['msg'] = "Refund has been processed and sent to %s" % sub['email']
                        #pd(sub)
                        
                        refund = stripe.Refund.create(
                          amount=int(refund_amount_val*100.),
                          payment_intent=sub['stripe_payment_intent_decrypted'],
                        )
                        
                        r = generate_stripe_response(refund)
                        lg(str(r))
                        if 'success' not in r[0]:
                            misc['msg'] = None
                            misc['error']= "Refund failed on the stripe side\n\n%s" % str(r)
                        else:
                            queries.append("UPDATE LRP_Subscriptions set status=%s where ID=%s")
                            params.append(["cancelled", sub['ID']])
                                
                            if sub['group_ID'] is not None:
                                group_access = [z['user_ID'] for z in access if z['group_ID'] == sub['group_ID'] and z['status'] == "active" and z['active']]
                                queries.append("UPDATE LRP_Group_Access set status='inactive' where group_ID=%s")
                                params.append([sub['group_ID']])
                                
                                for u in group_access:
                                    queries.append("UPDATE LRP_Users set user_type=NULL where ID=%s")
                                    params.append([u])    
                            
                            else:
                                queries.append("UPDATE LRP_Users set user_type=NULL where ID=%s")
                                params.append([user_obj['ID']])
                                
                            msg = {'email': sub['email'], 'subject': "Refund Processed for LacrosseReference PRO", 'content': sub['refund_msg']}
                            mail_res, dbrec = finalize_mail_send(msg)
                            if mail_res != "": create_mail_record(dbrec)
                        
                        ex_queries(queries, params)
                    elif misc['action'] == "edit_refund":
                        misc['confirmed'] = "no"
                else:
                    misc['confirmed'] = "no"
                
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
        
        target_template = "admin_subscriptions.html"
        
        misc = {'handler': 'createRefund', 'subscription_ID': None, 'confirmed': 'no', 'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth'] and user_obj['is_admin']:
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT * from LRP_Subscriptions where active", [])
                misc['subscriptions'] = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Groups where active", [])
                groups = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Group_Access where active", [])
                access = zc.dict_query_results(cursor)
                cursor.execute("SELECT ID, email from LRP_Users where active", [])
                users = zc.dict_query_results(cursor)
                cursor.close(); conn.close()
                
                for u in users:
                    u['email_decrypted'] = decrypt(u['email'])
                
                for p in misc['products']:
                    for o in p['offers']:
                        o['date_created'] = "" if o['date_created'] in ["", None] else o['date_created'].strftime("%b %d, %Y").replace(" 0", " ")
                for sub in misc['subscriptions']:
                    sub['refund_amount'] = sub['price_paid']
                    if sub['user_ID'] is not None:
                        sub['user'] = users[ [z['ID'] for z in users].index(sub['user_ID']) ]
                        sub['group'] = None
                        sub['email'] = decrypt(sub['user']['email'])
                        
                    elif sub['group_ID'] is not None:
                        sub['group'] = groups[ [z['ID'] for z in groups].index(sub['group_ID']) ]
                        sub['user'] = None
                        
                        group_access = [z['user_ID'] for z in access if z['admin'] and z['group_ID'] == sub['group_ID'] and z['status'] == "active"]
                        sub['emails'] = [z for z in users if z['ID'] in group_access]
                        sub['email'] =  None if len(sub['emails']) != 1 else sub['emails'][0]['email_decrypted']
                        
                    sub['display'] = "hidden"
                    sub['start_date_str'] = sub['start_date'].strftime("%b %d, %Y").replace(" 0", " ")
                    sub['end_date_str'] = sub['end_date'].strftime("%b %d, %Y").replace(" 0", " ")
                    sub['start_date'] = None
                    sub['end_date'] = None
                    if sub['user_ID'] is None: sub['user_ID'] = ""
                    if sub['group_ID'] is None: sub['group_ID'] = ""
                    sub['product'] = misc['products'] [ [z['ID'] for z in misc['products']].index(sub['product_ID']) ]
                    
                    sub['product']['date_created'] = ""
                
                misc['subscriptions_json'] = json.dumps(misc['subscriptions'])
                
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

            
class ExtendSubscriptionHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "admin_subscriptions.html"
        misc = {'handler': 'extendSubscription', 'error': None}; user_obj = None; queries = []; params = []
        
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth'] and user_obj['is_admin']:
        
                misc['subscription_ID'] = int(self.request.get('subscription_ID'))
                misc['action'] = self.request.get('action')
                misc['confirmed'] = self.request.get('confirmed')
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT * from LRP_Subscriptions where active", [])
                misc['subscriptions'] = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Groups where active", [])
                groups = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Group_Access where active", [])
                access = zc.dict_query_results(cursor)
                cursor.execute("SELECT ID, email from LRP_Users where active", [])
                users = zc.dict_query_results(cursor)
                cursor.close(); conn.close()
                
                for u in users:
                    u['email_decrypted'] = decrypt(u['email'])
                
                for p in misc['products']:
                    for o in p['offers']:
                        o['date_created'] = "" if o['date_created'] in ["", None] else o['date_created'].strftime("%b %d, %Y").replace(" 0", " ")
                for sub in misc['subscriptions']:
                    if sub['user_ID'] is not None:
                        sub['user'] = users[ [z['ID'] for z in users].index(sub['user_ID']) ]
                        sub['group'] = None
                        sub['email'] = decrypt(sub['user']['email'])
                        
                    elif sub['group_ID'] is not None:
                        sub['group'] = groups[ [z['ID'] for z in groups].index(sub['group_ID']) ]
                        sub['user'] = None
                        group_access = [z['user_ID'] for z in access if z['admin'] and z['group_ID'] == sub['group_ID'] and z['status'] == "active" and z['active']]
                        sub['emails'] = [z for z in users if z['ID'] in group_access]
                        sub['email'] =  None if len(sub['emails']) != 1 else sub['emails'][0]['email_decrypted']
                        for e in sub['emails']:
                            e['selected'] = ""
                            if self.request.get("selected_email") == e['email_decrypted']: 
                                e['selected'] = " selected" 
                                sub['email'] = e['email_decrypted']
                            
                    sub['display'] = "visible" if misc['subscription_ID'] == sub['ID'] else "hidden"
                    sub['extend_msg'] = self.request.get('extend_msg') if misc['subscription_ID'] == sub['ID'] else ""
                    sub['start_date_str'] = sub['start_date'].strftime("%b %d, %Y").replace(" 0", " ")
                    sub['end_date_str'] = sub['end_date'].strftime("%b %d, %Y").replace(" 0", " ")
                    sub['start_date'] = None
                    sub['end_date'] = None
                    if sub['user_ID'] is None: sub['user_ID'] = ""
                    if sub['group_ID'] is None: sub['group_ID'] = ""
                    sub['product'] = misc['products'] [ [z['ID'] for z in misc['products']].index(sub['product_ID']) ]
                    
                    sub['product']['date_created'] = ""
                
                misc['subscriptions_json'] = json.dumps(misc['subscriptions'])
                
                
                    
                sub = misc['subscriptions'][ [z['ID'] for z in misc['subscriptions']].index(misc['subscription_ID'])]
                if sub['extend_msg'] in [None,'']:
                    misc['error'] = "Please enter a message to be sent to the user."
                end_date = None
                sub['new_date_str'] = self.request.get('new_date_str')
                try:
                    end_date = datetime.strptime(self.request.get("new_date_str"), "%Y-%m-%d")
                except Exception:
                    misc['error'] = "Date must be in the YYYY-MM-DD format"
            
                if sub['email'] is None:
                    misc['error'] = "Please select the recipient of the extension notification."
                
                if misc['error'] in ['', None]:
                    
                  
                        
                    if misc['action'] == "create_extension" and misc['confirmed'] == "no":
                        # This is where we are confirming that everything we entered was correct
                        misc['confirmed'] = "yes"
                        
                    elif misc['action'] == "create_extension" and misc['confirmed'] == "yes":
                        # This is where we are actually processing the extension
                        misc['msg'] = "Extension has been processed and sent to %s" % sub['email']
                        #pd(sub)
                        
                        queries.append("UPDATE LRP_Subscriptions set end_date=%s where ID=%s")
                        params.append([end_date, sub['ID']])
                            
                        
                            
                        msg = {'email': sub['email'], 'subject': "Your LacrosseReference PRO subscription end date has changed", 'content': sub['extend_msg']}
                        mail_res, dbrec = finalize_mail_send(msg)
                        if mail_res != "": create_mail_record(dbrec)
                        
                        ex_queries(queries, params)
                    elif misc['action'] == "edit_extension":
                        misc['confirmed'] = "no"
                else:
                    misc['confirmed'] = "no"
                
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
        
        target_template = "admin_subscriptions.html"
        
        misc = {'handler': 'extendSubscription', 'subscription_ID': None, 'confirmed': 'no', 'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth'] and user_obj['is_admin']:
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT * from LRP_Subscriptions where active", [])
                misc['subscriptions'] = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Groups where active", [])
                groups = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Group_Access where active", [])
                access = zc.dict_query_results(cursor)
                cursor.execute("SELECT ID, email from LRP_Users where active", [])
                users = zc.dict_query_results(cursor)
                cursor.close(); conn.close()
                
                for u in users:
                    u['email_decrypted'] = decrypt(u['email'])
                
                for p in misc['products']:
                    for o in p['offers']:
                        o['date_created'] = "" if o['date_created'] in ["", None] else o['date_created'].strftime("%b %d, %Y").replace(" 0", " ")
                
                for sub in misc['subscriptions']:
                    sub['refund_amount'] = sub['price_paid']
                    if sub['user_ID'] is not None:
                        sub['user'] = users[ [z['ID'] for z in users].index(sub['user_ID']) ]
                        sub['group'] = None
                        sub['email'] = decrypt(sub['user']['email'])
                        
                    elif sub['group_ID'] is not None:
                        sub['group'] = groups[ [z['ID'] for z in groups].index(sub['group_ID']) ]
                        sub['user'] = None
                        
                        group_access = [z['user_ID'] for z in access if z['admin'] and z['group_ID'] == sub['group_ID'] and z['status'] == "active"]
                        sub['emails'] = [z for z in users if z['ID'] in group_access]
                        sub['email'] =  None if len(sub['emails']) != 1 else sub['emails'][0]['email_decrypted']
                        
                    sub['display'] = "hidden"
                    sub['start_date_str'] = sub['start_date'].strftime("%b %d, %Y").replace(" 0", " ")
                    sub['end_date_str'] = sub['end_date'].strftime("%b %d, %Y").replace(" 0", " ")
                    sub['start_date'] = None
                    sub['end_date'] = None
                    if sub['user_ID'] is None: sub['user_ID'] = ""
                    if sub['group_ID'] is None: sub['group_ID'] = ""
                    sub['product'] = misc['products'] [ [z['ID'] for z in misc['products']].index(sub['product_ID']) ]
                    
                    sub['product']['date_created'] = ""
                
                misc['subscriptions_json'] = json.dumps(misc['subscriptions'])
                
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
        misc = {'handler': 'createQuote', 'error': None}; user_obj = None; queries = []; params = []
        
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
                misc['email'] = self.request.get('email').strip()
                misc['email_decrypted'] = self.request.get('email').strip()
                misc['group_ID'] = int(self.request.get('group_ID'))
                
                for p in misc['product_requests']:
                    p['email_decrypted'] = decrypt(p['email'])
                    p['selected'] = " selected" if p['ID'] == misc['request_ID'] else ""
                
                misc['context'] = ""
                if misc['request_ID'] not in  ['', None, -1]:
                    request = misc['product_requests'][ [z['ID'] for z in misc['product_requests']].index(misc['request_ID']) ]
                    misc['context'] = request['email_decrypted']
                    misc['request_team_ID'] = request['team_ID']
                    if misc['request_team_ID'] is not None:
                        gr = groups[ [z['team_ID'] for z in groups].index(misc['request_team_ID'])]
                        misc['context'] += " (team: %s)" % (gr['group_name'])
                        misc['group_name'] = gr['group_name'] 
                        misc['group_ID'] = gr['ID']                         
                elif misc['email'] not in [None, ''] and misc['group_ID'] not in [None, -1, '']:
                    misc['request_team_ID'] = None
                    misc['context'] = misc['email_decrypted']
                    gr = groups[ [z['ID'] for z in groups].index(misc['group_ID'])]
                    misc['context'] += " (team: %s)" % (gr['group_name'])
                    misc['group_name'] = gr['group_name']   
                    misc['group_ID'] = gr['ID']                
                    
                else:
                    misc['error'] = "You must select a product request or specify team/email"
                if self.request.get('trial') == "":
                    misc['error'] = "Specify whether this is a trial or not."
                    misc['trial'] = None
                else:
                    misc['trial'] = int(self.request.get('trial'))
                
                misc['product_ID'] = int(self.request.get('product_ID'))
                misc['product_name'] = None if misc['product_ID'] == -1 else misc['products'][ [z['ID'] for z in misc['products']].index(misc['product_ID']) ]['product_name']
                misc['msg_body'] = self.request.get('msg_body').strip()
                misc['msg_body_html'] = misc['msg_body'].replace("\n", "<BR>")
                misc['price_str'] = self.request.get('price')
                misc['trial_end_str'] = self.request.get('trial_end')
                misc['valid_until_str'] = self.request.get('valid_until')
                misc['price_type'] = self.request.get('price_type')
                misc['trial_str'] = "Yes" if misc['trial'] else "No"
                misc['groups'] = groups
                for g in misc['groups']:
                    g['selected'] = " selected" if g['ID'] == misc['group_ID'] else ""
                
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
                elif '[quote-hash-link]' not in misc['msg_body']:
                    misc['error'] = "The message body must contain the tag [quote-hash-link]"
                    
                misc['trial_end_formatted'] = "N/A"; misc['valid_until_formatted'] = "N/A"
                if misc['error'] is None:
                    try:
                       misc['price'] = float(misc['price_str'].replace("$", "").replace(",", "").strip())
                       
                    except Exception:
                        misc['error'] = "Price must be a valid number."
                    if misc['trial']:
                        try:
                            trial_end_dt = datetime.strptime(misc['trial_end_str'].replace(" ", "").replace("/", "-").strip(), "%Y-%m-%d")
                            misc['trial_end_formatted'] = datetime.strptime(misc['trial_end_str'].replace(" ", "").replace("/", "-").strip(), "%Y-%m-%d").strftime("%b %d, %Y")
                            if not misc['email_decrypted'].startswith("newuser202") and trial_end_dt < datetime.now():
                                misc['error'] = "Trial End date can't be in the past."
                        except Exception:
                            #logging.info(traceback.format_exc())
                            misc['error'] = "Trial End date must be YYYY-MM-DD."
                    try:
                        valid_until_dt = datetime.strptime(misc['valid_until_str'].replace(" ", "").replace("/", "-").strip(), "%Y-%m-%d")
                        misc['valid_until_formatted'] = datetime.strptime(misc['valid_until_str'].replace(" ", "").replace("/", "-").strip(), "%Y-%m-%d").strftime("%b %d, %Y")
                        if not misc['email_decrypted'].startswith("newuser202") and valid_until_dt < datetime.now():
                            misc['error'] = "Valid Until date can't be in the past."
                    except Exception:
                        #logging.info(traceback.format_exc())
                        misc['error'] = "Valid Until date must be YYYY-MM-DD."
                
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
        
        misc = {'handler': 'createQuote', 'error': None, 'msg': None}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth'] and user_obj['is_admin']:
                
                conn, cursor = mysql_connect()
                misc['products'] = get_products(cursor, "Data Subscriptions")
                cursor.execute("SELECT * from LRP_Product_Requests where status='active' order by datestamp desc", [])
                misc['product_requests'] = zc.dict_query_results(cursor)
                cursor.execute("SELECT * from LRP_Groups where active order by group_name asc", [])
                misc['groups'] = zc.dict_query_results(cursor)
                cursor.close(); conn.close()
                
                misc['price_type_options'] = self.price_type_options
                misc['trial_options'] = self.trial_options
                
                for p in misc['product_requests']:
                    p['email_decrypted'] = decrypt(p['email'])
                
                
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

def display_quote(misc):
    conn, cursor = mysql_connect()
    
    cursor.execute("SELECT * from LRP_Quotes where active and hash=%s", [misc['quote_hash']])
    misc['quote'] = None
    res = zc.dict_query_results(cursor)
    if len(res) == 1:
        misc['quote'] = res[0]
    elif len(res) > 1:
        misc['quote'] = res[0]
        logging.error("There were multiple active LRP_Quotes records with hash=%s" % misc['quote_hash'])
    else:
        misc['error'] = "There is no quote record associated with this link. If you believe there should be, please contact me via <a href='/help?c=viewQuote'>this form</a>." 
    if misc['quote'] is not None:
        misc['quote']['team_ID'] = None    
        if misc['quote'] is not None and misc['quote']['group_ID'] is not None:
            misc['quote']['valid'] = 1 if misc['quote']['valid_until'] > datetime.now() else 0
        
            misc['quote']['price_str'] = "${:,.2f}".format(misc['quote']['price'])
            cursor.execute("SELECT * from LRP_Products where active and ID=%s", [misc['quote']['product_ID']])
            product = zc.dict_query_results(cursor)[0]
            cursor.execute("SELECT * from LRP_Groups where active and ID=%s", [misc['quote']['group_ID']])
            groups = zc.dict_query_results(cursor)
            misc['group_name'] = None
            misc['max_users'] = 100; 
            

            if len(groups) > 0:
                group = groups[0]
                misc['group_name'] = group['group_name']
                misc['max_users'] = misc['max_users'] if group['max_users'] is None else group['max_users']
                misc['quote']['team_ID'] = group['team_ID']
                
            misc['max_users_str'] = "s" if misc['max_users'] != 1 else ""
            
            misc['price'] = misc['quote']['price']
            misc['discount_pct_str'] = None; misc['discount_pct'] = None; misc['discount'] = None; misc['list_price'] = None; misc['list_price_str'] = None
            misc['product_user_type'] = None; misc['product_ID'] = None
            if product is not None:
                misc['product_ID'] = product['ID']
                if product['product_name'] == "Team":
                    misc['product_user_type'] = "team"
                elif product['product_name'] == "Media":
                    misc['product_user_type'] = "media"
                elif product['product_name'] == "Basic":
                    misc['product_user_type'] = "individual"
                misc = calc_discount(misc, product)                
            if misc['quote']['trial']:
                misc['quote']['trial_end_str'] = misc['quote']['trial_end'].strftime("%b %d, %Y").replace(" 0", " ")
            
            misc['quote']['valid_until_str'] = misc['quote']['valid_until'].strftime("%b %d, %Y").replace(" 0", " ")
    cursor.close(); conn.close()
    return misc
    
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
        target_template = "quote.html"
        misc = {'handler': 'viewQuote', 'error': None}; user_obj = None; queries = []; params = []
        
        misc['action'] = self.request.get("action")
        misc['quote_hash'] = self.request.get("hash")
            
        misc = display_quote(misc)
        
        misc['login_tag_display'] = "tag-on"
        misc['login_display'] = "visible"
        misc['create_account_tag_display'] = "tag-off"
        misc['create_account_display'] = "hidden"
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                user_obj['user_cookie'] = None
                layout = "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"
            else:
                user_obj = process_non_auth(self)
                layout = "layout_no_auth.html"
        else: 
            user_obj = process_non_auth(self)
            layout = "layout_no_auth.html"
      
        if misc['action'] == "requote":
            
            tup = (datetime.now().strftime("%Y%m%d"), misc['quote']['user_email'], misc['quote']['team_ID'], misc['quote']['product_ID'])
            conn, cursor = mysql_connect()
            cursor.execute("SELECT datestamp, email, team_ID, product_ID from LRP_Product_Requests where active", [])
            requests = zc.dict_query_results(cursor)
            cursor.close(); conn.close()
            lg(str(tup))
            for z in requests:
                z['tup'] = (z['datestamp'].strftime("%Y%m%d"), z['email'], z['team_ID'], z['product_ID'])
            
            if tup not in [z['tup'] for z in requests]:
                query = "INSERT INTO LRP_Product_Requests (ID, datestamp, email, team_ID, product_ID, group_ID, status, active, request_type) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Product_Requests fds), %s, %s, %s, %s, %s, %s, %s, %s)"
                param = [datetime.now(), misc['quote']['user_email'], misc['quote']['team_ID'], misc['quote']['product_ID'], misc['quote']['group_ID'], 'active', 1, 'trial-request']
                queries.append(query); params.append(param)
                
                misc['resend_msg'] = "Thank you for your request. We will be in touch via email within 48 hours."
            else:
                misc['resend_msg'] = "We have recorded your request and will be in touch within 48 hours."
                
        ex_queries(queries, params)
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
        path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

    def get(self):
        
        target_template = "quote.html"
        
        misc = {'handler': 'viewQuote', 'quote_hash': self.request.get('c'), 'error': None, 'msg': None}; user_obj = None
        
        misc['login_tag_display'] = "tag-on"
        misc['login_display'] = "visible"
        misc['create_account_tag_display'] = "tag-off"
        misc['create_account_display'] = "hidden"
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                user_obj['user_cookie'] = None
                layout = "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"
                
            else:
                layout = 'layout_no_auth.html'
        else: 
            user_obj = process_non_auth(self)
            layout = 'layout_no_auth.html'
        
        misc = display_quote(misc)
        pd(misc)
                
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout }
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
        misc = {'handler': 'switchGroups', 'error': None}; user_obj = None; queries = []; params = []
        
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
        
        misc = {'handler': 'switchGroups', 'error': None, 'msg': None}; user_obj = None
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
        
        misc = {'handler': 'preferences', 'error': None, 'msg': None}; user_obj = None; queries = []; params = []
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
                
                misc['msg'] = "Preferences have been updated."
                
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
        
        misc = {'handler': 'preferences', 'error': None, 'msg': None}; user_obj = None; queries = []; params = []
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
        
        misc = {'handler': 'profile', 'error': None, 'msg': None}; user_obj = None; queries = []; params = []
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
                    vals.append(encrypt(self.request.get(r)))
                
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
        
        misc = {'handler': 'profile', 'error': None, 'msg': None}; user_obj = None; queries = []; params = []
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
        misc = {'handler': 'forgot', 'error': None}; user_obj = process_non_auth(self); queries = []; params = []
        user_obj['ID'] = None
        
        misc['username'] = self.request.get('username').strip().lower()
        
        conn, cursor = mysql_connect()
        cursor.execute("SELECT * from LRP_Users")
        users = zc.dict_query_results(cursor)
        cursor.execute("SELECT * from LRP_Email_Templates where template_desc='Password Reset'")
        msg = zc.dict_query_results(cursor)[0]
        cursor.close(); conn.close()
        
        
        if "" == misc['username']:
            misc['error'] = "You must enter a valid value for username/email."
        elif misc['username'] not in [decrypt(z['username']).strip().lower() for z in users] and misc['username'] not in [decrypt(z['email']).strip().lower() for z in users]:
            misc['error'] = "Could not find an account associated with your entry."
        
        if misc['error'] is None:
            
            
            user = None
            if misc['username'] in [decrypt(z['username']).strip().lower() for z in users]:
                user = users[ [decrypt(z['username']).strip().lower() for z in users].index(misc['username']) ]
            elif misc['username'] in [decrypt(z['email'].strip().lower()) for z in users]:
                user = users[ [decrypt(z['email'].strip().lower()) for z in users].index(misc['username']) ]
            
            misc['msg'] = "Password has been reset; check your inbox for a password reset message."
            
            tmp_password = create_temporary_password()
            msg['email'] = decrypt(user['email'])
            msg['subject'] = "Password Reset"
            
            query = "UPDATE LRP_Users set password=%s where ID=%s"
            param = [encrypt(tmp_password), user['ID']]
            queries.append(query); params.append(param)
            
            
            msg['content'] = get_file(msg['bucket'], msg['fname'])
            msg['content'] = msg['content'].replace("[password]", tmp_password)
            msg['content'] = msg['content'].replace("[username]", decrypt(user['username']))
            msg['content'] = msg['content'].replace("\r\n", "\\n")
            msg['content'] = msg['content'].replace("\n", "\\n")
            
            mail_res, dbrec = finalize_mail_send(msg)
            if mail_res != "": create_mail_record(dbrec)
            
            ex_queries(queries, params)
                    
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
        path = os.path.join("templates", target_template)
        self.response.out.write(template.render(path, tv))

    
        
        
    
    def get(self):
        
        target_template = "forgot.html"
        
        misc = {'handler': 'forgot', 'username': '', 'password': '', 'email': '', 'phone': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                target_template = "index.html"
                misc['msg'] = "You are already registered and logged in."
            
                tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
            else:
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

class CronHandler(webapp2.RequestHandler):
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
        misc = {'handler': 'forgot', 'error': None}; user_obj = process_non_auth(self); queries = []; params = []
        user_obj['ID'] = None
        
        misc['username'] = self.request.get('username').strip().lower()
        
        conn, cursor = mysql_connect()
        cursor.execute("SELECT * from LRP_Users")
        users = zc.dict_query_results(cursor)
        cursor.execute("SELECT * from LRP_Email_Templates where template_desc='Password Reset'")
        msg = zc.dict_query_results(cursor)[0]
        cursor.close(); conn.close()
        
        
        if "" == misc['username']:
            misc['error'] = "You must enter a valid value for username/email."
        elif misc['username'] not in [decrypt(z['username']).strip().lower() for z in users] and misc['username'] not in [decrypt(z['email']).strip().lower() for z in users]:
            misc['error'] = "Could not find an account associated with your entry."
        
        if misc['error'] is None:
            
            
            pd (misc)
            user = None
            lg(str([decrypt(z['username']).strip().lower() for z in users]))
            lg(misc['username'] in [decrypt(z['username']).strip().lower() for z in users])
            if misc['username'] in [decrypt(z['username']).strip().lower() for z in users]:
                user = users[ [decrypt(z['username']).strip().lower() for z in users].index(misc['username']) ]
            elif misc['username'] in [decrypt(z['email'].strip().lower()) for z in users]:
                user = users[ [decrypt(z['email'].strip().lower()) for z in users].index(misc['username']) ]
            
            misc['msg'] = "Password has been reset; check your inbox for a password reset message."
            
            tmp_password = create_temporary_password()
            msg['email'] = decrypt(user['email'])
            msg['subject'] = "Password Reset"
            
            query = "UPDATE LRP_Users set password=%s where ID=%s"
            param = [encrypt(tmp_password), user['ID']]
            queries.append(query); params.append(param)
            
            
            msg['content'] = get_file(msg['bucket'], msg['fname'])
            msg['content'] = msg['content'].replace("[password]", tmp_password)
            msg['content'] = msg['content'].replace("[username]", decrypt(user['username']))
            msg['content'] = msg['content'].replace("\r\n", "\\n")
            msg['content'] = msg['content'].replace("\n", "\\n")
            
            mail_res, dbrec = finalize_mail_send(msg)
            if mail_res != "": create_mail_record(dbrec)
            
            ex_queries(queries, params)
                    
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj)}
        path = os.path.join("templates", target_template)
        self.response.out.write(template.render(path, tv))

    
        
        
    """
    List of Cron Jobs
    
    - hello
    
    Send hello email to zcapozzi@gmail.com
    
    - ping
    
    Store a user event
    
    - notify-expiring-subs
    
    Create a notification item for subscriptions ending in exactly 7 days
    
    - send-mail
    
    Send scheduled emails
    
    """
    def get(self, orig_url):
        lg("Cron: %s" % orig_url)
        misc = {}; status = 200
        
        if orig_url == "hello":
            
            subjects = ["Hello from LRP!!!"]#, "Your weekly download from LRP", "The week that was in college lacrosse"]
            recipients = ["zcapozzi@gmail.com"]#, "zack@lacrossereference.com", "zack@looseleafguide.com", "zack@mainstreetdataguy.com", "bot@lacrossereference.com", "kyle@lacrossereference.com", "guide@looseleafguide.com", "zack@durhamcornholecompany.com"]
            contents = ['It\'s your daily cron hello...']
            contents.append("So what went down on %s you ask? Great question. Here we go." % datetime.now().strftime("%b %d, %Y"))
            contents.append("It was a wild week in the world of college lacrosse. Teams won. Other teams lost. Goals were scored...")
            contents.append("Go see for yourself how great <a href='https://pro.lacrossereference.com'>LRP</a> is.")
            
            random.seed(time.time())
            subject = subjects[int((random.random()) * (-.00001 + float(len(subjects))))]; time.sleep(.02); random.seed(time.time())
            recipient = recipients[int((random.random()) * (-.00001 + float(len(recipients))))]; time.sleep(.02); random.seed(time.time())
            content = contents[int((random.random()) * (-.00001 + float(len(contents))))]; time.sleep(.02); random.seed(time.time())
            
            msg = {'email': recipient, 'subject': subject, 'content': content}
            misc['msg'] = json.dumps(msg)
            mail_res, dbrec = finalize_mail_send(msg)
            if mail_res != "": create_mail_record(dbrec)
            if mail_res != "Success":
                misc['error'] = "Cron failed (%s)" % orig_url
                status = 500
        if orig_url == "ping":
        
            conn, cursor = mysql_connect()
            cursor.execute("INSERT INTO LRP_User_Event_Logs(event_ID, user_ID, send_date)  VALUES (%s, %s, %s)", [11, 1, datetime.now()]); conn.commit()
            cursor.close(); conn.close()
        if orig_url == "send-mail":
            utc_dt = datetime.utcnow()
            utc_dt_local = datetime.strptime(utc_dt.strftime("%Y%m%d %H%M%S"), "%Y%m%d %H%M%S")
            conn, cursor = mysql_connect()
            cursor.execute("SELECT * from LRP_Emails where active and status='scheduled'", []); 
            emails = zc.dict_query_results(cursor)
            cursor.close(); conn.close()
            
            
            
            for z in emails:
                z['seconds_until'] = (z['send_date'] - utc_dt_local).total_seconds()
                
            to_send = [z for z in emails if -600 <= z['seconds_until'] <= 600]
            
            
            misc['msg'] = "Found %d emails to send (out of %d scheduled)<BR><BR>" % (len(to_send), len(emails))
            misc['msg'] += "<BR>".join(["Time: %s UTC; Recipient: %s; Subject: %s; Seconds Until: %d" % (z['send_date'].strftime("%b %d, %Y %I:%M %p"), z['recipient'], z['subject'], z['seconds_until']) for z in to_send])
            
            for i, msg in enumerate(to_send):
                msg['content'] = None
                    
                server_path = "/capozziinc.appspot.com/SentEmailRecords/%s" % (misc['hash'])
                
                if env.startswith('Google App Engine/'):
                    try:
                        msg['content'] = cloudstorage.open(server_path).read()
                    except Exception, e:
                        misc['error'] = "The email record file could not be read from the Storage bucket"
                        logging.error = "Scheduled email content not found. Hash = %s" % msg['hash']
                
                if msg['content'] is not None:
                    mail_res, dbrec = finalize_mail_send(msg)
                    if mail_res != "": create_mail_record(dbrec)
                    if mail_res == "Success" or client_secrets['local']['--no-mail'] in ["Y", 'y', 'yes']:
                
                        # Success
                        misc['msg'] = "Email was resent."
                        
                    else:
                        misc['error'] = "Resend failed"
                        misc['msg'] = None
            
    
        
        if orig_url == "notify-expiring-subs":
            pass
        self.response.set_status(status)
        self.response.out.write(json.dumps(misc))
        
def check_submission_for_spam(msg):
    msg['spam'] = 0
    # msg_content, subject, email, name
    
    return msg

class ContactHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "contact.html"
        user_obj = None; queries = []; params = []
        
        misc = dict_request(self.request); misc['error'] = None
        misc['handler'] = "contact"
        misc['email'] = misc['email'].lower().strip()
        
            
        if misc['email'] == "":
            misc['error'] = "Please enter an email address."
  
        elif email_regex.search(misc['email']) is None:
            misc['error'] = "The email address you entered was invalid."

        elif misc['msg_content'] == "":
            misc['error'] = "The contact form was blank."

        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:      
                user_obj['user_cookie'] = None
                layout = "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"
            else:
                user_obj = process_non_auth(self); user_obj['ID'] = None
                layout = 'layout_no_auth.html'
        else:
            user_obj = process_non_auth(self); user_obj['ID'] = None
            layout = 'layout_no_auth.html'                
                    
        
        if misc['error'] is None:
            
            
            if misc['subject'] == "":
                misc['final_subject'] = "LRP Contact Page: No Subject Given"
            else:
                misc['final_subject'] = "LRP Contact Page: %s" % misc['subject']
            misc['msg'] = "Thank you for contacting LacrosseReference."
            
            misc = check_submission_for_spam(misc)
            
            query = "INSERT INTO LRP_Contact_Submissions (ID, active, user_ID, user_cookie, email, subject, name, msg, datestamp) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Contact_Submissions fds), %s, %s, %s, %s, %s, %s, %s, %s)"
            param = [1, user_obj['ID'], user_obj['user_cookie'], encrypt(misc['email']), misc['final_subject'], encrypt(misc['name']), misc['msg_content'], datetime.now()]
            queries.append(query); params.append(param)
            ex_queries(queries, params)
            
            msg = {'email': "admin@lacrossereference.com", 'subject': misc['final_subject'], 'content': "Email: %s\nName: %s\nSubject: %s\n\n\n%s" % (misc['email'], misc['name'], misc['subject'], misc['msg_content'])}
            
            pd(misc)
            if misc['spam'] == 0:
                mail_res, dbrec = finalize_mail_send(msg)
                if mail_res != "": create_mail_record(dbrec)
                if mail_res == "Success" or client_secrets['local']['--no-mail'] in ["Y", 'y', 'yes']:
                    
                    # Success
                    pass
                    
                else:
                    misc['error'] = "Your message could not be sent. Please try again shortly."
                    misc['msg'] = None
                    
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
        path = os.path.join("templates", target_template)
        self.response.out.write(template.render(path, tv))

    
        
        
    
    def get(self):
        
        target_template = "contact.html"
        
        misc = {'handler': 'contact', 'username': '', 'password': '', 'email': '', 'phone': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:      
                user_obj['user_cookie'] = None
                misc['email'] = decrypt(user_obj['email'])
                layout = "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"
            else:
                user_obj = process_non_auth(self); user_obj['ID'] = None
                layout = 'layout_no_auth.html'
        else:
            user_obj = process_non_auth(self); user_obj['ID'] = None
            layout = 'layout_no_auth.html'
            
           
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
        path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

class EmailHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    def process_emails(self, misc):
        
        for m in misc['emails']:
            m['subject_decrypted'] = decrypt(m['subject'])
            m['recipient_decrypted'] = decrypt(m['recipient'])
            if ".com" not in m['recipient_decrypted'] :
                m['subject_decrypted'] = m['subject']
                m['recipient_decrypted'] = m['recipient']
            m['subject_decrypted'] = m['subject_decrypted'].replace("LacrosseReference PRO", "LRP")
            m['subject_title'] = ''
            if len(m['subject_decrypted']) > 43:
                m['subject_title'] = m['subject_decrypted'] 
                m['subject_decrypted'] = m['subject_decrypted'][0:40] + "..."
                
            m['send_date_str'] = m['send_date'].strftime("%Y-%m-%d %H:%M")
            m['new_date_str'] = m['send_date'].strftime("%Y-%m-%d %H:%M")
            m['status_str'] = "" if m['status'] is None else m['status'].title()
            if m['status'] == "test":
                m['status_style'] = "color: #AAA; font-style:italic;"
            if m['status'] == "inactive":
                m['status_style'] = "color: #AAA; font-style:italic;"
            if m['status'] == "scheduled":
                m['status_style'] = "color: #22F; font-weight:700;"
            if m['status'] == "sent":
                m['status_style'] = "color: #2F2; font-weight:700;"
            if m['status'] == "failed":
                m['status_style'] = "color: red; font-weight:700;"
            
            
            
            if m['status'] is None:
                m['options'] = None
            elif m['status'] == "sent":
                m['options'] = [{'val':'resend', 'desc': "Re-send"}]
            elif m['status'] == "scheduled":
                m['options'] = [{'val':'reschedule', 'desc': "Re-schedule"}, {'val':'deactivate', 'desc': "De-activate"}, {'val':'delete', 'desc': "Delete"}]
            elif m['status'] == "inactive":
                m['options'] = [{'val':'reactivate', 'desc': "Re-activate"}, {'val':'delete', 'desc': "Delete"}]
            else:
                m['options'] = [{'val':'resend', 'desc': "Re-send"}]

            if m['options'] is not None:
                for o in m['options']:
                    o['selected'] = " selected" if misc['action'] == o['val'] else ""
                
        return misc
    
    def post(self):
        target_template = "email.html"
        user_obj = None; queries = []; params = []
        misc = dict_request(self.request); misc['error'] = None
        
        local = not os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/')
        session_ID = self.session.get('session_ID')
        if local or session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if local or (user_obj['auth'] and user_obj['is_admin']):
                if misc['error'] is None:
                    
                    misc['selected_hash'] = misc['hash']
                    conn, cursor = mysql_connect()
                    cursor.execute("SELECT * from LRP_Emails where active order by send_date desc", [])
                    misc['emails'] = zc.dict_query_results(cursor)
                    cursor.close(); conn.close()
                    misc = self.process_emails(misc)
                    
                    msg = misc['emails'][ [z['hash'] for z in misc['emails']].index(misc['hash']) ]
                        
                    if misc['action'] == "resend" and misc['confirmed'] == "no":
                        misc['confirm_msg'] = "Are you sure you want to resend this email?"
                        misc['confirmed'] = "yes"
                    elif misc['action'] == "deactivate" and misc['confirmed'] == "no":
                        misc['confirm_msg'] = "Are you sure you want to deactivate this email?"
                        misc['confirmed'] = "yes"
                    elif misc['action'] == "reactivate" and misc['confirmed'] == "no":
                        misc['confirm_msg'] = "Are you sure you want to reactivate this email?"
                        misc['confirmed'] = "yes"
                    elif misc['action'] == "delete" and misc['confirmed'] == "no":
                        misc['confirm_msg'] = "Are you sure you want to delete this email?"
                        misc['confirmed'] = "yes"
                    elif misc['action'] == "reschedule" and misc['confirmed'] == "no":
                        misc['confirmed'] = "yes"
                        
                        
                    elif misc['action'] == "reschedule" and misc['confirmed'] == "yes":
                        try:
                            new_date = datetime.strptime(misc['new_date_str'].replace("/", "-").strip(), "%Y-%m-%d %H:%M")
                            
                            # Calculate the difference between ET and UTC and add that to the scheduled email date
                            utc_dt = datetime.utcnow()
                            utc_dt_local = datetime.strptime(utc_dt.strftime("%Y%m%d %H%M%S"), "%Y%m%d %H%M%S")
            
                            import pytz
                            loc_dt = datetime.now(pytz.timezone('US/Eastern'))
                            loc_dt_local = datetime.strptime(loc_dt.strftime("%Y%m%d %H%M%S"), "%Y%m%d %H%M%S")
                            diff = (utc_dt_local - loc_dt_local).total_seconds()
                            new_date += timedelta(seconds=diff)
                            
                            if new_date < datetime.now():
                                misc['confirm_msg'] = "Send date can't be in the past."
                                
                            else:
                                queries.append("UPDATE LRP_Emails set send_date=%s where hash=%s")
                                params.append([new_date, misc['hash']])
                                msg['send_date'] = new_date
                                misc['msg'] = "Email schedule adjusted."
                                misc['selected_hash'] = None
                                
                        except Exception:
                            logging.info(traceback.format_exc())
                            misc['confirm_msg'] = "Send date must be YYYY-MM-DD HH:MM."
            
                        
                    elif misc['action'] == "delete" and misc['confirmed'] == "yes":
                        queries.append("UPDATE LRP_Emails set active=0 where hash=%s")
                        params.append([misc['hash']])
                        msg['status'] = "deleted"
                        misc['confirmed'] = "no"
                    elif misc['action'] == "deactivate" and misc['confirmed'] == "yes":
                        queries.append("UPDATE LRP_Emails set status='inactive' where hash=%s")
                        params.append([misc['hash']])
                        msg['status'] = "inactive"
                        misc['confirmed'] = "no"
                    elif misc['action'] == "reactivate" and misc['confirmed'] == "yes":
                        queries.append("UPDATE LRP_Emails set status='scheduled' where hash=%s")
                        params.append([misc['hash']])
                        msg['status'] = "scheduled"
                        misc['confirmed'] = "no"
                    elif misc['action'] == "resend" and misc['confirmed'] == "yes":
                        misc['confirmed'] = "no"
                        msg['email'] = msg['recipient_decrypted']
                        msg['subject'] = msg['subject_decrypted']
                        env = os.getenv('SERVER_SOFTWARE')
                        msg['content'] = None
                        
                        server_path = "/capozziinc.appspot.com/SentEmailRecords/%s" % (misc['hash'])
                        local_path = os.path.join("LocalDocs", "SentEmailRecords", misc['hash'])
                        
                        if env.startswith('Google App Engine/'):
                            try:
                                msg['content'] = cloudstorage.open(server_path).read()
                            except Exception, e:
                                misc['error'] = "The email record file could not be read from the Storage bucket"
                        else:
                            try:
                                msg['content'] = open(local_path, 'r').read()
                            except Exception, e:
                                misc['error'] = "The email record file could not be read from the LocalDocs bucket"
                    
                        if msg['content'] is not None:
                            mail_res, dbrec = finalize_mail_send(msg)
                            if mail_res != "": create_mail_record(dbrec)
                            if mail_res == "Success" or client_secrets['local']['--no-mail'] in ["Y", 'y', 'yes']:
                        
                                # Success
                                misc['msg'] = "Email was resent."
                                
                            else:
                                misc['error'] = "Resend failed"
                                misc['msg'] = None
                    
                    if len(queries) > 0:
                        misc = self.process_emails(misc)
                        lg("\nQueries\n")
                    ex_queries(queries, params)
                layout = 'layout_admin.html'
            else:
                user_obj = process_non_auth(self); user_obj['ID'] = None
                layout = 'layout_no_auth.html'
        else:
            user_obj = process_non_auth(self); user_obj['ID'] = None
            layout = 'layout_no_auth.html'                
                    
        
        
            
            
           
                    
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
        path = os.path.join("templates", target_template)
        self.response.out.write(template.render(path, tv))

    
        
        
    
    def get(self):
        
        target_template = "email.html"
        
        misc = {'handler': 'email', 'confirmed': 'no', 'selected_ID': None, 'action': 'view', 'new_date_str': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
        local = not os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/')
        session_ID = self.session.get('session_ID')
        if local or session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if local or (user_obj['auth'] and user_obj['is_admin']):    
                user_obj['user_cookie'] = None
                
                conn, cursor = mysql_connect()
                cursor.execute("SELECT * from LRP_Emails where active order by send_date desc", [])
                misc['emails'] = zc.dict_query_results(cursor)
                cursor.close(); conn.close()
                misc = self.process_emails(misc)
                
                layout = "layout_admin.html"
            else:
                user_obj = process_non_auth(self); user_obj['ID'] = None
                layout = 'layout_no_auth.html'
        else:
            user_obj = process_non_auth(self); user_obj['ID'] = None
            layout = 'layout_no_auth.html'
            
           
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
        path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

class HelpHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        target_template = "help.html"
        user_obj = None; queries = []; params = []
        
        

        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:      
                user_obj['user_cookie'] = None
                misc = dict_request(self.request); misc['error'] = None
                misc['handler'] = "help"
                if 'category' not in misc:
                    misc['category'] = None
                    
                if misc['question'] == "":
                    misc['error'] = "The question form was blank."
                layout = "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"
                
                if misc['error'] is None:
            
            
                    misc['final_subject'] = "LRP Help Request from %s" % decrypt(user_obj['email'])
                    misc['msg'] = "Thank you for your question."
                    
                    misc = check_submission_for_spam(misc)
                    
                    query = "INSERT INTO LRP_Help_Requests (ID, active, user_ID, datestamp, question, category, source_handler) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Help_Requests fds), %s, %s, %s, %s, %s, %s)"
                    param = [1, user_obj['ID'], datetime.now(), misc['question'], misc['category'], misc['source_handler']]
                    queries.append(query); params.append(param)
                    ex_queries(queries, params)
                    
                    msg = {'email': "admin@lacrossereference", 'subject': misc['final_subject'], 'content': "Email: %s\n\n%s" % (decrypt(user_obj['email']), misc['question'])}
                    if misc['spam'] == 0:
                        mail_res, dbrec = finalize_mail_send(msg)
                        if mail_res != "": create_mail_record(dbrec)
                        if mail_res == "Success" or client_secrets['local']['--no-mail'] in ["Y", 'y', 'yes']:
                    
                            # Success
                            pass
                            
                        else:
                            misc['error'] = "Your question could not be sent. Please try again shortly."
                            misc['msg'] = None
            else:
                user_obj = process_non_auth(self); user_obj['ID'] = None
                layout = 'layout_no_auth.html'
        else:
            user_obj = process_non_auth(self); user_obj['ID'] = None
            layout = 'layout_no_auth.html'                
                    
        
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
        path = os.path.join("templates", target_template)
        self.response.out.write(template.render(path, tv))

    
        
        
    
    def get(self):
        
        target_template = "help.html"
        
        misc = {'handler': 'help', 'source_handler': self.request.get('c'), 'username': '', 'password': '', 'email': '', 'phone': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:      
                user_obj['user_cookie'] = None
                layout = "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"
            else:
                target_template = "index.html"
                user_obj = process_non_auth(self); user_obj['ID'] = None
                layout = 'layout_no_auth.html'
        else:
            target_template = "index.html"
            user_obj = process_non_auth(self); user_obj['ID'] = None
            layout = 'layout_no_auth.html'
            
           
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
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
        
        
        
        misc = {'handler': 'productSummary', 'error': None, 'product_tag': product_tag,  'team_ID': None}; user_obj = None; queries = []; params = []
        
        conn, cursor = mysql_connect()
        cursor.execute("SELECT * from LRP_Groups where active", [])
        groups = zc.dict_query_results(cursor)
        products = get_products(cursor)
        cursor.execute("SELECT count(1)+1 'cnt' from LRP_Cart", [])
        next_cart_ID = zc.dict_query_results(cursor)[0]['cnt']
        cursor.execute("SELECT datestamp, email, team_ID, product_ID from LRP_Product_Requests where active", [])
        requests = zc.dict_query_results(cursor)
        cursor.close(); conn.close()
           
        for z in requests:
            z['tup'] = (z['datestamp'].strftime("%Y%m%d"), z['email'], z['team_ID'], z['product_ID'])
                
        misc['product'] = products[ [z['tag'] for z in products].index(product_tag.lower()) ]
        misc['email'] = self.request.get('email').strip().lower()
        misc['email_decrypted'] = self.request.get('email').strip().lower()
        
        misc['action'] = self.request.get('action').lower().strip()
        misc['request_type'] = self.request.get('request_type')
        misc['AB_group'] = self.request.get('AB_group')
        misc['group_ID'] = None
        if product_tag == "team":
            misc['team_ID'] = int(self.request.get('team_select'))
            gr = groups[ [z['team_ID'] for z in groups].index(misc['team_ID'])]
            misc['group_ID'] = gr['ID']
            
        if misc['action'] in ["pre-register", "quotable"]:
            email_match = email_regex.search(misc['email'])
            if email_match is None:
                misc['error'] = "You must enter a valid email."
        
        
        if misc['product_tag'] == "team":
            if misc['team_ID'] in ["-1", -1,  None, '']:
                misc['error'] = "You must select a team."

        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:      
                user_obj['user_cookie'] = None
                layout = "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"
            else:
                user_obj = process_non_auth(self); user_obj['ID'] = None
                layout = 'layout_no_auth.html'
        else:
            user_obj = process_non_auth(self); user_obj['ID'] = None
            layout = 'layout_no_auth.html'
            
        if misc['error'] is None:
            if misc['action'] in ["pre-register", "quotable"]:
                email_match = email_regex.search(misc['email'])
                if email_match is None:
                    misc['error'] = "You must enter a valid email."
                else:
                    tmp_keys = ['email']
                    for k in tmp_keys:
                        misc["%s_encrypted" % k] =  encrypt(misc[k])
                    
                    tup = (datetime.now().strftime("%Y%m%d"), misc['email_encrypted'], misc['team_ID'], misc['product']['ID'])
                    if tup not in [z['tup'] for z in requests]:
                        query = "INSERT INTO LRP_Product_Requests (ID, datestamp, email, team_ID, group_ID, product_tag, product_ID, status, active, request_type, request_comments) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Product_Requests fds), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        param = [datetime.now(), misc['email_encrypted'], misc['team_ID'], misc['group_ID'], misc['product_tag'], misc['product']['ID'], 'active', 1, misc['request_type'], None]
                        queries.append(query); params.append(param)
                        misc['msg'] = "Request received."
                    else:
                        misc['msg'] = "Your request was received."
                    
                ex_queries(queries, params)
            elif misc['action'] in ["available"] and misc['product']['call_to_action'] == "ADD TO CART":

                tup = (user_obj['ID'], user_obj['user_cookie'], misc['product']['ID'])
                if tup not in [(z['user_ID'], z['user_cookie'], z['product_ID']) for z in user_obj['cart'] if z['status'] in ["added"]]:
                    
                    price = misc['product']['price']
                    list_price = price
                    
                    query = "INSERT INTO LRP_Cart (ID, user_ID, user_cookie, product_ID, status, date_added, price, discount_tag, list_price, active) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Cart fds), %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    param = [user_obj['ID'], user_obj['user_cookie'], misc['product']['ID'], 'added', datetime.now(), price, None, list_price, 1]
                    queries.append(query); params.append(param)
                    misc['msg'] = "Cart has been updated."                    
                    ex_queries(queries, params)
                    
                    
                    
                    
                    user_obj['cart'].append({'ID': next_cart_ID, 'user_ID': user_obj['ID'], 'user_cookie': user_obj['user_cookie'], 'product_ID': misc['product']['ID'], 'date_added': datetime.now(), 'status': 'added', 'active': 1, 'price': price, 'list_price': list_price, 'product': misc['product']}); next_cart_ID += 1
                else:
                    misc['error'] = "Product has been added already."
  

        
            
        conn, cursor = mysql_connect()
        cursor.execute("SELECT * from LRP_Groups where active=1 order by group_name asc", [])
        misc['groups'] = zc.dict_query_results(cursor)
        cursor.close(); conn.close()
        for g in misc['groups']:
            g['selected'] = " selected" if misc['team_ID'] == g['team_ID'] else ""
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
        path = os.path.join("templates", "product_summary_%s%s.html" % (product_tag, misc['AB_group'])); self.response.out.write(template.render(path, tv))

    
        
    def get(self, orig_url):
        
        misc = {'handler': 'productSummary', 'user_ID': None, 'email': "", "AB_group": None, 'hash': create_temporary_password()}; user_obj = None
        random.seed(time.time()); misc['AB_group'] = "A" if random.random() < .5 else "B"
        if self.request.get('v') != "": misc['AB_group'] = self.request.get('v')
        url_match = self.url_regex.search(orig_url)
        product_tag = url_match.group(1)
        
        
        conn, cursor = mysql_connect()
        products = get_products(cursor)
        cursor.close(); conn.close()
        misc['product'] = products[ [z['tag'] for z in products].index(product_tag.lower()) ]
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:
                misc['user_ID'] = user_obj['ID']
                misc['email'] = user_obj['email']
                misc['email_decrypted'] = decrypt(user_obj['email'])
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

def generate_stripe_response(intent):
  if intent.status == 'succeeded':
    # Handle post-payment fulfillment
    return json.dumps({'success': True}), 200
  else:
    # Any other status would be unexpected, so error
    return json.dumps({'error': 'Invalid PaymentIntent status'}), 500
    
class CheckoutHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        
        target_template = "checkout.html"
        misc = {'handler': 'checkout', 'error': None, 'msg': None}; user_obj = None; queries = []; params = []
        
        stripe.api_key = client_secrets['web']['StripeServerKey']
        misc['clientKey'] = client_secrets['web']['StripeClientKey']

        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:      
                user_obj['user_cookie'] = None
                layout = "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"
            else:
                user_obj = process_non_auth(self); user_obj['ID'] = None
                layout = 'layout_no_auth.html'
        else:
            user_obj = process_non_auth(self); user_obj['ID'] = None
            layout = 'layout_no_auth.html'
            
        misc['login_tag_display'] = "tag-on"
        misc['login_display'] = "visible"
        misc['create_account_tag_display'] = "tag-off"
        misc['create_account_display'] = "hidden"
        
        future_user_type = None
        if 3 in [z['product_ID'] for z in user_obj['cart'] if z['active'] and z['status'] == "added"]:
            future_user_type = "team"
        elif 2 in [z['product_ID'] for z in user_obj['cart'] if z['active'] and z['status'] == "added"]:
            future_user_type = "media"
        elif 1 in [z['product_ID'] for z in user_obj['cart'] if z['active'] and z['status'] == "added"]:
            future_user_type = "individual"
            
        misc['payment_completed'] = None
        data = {}
        if self.request.body not in ['action=checkout', '', None]:
            data = json.loads(self.request.body)
        
        misc['response'] = None
        cart_total_in_cents = int(100. * sum([z['price'] for z in user_obj['cart'] if z['active'] and z['status'] == "added"]))
        misc['active_cart'] = [z for z in user_obj['cart'] if z['active'] and z['status'] == "added"]
        
        if 'payment_method_id' in data:
            
                try:
                    user_obj['email_decrypted'] = decrypt(user_obj['email'])
                    # Create the PaymentIntent
                    intent = stripe.PaymentIntent.create(
                      amount=cart_total_in_cents,
                      currency='usd',
                      payment_method=data['payment_method_id'],

                      # A PaymentIntent can be confirmed some time after creation,
                      # but here we want to confirm (collect payment) immediately.
                      confirm=True,

                      # If the payment requires any follow-up actions from the
                      # customer, like two-factor authentication, Stripe will error
                      # and you will need to prompt them for a new payment method.
                      error_on_requires_action=True,
                    )
                    payment_intent = intent.id
                    
                    r = generate_stripe_response(intent)
                    if 'success' in r[0]:
                    
                        # Update LRP_Users with the stripe payment record:
                        customer = stripe.Customer.create(email=user_obj['email_decrypted'])
                        query = "UPDATE LRP_Users set user_type=%s, stripe_customer_ID=%s where ID=%s"
                        param = [future_user_type, encrypt(customer.id), user_obj['ID']]
                        queries.append(query); params.append(param)
                        
                        start_date = datetime.now()
                        end_date = datetime.now() + timedelta(days=365)
                        for item in misc['active_cart']:
                            is_group = False
                            if item['product_ID'] in [3]:
                                is_group = True
                                
                            
                            
                            if is_group:
                                
                                conn, cursor = mysql_connect()
                                cursor.execute("SELECT * from LRP_Quotes where active", [])
                                quotes = zc.dict_query_results(cursor)
                                cursor.execute("SELECT * from LRP_Subscriptions where active", [])
                                subscriptions = zc.dict_query_results(cursor)
                                cursor.execute("SELECT * from LRP_Groups where active", [])
                                groups = zc.dict_query_results(cursor)
                                cursor.execute("SELECT * from LRP_Group_Access where active", [])
                                all_group_access = zc.dict_query_results(cursor)
                                group_access = [z for z in all_group_access if z['user_ID'] == user_obj['ID']]
                                cursor.close(); conn.close()
                                
                                # Kill the existing trial subscription if one exists for this group
                                quote = quotes[ [ z['ID'] for z in quotes].index(item['quote_ID']) ]                            
                                group = groups[ [ z['ID'] for z in groups].index(quote['group_ID']) ]                            
                                
                                if item['trial_subscription_ID'] is not None:
                                    sub = subscriptions[ [z['ID'] for z in subscriptions].index(item['trial_subscription_ID']) ]
                                    queries.append("UPDATE LRP_Subscriptions set status=%s, end_date=%s where ID=%s")
                                    params.append(["inactive", datetime.now(), sub['ID']])
                                    
                                    
                                
                                # Set up the relevant subscriptions
                                queries.append("INSERT INTO LRP_Subscriptions (ID, active, start_date, end_date, group_ID, product_ID, quote_ID, status, trial, price_paid, stripe_payment_intent) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Subscriptions fds), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
                                params.append([1, start_date, end_date, group['ID'], item['product_ID'], item['quote_ID'], 'active', 0, item['price'], encrypt(payment_intent)])
                                
                                tup = (user_obj['ID'], group['ID'])
                                if tup in [(z['user_ID'], z['group_ID']) for z in group_access if z['status'] == "active"]:
                                    queries.append("UPDATE LRP_Group_Access set active=1, status='active' where user_ID=%s and group_ID=%s")
                                    params.append([user_obj['ID'], group['ID']])
                                else:
                                    queries.append("INSERT INTO LRP_Group_Access (ID, user_ID, group_ID, status, active, admin) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Group_Access fds), %s, %s, %s, %s, %s)")
                                    params.append([user_obj['ID'], group['ID'], 'active', 1, 1])
                                
                                query = "UPDATE LRP_Users set active_group=%s where ID=%s"
                                param = [group['ID'], user_obj['ID']]
                                queries.append(query); params.append(param)
                                
                            else:
                                queries.append("INSERT INTO LRP_Subscriptions (ID, active, start_date, end_date, user_ID, product_ID, quote_ID, status, trial, price_paid, stripe_payment_intent) VALUES ((SELECT IFNULL(max(ID), 0) + 1 from LRP_Subscriptions fds), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
                                params.append([1, start_date, end_date, user_obj['ID'], item['product_ID'], item['quote_ID'], 'active', 0, item['price'], encrypt(payment_intent)])
                        
                                
                        
                        

                        # Update the actual cart elements to mark them as paid
                        query = "UPDATE LRP_Cart set status='paid' where active and user_ID=%s and status='added'"
                        param = [user_obj['ID']]
                        queries.append(query); params.append(param)
                        
                        # Send the receipt
                        misc['receipt_email'] = user_obj['email_decrypted']
                        misc['end_date_formatted'] = end_date.strftime("%b %d, %Y").replace(" 0", " ")
                        misc['end_date'] = end_date
                        misc['receipt'] = create_receipt_msg(misc)
                        
                        mail_res, dbrec = finalize_mail_send(misc['receipt'])
                        if mail_res != "": create_mail_record(dbrec)
                        if not (mail_res == "Success" or not ('--no-mail' not in client_secrets['local'] or client_secrets['local']['--no-mail'] not in ["Y", 'y', 'yes'])):
                            logging.error("Receipt mail send failed for %s" % (user_obj['email_decrypted']))
                    
                    self.response.set_status(r[1])
                    self.response.out.write(r[0])
                    ex_queries(queries, params)
                    
                    
                except stripe.error.CardError as e:
                    logging.error("Error (on the Stripe side) processing a $%.2f payment for %s" % (cart_total_in_cents/100.,  user_obj['email_decrypted']))
                    logging.error(traceback.format_exc())
                    self.response.set_status(500)
                    self.response.out.write(json.dumps({'error': e.user_message}))
               
                except Exception as e:
                    logging.error("Error (on my end) processing a $%.2f payment for %s" % (cart_total_in_cents/100.,  user_obj['email_decrypted']))
                    logging.error(traceback.format_exc())
                    self.response.set_status(500)
                    self.response.out.write(json.dumps({'error': "Something went wrong during payment processing."}))
               
                
        
        else:
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

    
        
    def get(self):
        target_template = "index.html"
        default_get(self)
            
class ReportHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self): self.response.headers.add_header('X-Frame-Options', 'DENY'); self.response.headers.add('Strict-Transport-Security' ,'max-age=31536000; includeSubDomains'); return self.session_store.get_session()

    
    def post(self):
        
        target_template = "report.html"
        misc = {'handler': 'report', 'error': None, 'msg': None, 'action': self.request.get('action')}; user_obj = None; queries = []; params = []

        pd(misc)
        
        session_ID = self.session.get('session_ID')
        if session_ID not in [None, 0]:
            user_obj = get_user_obj({'session_ID': session_ID})
            if user_obj['auth']:      
                user_obj['user_cookie'] = None
                layout = "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"
            else:
                user_obj = process_non_auth(self); user_obj['ID'] = None
                layout = 'layout_no_auth.html'
        else:
            user_obj = process_non_auth(self); user_obj['ID'] = None
            layout = 'layout_no_auth.html'
            
        
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': layout}
        path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))

    
        
    def get(self):
        target_template = "index.html"
        default_get(self)
            
def url_escape(url):
    if url is None: return url
    url = (url
    
    .replace("%", "%25")
    
    .replace(" ", "%20")
    .replace("!", "%21")
    .replace('"', "%22")
    .replace("#", "%23")
    .replace("$", "%24")
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
        
        misc = {'handler': 'editGroup', 'emails': "", 'error': None, 'msg': None}; user_obj = None; queries = []; params = []
        misc['add_members_msg'] = None
        misc['add_members_error'] = None
        misc['edit_members_msg'] = None
        misc['edit_members_error'] = None
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
                        
                        misc['edit_members_msg'] = "Your edits have been processed."
                        ex_queries(queries, params)
        
                    elif req['action'] == "add_members":
                        conn, cursor = mysql_connect()
                        cursor.execute("SELECT * from LRP_Users")
                        users = zc.dict_query_results(cursor)
                        cursor.execute("SELECT * from LRP_Group_Access")
                        access = zc.dict_query_results(cursor)
                        cursor.close(); conn.close()
                        
                        for z in users:
                            z['username_decrypted'] = decrypt(z['username'])
                            z['email_decrypted'] = decrypt(z['email'])
                            
                        next_user_ID = max([z['ID'] + 1 for z in users]) if len(users) > 0 else 1
                    
                        
                        matches = [{'seq': i, 'email': z.strip().lower()} for i, z in enumerate(list(set(re.findall(email_regex, req['emails']))))]
                        if len(matches) == 0:
                            misc['add_members_error'] = "No email addresses were detected in your entry."
                        for m in matches:
                            m['user_exists'] = 1 if m['email'] in [z['email_decrypted'].strip().lower() for z in users] else 0
                            m['user_ID'] = None; m['access_exists'] = 0; m['access_active'] = 0
                            if m['user_exists']:
                            
                                tmp_user = users[ [z['email_decrypted'].strip().lower() for z in users].index(m['email']) ] 
                                m['user_ID'] = tmp_user['ID'] 
                                m['access_exists'] = 1 if m['user_ID'] in [z['user_ID'] for z in access if z['group_ID'] == misc['group_ID']] else 0
                                m['access_active'] = 1 if m['user_ID'] in [z['user_ID'] for z in access if z['status'] == "active" and z['group_ID'] == misc['group_ID']] else 0
                            else:
                                random.seed(time.time() + m['seq'] + 9518)
                                m['ab_group'] = min(47, int(random.random()*48.))
                                m['tmp_password'] = create_temporary_password(m['seq'])
                                m['username'] = m['email'].split("@")[0]
                                if m['username'] in [z['username_decrypted'] for z in users]:
                                    orig = m['username']; seq = 1
                                    while "%s%s" % (orig,seq) in [z['username_decrypted'] for z in users]:
                                        seq += 1
                                    m['username'] = "%s%s" % (orig,seq)
                            if not m['user_exists']:
                                if os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/') or not (m['username'].startswith("newuser")):
       
                                    tmp1 = create_temporary_password()
                                    tmp2 = create_temporary_password()
                                    m['activation_code'] = "%s%s" % (tmp1, tmp2)
                                else:
                                    m['activation_code'] = "%s%s" % (m['username'], datetime.now().strftime("%Y%m%d"))
                                
                                
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
                                
                                tmp_keys = ['username', 'email', 'tmp_password']
                                for k in tmp_keys:
                                    m["%s_encrypted" % k] =  encrypt(m[k])
                                queries.append("INSERT INTO LRP_Users (ID, email, active, logins, user_type, password, username, AB_group, date_created, track_GA, active_group, is_admin, activation_code, activated, activation_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
                                params.append([next_user_ID, m['email_encrypted'], 1, 0, 'team', m['tmp_password_encrypted'], m['username_encrypted'], m['ab_group'], datetime.now(), 1, misc['group_ID'], 0, m['activation_code'], 0, 'full'])
                                
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
                                
                                mail_res, dbrec = finalize_mail_send(msg)
                                if mail_res != "": create_mail_record(dbrec)
                            
                            
                            if not m['access_active']:
                                msg = email_templates[ [z['template_desc'] for z in email_templates].index('Added User to Group') ]
                                msg['email'] = m['email']
                                msg['subject'] = "You've been added to %s" % (user_obj['active_group_name'])
                                
                                msg['content'] = get_file(msg['bucket'], msg['fname'])
                                msg['content'] = msg['content'].replace("[group_name]", user_obj['active_group_name'])
                                
                                mail_res, dbrec = finalize_mail_send(msg)
                                if mail_res != "": create_mail_record(dbrec)
                        
                        
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
                
                if user_obj['inactive_group_members'] is not None:
                    for u in user_obj['inactive_group_members']:
                        u['username_decrypted'] = decrypt(u['username'])
                        u['username'] = ""
                if user_obj['active_group_members'] is not None:
                    for u in user_obj['active_group_members']:
                        u['username_decrypted'] = decrypt(u['username'])
                        u['username'] = ""
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
        
        misc = {'handler': 'resend', 'emails': "", 'error': None, 'msg': None}; user_obj = None; queries = []; params = []
    
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
                
                msg['email'] = decrypt(user['email'])
                msg['subject'] = "Your LacrosseReference PRO account is ready (Resend)"
                
                msg['content'] = get_file(msg['bucket'], msg['fname'])
                msg['content'] = msg['content'].replace("[activation_link]", "https://pro.lacrossereference.com/activate?c=%s" % (url_escape(activation_code)))
                
                mail_res, dbrec = finalize_mail_send(msg)
                if mail_res != "": create_mail_record(dbrec)
                
                misc['msg'] = "Activation email has been resent to %s" % decrypt(user['email'])
                
                
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
        
        default_get(self)

def default_get(self):
    target_template = "index.html"
    misc = {'handler': 'index', 'username': '', 'password': '', 'email': '', 'phone': '', 'user_ID': None, 'process_step': 'start'}; user_obj = None
    session_ID = self.session.get('session_ID')
    if session_ID not in [None, 0]:
        user_obj = get_user_obj({'session_ID': session_ID})
        if user_obj['auth']:
            
            
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_main.html" if user_obj['user_type'] is not None else "layout_lurker.html"}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else:
            tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
            path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
    else: 
        user_obj = process_non_auth(self)
        tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
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
        misc = {'handler': 'preferences', 'error': None, 'msg': None}; user_obj = None
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
        misc = {'handler': 'account', 'error': None, 'msg': None}; user_obj = None
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
                
                profile_keys = ['email', 'username', 'phone']
                for p in profile_keys:
                    if user_obj[p] is None:
                        user_obj['%s_str' % p] = ""
                    else:
                        user_obj['%s_str' % p] = decrypt(user_obj[p])
                profile_keys = ['name']
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
                tv = {'user_obj': None, 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
                path = os.path.join("templates", target_template); self.response.out.write(template.render(path, tv))
        else: 
        
            target_template = "index.html"
            user_obj = process_non_auth(self)
            tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': 'layout_no_auth.html'}
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
    misc = {'handler': '404', 'error': None, 'msg': None}
    tv = {'user_obj': finish_user_obj(user_obj), 'misc': finish_misc(misc, user_obj), 'layout': "layout_no_auth.html"}
    response.set_status(404)
    path = os.path.join("templates", 'error_404.html'); response.out.write(template.render(path, tv))
    
def handle_500(request, response, exception):
    logging.exception(exception)
    user_obj = get_user_obj()
    misc = {'handler': '500', 'error': None, 'msg': None}
    if not os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/'):
        misc['error'] = traceback.format_exc()
        txt = misc['error'].split("File")[-1]
        regexes = []
        regexes.append({'regex': re.compile(r'\"(.*?.py)\", (line [0-9]+?), in ([^\s]+?)\s([\s\S]+)', re.IGNORECASE)})
        for r in regexes:
        
            match = r['regex'].search(txt)
            if match:
                sections = []
                sections.append("<div class='col-12' style='padding-bottom: 30px;'><span class='font-36 bold' style='display:contents;'>%s</span></div>" % ("%s - %s" % (match.group(1).split("\\")[-1], match.group(2))))
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
    ,('/register_config_dead', RegisterConfigHandler)
    ,('/cart', CartHandler)
    
    ,('/preferences', PreferencesHandler)
    ,('/switch_groups', SwitchGroupsHandler)
    ,('/password', PasswordHandler)
    ,('/profile', ProfileHandler)
    ,('/subscription', SubscriptionHandler)
    
    
    ,('/activate', ActivateHandler)
    ,('/privacy', PrivacyHandler)
    ,('/terms', TermsHandler)
    ,('/edit_group', EditGroupHandler)
    ,('/create', CreateHandler)
    ,('/admin', AdminHandler)
    ,('/upload', UploadHandler)
    ,('/resend', ResendHandler)
    ,('/quote', ViewQuoteHandler)
    ,('/create-refund', CreateRefundHandler)
    ,('/extend-subscription', ExtendSubscriptionHandler)
    ,('/create-quote', CreateQuoteHandler)
    ,('/review-quote', ReviewQuoteHandler)
    ,('/checkout', CheckoutHandler)
    ,('/email', EmailHandler)
    ,('/contact', ContactHandler)
    ,('/report', ReportHandler)
    ,('/help', HelpHandler)
    ,('/cron-(.+)', CronHandler)
    
    
    ,('/teamshome', TeamsHomeHandler)
    
    ,('/(product-summary.+)', ProductSummaryHandler)
    
], config=config)

app.error_handlers[500] = handle_500
app.error_handlers[404] = handle_404
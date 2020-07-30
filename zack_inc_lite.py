
import os, time, datetime, re, random, sys, traceback

def goo_shorten_url(url):
    import json, requests
    if False: # Old Google Stuff
        paths = ['/home/pi/zack/zackcapozzi_google_api_key', 'C:\Users\zcapo\Documents\workspace\ZackInc\zackcapozzi_google_api_key']
        for p in paths:
            if os.path.isfile(p):
                api_key = open(p, 'r').read().strip(); break

        post_url = 'https://www.googleapis.com/urlshortener/v1/url?key=%s' % api_key
        payload = {'long_Url': url}
        r = requests.post(post_url, data=json.dumps(payload), headers=headers)
        headers = {'content-type': 'application/json'}
        d = json.loads(r.text)
    else:
        paths = ['/home/pi/zack/zcapozzi_bitly_api_key', 'C:\Users\zcapo\Documents\workspace\ZackInc\zcapozzi_bitly_api_key']
        for p in paths:
            if os.path.isfile(p):
                api_key = open(p, 'r').read().strip(); break


        group_guid = "Bj44ezK0gOW"
        if group_guid not in['', None]:
            headers = {'Host': 'api-ssl.bitly.com', 'Authorization': 'Bearer %s' % api_key, 'Accept': 'application/json'}

            groups_url = "https://api-ssl.bitly.com/v4/groups"
            r = json.loads(requests.get(groups_url, headers=headers).content)
            group_guid = r['groups'][0]['guid']
            print "\n\nResponse #1\n"
            print r
            print "\n\n"

        print "Use Bitly"
        headers = {'Host': 'api-ssl.bitly.com', 'Authorization': 'Bearer %s' % api_key, 'Content-Type': 'application/json'}
        post_url = 'https://api-ssl.bitly.com/v4/shorten'
        payload = {'long_url': url, 'group_guid': group_guid}
        print_dict(headers)
        print_dict(payload)
        r = requests.post(post_url, data=json.dumps(payload), headers=headers)
        print "\n\nResponse #2\n"
        print r
        print "\n\n"

        d = json.loads(r.text)

    #send_telegram(r.text, bot_token)
    if 'id' in d:
        if 'ztclaxpower' in url:
            return d['id']
        else:
            return d['id'].replace("https://", "")

    if 'Rate Limit Exceeded' in str(r.text):
        return url




    return url


def file_to_dict(path):
    games = [z.split(",") for z in filter(None, open(path, 'r').read().split("\n"))]
    if len(games) > 0:
        game_headers = games[0]; games = games[1:]
        for i, g_ in enumerate(games):
            d = {}
            for k, v in zip(game_headers, g_):
                d[k] = v
            games[i] = d
    return games

def dict_to_file(dict_obj, path):
    f = open(path, 'w')
    keys = dict_obj[0].keys()
    header = ",".join(keys)
    f.write("%s\n" % header)
    for r in dict_obj:
        recs = []
        for k in keys:
            recs.append(str(r[k]).replace(",", ";"))
        f.write("%s\n" % (",".join(recs)))
    f.close()
    print "%d rows written to %s" % (len(dict_obj), path)

def dict_query_results(cursor):
    results = []
    res = cursor.fetchall()
    data = []
    num_fields = []
    columns = []
    types_ = []

    if cursor is not None and res is not None:
        if cursor.description is not None:
            columns = [i[0] for i in cursor.description]
            for i, row in enumerate(res):
                d = {}
                for c, r in zip(columns, row):

                    d[c] = r
                results.append(d)
    return results

def remove_non_ascii(s): return "".join(filter(lambda x: ord(x) < 128, s)) if s is not None else s



def print_dict(d):
    s = ""
    if isinstance(d, dict):
        tmp_keys = sorted(d.keys())
        for k in tmp_keys:
            s += ("\n%s: %s" % (k, d[k]))
    elif d is not None:
        for d_ in d:
            tmp_keys = sorted(d_.keys())
            for k in tmp_keys:
                s += ("\n%s: %s" % (k, d_[k]))
            s += ("\n---------------------------")
    
    return s

def num_to_val(s):
    if s.lower() == "one"               : return 1
    elif s.lower() == "two"             : return 2
    elif s.lower() == "three"           : return 3
    elif s.lower() == "four"            : return 4
    elif s.lower() == "five"            : return 5
    elif s.lower() == "six"             : return 6
    elif s.lower() == "seven"           : return 7
    elif s.lower() == "eight"           : return 8
    elif s.lower() == "nine"            : return 9
    elif s.lower() == "ten"             : return 10
    elif s.lower() == "eleven"             : return 11
    elif s.lower() == "twelve"             : return 12
    elif s.lower() == "thirteen"             : return 13
    elif s.lower() == "fourteen"             : return 14
    elif s.lower() == "fifteen"             : return 15
    elif s.lower() == "sixteen"             : return 16
    elif s.lower() == "seventeen"             : return 17
    elif s.lower() == "eighteen"             : return 18
    elif s.lower() == "nineteen"             : return 19
    elif s.lower() == "twenty"             : return 20
    else:
        print("Failed to convert %s to number" % s); sys.exit()

current_milli_time = lambda: int(round(time.time() * 1000))

def get_number_suffix(i):
    i = int(i)
    if 4 <= i <= 20 or i % 10 > 3:
        return "th"
    elif i % 10 == 0:
        return "th"
    elif i % 10 == 1:
        return "st"
    elif i % 10 == 2:
        return "nd"
    elif i % 10 == 3:
        return "rd"


import tweepy
import couchdb
import sys

def set_keys(keyfile):
    with open(keyfile) as textfile:
        keys = textfile.readline().split()
        consumer_key = keys[0]
        consumer_secret = keys[1]
        access_token_key = keys[2]
        access_token_secret = keys[3]
        return consumer_key, consumer_secret, access_token_key, access_token_secret

def get_login(loginfile):
    with open(loginfile) as textfile:
        logins = textfile.readline().split()
        username = logins[0]
        password = logins[1]
        return username, password



def get_tweet_auth(keyfile):
    consumer_key, consumer_secret, access_token_key, access_token_secret=set_keys(keyfile)
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token_key, access_token_secret)
    return auth

def get_couchdb(couch_login,couch_server,database,ini=False):
    db_user, db_pwd=get_login(couch_login)
    couch = couchdb.Server("http://" + db_user + ":" + db_pwd + "@" + couch_server)
    try:
        db = couch[database]
        return db
    except:
        if ini:
            db = couch.create(database)
            return db
        else:
            sys.exit('Reference database does not exist')





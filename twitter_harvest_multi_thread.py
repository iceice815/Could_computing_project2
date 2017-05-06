import tweepy
import time
import sys
import threading
import sentiment_analysis as sa
from tweets_tools import get_tweet_auth,get_couchdb

tweet_login_stream = sys.argv[1] #auth_streaming
tweet_login_rest_steam =sys.argv[2] #auth_stream_rest
tweet_login_followers = sys.argv[3]  #auth_followers
tweet_login_friends = sys.argv[4]   #auth_friends
tweet_login_rest = sys.argv[5]  #auth_rest
couch_login = sys.argv[6]   #couch_login
couch_server = sys.argv[7]  # http://115.146.93.83:5984
database = sys.argv[8]  #databse name sydeny
#user_databse = sys.argv[9] #userlist
locationsteam = [float(x) for x in sys.argv[9].split(',')] #streaming ""
locationrest =sys.argv[10]
geocode =sys.argv[11]
def main():
    # 创建新线程
    global classifier
    classifier = sa.ta_classifier()
    thread1 = harvestThread(1, "Thread-steaming")
    thread1.start()
    time.sleep(5)

    thread2 = harvestThread(2, "Thread-rest-streaming")
    thread3 = harvestThread(3, "Thread-followers")
    thread4 = harvestThread(4, "Thread-friends")
    thread5 = harvestThread(5, "Thread-rest")

    thread2.start()
    thread3.start()
    thread4.start()
    thread5.start()

    print("Exiting Main Thread")

class harvestThread(threading.Thread):   #继承父类threading.Thread
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        if self.threadID == 1:
            print("Starting " + self.name)
            db_data = get_couchdb(couch_login, couch_server, database, True)

            #db_users = get_couchdb(couch_login, couch_server, user_databse, True)
            auth_steam = get_tweet_auth(tweet_login_stream)
            api_steam = tweepy.API(auth_steam)
            sapi = tweepy.streaming.Stream(auth=auth_steam, listener=CustomStreamListener(api_steam, db_data))

            while True:
                try:
                    sapi.filter(locations=locationsteam)
                except:
                    pass
        elif self.threadID == 2:
            print("Starting " + self.name)
            db_users = get_couchdb(couch_login, couch_server, database)
            auth_rest_steam = get_tweet_auth(tweet_login_rest_steam)
            api_rest_stream = tweepy.API(auth_rest_steam)
            temp_rowskey = []
            try:
                while True:
                    rows=db_users.view('_design/_view/_view/by_userid', group=True).rows
                    rowskey=[]
                    for ele in rows:
                        rowskey.append(ele.key)
                    for ele in temp_rowskey:
                        rowskey.remove(ele)
                    for ele in rowskey:
                        user_id = ele
                        process_user(api_rest_stream, user_id, db_users)
                        print('Processed user_id %s' % user_id)
                    temp_rowskey = rowskey

            except KeyboardInterrupt:
                print('\nKeyboard Interrupt\nShutting down the harvester')

        elif self.threadID == 3:
            print("Starting " + self.name)
            db_users = get_couchdb(couch_login, couch_server, database)
            auth_followers = get_tweet_auth(tweet_login_followers)
            api_followers = tweepy.API(auth_followers)
            temp_rowskey = []
            try:
                while True:
                    rows = db_users.view('_design/_view/_view/by_userid', group=True).rows
                    rowskey = []
                    for ele in rows:
                        rowskey.append(ele.key)
                    for ele in temp_rowskey:
                        rowskey.remove(ele)
                    for ele in rowskey:
                        user_id = ele

                        followers_id = get_followers(user_id, api_followers)

                        for follower_id in followers_id:
                            process_user(api_followers, follower_id, db_users)

                            print('Processed followers_id %s' % follower_id)
                    temp_rowskey = rowskey
            except KeyboardInterrupt:
                print('\nKeyboard Interrupt\nShutting down the harvester')

        elif self.threadID ==4:
            print("Starting " + self.name)
            db_users = get_couchdb(couch_login, couch_server, database)
            auth_friends = get_tweet_auth(tweet_login_friends)
            api_friends = tweepy.API(auth_friends)
            temp_rowskey = []
            try:
                while True:
                    rows = db_users.view('_design/_view/_view/by_userid', group=True).rows
                    rowskey = []
                    for ele in rows:
                        rowskey.append(ele.key)
                    for ele in temp_rowskey:
                        rowskey.remove(ele)
                    for ele in rowskey:
                        user_id = ele
                        friends_id = get_friends(user_id, api_friends)
                        # print(friends_id)

                        for friend_id in friends_id:
                            process_user(api_friends, friend_id, db_users)

                            print('Processed friends_id %s' % friend_id)
                    temp_rowskey = rowskey
            except KeyboardInterrupt:
                print('\nKeyboard Interrupt\nShutting down the harvester')

        elif self.threadID ==5:
            print("Starting " + self.name)
            db_users = get_couchdb(couch_login, couch_server, database)
            auth_rest = get_tweet_auth(tweet_login_rest)
            api_rest = tweepy.API(auth_rest)
            api_rest.wait_on_rate_limit = True
            api_rest.wait_on_rate_limit_notify = True

            try:
                while True:
                    try:
                        new_tweets = api_rest.search(geocode=geocode, count=100)
                        add_tweets_to_db(new_tweets, db_users)
                    except tweepy.TweepError as e:
                        # Just exit if any error
                        print("some error : " + str(e))
                        time.sleep(10)
                        continue
            except KeyboardInterrupt:
                print('\nKeyboard Interrupt\nShutting down the harvester')


def get_friends(user_id,api):
    friends = []
    page_count = 0
    try:
        for friend in tweepy.Cursor(api.friends_ids, id=user_id, count=200).pages():
            page_count += 1
            friends.extend(friend)
    except:
        pass
    return friends

def get_followers(user_id,api):
    followers = []
    page_count = 0
    try:
        for follower in tweepy.Cursor(api.followers_ids, id=user_id, count=200).pages():
            page_count += 1
            followers.extend(follower)
    except:
        pass
    return followers

def process_user(api, user_id, db):
    try:
        user_statuses = api.user_timeline(id=user_id, count=200)
        add_tweets_to_db(user_statuses, db)
    except:
        pass

def add_tweets_to_db(statuses, db):
    for status in statuses:
        try:
            if status.place.full_name  == locationrest:
                if status.id_str not in db:
                    tweet = status._json
                    tweet['_id'] = status.id_str
                    print("1111111111")
                    try:
                        print("22222222")
                        label = sa.predict(classifier, tweet['text'])
                        tweet['label'] = label
                        db.save(tweet)

                        print('Tweet added to CouchDB: ')
                    except :
                        pass
        except :
               pass

class CustomStreamListener(tweepy.StreamListener):
    def __init__(self, api, db):
        self.db = db
        #self.db_user =db_user
        self.api = api
        super(tweepy.StreamListener, self).__init__()

    def on_status(self, status):
        tweet = status._json
        print(tweet)
        tweet['_id'] = status.id_str

        if tweet['_id'] not in self.db:
            try:
                label = sa.predict(classifier, tweet['text'])
                tweet['label'] = label
                self.db.save(tweet)
                print("Tweets saved by streaming")
                #self.db_user.save(tweet.user.id)#add id
            except:
                pass

    def on_error(self, status_code):
            print('Encountered error with status code:', status_code, file=sys.stderr)
            return True  # Don't kill the stream

    def on_timeout(self):
            print('Timeout...', file=sys.stderr)
            return True  # Don't kill the stream


# Run the Main Method
if __name__ == '__main__':
    main()
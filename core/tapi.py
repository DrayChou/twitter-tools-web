#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import sys
import time
import yaml
import json
import argparse
import twitter
from twitter import TwitterError
from requests_oauthlib import OAuth1Session
import webbrowser

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'


class TApi(object):
    def __init__(self, sid=None):
        self.tid = None
        self.sid = sid
        self.user = None
        self.api = None

        self.consumer_key = None
        self.consumer_secret = None
        self.oauth_token = None
        self.oauth_token_secret = None
        self.access_token = None
        self.access_token_secret = None

        self.load_consumer()
        self.load_credentials()
        pass

    def load_consumer(self):
        if self.consumer_key and self.consumer_secret:
            return self.consumer_key, self.consumer_secret

        try:
            path = os.path.join(os.path.dirname(os.path.dirname(
                __file__)), 'settings.yml')
            print("api", "load_consumer", path)

            with open(path) as f:
                c = yaml.safe_load(f)
                print("api", "load_consumer", c)

                self.consumer_key = c.get('consumer_key')
                self.consumer_secret = c.get('consumer_secret')
                return c['consumer_key'], c['consumer_secret']
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("api", "load_consumer", "Error->", exc_type, fname, exc_tb.tb_lineno, e)

        return None, None

    def load_credentials(self):
        try:
            if self.sid is None:
                return False

            base_path = os.path.join(os.path.dirname(os.path.dirname(
                __file__)), "cache", self.sid)
            if not os.path.exists(base_path):
                os.makedirs(base_path)
            path = os.path.join(base_path, 'credentials.yml')
            print("api", "load_credentials", base_path, path)

            with open(path) as f:
                c = yaml.safe_load(f)
                if c.get("user", None) != self.sid:
                    return

                self.access_token = c['access_token']
                self.access_token_secret = c['access_token_secret']

                return c
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("api", "load_credentials", "Error->", exc_type, fname, exc_tb.tb_lineno, e)

        return False

    def save_credentials(self):
        try:
            if self.sid is None:
                return False

            base_path = os.path.join(os.path.dirname(os.path.dirname(
                __file__)), "cache", self.sid)
            if not os.path.exists(base_path):
                os.makedirs(base_path)

            yml_f = os.path.join(base_path, 'credentials.yml')
            print("api", "save_credentials", yml_f)
            with open(yml_f, 'w') as f:
                yaml.dump({
                    "access_token": self.access_token,
                    "access_token_secret": self.access_token_secret,
                    "sid": self.sid,
                    "user": self.user,
                }, f, default_flow_style=False)

            json_f = os.path.join(base_path, 'credentials.json')
            print("api", "save_credentials", json_f)
            with open(json_f, 'w') as f:
                json.dump({
                    "access_token": self.access_token,
                    "access_token_secret": self.access_token_secret,
                    "sid": self.sid,
                    "user": self.user.__dict__,
                }, f, indent=2)

            return True
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("api", "save_credentials", "Error->", exc_type, fname, exc_tb.tb_lineno, e)

        return False

    def get_url(self):
        try:
            ck, cs = self.load_consumer()
            if self.consumer_key is None:
                return

            oauth_client = OAuth1Session(
                client_key=self.consumer_key, client_secret=self.consumer_secret, callback_uri='oob')

            resp = oauth_client.fetch_request_token(REQUEST_TOKEN_URL)
            if resp.get("oauth_token", None) is None:
                return
            print("api", "get_url", resp)

            self.oauth_token = resp.get('oauth_token')
            self.oauth_token_secret = resp.get('oauth_token_secret')

            url = oauth_client.authorization_url(AUTHORIZATION_URL)
            return url
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("api", "get_url", "Error->", exc_type, fname, exc_tb.tb_lineno, e)

        return

    def auth(self, pincode):
        try:
            print('\nGenerating and signing request for an access token...\n')
            ck, cs = self.load_consumer()
            if ck is None:
                return

            print("api", "auth", pincode)
            oauth_client = OAuth1Session(
                client_key=ck, client_secret=cs,
                resource_owner_key=self.oauth_token,
                resource_owner_secret=self.oauth_token_secret,
                verifier=pincode
            )
            print("api", "auth", self.__dict__)
            resp = oauth_client.fetch_access_token(ACCESS_TOKEN_URL)
            print("api", "auth", resp)
            if resp.get("oauth_token", None) is None:
                return
            self.access_token = resp.get('oauth_token')
            self.access_token_secret = resp.get('oauth_token_secret')
            self.api = twitter.Api(
                consumer_key=ck, consumer_secret=cs,
                access_token_key=self.access_token, access_token_secret=self.access_token_secret
            )

            if self.sid is None:
                self.user = self.get_myself()
                self.sid = self.user.screen_name

            self.save_credentials()

            return True
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("api", "auth", "Error->", exc_type, fname, exc_tb.tb_lineno, e)

        return

    def get_myself(self):
        res_post = self.api.PostUpdate("test:"+str(time.time()))
        print("api","get_myself","PostUpdate", res_post)
        if res_post and res_post.id:
            res_del = self.api.DestroyStatus(res_post.id)
            print("api","get_myself","DestroyStatus", res_del)
            return res_post.user

        return

class TApiManager(object):
    def __init__(self):
         self.tapi_dict = dict()
    
    def get_tapi(self, tid):
        if self.tapi_dict.get(tid, None) is None:
            tapi = TApi()
            tapi.tid = tid
            print("TApiManager", "get_tapi", tapi.__dict__)
            self.tapi_dict[tid] = tapi

        return self.tapi_dict.get(tid)

tapi_mgr = TApiManager()

if __name__ == '__main__':
    tapi = TApi()
    url = tapi.get_url()
    print("url", url)

    pincode = input('\nEnter your pincode? ')
    tapi.auth(pincode)
    print("api", tapi)

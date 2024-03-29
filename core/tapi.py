#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import sys
import yaml
import json
import time
from datetime import datetime
import twitter
from twitter import TwitterError
from requests_oauthlib import OAuth1Session
from core.settings import s_mgr

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'


class Task(object):
    def __init__(self, timer, owner, seconds, *args, **kwargs):
        self.v = 1
        self.timer = timer
        self.owner = owner
        self.seconds = seconds
        self.args = args
        self.kw = kwargs
        self.run_time = time.time() + seconds

    def __repr__(self):
        return str(self.__dict__)

    def excuse(self):
        self.owner.on_timer(*self.args, **self.kw)


class TApi(object):
    def __init__(self, sid=None, tid=None):
        self.tid = tid
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

        self.timers = {}
        self.timer_active = True
        self.timer_no_stop = [
        ]
        self.timer_data = {}

        self.ct = 0
        pass

    def set_timer(self, timer, seconds, *args, **kwargs):  # 设置定时器
        """
        仅支持基本数据类型，不支持实例对象
        :param timer:string
        :param seconds:int
        :param args:list
        :param kwargs:dict
        :return:
        """
        my_task = Task(self, timer, seconds, *args, **kwargs)
        self.timers[timer] = my_task
        print("Timer set_timer timer={}, seconds={}, now_timer={}, real_timer={}, delay={}".format(
            timer, seconds,
            datetime.utcfromtimestamp(
                time.time()).strftime('%Y-%m-%d %H:%M:%S'),
            datetime.utcfromtimestamp(
                my_task.run_time).strftime('%Y-%m-%d %H:%M:%S'),
            my_task.run_time - time.time()
        ))

    # 取消定时器
    def kill_timer(self, timer):
        task = self.timers.get(timer)
        if task:
            print("Timer kill_timer timer={}, seconds={}, now_timer={}, real_timer={}, delay={}".format(
                timer, task.seconds,
                datetime.utcfromtimestamp(
                    time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                datetime.utcfromtimestamp(
                    task.run_time).strftime('%Y-%m-%d %H:%M:%S'),
                task.run_time - time.time()
            ))
            task.v = 0

    # 删除定时器
    def del_timer(self, timer):
        task = self.timers.get(timer)
        if task:
            print("Timer del_timer timer={}, seconds={}, now_timer={}, real_timer={}, delay={}".format(
                timer, task.seconds,
                datetime.utcfromtimestamp(
                    time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                datetime.utcfromtimestamp(
                    task.run_time).strftime('%Y-%m-%d %H:%M:%S'),
                task.run_time - time.time()
            ))

            try:
                task.v = 0
                self.timers.pop(timer, None)
                del task
            except Exception as ex:
                print("Timer del_timer timer={}, task={}, ex={}".format(
                    timer, task, ex))

    def get_timer_left(self, timer):
        '''
        获取定时器剩余时间
        :param timer:
        :return:
        '''
        task = self.timers.get(timer)
        if task:
            return task.seconds
        return -1

    def get_timer_end_time(self, timer):
        '''
        获取定时器结束时间戳
        :param timer:
        :return:
        '''
        task = self.timers.get(timer)
        if task:
            return task.run_time
        return -1

    def is_exist_timer(self, timer):
        return timer in self.timers

    def pause_timer(self):  # 暂停定时器
        self.timer_active = False

    def resume_timer(self):  # 恢复定时器
        self.timer_active = True

    def clear_timer(self):
        '''
        清理当前这小局的定时器
        :return:
        '''
        del_timers = []
        for k, v in self.timers.items():
            if k in self.timer_no_stop:
                continue
            del_timers.append(k)
        for k in del_timers:
            self.del_timer(k)

    # 心跳的时候检查定时任务
    def heartbeat(self):
        # if not self.timer_active:
        #     return

        # 删除无需
        dirty_timer_set = [k for k, v in self.timers.items() if v.v == 0]
        for k in dirty_timer_set:
            del self.timers[k]

        # 遍历现有的
        curr_timer_list = [k for k in self.timers.keys()]
        for k in curr_timer_list:
            # 如果定时器暂停了
            if not self.timer_active:
                if k in self.timer_no_stop:
                    # 解散房间的倒计时不暂停，其他倒计时可以暂停
                    pass
                else:
                    continue

            task = self.timers[k]
            task.seconds = task.run_time - time.time()
            if task.run_time < time.time():
                self.on_timer(k, task.args, task.kw)
                task.v = 0  # 标记删除
            else:
                pass

    # 启动定时器
    def on_timer(self, timer, args=None, kw=None):
        print("Timer on_timer tapi_id:{} timer:{} args:{} kw:{}".format(
            self.tid, timer, args, kw))

        if timer == "call_followers_clear":
            self.call_followers_clear(args, kw)
        pass

    def call_followers_clear(self, args=None, kw=None):
        print("Timer call_followers_clear sid:{} args:{} kw:{}".format(
            self.sid, args, kw
        ))

        # 初始化
        is_start = kw.get("start", False)
        if is_start:
            # 拿到配置信息
            config = kw.get("config", {})
            if type(config) is str:
                try:
                    config_tmp = json.dumps(config)
                    if config_tmp:
                        config = config_tmp
                except Exception as identifier:
                    config = {}

            self.timer_data["call_followers_clear"] = {
                "state": 0,
                "config": config,
                "create_time": time.time(),
                "try_num": 0,
                # 需要处理的玩家
                "mutual_followers": {
                    # 0: {
                    #     "id": 0,
                    #     "screen_name": "test",
                    #     "name": "test",
                    #     "profile_image_url_https": "https://twitter.com/SORA_MATO_46AAA",
                    #     "protected": "False",
                    #     "default_profile_image": "False",
                    #     "statuses_count": 0,
                    #     "followers_count": 0,
                    # }
                },
                "block_failed_ids": [],
                "unblock_failed_ids": [],
            }

        # 拿到配置信息
        config =  self.timer_data["call_followers_clear"].get("config", {})
        print(self.sid, 'call_followers_clear', 'config', config)

        # 超时的结束掉
        create_time = self.timer_data["call_followers_clear"].get("create_time", 0)
        if abs(time.time() - create_time) > 3600 * 24 * 3:
            self.timer_data["call_followers_clear"]["state"] = 4
            print(self.sid, 'call_followers_clear', 'run over 3 day', 'kill !!!!')
            return

        # 拿一页数据
        follower_ids_cursor = self.timer_data["call_followers_clear"].get("follower_ids_cursor", -1)

        # 拿到自己的 followers
        print(self.sid, 'call_followers_clear', 'Getting followers list')
        ids = []
        try:
            print(self.sid, 'call_followers_clear', 'before',
                  'follower_ids_cursor', follower_ids_cursor)
            follower_ids_cursor, _, ids = self.api.GetFollowersPaged(
                cursor=follower_ids_cursor, count=50)
            print(self.sid, 'call_followers_clear', 'after',
                  'follower_ids_cursor', follower_ids_cursor,
                  'get {} followers'.format(len(ids)))
        except TwitterError as e:
            # 报错了，重新来
            self.set_timer("call_followers_clear", 5, config=config)
            print(self.sid, 'call_followers_clear', 'TwitterError', e)
            return
        except Exception as e:
            print(self.sid, 'call_followers_clear', 'Exception', e)
            return

        # print(self.sid, 'call_followers_clear', 'ids', ids)

        # 保存状态
        self.timer_data["call_followers_clear"]["state"] = 1
        self.timer_data["call_followers_clear"]["try_num"] += 1
        self.timer_data["call_followers_clear"]["follower_ids_cursor"] = follower_ids_cursor

        # 需要清理的账号
        white_list = config.get("white_list", [])
        print(self.sid, 'call_followers_clear',
              'Getting zero or default profile image user info')
        for user_info in ids:
            try:
                # print(self.sid, 'call_followers_clear', 'user_info', user_info)
                need_mutu = False
                # user_info = api.GetUser(user_id=user_id)

                # 白名单
                if user_info.screen_name in white_list:
                    continue

                # 我关注的，跳过
                if user_info.following:
                    continue

                # 少于多少推的处理，处理
                if user_info.statuses_count <= int(config.get("less_statuses_count", 0)):
                    need_mutu = True

                # 少于多少个关注着的处理，处理
                if user_info.followers_count <= int(config.get("less_followers_count", 0)):
                    need_mutu = True

                # 默认头像的，处理
                if config.get("default_profile_image", True):
                    if user_info.default_profile_image == True:
                        need_mutu = True

                # 锁推&关注了我&没有被我关注
                if config.get("check_protected", False):
                    if user_info.protected == True:
                        if user_info.status == None:
                            need_mutu = True

                 # 锁推&关注了我&没有被我关注
                if config.get("check_menofollow", False):
                    if user_info.following == False:
                        need_mutu = True

                if need_mutu == False:
                    continue

                try:
                    # B掉
                    print(self.sid, 'call_followers_clear',
                          'blocking %d' % user_info.id)
                    self.api.CreateBlock(user_info.id)
                except TwitterError:
                    self.timer_data["call_followers_clear"]["block_failed_ids"].append(
                        user_info.id)
                if config.get("unblock", True):
                    try:
                        # 解除 B
                        print(self.sid, 'call_followers_clear',
                              'unblocking %d' % user_info.id)
                        self.api.DestroyBlock(user_info.id)
                    except TwitterError:
                        self.timer_data["call_followers_clear"]["unblock_failed_ids"].append(
                            user_info.id)

                # 记录下来
                user_data = {
                    "id": user_info.id,
                    "screen_name": user_info.screen_name,
                    "name": user_info.name,
                    "profile_image_url_https": user_info.profile_image_url_https,
                    "protected": str(user_info.protected),
                    "default_profile_image": str(user_info.default_profile_image),
                    "statuses_count": user_info.statuses_count,
                    "followers_count": user_info.followers_count,
                }
                print(self.sid, 'call_followers_clear', 'user_info', user_info, 'user_data', user_data)
                self.timer_data["call_followers_clear"]["mutual_followers"][user_info.id] = user_data

            except Exception as e:
                print(e)

        print(self.sid, 'call_followers_clear', 'mutual_followers', len(
            self.timer_data["call_followers_clear"]["mutual_followers"]))

        # 继续抓新流程
        if follower_ids_cursor > 0:
            self.set_timer("call_followers_clear", 5, config=config)
        else:
            # 标记为已经结束
            self.timer_data["call_followers_clear"]["state"] = 4
        pass

    def load_consumer(self):
        if self.consumer_key and self.consumer_secret:
            return self.consumer_key, self.consumer_secret

        try:
            if s_mgr.s_dict.get('consumer_key', None):
                self.consumer_key = s_mgr.s_dict.get('consumer_key')
                self.consumer_secret = s_mgr.s_dict.get('consumer_secret')
                return self.consumer_key, self.consumer_secret
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("api", "load_consumer", "Error->",
                  exc_type, fname, exc_tb.tb_lineno, e)

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
            print("api", "load_credentials", "Error->",
                  exc_type, fname, exc_tb.tb_lineno, e)

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
                    "consumer_key": self.consumer_key,
                    "consumer_secret": self.consumer_secret,
                    "access_token": self.access_token,
                    "access_token_secret": self.access_token_secret,
                    "sid": self.sid,
                    "tid": self.tid,
                    "user": self.user,
                }, f, default_flow_style=False)

            json_f = os.path.join(base_path, 'credentials.json')
            print("api", "save_credentials", json_f)
            with open(json_f, 'w') as f:
                json.dump({
                    "consumer_key": self.consumer_key,
                    "consumer_secret": self.consumer_secret,
                    "access_token": self.access_token,
                    "access_token_secret": self.access_token_secret,
                    "sid": self.sid,
                    "tid": self.tid,
                    "user": self.user.__dict__,
                }, f, indent=2)

            return True
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("api", "save_credentials", "Error->",
                  exc_type, fname, exc_tb.tb_lineno, e)

        return False

    def get_url(self, ck=None, cs=None):
        try:
            if ck is None and cs is None:
                ck, cs = self.load_consumer()
            else:
                self.consumer_key = ck
                self.consumer_secret = cs

            if ck is None:
                return

            oauth_client = OAuth1Session(
                client_key=ck, client_secret=cs, callback_uri='oob')

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
            print("api", "get_url", "Error->",
                  exc_type, fname, exc_tb.tb_lineno, e)

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
            print("api", "auth", "Error->", exc_type,
                  fname, exc_tb.tb_lineno, e)

        return

    def get_myself(self):
        res_post = self.api.PostUpdate("test:"+str(time.time()))
        print("api", "get_myself", "PostUpdate", res_post)
        if res_post and res_post.id:
            res_del = self.api.DestroyStatus(res_post.id)
            print("api", "get_myself", "DestroyStatus", res_del)
            return res_post.user

        return


class TApiManager(object):
    def __init__(self):
        self.tapi_dict = dict()

    def get_tapi(self, tid):
        # print(
        #     "TApiManager", "get_tapi", "--0--",
        #     "tid", tid, type(tid),
        #     "tapi_dict", self.tapi_dict.keys()
        # )

        if type(tid) is bytes:
            tid = tid.decode(encoding='utf-8')
        elif type(tid) is not str:
            tid = str(tid)

        if self.tapi_dict.get(tid, None) is None:
            tapi = TApi(tid=tid)
            print("TApiManager", "get_tapi", "new", tapi.tid)
            self.tapi_dict[tid] = tapi

        return self.tapi_dict.get(tid)

        # 心跳，检查定时任务
    def heartbeat(self):
        try:
            # todo 循环中解散房间导致报错
            tapi_ls = list(self.tapi_dict.keys())
            timeout_tapi = set()
            for tapi_id in tapi_ls:
                now_time = time.time()
                tapi = self.get_tapi(tapi_id)
                if tapi:
                    wait_time = 86400 * 7
                    # 房间创建超过
                    if tapi.ct > 0 and (now_time - tapi.ct) > wait_time:
                        timeout_tapi.add(tapi.tapi_id)
                        continue

                    # 处理定时心跳任务
                    tapi.heartbeat()

            # 删除离线太久的
            for tapi_id in timeout_tapi:
                self.tapi_dict.pop(tapi_id, None)

        except Exception as ex:
            import traceback
            traceback.print_exc()
            print("[tapi_mgr.heartbeat][error] exec error ", ex)
            print("tapi_mgr.heartbeat Exception={}".format(ex))


tapi_mgr = TApiManager()

if __name__ == '__main__':
    tapi = TApi()
    url = tapi.get_url()
    print("url", url)

    pincode = input('\nEnter your pincode? ')
    tapi.auth(pincode)
    print("api", tapi)

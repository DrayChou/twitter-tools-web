# !/usr/bin/env python3
# -  *  - coding:UTF-8 -  *  -

import os
import datetime
import uuid
import tornado.ioloop
import tornado.web
from tornado.options import define, options
from tornado.web import authenticated  # 导入装饰器
from core.tapi import tapi_mgr


class BaseHandler(tornado.web.RequestHandler):
    '''
    设置BaseHandler类，重写函数get_current_user
    '''

    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)

    def get_current_user(self):  # 前面有绿色小圆圈带个o，再加一个箭头表示重写
        tapi = self.get_tapi()
        print("BaseHandler", "get_current_user",
              "tid", tapi.tid if tapi else "")
        if tapi and tapi.user:
            print("BaseHandler", "get_current_user", "sid", tapi.sid)
            return tapi.user
        return

    def get_uuid(self):
        tid = None
        tid_c = self.get_secure_cookie('tid')
        if tid_c:
            tid = tid_c
        else:
            tid = uuid.uuid1()

        if type(tid) is bytes:
            tid = tid.decode(encoding='utf-8')
        elif type(tid) is not str:
            tid = str(tid)

        self.set_secure_cookie("tid", tid)

        return tid

    def get_tapi(self):
        tid = self.get_uuid()
        if tid:
            return tapi_mgr.get_tapi(tid)
        return


class NotFindHandler(BaseHandler):
    def post(self):
        dict_data = dict()
        dict_data["state"] = 404
        dict_data["msg"] = "not find url"
        self.set_status(404)
        self.write(dict_data)

    def get(self):
        dict_data = dict()
        dict_data["state"] = 404
        dict_data["msg"] = "not find url"
        self.set_status(404)
        self.write(dict_data)


class LoginHandler(BaseHandler):
    def get(self):
        next_url = self.get_argument('next', '')  # 获取之前页面的路由
        self.render('login.html', next_url=next_url)

    def post(self):
        next_url = self.get_argument('next', '')  # 获取之前页面的路由

        do = self.get_argument('do', '')
        # 如果是请求授权页面
        if do == "auth":
            key = self.get_argument('key', '')
            secret = self.get_argument('secret', '')
            tapi = self.get_tapi()
            url = tapi.get_url(key, secret)
            if url is None:
                print("LoginHandler", "get", "key",key,"secret",secret)
                self.set_status(400)
                return
            self.redirect(url)
            return

        code = self.get_argument('code', '')
        tapi = self.get_tapi()
        print("LoginHandler", "post", tapi.__dict__)
        if tapi.oauth_token:
            if tapi.auth(code):
                self.set_secure_cookie('id', tapi.sid)  # 设置加密cookie
                self.redirect("/")  # 跳转到之前的路由
                return

        self.render('login.html', next_url=next_url)


# 在BuyHandler类里面添加装饰器, 装饰需要验证的请求
class IndexHandler(BaseHandler):
    # 装饰器判断有没有登录，如果没有则跳转到配置的路由下去
    @authenticated
    def get(self):
        # self.write('buy买买买！')
        self.render('index.html')

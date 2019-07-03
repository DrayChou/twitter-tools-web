# !/usr/bin/env python3
# -  *  - coding:UTF-8 -  *  -

import os
import datetime
import tornado.ioloop
import tornado.web
from tornado.options import define, options
from core.settings import load_settings
from web.handle import *


def main():
    define('port', default=8888, help='run port', type=int)

    settings = load_settings()

    tornado.web.Application(
        handlers=[
            (r'/', IndexHandler),
            (r'/login', LoginHandler),
            (r'/index', IndexHandler),
        ],
        default_handler_class=NotFindHandler,
        cookie_secret=settings.get("cookie_secret", "1q2w3e4r"),
        # 设置跳转路由，为了防止在没有登录情况下，直接输入需要登录才可见的url进行访问，做判断，如果没有登录则跳转到这个路由下
        login_url='/login',
        static_path=os.path.join(os.path.dirname(__file__), "web", "static"),
        # 想要Tornado能够正确的找到html文件，需要在 Application 中指定文件的位置
        template_path=os.path.join(
            os.path.dirname(__file__), "web", "templates"),
        # debug=True  # 调试模式，修改后自动重启服务，不需要自动重启，生产情况下切勿开启，安全性
    ).listen(options.port)

    from core.tapi import tapi_mgr
    tornado.ioloop.PeriodicCallback(tapi_mgr.heartbeat, 1000 * 6).start()
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()

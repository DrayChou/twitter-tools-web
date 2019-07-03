#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import datetime
import tornado.ioloop
import tornado.web
from web.handle import *

if __name__ == "__main__":
    tornado.web.Application(
        handlers=[
             (r"/", IndexHandler)
        ],
        default_handler_class=NotFindHandler,
        static_path=os.path.join(os.path.dirname(__file__), "web", "static")
    ).listen(8888)

    from core.task_mgr import task_mgr
    tornado.ioloop.PeriodicCallback(task_mgr.heartbeat, 1000 * 6).start()
    tornado.ioloop.IOLoop.current().start()

    
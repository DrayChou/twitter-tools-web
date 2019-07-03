# !/usr/bin/env python3
# -  *  - coding:UTF-8 -  *  - 

import os
import datetime
import tornado.ioloop
import tornado.web

class NotFindHandler(tornado.web.RequestHandler):
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

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        # self.write("Hello, world")

        template_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "template", 'index.html'
            )
        self.render(template_path)
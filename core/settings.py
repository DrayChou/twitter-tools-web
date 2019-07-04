#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import sys
import time
import yaml
import json

class Settings(object):
    def __init__(self):
        self.s_dict = {}
        self.load()
    
    def load(self):
        try:
            path = os.path.join(os.path.dirname(os.path.dirname(
                __file__)), 'settings.yml')
            print("settings", "load_settings", path)

            with open(path) as f:
                c = yaml.safe_load(f)
                print("settings", "load_settings", c)
                self.s_dict = c
                return c
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("settings", "load_settings", "Error->",
                exc_type, fname, exc_tb.tb_lineno, e)

        return

s_mgr = Settings()
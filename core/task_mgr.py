#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import json
import time, datetime

class TaskManager(object):
    def __init__(self):
        pass

    def heartbeat(self):
        print("[{}] heartbeat".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        pass


task_mgr = TaskManager()
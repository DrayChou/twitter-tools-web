import time
import os
import concurrent.futures
from twitter import TwitterError
from core.tapi import tapi_mgr, TApi


class FollowersClear(object):
    def __init__(self, api: TApi, config={}):
        self.api = api
        self.config = config
        self.log_file = "followers_clear.csv"

        # 玩家指针
        self.follower_ids_cursor = -1
        self.follower_dict = {}

        self.block_failed_ids = []
        self.unblock_failed_ids = []
        self.block_ids = []
        self.unblock_ids = []
        self.removed_ids = []

    def remove_follower(self, uid):
        is_block = None
        is_unblock = None

        try:
            # B掉
            print('blocking %d' % uid)
            self.api.CreateBlock(uid)
            self.block_ids.append(uid)
            is_block = True
        except Exception as e:
            self.block_failed_ids.append(uid)
            is_block = False

        if self.config.get("unblock", True):
            try:
                # 解除 B
                print('unblocking %d' % uid)
                self.api.DestroyBlock(uid)
                self.unblock_ids.append(uid)
                is_unblock = True
            except Exception as e:
                self.unblock_failed_ids.append(uid)
                is_unblock = False

        if is_block is True and (is_unblock is None or is_unblock is True):
            self.removed_ids.append(uid)
            return True
        return False

    def get_followers(self):
        follower_ls = []

        # 拿到自己的 followers
        print('Getting followers list')
        if self.follower_ids_cursor == 0:
            return follower_ls

        ids = []
        try:
            self.follower_ids_cursor, _, ids = self.api.GetFollowersPaged(
                cursor=self.follower_ids_cursor)
            print('get %d followers' % len(ids))
            follower_ls += ids
            time.sleep(5)
        except Exception as e:
            print("FollowersClear", "get_follers", e)
            pass

        return follower_ls

    def filter(self, ids=[]):
        no_mutual_followers = []

        # 需要清理的账号
        white_list = self.config.get("white_list", [])
        print('Getting zero or default profile image user info')
        for user_info in ids:
            try:
                need_mutu = False
                # user_info = api.GetUser(user_id=user_id)

                # 白名单
                if user_info.id in white_list or user_info.screen_name in white_list:
                    continue

                # 少于多少推的处理，处理
                if user_info.statuses_count <= self.config.get("less_statuses_count", 0):
                    need_mutu = True

                # 少于多少个关注着的处理，处理
                if user_info.followers_count <= self.config.get("less_followers_count", 0):
                    need_mutu = True

                # 默认头像的，处理
                if self.config.get("default_profile_image", True):
                    if user_info.default_profile_image == True:
                        need_mutu = True

                # 锁推&关注了我&没有被我关注
                if self.config.get("check_protected", False):
                    if user_info.protected == True:
                        if user_info.status == None:
                            need_mutu = True

                if need_mutu == False:
                    continue

                # 加到需要 B 的队列中
                print(
                    user_info.id, user_info.screen_name, user_info.name, "\t\t\t",
                    "protected:", user_info.protected,
                    "default_profile_image:", user_info.default_profile_image,
                    "statuses_count:", user_info.statuses_count,
                    "followers_count:", user_info.followers_count
                )
                no_mutual_followers.append(user_info.id)
                self.follower_dict[user_info.id] = user_info
            except TwitterError as e:
                print(e)
                break
            except Exception as e:
                print(e)

        return no_mutual_followers

    def run(self):
        # 获取玩家列表
        follower_ls = self.get_followers()
        no_mutual_followers = self.filter(follower_ls)

        for user_id in no_mutual_followers:
            self.remove_follower(user_id)
        
        self.save_log()

    def get_log_path(self):
        if self.api is None or self.api.sid is None:
            return

        base_path = os.path.join(os.path.dirname(os.path.dirname(
            __file__)), "cache", self.api.sid)
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        return os.path.join(base_path, self.log_file)

    def clear_log(self):
        log_f = self.get_log_path()
        print("FollowersClear", "clear_log", log_f)
        os.remove(log_f)

    def save_log(self):
        log_f = self.get_log_path()
        print("FollowersClear", "save_log", log_f)
        with open(log_f, 'w+') as f:
            for user_id in self.removed_ids:
                user_info = self.follower_dict.get(user_id)
                if user_info:
                    f.write("{},\"{}\",\"{}\",{},{},{},{}".format(
                        user_id, user_info.screen_name, user_info.name,
                        user_info.protected, user_info.default_profile_image,
                        user_info.statuses_count, user_info.followers_count
                    ))

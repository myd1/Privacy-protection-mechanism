#-*- coding: UTF-8 -*-
from mongoengine import *
from math import log,floor
from sklearn.cluster import KMeans
import random
import collections
import json
import re
Info = {'addr': '127.0.0.1',
        'port': 27017,
        'database': 'Sina'}

from aip import AipNlp

""" 你的 APPID AK SK """
APP_ID = '10799517'
API_KEY = 'xzMsCEd2ZkGwEEa8aiyRWGO8'
SECRET_KEY = 'QtCUG2sBHSvp4LegMO7XzsEwBOhhXGBe '
client = AipNlp(APP_ID, API_KEY, SECRET_KEY)

class Tweets(Document):
    """ 微博信息 """
    _id = StringField()  # 用户ID-微博ID
    ID = StringField()  # 用户ID
    Content = StringField()  # 微博内容
    PubTime = StringField()  # 发表时间
    Co_oridinates = StringField()  # 定位坐标
    Tools = StringField()  # 发表工具/平台
    Like = IntField()  # 点赞数
    Comment = IntField()  # 评论数
    Transfer = IntField()  # 转载数
    SimScore = 0
    meta = {'collection': 'Tweets'}

    def get_id(self):
        return self._id


class UserInfo(Document):
    """ 个人信息 """
    _id = StringField()  # 用户ID
    NickName = StringField()  # 昵称
    Gender = StringField()  # 性别
    Province = StringField()  # 所在省
    City = StringField()  # 所在城市
    Signature = StringField()  # 个性签名
    Birthday = DateTimeField()  # 生日
    Num_Tweets = IntField()  # 微博数
    Num_Follows = IntField()  # 关注数
    Num_Fans = IntField()  # 粉丝数
    Sex_Orientation = StringField()  # 性取向
    Marriage = StringField()  # 婚姻状况
    URL = StringField()  # 首页链接
    common_tools = []
    common_time = 0
    meta = {'collection': 'Information'}

    def get_id(self):
        return self._id

    '''
    昵称：如果全为数字，减分（5%）
    仅该项为减分项
    性别：已填加分（3%）
    省：已填加分（3%）
    市：已填加分（3%）
    个性签名：已填加分（5%）
    生日：已填加分（5%）
    微博数：取自然对数后/8（23%），小于20计0.
    关注数：取自然对数后/7（18%），小于20计0
    粉丝数：取自然对数后/10(34%),小于15计0.
    性取向：已填加分（3%）
    婚姻状况：已填加分（3%）
    
    满分10分，不一定为整数。
    '''
    def Get_Trust_Value(self):
        self.Trust_value=0
        if str(self.NickName).isdigit():
            self.Trust_value -= 0.5
        if self.Gender:
            self.Trust_value += 0.3
        if self.Province:
            self.Trust_value += 0.3
        if self.City:
            self.Trust_value += 0.3
        if self.Signature:
            self.Trust_value += 0.5
        if self.Birthday:
            self.Trust_value += 0.5
        if self.Num_Tweets >= 20:
            self.Trust_value += log(int(self.Num_Tweets)) / 8 * 2.3
        if self.Num_Follows >= 20:
            self.Trust_value += log(int(self.Num_Follows)) / 7 * 2.3
        if self.Num_Fans >= 20:
            self.Trust_value += log(int(self.Num_Fans)) / 10 * 2.3
        if self.Sex_Orientation:
            self.Trust_value += 0.3
        if self.Marriage:
            self.Trust_value += 0.3
        return self.Trust_value

    '''
    获取该用户的所有tweets
    '''
    def get_tweets(self):
        tweets = Tweets.objects(_id__startswith=self._id)
        return tweets

    def tweets_timer_cluster(self,tweets):
        self.tweets_timer=[]
        for tweet in tweets:
            ''''''
            timeObj = re.match('.*(\d{2,}):(\d{2,})',tweet.PubTime)
            hour = int(timeObj.group(1))
            minute = int(timeObj.group(2))
            self.tweets_timer.append([hour*60+minute,0])
        kmeans = KMeans(n_clusters=5).fit(self.tweets_timer)
        return kmeans

    def tweet_sim_cal(self,tweet,tweets):
        ''''''
        #构造随机数
        text1 = tweet.Content.encode('GBK','ignore')
        print('文本一:'+text1.decode('GBK'))
        num_of_tweets = tweets.count()
        if num_of_tweets < 5:
            cycles = num_of_tweets
        else:
            cycles = 5
        for i in range(cycles):
            ran = floor(random.random()*100) % num_of_tweets
            text2 = tweets[ran].Content.encode('GBK','ignore')
            print('文本二:'+text2.decode('GBK'))
            res = client.simnet(text1.decode('GBK'),text2.decode('GBK'))
            print(res)
            tweet.SimScore += res['score']
            print('和 "{}" 的相似度为{}'.format(text2.decode('GBK'),res['score']))
        tweet.SimScore /= cycles
        return tweet.SimScore

    def get_common_tools(self):
        '''读取常用工具'''
        self.common_tools = []
        return self.common_tools

    def is_common_tool(self,tool):
        for commontool in self.common_tools:
            if tool == commontool:
                return True
        return False

    def is_common_time(self,time):
        if time - self.common_time < 7200:
            return True
        return False

    def score_of_behave(self,tweet,tweets):
        '''计算用户微博行为得分'''
        score_b = 0
        zpz = tweet.Comment*1.5 + tweet.Transfer*2 + tweet.Like +2
        score_b += log(zpz)
        score_b*=(1-self.tweet_sim_cal(tweet,tweets))

        return score_b


class Fans(DynamicDocument):
    """粉丝信息"""
    _id = StringField()
    meta = {'collection': 'Fans'}

    def get_id(self):
        return self._id

    def get_items(self):
        """返回所有Fans的列表，第一个值是_id"""
        items = [self._id]
        for i in range(1, 200):
            try:
                items.append(self[str(i)])
            except KeyError:
                break
        return items


class Follows(DynamicDocument):
    """关注的人信息"""
    _id = StringField()
    meta = {'collection': 'Follows'}

    def get_id(self):
        return self._id

    def get_items(self):
        """返回所有Follows的列表，第一个值是_id"""
        items = [self._id]
        for i in range(1, 200):
            try:
                items.append(self[str(i)])
            except KeyError:
                break
        return items


if __name__ == '__main__':
    connect(
        Info['database'],
        host=Info['addr'],
        port=Info['port'],
    )
    Trust_value=open("trust1.tmp","w+")
    for user in UserInfo.objects[:1]:
        dump=collections.OrderedDict()
        dump["_id"]=user.get_id()
        dump["Trust_Value"]=user.Get_Trust_Value()
        json.dump(dump,Trust_value)
        Trust_value.write('\n')

        tweets = user.get_tweets()
        kmeans = user.tweets_timer_cluster(tweets)
        labels_ = kmeans.labels_.tolist()
        cluster_centers_ = kmeans.cluster_centers_.tolist()
        #print(kmeans.labels_)
        #print(kmeans.cluster_centers_)
        #print(user.tweets_timer)
        print('时间片聚类结束，开始相似度计算')
        score = user.tweet_sim_cal(tweets[1],tweets)
        print('整体相似度为'+str(score))

    Trust_value.close()
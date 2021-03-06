from pygraph.classes.digraph import digraph
from mongoengine import *
from math import log
from sklearn.cluster import KMeans
import collections
import json
import re

CLUSTER = 3
TIMELIMIT=150
Info = {'addr': '127.0.0.1',
        'port': 27017,
        'database': 'Sina'}


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
        self.Trust_value = 0
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

    def tweets_timer_cluster(self, tweets):
        self.tweets_timer = []
        for tweet in tweets:
            ''''''
            timeObj = re.match('.*?(\d{2,}):(\d{2,})', tweet.PubTime)
            hour = int(timeObj.group(1))
            minute = int(timeObj.group(2))
            self.tweets_timer.append([hour * 60 + minute, 0])

        kmeans = KMeans(n_clusters=CLUSTER).fit(self.tweets_timer)

        return kmeans




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
    meta = {'collection': 'follows3'}

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




class PRIterator:
    __doc__ = '''计算一张图中的PR值'''

    def __init__(self, dg):
        self.damping_factor = 0.85  # 阻尼系数,即α
        self.max_iterations = 100  # 最大迭代次数
        self.min_delta = 0.00001  # 确定迭代是否结束的参数,即ϵ
        self.graph = dg

    def page_rank(self):
        #  先将图中没有出链的节点改为对所有节点都有出链
        for node in self.graph.nodes():
            if len(self.graph.neighbors(node)) == 0:
                for node2 in self.graph.nodes():
                    digraph.add_edge(self.graph, (node, node2))

        nodes = self.graph.nodes()
        graph_size = len(nodes)

        if graph_size == 0:
            return {}
        page_rank = dict.fromkeys(nodes, 1.0 / graph_size)  # 给每个节点赋予初始的PR值
        damping_value = (1.0 - self.damping_factor) / graph_size  # 公式中的(1−α)/N部分

        flag = False
        for i in range(self.max_iterations):
            change = 0
            for node in nodes:
                rank = 0
                for incident_page in self.graph.incidents(node):  # 遍历所有“入射”的页面
                    rank += self.damping_factor * (page_rank[incident_page] / len(self.graph.neighbors(incident_page)))
                rank += damping_value
                change += abs(page_rank[node] - rank)  # 绝对值
                page_rank[node] = rank

            print("This is NO.%s iteration" % (i + 1))
            print(page_rank)

            if change < self.min_delta:
                flag = True
                break
        if flag:
            print("finished in %s iterations!" % node)
        else:
            print("finished out of 100 iterations!")
        return page_rank


if __name__ == '__main__':
    connect(
        Info['database'],
        host=Info['addr'],
        port=Info['port'],
    )


    dg = digraph()
    follows=[]
    for follow in Follows.objects.timeout(False):
        follows.append(follow.get_id())



    dg.add_nodes(follows)
    for follow in Follows.objects.timeout(False):

        targets=follow.get_items()
        items=list(set(targets))

        see=follow.get_id()
        for target in items:
            if target  not in follows:
                dg.add_node(target)
                follows.append(target)
            dg.add_edge((see,target))

    pr = PRIterator(dg)
    page_ranks = pr.page_rank()

    print("The final page rank is\n", page_ranks)
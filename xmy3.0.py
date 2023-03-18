import quart
import aiohttp
import json
import os
import asyncio
# from revChatGPT.V1 import AsyncChatbot        # 使用v1会被封号，改用v3
from revChatGPT.V3 import Chatbot

import threading
app = quart.Quart(__name__)
class xumingyu:
    
    def __init__(self):
        self.recent_message = {}
        self.msg_num = {}
        self.headers = {'Content-Type': 'application/json'}
        self.group_image = {
        }
        # self.chatbot = AsyncChatbot(config={
        #     "email": "yueerwen@sjtu.edu.cn",
        #     "password": "#ya.EnKWC5!T*PF"
        # })    # v1版本
        self.chatbot = Chatbot(api_key="")    # v3版本
        self.question_list = []

    async def request(self, client, url, body=None):
        response = await client.post('http://127.0.0.1:5700/' + url, json=body)
        return response

    def v3_ai(self, prompt):
        message = ""
        for data in self.chatbot.ask(prompt):
            # print(data, end="", flush=True)
            message += data
        return message

    # 该函数是revChatGPT.v1版本的，v3版本不支持异步
    async def ai(self, prompt):
        message = ""
        async for data in self.chatbot.ask(prompt):
            message = data["message"]
        return message

    # async def chat_robot(self, client, gid, uid, task_list, prompt):
    #     message = await self.ai(prompt)
    #     tmp_message = '[CQ:at,qq=' + str(uid) + message
    #     self.recent_message[str(gid)][self.msg_num[str(gid)]%5] = tmp_message
    #     self.msg_num[str(gid)] += 1
    #     task_list.append(
    #         asyncio.create_task(
    #             self.request(
    #                 client, 
    #                 "send_group_msg", 
    #                 {'group_id':str(gid), 'message':tmp_message}
    #             )
    #         )
    #     )

    async def chat_robot(self, gid, uid, prompt):
        try:
            message = self.v3_ai(prompt)        # v3版本
            # message = await self.ai(prompt)   # v1版本
            print("chatGPT: " + message)
        except Exception as e:
            message = str(e)
        if gid is not None:
            tmp_message = '[CQ:at,qq=' + str(uid) + ']' +  message
            self.recent_message[str(gid)][self.msg_num[str(gid)]%5] = tmp_message
            self.msg_num[str(gid)] += 1
            async with aiohttp.ClientSession() as client:
                print(tmp_message)
                response = await self.request(
                        client, 
                        "send_group_msg", 
                        {'group_id':str(gid), 'message':tmp_message}
                    )
                print(response)
        else:
            async with aiohttp.ClientSession() as client:
                response = await self.request(
                        client, 
                        "send_private_msg", 
                        {'user_id':str(uid), 'message':message}
                    )
                print(response)

    def between_function(self):     # 用来协调多线程和异步之间的函数
        global lock 
        lock.acquire()              # 同一时间只能有一个线程访问问题队列
        if len(self.question_list) == 0:
            lock.release()
            return
        print("question_list is " + str(self.question_list))
        dic = self.question_list[0]
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.chat_robot(dic["gid"], dic["uid"], dic["message"]))
        loop.close()
        self.question_list.pop(0)       # 发完消息才能退出问题队列
        lock.release()       

    def private_talk(self, message, uid):
        self.question_list.append({"gid":None, "uid":uid, "message":message})    #chatgpt的问题队列

    # 群消息处理
    async def main(self, message, uid, gid, name):
        myclient = aiohttp.ClientSession()
        async with myclient as client:
            task_list = []
            if message[0:21] == '[CQ:at,qq=1471805427]':     #判断是否是@自己
                # task_list.append(self.chat_robot(client, gid, uid, task_list, message[22:]))
                # t1 = threading.Thread(target=self.between_function, args=(gid, uid, message[22:]))
                # t1.start()
                self.question_list.append({"gid":gid, "uid":uid, "message":message[22:]})    #chatgpt的问题队列
            if os.path.isfile('./' + str(gid) + '_integrity.json') == False:        #初始化群成员信用值
                response = await self.request(client, "get_group_member_list?group_id="+str(gid))
                # print("response是")
                # print(response)
                # <ClientResponse(http://127.0.0.1:5700/get_group_member_list?group_id=496640666) [200 OK]>
                # <CIMultiDictProxy('Content-Type': 'application/json; charset=utf-8', 'Date': 'Thu, 02 Mar 2023 01:36:50 GMT', 'Conte
                # nt-Length': '687')>
                # print("response的类型是" + str(type(response)))
                # <class 'aiohttp.client_reqrep.ClientResponse'>
                response = await response.json()
                group = {}      
                # print("response.json()是")
                # print(response)
                # print("response.json()的类型是" + str(type(response)))
                # print("response['data']是" + str(response['data']))
                for i in response['data']:
                    group[ i['user_id'] ] = [5, 5]
                with open('./' + str(gid) + '_integrity.json', 'w') as f:
                    json.dump(group, f)
            # print(message, str(type(message)))
            # print(uid, str(type(uid)))
            # print(gid, str(type(gid)))
            if message[0:9] == '[CQ:image':         #图片格式特殊处理
                # print("图片格式")
                message = message[14:50]            #提取md5值，QQ传输图片信息格式如下，14:50即为file=后面
                #[CQ:image,file=efa0fe57110dc52f711716d9b0d50828.image
            # else: 
            #     print("不是图片格式")    

            if str(gid) not in self.recent_message:    #考虑多个群聊，最近消息要分开
                self.recent_message[str(gid)] = ['0','0','0','0','0']
                self.msg_num[str(gid)] = 0
            repeat_num = 0
            for i in self.recent_message[str(gid)]:    
                if i == message:
                    repeat_num += 1     #最近的十条消息，每有一条重复，罪加一等！
            self.recent_message[str(gid)][self.msg_num[str(gid)]%5] = message
            self.msg_num[str(gid)] += 1
            if repeat_num != 0:
                # 有复读行为，开始正义执行
                
                with open('./' + str(gid) + '_integrity.json', 'r') as f:
                    integrity = json.load(f)
                cur_integrity = integrity[str(uid)][0]
                cur_integrity -= repeat_num
                if cur_integrity <= 0:     #开始惩罚
                    tmp_message = name + '(' + str(uid) + ')' + '的信用值已降至零，正義执行！'
                    self.recent_message[str(gid)][self.msg_num[str(gid)]%5] = tmp_message
                    self.msg_num[str(gid)] += 1
                    task_list.append(
                        asyncio.create_task(
                            self.request(
                                client, 
                                "send_group_msg", 
                                {'group_id':str(gid), 'message':tmp_message}
                            )
                        )
                    )
                    task_list.append(
                        asyncio.create_task(
                            self.request(
                                client, 
                                "set_group_ban", 
                                {'group_id':str(gid), 'user_id':str(uid), 'duration':600}
                            )
                        )
                    )   # duartion = 86400, 禁言一天
                    task_list.append(
                        asyncio.create_task(
                            self.request(
                                client, 
                                "set_group_card", 
                                {'group_id':str(gid), 'user_id':str(uid), 'card':(name + '（忏悔中）')}
                            )
                        )
                    )   # 修改群名片
                    if os.path.isfile(self.group_image[str(uid)]):
                        #设置为群头像
                        print("设置为群头像")
                        task_list.append(
                            asyncio.create_task(
                                self.request(
                                    client, 
                                    "set_group_portrait", 
                                    {'group_id':str(gid), 'file':'file://' + self.group_image[str(uid)]}
                                )
                            )
                        )
                    if integrity[str(uid)][1] != 1:
                        integrity[str(uid)][1] -= 1
                        integrity[str(uid)][0] = integrity[str(uid)][1]     #信用值重置
                    else:
                        integrity[str(uid)][0] = 1
                    tmp_message = name + '(' + str(uid) + ')' + '当前的信用值上限为' + str(integrity[str(uid)][1]) + '，希望你好自为之！'
                    self.recent_message[str(gid)][self.msg_num[str(gid)]%5] = tmp_message
                    self.msg_num[str(gid)] += 1
                    task_list.append(
                        asyncio.create_task(
                            self.request(
                                client, 
                                "send_group_msg", 
                                {'group_id':str(gid), 'message':tmp_message}
                            )
                        )
                    )
                    with open('./' + str(gid) + '_integrity.json', 'w') as f:
                        json.dump(integrity, f)
                else:
                    tmp_message = '检测到' + name + '(' + str(uid) + ')' + '的复读行为，信用值降低为' + str(cur_integrity)
                    self.recent_message[str(gid)][self.msg_num[str(gid)]%5] = tmp_message
                    self.msg_num[str(gid)] += 1
                    task_list.append(
                        asyncio.create_task(
                            self.request(
                                client, 
                                "send_group_msg", 
                                {'group_id':str(gid), 'message':tmp_message}
                            )
                        )
                    )                    
                    integrity[str(uid)][0] = cur_integrity     #修改信用值
                    with open('./' + str(gid) + '_integrity.json', 'w') as f:
                        json.dump(integrity, f)
            if message[0:21] == '[CQ:at,qq=1471805427]':     #判断是否是@自己
                # print(message[22:])
                if message[22:] == '查询我的信用值':        
                    with open('./' + str(gid) + '_integrity.json', 'r') as f:
                        integrity = json.load(f)
                    cur_integrity = integrity[str(uid)][0]
                    tmp_message = name + '(' + str(uid) + ')' + '当前信用值为' + str(integrity[str(uid)][0]) +'，当前信用值上限为' + str(integrity[str(uid)][1])
                    self.recent_message[str(gid)][self.msg_num[str(gid)]%5] = tmp_message
                    self.msg_num[str(gid)] += 1
                    task_list.append(
                        asyncio.create_task(
                            self.request(
                                client, 
                                "send_group_msg", 
                                {'group_id':str(gid), 'message':tmp_message}
                            )
                        )
                    )
                elif message[22:] == '查询米娜桑的信用值':
                    with open('./' + str(gid) + '_integrity.json', 'r') as f:
                        integrity = json.load(f)
                    response = await self.request(client, "get_group_member_list?group_id="+str(gid)).json()
                    tmp_message = ''
                    for i in response['data']:
                        name = i['card'] if i['card'] != '' else i['nickname']
                        cur_message = str(name) + '(' + str(i['user_id']) + ')' + '当前信用值为' + str(integrity[str(i['user_id'])][0]) +'，当前信用值上限为' + str(integrity[str(i['user_id'])][1])
                        tmp_message = tmp_message + cur_message + '\n'
                    self.recent_message[str(gid)][self.msg_num[str(gid)]%5] = tmp_message
                    self.msg_num[str(gid)] += 1
                    task_list.append(
                        asyncio.create_task(
                            self.request(
                                client, 
                                "send_group_msg", 
                                {'group_id':str(gid), 'message':tmp_message}
                            )
                        )
                    )
                # else:
                #     tmp_message = '[CQ:at,qq=' + str(uid) + '] 你在狗叫什么？'
                #     self.recent_message[str(gid)][self.msg_num[str(gid)]%5] = tmp_message
                #     self.msg_num[str(gid)] += 1
                #     task_list.append(
                #         asyncio.create_task(
                #             self.request(
                #                 client, 
                #                 "send_group_msg", 
                #                 {'group_id':str(gid), 'message':tmp_message}
                #             )
                #         )
                #     )

            await asyncio.gather(*task_list)

xmy = xumingyu()
lock = threading.Lock()
@app.route('/', methods=["POST"])
async def post_data():
    # if flask.request.get_json().get('message_type') == 'private':  # 私聊信息
    #     uid = flask.request.get_json().get('sender').get('user_id')  # 获取信息发送者的 QQ号码
    #     message = flask.request.get_json().get('raw_message')  # 获取原始信息
    #     keyword(message, uid)  # 将 Q号和原始信息传到我们的后台
    data = await quart.request.get_json()
    # print(data)
    if data.get('message_type') == 'group':  # 如果是群聊信息
        gid = data.get('group_id')  # 获取群号
        uid = data.get('sender').get('user_id')  # 获取信息发送者的 QQ号码
        #print(type(uid))   # str
        #获取发送者的昵称或群名片
        if data.get('sender').get('card') != '':
            name = data.get('sender').get('card')
        else:
            name = data.get('sender').get('nickname')
        message = data.get('raw_message')  # 获取原始信息
        print("*" * 10 + "收到群聊消息" + "*" * 10)
        await xmy.main(message, uid, gid, name)  # 将 Q号和原始信息传到我们的后台
        t1 = threading.Thread(target=xmy.between_function, args=()) # chatgpt回复较慢，新开一个线程用于chatgpt对话
        t1.start()
    elif data.get('message_type') == 'private':
        uid = data.get('sender').get('user_id')  # 获取信息发送者的 QQ号码
        # name = data.get('sender').get('nickname')
        message = data.get('raw_message')  # 获取原始信息
        print("*" * 10 + "收到私聊消息" + "*" * 10)
        xmy.private_talk(message, uid)
        t1 = threading.Thread(target=xmy.between_function, args=()) # chatgpt回复较慢，新开一个线程用于chatgpt对话
        t1.start()
        
    return "None"

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5701)
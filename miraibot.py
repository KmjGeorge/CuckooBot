import json
import http.client
import os.path
import re
import requests
import asyncio
import threading
import socket
from llm_server import LLMServer
from mirai.tts_server import TTSServer

LLM_HOST = "localhost"  # The server's hostname or IP address
LLM_PORT = 11434  # The port used by the server
# 信任qq好友
whitelist = [804235820]
audiocache_path = 'F:/Project/mirai/audiocache/'


class bot:
    def __init__(self, host="localhost", port=8080, verifyKey="114514"):
        """
        :param host: 监听地址
        :param port: 监听端口
        :param verifyKey: key
        """
        self.VisitHttpPath = http.client.HTTPConnection(host, port)
        self.verifyKey = verifyKey
        self.qq = 2306922282
        self.header = {"Content-Type": "application/json"}
        self.sessionKey = self.bind()
        print('$$$$$$$$$$$$$$  miraibot初始化完成 $$$$$$$$$$$$')
        self.llmserver = LLMServer("localhost", "11434")
        print('$$$$$$$$$$$$$$  LLM初始化完成 $$$$$$$$$$$$')
        self.ttsserver = TTSServer("localhost", "9880")
        self.enable_tts = False
        self.ready_to_send = True

    def bind(self):
        auto = json.dumps({"verifyKey": self.verifyKey})
        VisitHttpPath = self.VisitHttpPath

        VisitHttpPath.request("POST", "/verify", body=auto, headers=self.header)
        response = VisitHttpPath.getresponse()
        session = response.read().decode("utf-8")
        print("认证成功:", str(session))
        sessionKey = json.loads(session)['session']
        bind = json.dumps({"sessionKey": sessionKey, "qq": self.qq})
        VisitHttpPath.request("POST", '/bind', bind, headers=self.header)
        response = VisitHttpPath.getresponse().read().decode("utf-8")
        print("绑定成功:", str(response))

        return sessionKey

    def set_tts(self, status: bool):
        self.enable_tts = status
        print('TTS enabled:', status)

    def sendFriendMessage(self, target, messageChain):
        if self.ready_to_send:
            params = json.dumps({
                "sessionKey": self.sessionKey,
                "target": target,
                "messageChain": messageChain
            })
            VisitHttpPath = self.VisitHttpPath
            VisitHttpPath.request("POST", "/sendFriendMessage", params, self.header)
            response = VisitHttpPath.getresponse().read().decode('utf-8')
            print('消息发送', messageChain)

    def getSessionInfo(self):
        VisitHttpPath = self.VisitHttpPath
        VisitHttpPath.request("GET", '/sessionInfo')
        response = VisitHttpPath.getresponse()
        print(response.read().decode('utf-8'))

    def getBotList(self):
        VisitHttpPath = self.VisitHttpPath
        VisitHttpPath.request("GET", '/botList')
        response = VisitHttpPath.getresponse()
        print(response.read().decode('utf-8'))

    def release(self):
        params = json.dumps({
            "sessionKey": self.sessionKey,
            "qq": self.qq
        })
        VisitHttpPath = self.VisitHttpPath
        VisitHttpPath.request("POST", '/release', params, self.header)
        response = VisitHttpPath.getresponse()
        print('session已释放', response.read().decode('utf-8'))

    async def run(self):
        method = [asyncio.create_task(self.messageEvent())]
        await asyncio.gather(*method)

    async def messageEvent(self):
        VisitHttpPath = self.VisitHttpPath
        count = 10
        while True:
            VisitHttpPath.request('GET',
                                  '/fetchLatestMessage?sessionKey={}&count={}'.format(self.sessionKey, count))
            response = VisitHttpPath.getresponse().read().decode('utf-8')
            data = json.loads(response)
            if data['data']:
                # threading.Thread(target=self.dispose, args=(data,)).start()
                try:
                    text, id, nickname, remark = self.dispose(data)
                    print('消息接收', text, '(from: {})'.format(id))
                    if text and (id in whitelist):
                        # 指令
                        if text == '.clear':
                            self.llmserver.clear()
                            messageChain_text = [
                                {'type': 'Plain', 'text': 'History Cleared!'}
                            ]
                            self.sendFriendMessage(target=id, messageChain=messageChain_text)
                        elif text == '.tts off':
                            self.set_tts(False)
                            messageChain_text = [
                                {'type': 'Plain', 'text': 'TTS Disabled!'}
                            ]
                            self.sendFriendMessage(target=id, messageChain=messageChain_text)
                        elif text == '.tts on':
                            self.set_tts(True)
                            messageChain_text = [
                                {'type': 'Plain', 'text': 'TTS Enabled!'}
                            ]
                            self.sendFriendMessage(target=id, messageChain=messageChain_text)
                        elif text == '.relaunch tts':
                            self.ttsserver.relaunch()
                            messageChain_text = [
                                {'type': 'Plain', 'text': 'TTS Relaunched!'}
                            ]
                            self.sendFriendMessage(target=id, messageChain=messageChain_text)
                        elif text == '.reply on':
                            self.ready_to_send = True
                            messageChain_text = [
                                {'type': 'Plain', 'text': 'Reply on!'}
                            ]
                            self.sendFriendMessage(target=id, messageChain=messageChain_text)
                        elif text == '.reply off':
                            messageChain_text = [
                                {'type': 'Plain', 'text': 'Reply off!'}
                            ]
                            self.sendFriendMessage(target=id, messageChain=messageChain_text)
                            self.ready_to_send = False
                        elif text == '.status':
                            messageChain = [{'type': 'Plain',
                                             'text': 'verifyKey: {}'.format(
                                                 self.verifyKey) + '\n' + 'ready_to_send : {}'.format(
                                                 self.ready_to_send) + '\n' + 'tts : {}'.format(self.enable_tts)}
                                            ]
                            self.sendFriendMessage(id, messageChain)
                        elif text == '.list':
                            model_list = self.llmserver.get_model_list()
                            response_text = ''
                            for info in model_list:
                                for k, v in info.items():
                                    response_text += str(k)
                                    response_text += ': '
                                    response_text += str(v)
                                    response_text += '\n'
                                response_text += '\n'
                            messageChain = [{'type': 'Plain',
                                             'text': response_text}
                                            ]
                            self.sendFriendMessage(id, messageChain)
                        elif text == '.history':
                            history = self.llmserver.history
                            response_history = ''
                            for idx, item in enumerate(history):
                                response_history += str(item)
                                response_history += '\n'
                                if (idx + 1) % 2 == 0:
                                    response_history += '\n'
                            response_history = response_history[:-1]
                            messageChain = [{'type': 'Plain',
                                             'text': response_history}
                                            ]
                            self.sendFriendMessage(id, messageChain)
                        elif re.match(re.compile(r'\.switch (.*)'), text):
                            model_name = re.match(re.compile(r'\.switch (.*)'), text).group(1)
                            print(model_name)
                            if self.llmserver.switch(model_name):
                                messageChain = [{'type': 'Plain',
                                                 'text': 'Switch model to {}'.format(model_name)}
                                                ]
                            else:
                                messageChain = [{'type': 'Plain',
                                                 'text': 'Switch Failed'}
                                                ]
                            self.sendFriendMessage(id, messageChain)
                        # 正常回复
                        else:
                            llmres = self.llmserver.chat(text)  # 获取LLM输出
                            llm_text = llmres.message['content']
                            # print('Bot:', llm_text)
                            messageChain_text = [
                                {'type': 'Plain', 'text': llm_text}
                            ]
                            self.sendFriendMessage(target=id, messageChain=messageChain_text)
                            if llm_text != 'Filtered.':
                                # 发送语音到目标
                                if self.enable_tts:
                                    self.ttsserver.inference(llm_text)  # 获取TTS输出
                                    if os.path.exists(os.path.join(audiocache_path, "audio.wav")):
                                        # 发送
                                        messageChain_voice = [
                                            {"type": "Voice", "path": os.path.join(audiocache_path, 'audio.wav')}]
                                        self.sendFriendMessage(target=id, messageChain=messageChain_voice)
                            else:
                                if self.enable_tts:
                                    messageChain_voice = [
                                        {"type": "Voice", "path": os.path.join(audiocache_path, 'filtered.wav')}]
                                    self.sendFriendMessage(target=id, messageChain=messageChain_voice)


                except Exception as e:
                    print(e)

    def dispose(self, data):
        try:
            data = data['data']
            type = data[0]['type']
            if type == 'FriendMessage':  # 不处理群聊
                messages, sender = data[0]['messageChain'], data[0]['sender']
                # 各种信息
                text = messages[1]['text']
                id = sender['id']
                nickname = sender['nickname']
                remark = sender['remark']
                return text, id, nickname, remark
            return None
        except Exception as e:
            return None


if __name__ == '__main__':
    b = bot()
    asyncio.run(b.run())

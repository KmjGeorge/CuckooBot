import json
import http.client
import os.path

import requests

def get_lang(word):
    for char in word:
        if not ('a' <= char <= 'z' or 'A' <= char <= 'Z' or '0' <= char <= '9' or char in
                ['(', ')', ',', '.', '，', '。', '!', '！', '~', '?', '？', '/', ' ', '[', ']', '\'', '\"', '-', '=', '’',
                 '~', ':']):
            return 'en'
    return 'zh'


class TTSServer:
    def __init__(self, host="localhost", port="9880"):
        self.address = http.client.HTTPConnection(host, port)

    def inference(self, text):
        params = json.dumps({
            "text": text,
            "text_language": get_lang(text)
        })
        self.address.request("POST", "/", params)
        response = self.address.getresponse().read()
        with open('../audiocache/audio.wav', 'wb') as f:
            f.write(response)
        return response


if __name__ == '__main__':
    ttsserver = TTSServer()
    # res = ttsserver.inference("There is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long textThere is a long text")
    # print(res)
    ttsserver.relaunch()

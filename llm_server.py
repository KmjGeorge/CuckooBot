import json
import http.client
import requests

'''
Ollama Parameters
    model: (required) the model name
    prompt: the prompt to generate a response for
    images: (optional) a list of base64-encoded images (for multimodal models such as llava)
Advanced parameters (optional):
    format: the format to return a response in. Currently the only accepted value is json
    options: additional model parameters listed in the documentation for the Modelfile such as temperature
    system: system message to (overrides what is defined in the Modelfile)
    template: the prompt template to use (overrides what is defined in the Modelfile)
    context: the context parameter returned from a previous request to /generate, this can be used to keep a short conversational memory
    stream: if false the response will be returned as a single response object, rather than a stream of objects
    raw: if true no formatting will be applied to the prompt. You may choose to use the raw parameter if you are specifying a full templated prompt in your request to the API
    keep_alive: controls how long the model will stay loaded into memory following the request (default: 5m)
'''


class LLMResponse_G:
    def __init__(self, response):
        self.model = response['model']
        self.created_at = response['created_at']
        self.response = response['response']
        self.done = response['done']
        self.context = response['context']
        self.total_duration = response['total_duration'] / 1e9
        self.load_duration = response['load_duration'] / 1e9
        self.prompt_eval_count = response['prompt_eval_count']
        self.prompt_eval_duration = response['prompt_eval_duration']
        self.eval_count = response['eval_count']
        self.eval_duration = response['eval_duration'] / 1e9


class LLMResponse_C:
    def __init__(self, response):
        self.model = response['model']
        self.created_at = response['created_at']
        self.done = response['done']
        self.message = response['message']
        self.total_duration = response['total_duration'] / 1e9
        self.load_duration = response['load_duration'] / 1e9
        self.prompt_eval_count = response['prompt_eval_count']
        self.prompt_eval_duration = response['prompt_eval_duration']
        self.eval_count = response['eval_count']
        self.eval_duration = response['eval_duration'] / 1e9

class LLMServer:
    def __init__(self, host, port):
        self.address = http.client.HTTPConnection(host, port)
        self.history = []
        self.model = 'llama3:8b-instruct-fp16'

    def generate(self, prompt):
        params = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": '30m'
        })
        self.address.request("POST", "/api/generate", params)
        response_raw = self.address.getresponse()
        res = LLMResponse_G(json.loads(response_raw.read().decode('utf-8')))
        print('回复: ', res.response)
        print('速度：', res.eval_count / res.eval_duration, 'token/s')

    def chat(self, message):
        query = {"role": "user",
                 "content": message}
        self.history.append(query)
        params = json.dumps({
            "model": self.model,
            "messages": self.history,
            "stream": False,
            "keep_alive": '30m'
        })
        self.address.request("POST", "/api/chat", params)
        response_raw = self.address.getresponse()
        res = LLMResponse_C(json.loads(response_raw.read().decode('utf-8')))
        self.history.append(res.message)
        # print('回复: ', res.message['content'])
        # history.append(res.message['content'])
        # print('速度：', res.eval_count / res.eval_duration, 'token/s')
        return res

    def clear(self):
        self.history = []
        print('LLM History Cleared !')
    def switch(self, model):
        if model in str(self.get_model_list()):
            self.model = model
            print('LLM Switched to {}'.format(model))
            return True
        else:
            return False
    def get_model_list(self):
        self.address.request("GET", "/api/tags")
        response_raw = self.address.getresponse()
        model_info = json.loads(response_raw.read().decode('utf-8'))['models']
        return model_info

if __name__ == '__main__':
    host = '127.0.0.1'
    port = '11434'
    server = LLMServer(host, port)

    '''
    while True:
        prompt = input('You: ')
        if prompt == 'Exit':
            break
        server.chat(prompt)
    '''

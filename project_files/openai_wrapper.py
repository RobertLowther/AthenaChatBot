import os
import re
import openai
import numpy as np
from numpy.linalg import norm
from time import time, sleep
from uuid import uuid4
from util import *


class OpenAiWrapper():
    on_response = None

    def __init__(self, apiKey, user = 'USER', athena = 'ATHENA', projDir = os.getcwd() + '\\project_files\\'):
        openai.api_key = apiKey
        self.user = user
        self.athena = athena
        self.projectDir = projDir
        self.model = 'text-davinci-003'
        self.temp = .5
        self.maxLength = 400
        self.topP = 1
        self.freqPen = 0
        self.presPen = 0

    def SetTemp(self, val):
        self.temp = val

    def SetMaxLength(self, val):
        self.maxLength = val

    def SetTopP(self, val):
        self.topP = val

    def SetFreqPen(self, val):
        self.freqPen = val

    def SetPresPen(self, val):
        self.presPen = val

    def Gpt3Embedding(self, content, engine='text-embedding-ada-002'):
        content = content.encode(encoding='ASCII', errors='ignore').decode()
        response = openai.Embedding.create(input=content, engine=engine)
        vector = response['data'][0]['embedding']
        return vector

    def Similarity(self, v1, v2):
        # based upon https://stackoverflow.com/questions/18424228/cosine-similarity-between-2-number-lists
        return np.dot(v1, v2) / (norm(v1) * norm(v2))

    def FetchMemories(self, vector, logs, count):
        scores = list()

        for i in logs:
            if vector == i['vector']:
                continue

            score = self.Similarity(i['vector'], vector)
            i['score'] = score
            scores.append(i)

        ordered = sorted(scores, key=lambda d: d['score'], reverse=True)
        #TODO - pick more memories temporally nearby the top most relevant memories

        try:
            ordered = ordered[:count]
            return ordered
        except:
            return ordered

    def LoadConvo(self):
        files = os.listdir(self.projectDir + '/chat_logs')
        files = [i for i in files if '.json' in i]

        result = list()

        for file in files:
            data = LoadJson(f'{self.projectDir}chat_logs/{file}')
            result.append(data)

        ordered = sorted(result, key=lambda d: d['time'], reverse=False)
        return result

    def SummarizeMemories(self, memories):
        memories = sorted(memories, key=lambda d: d['time'], reverse=False)
        block = ''
        for mem in memories:
            block += f'%s: %s\n\n' % (mem['speaker'], mem['message'])
        block = block.strip()
        prompt = OpenFile(f'{self.projectDir}prompt_notes.txt').replace('<<INPUT>>', block)
        #TODO - do this in the background over time to handle huge amounts of memories
        notes = self.Gpt3Completion(prompt, self.model)
        return notes

    def GetLastMessage(self, conversation, limit):
        try:
            short = conversation[-limit:]
        except:
            short = conversation
        output = ''
        for i in short:
            output += '%s: %s\n\n' % (i['speaker'], i['message'])
        output = output.strip()
        return output

    def Gpt3Completion(self, prompt, model, temp=0.0, top_p=1.0, tokens=400, freq_pen=0.0, pres_pen=0.0, stop=[f'{"USER"}:', f'{"ATHENA"}:']):
        maxRetry = 5
        retry = 0
        prompt = prompt.encode(encoding='ASCII', errors='ignore').decode()
        while True:
            try:
                response = openai.Completion.create(
                    engine=model,
                    prompt=prompt,
                    temperature=temp,
                    max_tokens=tokens,
                    top_p=top_p,
                    frequency_penalty=freq_pen,
                    presence_penalty=pres_pen,
                    stop=stop
                )
                text = response['choices'][0]['text'].strip()
                text = re.sub('[\r\n]+', '\n', text)
                text = re.sub('[\t ]+', ' ', text)
                filename = f'{time()}_gpt3.txt'
                if not os.path.exists(self.projectDir + 'gpt3_logs'):
                    os.makedirs(self.projectDir + 'gpt3_logs')
                SaveFile(f'{self.projectDir}gpt3_logs/{filename}', prompt + '\n\n==========\n\n' + text)
                return text
            except Exception as oops:
                retry += 1
                if retry > maxRetry:
                    return f"GPT3 error: {oops}"
                print('Error communicating with OpenAI:', oops)
                sleep(1)

    def CreateChatLog(self, speaker, content, vector):
        info = {'speaker': speaker, 'time': time(), 'vector': vector, 'message': content, 'uuid': str(uuid4())}
        filename = f'log_{time()}_{speaker}.json'
        SaveJson(f'{self.projectDir}chat_logs/{filename}', info)

    def Prompt(self, prompt):
        print("called")
        #### get user input, vectorize it, package it with relevent data, and save it
        userInput = prompt
        vector = self.Gpt3Embedding(userInput)
        self.CreateChatLog(self.user, userInput, vector)
        # TODO - add memory chunking for efficiency
        
        #### Compose Corpus
        conversation = self.LoadConvo()
        memories = self.FetchMemories(vector, conversation, 10)
        # TODO - fetch declarative memories (facts, wikis, KB, company data, internet, etc)
        notes = self.SummarizeMemories(memories)
        recent = self.GetLastMessage(conversation, 4)
        prompt = OpenFile(f'{self.projectDir}prompt_response.txt').replace('<<NOTES>>', notes).replace('<<CONVERSATION>>', recent).replace('<<USER>>', self.user)

        #### generate response
        output = self.Gpt3Completion(prompt, self.model, temp=self.temp, top_p=self.topP, tokens=self.maxLength, freq_pen=self.freqPen, pres_pen=self.presPen)
        vector = self.Gpt3Embedding(output)
        self.CreateChatLog(self.athena, output, vector)

        print(f'\n\n{self.athena}: {output}')

        if self.on_response != None:
            self.on_response(output, self.athena)
        print("done")
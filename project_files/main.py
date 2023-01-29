from kivy.app import App, Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from openai_wrapper import OpenAiWrapper
from functools import partial
from kivy.clock import Clock
import threading
from util import *
import os

projectDir = os.getcwd() + '\\project_files\\'
apiKey = OpenFile(f"{projectDir}openaiapikey.txt")
openAI = OpenAiWrapper(OpenFile(projectDir + 'openaiapikey.txt'), projDir=projectDir)
models = ['ada', 'ada-code-search-code', 'ada-code-search-text', 'ada-search-document', 'ada-search-query', 'ada-similarity', 'ada:2020-05-03', 'audio-transcribe-001', 'babbage', 'babbage-code-search-code', 'babbage-code-search-text', 'babbage-search-document', 'babbage-search-query', 'babbage-similarity', 'babbage:2020-05-03', 'code-cushman-001', 'code-davinci-002', 'code-davinci-edit-001', 'code-search-ada-code-001', 'code-search-ada-text-001', 'code-search-babbage-code-001', 'code-search-babbage-text-001', 'curie', 'curie-instruct-beta', 'curie-search-document', 'curie-search-query', 'curie-similarity', 'curie:2020-05-03', 'cushman:2020-05-03', 'davinci', 'davinci-if:3.0.0', 'davinci-instruct-beta', 'davinci-instruct-beta:2.0.0', 'davinci-search-document', 'davinci-search-query', 'davinci-similarity', 'davinci:2020-05-03', 'if-curie-v2', 'if-davinci-v2', 'if-davinci:3.0.0', 'text-ada-001', 'text-ada:001', 'text-babbage-001', 'text-babbage:001', 'text-curie-001', 'text-curie:001', 'text-davinci-001', 'text-davinci-002', 'text-davinci-003', 'text-davinci-edit-001', 'text-davinci-insert-001', 'text-davinci-insert-002', 'text-davinci:001', 'text-embedding-ada-002', 'text-search-ada-doc-001', 'text-search-ada-query-001', 'text-search-babbage-doc-001', 'text-search-babbage-query-001', 'text-search-curie-doc-001', 'text-search-curie-query-001', 'text-search-davinci-doc-001', 'text-search-davinci-query-001', 'text-similarity-ada-001', 'text-similarity-babbage-001', 'text-similarity-curie-001', 'text-similarity-davinci-001']
kv = Builder.load_file(projectDir + "athena.kv")

class Main(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.base = BaseLayout()

    def build(self):
        return self.base


class BaseLayout(BoxLayout):
    pass


class MenuBox(BoxLayout):

    def UpdatePropertyLabel(self, textInput:TextInput, slider:Slider, isInt=False):
        try:
            val = float(textInput.text)
        except:
            textInput.background_color = (1, .2, .2, 1)
            return

        textInput.background_color = (1, 1, 1, 1)

        if isInt:
            val = int(val)
            textInput.text = str(val)

        if val == int(slider.value):
            return

        if val > slider.max or val < slider.min:
            val = clamp(val, slider.min, slider.max)

        slider.value = val
    
    def UpdateOpenAIValue(self, property, value, textInput:TextInput, isInt=False):
        match property:
            case "model":
                openAI.model = value
            case "temp":
                openAI.temp = value
            case "maxLen":
                openAI.maxLength = value
            case "topP":
                openAI.topP = value
            case "freqPen":
                openAI.freqPen = value
            case "presPen":
                openAI.freqPen = value

        try:
            if value == float(textInput.text):
                return
        except:
            return

        if isInt:
            textInput.text = f"{int(value)}"
        else:
            textInput.text = f"{value:.2f}"

class MessageBox(BoxLayout):
    
    def SetHeight(self, instance, value):
        self.height = value

class ChatBox(BoxLayout):
    m_padding = 5
    request_task = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        openAI.on_response = self.ScheduleMessage


    def SubmitQuery(self, instance, text):
        instance.focused = True
        if self.request_task != None:
            isAlive = self.request_task.is_alive()
        if text == '' or (self.request_task != None and self.request_task.is_alive()):
            return

        self.AddMessage(text, True)
        self.request_task = threading.Thread(target=openAI.Prompt, args=[text])
        self.request_task.start()
        instance.text = ""
        
    def ScheduleMessage(self, text, isUser, *largs):
        Clock.schedule_once(partial(self.AddMessage, text, isUser), -1)

    def AddMessage(self, text, isUser, *largs):
        chatRegion = self.ids.ChatRegion
        msgBox = MessageBox()
        padLabel = Label(size_hint=(.4, 0))
        if isUser == True:
            chatLabel=UserLabel(text=text)
        else:
            chatLabel=BotLabel(text=text)

        if (isUser == True):
            msgBox.add_widget(padLabel)
            msgBox.add_widget(chatLabel)
        else:
            msgBox.add_widget(chatLabel)
            msgBox.add_widget(padLabel)
        
        chatRegion.add_widget(msgBox)
        # self.ids.ChatScroll.scroll_to(msgBox)
        self.ids.ChatScroll.scroll_y = 0


class UserLabel(Label):
    pass


class BotLabel(Label):
    pass


class ModelDropdown(DropDown):
    pass


if __name__ == '__main__':
    Main().run()
    
    # openAI = OpenAiWrapper(OpenFile(projectDir + 'openaiapikey.txt'), projDir=projectDir)
    
    # while True:
    #     openAI.Prompt(input(f'\n\n{openAI.user}: '))

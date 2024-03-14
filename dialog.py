from openai import OpenAI
import sys
import os
import time
import random
import json
import langchain
import pyttsx3
from pathlib import Path
from openai import OpenAI
client = OpenAI()

"""
This will run the dialogue system for a bartending game where characters are having conversations
At the bar, the mechanism will be calls to open AIAPI in the following format:

import os
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)


async def main() -> None:
    chat_completion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say this is a test",
            }
        ],
        model="gpt-3.5-turbo",
    )


asyncio.run(main())

from pathlib import Path
from openai import OpenAI
client = OpenAI()

speech_file_path = Path(__file__).parent / "speech.mp3"
response = client.audio.speech.create(
  model="tts-1",
  voice="alloy",
  input="Today is a wonderful day to build something people love!"
)

response.stream_to_file(speech_file_path)


This will run similar to a turn based game, where each character says one thing each round
And the order is randomized each round with something like a initiative roll
The characters will be given a context of three parts. One is global context of the things going out in the world outside the bar.
The next is personal context, which is the things that they believe, and the various groups that they are aligned or unaligned with
And the third will be a local context, given recent happenings in the room that they are currently in (a bar)
To do this, I will use langchain and make calls to open AI For the prototype with the idea of moving to local open source models in production.
"""
OpenAI.api_key = os.environ.get("OPENAI_API_KEY")

def get_initiative():
    return random.randint(1, 20)


class NPC:
    def __init__(self, name, model, api_key):
        self.name = name
        self.model = model
        self.api_key = api_key
        self.disposition = {}
        self.background = ""
        self.messages = []
        self.client = OpenAI()
        self.voice = 'alloy'

    def speak(self, message):
        speech_file_path = Path(__file__).parent / f"{self.name}.mp3"
        response = client.audio.speech.create(
            model="tts-1",
            voice=self.voice,
            input=message
        )
        response.stream_to_file(speech_file_path)
        os.system(f"mpg123 {speech_file_path}")
    def add_message(self, message):
        self.messages.append(message)

    def get_messages(self):
        return self.messages

    def clear_messages(self):
        self.messages = []

    def disposition(self):
        return self.disposition

    def set_disposition(self, topic, value):
        # check if json na in format {"String": float range (-1 to 1)} and add to disposition dict
        if type(value) == float and value >= -1 and value <= 1:
            self.disposition[topic] = value
            return True
        else:
            return False

    def get_disposition(self, topic):
        if topic not in self.disposition:
            return 0
        else:
            return self.disposition[topic]

    def get_model(self):
        return self.model

    def get_name(self):
        return self.name

    def get_response(self, messages):
        chat_completion = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
        )
        return chat_completion

    def get_message(self, messages):
        response = self.get_response(messages)
        message = response.choices[0].message.content
        messages.append(message)
        return message

    def build_context(self, global_context, personal_context, local_context, instructions, messages):
        context = [
            {
                "role": "system",
                "content": f"Instructions: {instructions}",
                "role": "user",
                "content": f"Global Context: {global_context} \n\nPersonal Context: {personal_context} \n\nLocal Context: {local_context} \n\n"
                           f"A number of people are having a conversation at a bar.\n\n"
                           f"Here is the context for the conversation: {messages}"
                           f"based on this global context, and the character {self.name} and their personal context, {self.name} would respond with the following (remember to only respond with output that will be spoken in the character's voice):\n\n"
            }
        ]
        return context
    def get_message(self, context):
        response = self.get_response(context)
        return response.choices[0].message.content

def main():
    voicelist = ['nova', 'shimmer', 'echo', 'onyx', 'fable', 'alloy']
    # create the npcs
    npc1 = NPC("Bob", "gpt-4", os.environ.get("OPENAI_API_KEY"))
    npc2 = NPC("Alice", "gpt-4", os.environ.get("OPENAI_API_KEY"))
    npc3 = NPC("Charlie", "gpt-4", os.environ.get("OPENAI_API_KEY"))
    npcs = [npc1, npc2, npc3]
    # set npc voices
    for npc in npcs:
        npc.voice = voicelist.pop(random.randint(0, len(voicelist) - 1))
    # create the contexts
    global_context = "There is a festival celebrating the anniversary of the lasting peace from 100 years ago"
    npc1.background = "Bob was a soldier in the war, and he is now a member of the community garden club he believes that the flowers are the most important part of the festival and that the peace is a fragile thing that needs to be protected at all costs."
    npc2.background = "Alice is a merchant who sells flowers and other goods at the market, she believes that flowers are a profit center and that the peace is a good thing but not as important as the flowers"
    npc3.background = "Charlie is a spy who is working for the enemy, he needs information about a secret flower that can end the world but doesn't want to let on what he's looking for"
    local_context = "The bar is a popular hangout for peaceful neighbors"
    # create the instructions
    instructions = ("The characters are having a conversation at the bar. Respond only with the words that that character would say, without any context or commentary."
                    "You never have to say the name of the character or anything the only thing you need as your response is the words that the character would say no labels no stage directions"
                    "The output here is being fed directly to a text to speech engine, and therefore any commentary will be distracting to the end user")
    # create the messages
    messages = []
    # create the conversation
    for i in range(10):
        for npc in npcs:
            # todo: fix this so that they see each other's messages before they respond
            context = npc.build_context(global_context, npc.background, local_context, instructions, messages)
            message = npc.get_message(context)
            npc.add_message(message)
            messages.append(message)
            print(f"{npc.get_name()} says: {message}\n~~~~~~~~~~~~~~~~~~~~~\n")
            npc.speak(message)
    # print the conversation
    for npc in npcs:
        print(npc.get_name())
        print(npc.get_messages())
        print("\n\n")
    # save the conversation
    with open("conversation.json", "w") as f:
        json.dump([npc.get_messages() for npc in npcs], f)



if __name__ == "__main__":
    # npc_test = NPC("Bob", "gpt-4", os.environ.get("OPENAI_API_KEY"))
    # npc_test.voice = 'alloy'
    # npc_test.speak("Hello, I am Bob, and I am a character in a game")
    main()


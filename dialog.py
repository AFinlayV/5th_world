from openai import OpenAI
import os
import random
import json
from pathlib import Path

"""
TODO: Make the text generation and the playing of audio async, so that the playing of audio doesn't stop the text generation
TODO: Add a way to update the disposition of the characters based on the conversation
TODO: Make the conversation history persistent
TODO: Add a way to save the conversation history to a file
TODO: Add a way to load the conversation history from a file
TODO: Save an entire conversation to an audio file (append mp3?)
TODO: Add a way to save the conversation to a file (json?)
TODO: Add a way to load a conversation from a file (json?)
TODO: Make the code model-agnostic so that it doesn't have to run on GPT and can run on local llama or mistral models
"""

OpenAI.api_key = os.environ.get("OPENAI_API_KEY")


def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()


GLOBAL = read_file('global_context.txt')
LOCAL = read_file('local_context.txt')
INST = read_file('instructions.txt')
SPEAK = True


class NPC:
    def __init__(self, name, model, voice, dispositions, background):
        self.name = name
        self.model = model
        self.voice = voice
        self.dispositions = dispositions
        self.background = background
        self.client = OpenAI()

    def update_disposition(self, topic, value):
        if isinstance(value, float) and -1 <= value <= 1:
            self.dispositions[topic] = value

    def speak(self, message):
        if not SPEAK:
            return
        speech_file_path = Path(__file__).parent / f"{self.name}.mp3"
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=self.voice,
            input=message
        )
        response.stream_to_file(speech_file_path)
        os.system(f"mpg123 -q {speech_file_path}")


class Conversation:
    def __init__(self, participants, global_context, local_context, instructions):
        self.participants = participants  # List of NPCs involved in the conversation
        self.global_context = global_context
        self.local_context = local_context
        self.instructions = instructions
        self.dialogue_history = []

    def build_context(self, npc):
        personal_context = npc.background + " " + ". ".join(
            [f"{topic} disposition: {score}" for topic, score in npc.dispositions.items()])
        previous_messages = " ".join([f"{msg['character']} said: {msg['message']}" for msg in self.dialogue_history])
        prompt = f"{self.instructions} Global Context: {self.global_context}. Personal Context: {personal_context}. Local Context: {self.local_context}. Previous Messages: {previous_messages}"
        return prompt

    def add_message(self, npc_name, message):
        self.dialogue_history.append({"character": npc_name, "message": message})

    def conduct_round(self):
        print(f"Conducting a round of dialogue...\n\n Characters:{[npc.name for npc in self.participants]}\n\n")
        for npc in self.participants:
            prompt = self.build_context(npc)
            message = npc.client.chat.completions.create(
                model=npc.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "How does the character respond?"}
                ],
            ).choices[0].message.content
            self.add_message(npc.name, message)
            print(f"{npc.name} says: {message}")
            npc.speak(message)


def load_characters(file_path):
    with open(file_path, 'r') as file:
        characters_data = json.load(file)
    return characters_data


def main():
    global_context = GLOBAL
    local_context = LOCAL
    instructions = INST

    # Load character data from JSON file
    characters_data = load_characters('characters.json')

    # Choose 3 random characters from the list
    character_list = random.sample(list(characters_data.keys()), 3)
    npcs = [NPC(name, **characters_data[name]) for name in character_list]

    conversation = Conversation(npcs, global_context, local_context, instructions)

    # Example: Conduct three rounds of dialogue
    for _ in range(3):
        conversation.conduct_round()

    # For demonstration, printing the dialogue history
    for entry in conversation.dialogue_history:
        print(f"{entry['character']} said: {entry['message']}")


if __name__ == "__main__":
    main()

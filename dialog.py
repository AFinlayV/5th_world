import anthropic
import os
import random
import json
from pathlib import Path
import asyncio
import logging
import subprocess
from openai import OpenAI
import re
import argparse
import datetime
import io
from pydub import AudioSegment
from pydub.playback import play

"""
This script demonstrates how to use the Anthropic API to generate dialogue between NPCs in a conversational setting.
"""

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration from file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Verbose setting
verbose = config['verbose']

# Dev mode setting
dev_mode = config['dev_mode']

try:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    OpenAI.api_key = openai_api_key
except Exception as e:
    logger.error(f"Error: {e}. Please make sure all required API keys are set as environment variables.")
    exit(1)

def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError as e:
        logger.error(f"Error: {e}. Please make sure the file '{file_path}' exists.")
        exit(1)
    except IOError as e:
        logger.error(f"Error: {e}. An error occurred while reading the file '{file_path}'.")
        exit(1)

try:
    GLOBAL = read_file(config['global_context_file'])
    LOCAL = read_file(config['local_context_file'])
    INST = read_file(config['instructions_file'])
except Exception as e:
    logger.error(f"Error: {e}")
    exit(1)

# List of available voices on macOS
dev_voices = ["Alex", "Daniel", "Fiona", "Fred", "Karen", "Moira", "Rishi", "Samantha", "Tessa", "Veena", "Victoria"]

class NPC:
    def __init__(self, name, model, voice, dispositions, background):
        self.name = name
        self.model = model
        self.voice = voice
        self.dispositions = dispositions
        self.background = background
        if dev_mode:
            self.voice = self.select_voice()

    def select_voice(self):
        while True:
            voice = random.choice(dev_voices)
            try:
                subprocess.run(["say", "-v", voice, "Testing the voice"], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                return voice
            except subprocess.CalledProcessError:
                logger.warning(f"Voice '{voice}' not found. Selecting a different voice.")

    def update_disposition(self, topic, value):
        if isinstance(value, float) and -1 <= value <= 1:
            self.dispositions[topic] = value

    async def speak(self, message):
        # Remove text between asterisks (**) or brackets ([])
        message = re.sub(r'\*.*?\*|\[.*?\]', '', message)
        if verbose:
            logger.info(f"Speaking for {self.name}: {message}")
        if dev_mode:
            audio_data = subprocess.check_output(["say", "-v", self.voice, message])
        else:
            response = OpenAI().audio.speech.create(
                model="tts-1",
                voice=self.voice,
                input=message
            )
            audio_data = response.read()
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        return audio_segment

class Conversation:
    def __init__(self, participants, global_context, local_context, instructions):
        self.participants = participants
        self.global_context = global_context
        self.local_context = local_context
        self.instructions = instructions
        self.dialogue_history = []
        self.round_dialogues = []

    def build_context(self, npc):
        personal_context = npc.background + " " + ". ".join(
            [f"{topic} disposition: {score}" for topic, score in npc.dispositions.items()])
        prompt = f"{self.instructions} Global Context: {self.global_context}. Personal Context: {personal_context}. Local Context: {self.local_context} Instructions: {self.instructions}"
        return prompt

    def add_message(self, npc_name, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.dialogue_history.append({"character": npc_name, "message": message, "timestamp": timestamp})

    async def generate_dialogue(self, npc, round_num, dialogue_num):
        prompt = self.build_context(npc)
        try:
            if verbose:
                logger.info(f"Generating dialogue for {npc.name}")
            if dev_mode:
                model = "claude-3-haiku-20240307"
            else:
                model = "claude-3-sonnet-20240229"
            response = client.messages.create(
                model=model,
                max_tokens=1000,
                temperature=1,
                system=prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Previous Messages:{self.dialogue_history} \n\n~~~~~~~~~~~\n\nHow does the character respond? The output should strictly contain only the character's spoken dialogue, with NO stage directions, NO additional information, and NO special formatting. It should end with an open-ended question that invites conversation."
                            }
                        ]
                    }
                ]
            )
            message = response.content[0].text.strip()
            self.add_message(npc.name, message)
            self.round_dialogues.append((npc, message))
        except anthropic.APIError as e:
            logger.error(f"Error: {e}. An error occurred while generating dialogue for {npc.name}.")
        except Exception as e:
            logger.error(f"Error: {e}. An unexpected error occurred while generating dialogue for {npc.name}.")

    async def generate_audio(self, round_num):
        audio_tasks = []
        for i, (npc, message) in enumerate(self.round_dialogues):
            audio_task = asyncio.create_task(npc.speak(message))
            audio_tasks.append(audio_task)
        audio_segments = await asyncio.gather(*audio_tasks)
        combined_audio = AudioSegment.empty()
        for audio_segment in audio_segments:
            combined_audio += audio_segment
        return combined_audio

    async def play_audio(self, audio_segment):
        play(audio_segment)

    async def conduct_round(self, round_num):
        if verbose:
            logger.info(
                f"Conducting round {round_num} of dialogue...\n\n Characters:{[npc.name for npc in self.participants]}\n\n")

        bartender_interjection = await self.get_bartender_interjection(round_num)

        if bartender_interjection:
            self.add_message("Bartender", bartender_interjection)
            await self.update_dispositions(bartender_interjection)

        self.round_dialogues = []
        dialogue_tasks = []
        for i, npc in enumerate(self.participants):
            dialogue_task = asyncio.create_task(self.generate_dialogue(npc, round_num, i + 1))
            dialogue_tasks.append(dialogue_task)
        await asyncio.gather(*dialogue_tasks)

        audio_segment = await self.generate_audio(round_num)
        await self.play_audio(audio_segment)

    async def get_bartender_interjection(self, round_num):
        bartender_task = asyncio.create_task(self.prompt_bartender(round_num))
        try:
            bartender_interjection = await asyncio.wait_for(bartender_task, timeout=5)
            return bartender_interjection.strip() if bartender_interjection.strip() else None
        except asyncio.TimeoutError:
            return None

    async def prompt_bartender(self, round_num):
        return input(f"Bartender's interjection for round {round_num} (press Enter to skip): ")

    async def update_dispositions(self, bartender_interjection):
        prompt = f"Bartender's interjection: {bartender_interjection}\n\nBased on the bartender's interjection, how does it affect each character's disposition towards different topics? Provide the updates in the following format:\n\nCharacter1:\nTopic1: DispositionChange\nTopic2: DispositionChange\n...\n\nCharacter2:\nTopic1: DispositionChange\nTopic2: DispositionChange\n...\n\nCharacter3:\nTopic1: DispositionChange\nTopic2: DispositionChange\n..."
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=1,
            system=prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please provide the disposition updates for each character based on the bartender's interjection."
                        }
                    ]
                }
            ]
        )
        disposition_updates = response.content[0].text.strip()
        for update in disposition_updates.split("\n\n"):
            character_name, *topic_updates = update.split(":\n")
            character_name = character_name.strip()
            for npc in self.participants:
                if npc.name == character_name:
                    for topic_update in topic_updates:
                        topic, disposition_change = topic_update.split(":")
                        topic = topic.strip()
                        disposition_change = float(disposition_change.strip())
                        npc.update_disposition(topic, disposition_change)

    def save_dialogue_history(self, file_path):
        with open(file_path, 'w') as file:
            json.dump(self.dialogue_history, file, indent=2)

def load_characters(file_path):
    try:
        with open(file_path, 'r') as file:
            characters_data = json.load(file)
        return characters_data
    except FileNotFoundError as e:
        logger.error(f"Error: {e}. Please make sure the file '{file_path}' exists.")
        exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Error: {e}. The file '{file_path}' contains invalid JSON.")
        exit(1)
    except IOError as e:
        logger.error(f"Error: {e}. An error occurred while reading the file '{file_path}'.")
        exit(1)

async def main(num_rounds, num_characters):
    global_context = GLOBAL
    local_context = LOCAL
    instructions = INST
    try:
        # Load character data from JSON file
        characters_data = load_characters(config['characters_file'])
        # Choose random characters from the list
        character_list = random.sample(list(characters_data.keys()), num_characters)
        npcs = [NPC(name, **characters_data[name]) for name in character_list]
        conversation = Conversation(npcs, global_context, local_context, instructions)
        # Conduct the specified number of rounds with bartender interjections
        for round_num in range(1, num_rounds + 1):
            await conversation.conduct_round(round_num)
        # Save the dialogue history to a file
        conversation.save_dialogue_history(config['dialogue_history_file'])
    except Exception as e:
        logger.error(f"Error: {e}. An unexpected error occurred.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a conversation between NPCs.')
    parser.add_argument('--rounds', type=int, default=3, help='Number of rounds to conduct (default: 3)')
    parser.add_argument('--characters', type=int, default=3, help='Number of characters to include (default: 3)')
    args = parser.parse_args()

    asyncio.run(main(args.rounds, args.characters))

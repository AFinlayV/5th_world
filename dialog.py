from openai import OpenAI
import os
import random
import json
from pathlib import Path
"""
TODO: Make the text generation and the playing of audio async, so that the playing of audio doesn't stop the text generation
TODO: Add a way to update the disposition of the characters
TODO: make context and characters external to the code and saved in a database or a file
TODO: make the conversation history persistent
TODO: Add a way to save the conversation history to a file
TODO: Add a way to load a conversation history from a file
TODO: Add a way to save the characters to a file
TODO: Add a way to load the characters from a file
TODO: save an entire conversation to an audio file. (append mp3?)
TODO: Add a way to save the conversation to a file (json?)
TODO: Add a way to load a conversation from a file (json?)
TODO: Make the code model agnostic so that it doesn't have to run on GPT and can run on local llama or mistral models

"""
OpenAI.api_key = os.environ.get("OPENAI_API_KEY")
GLOBAL = """
    The 5th World Station, an architectural marvel and a testament to the power of unity and 
    collaboration, stands as a beacon of progress and peace in the cosmos. Crafted from the remnants of the asteroid 
    belt, it's not just a space station but a microcosm of the galaxy's diversity, serving as a melting pot for 
    countless species, cultures, and ideologies.

At its core, the Nexus, a fusion reactor capable of transmuting quantum foam into tangible matter, powers the entire 
station and fuels its economy. The technology behind the Nexus has heralded an era of post-scarcity for the station's 
inhabitants, creating a society where basic needs are universally met, and the pursuit of knowledge, art, 
and personal fulfillment has flourished.

The station is divided into five distinct rings, each contributing uniquely to its ecosystem. The First Ring, 
dedicated to Matter Generation, harnesses the Nexus's energy to create the building blocks of life and industry. The 
Second Ring, the heart of Manufacturing, transforms these blocks into goods and technologies that drive the station's 
economy and innovation. The Third Ring, bustling with Residential and Commercial life, is where the heartbeats of 
commerce and community resonate, offering a home to the station's diverse populace. The Fourth Ring celebrates 
Artisan and Cultural expression, preserving the heritage of myriad civilizations while fostering new forms of 
artistic collaboration. The Fifth Ring, enveloping the station, stands guard as the Defense and Logistics hub, 
ensuring the safety of all who call the 5th World their home.

Inhabitants of the 5th World Station come from all corners of the galaxy, bringing their traditions, languages, 
and cuisines to create a rich tapestry of life. Humanoid species coexist with those of incomprehensible form, 
and digital consciousnesses interface seamlessly with organic life. This diversity has given rise to a vibrant 
culture where any day might celebrate an alien festival, a technological breakthrough, or a galactic market filled 
with exotic goods.

Yet, beneath its utopian surface, the 5th World grapples with challenges. Political intrigue, cultural clashes, 
and debates over the Nexus's control simmer beneath the harmony, reflecting the complexity of creating a unified 
society from so diverse a population. Environmental stewardship of the station, ethical use of the Nexus, 
and the rights of artificial intelligences are hot topics of debate in the cantinas and forums, where the station's 
democratic spirit shines brightest.

The 5th World Station is more than a marvel of technology; it's a living, breathing entity that embodies the hopes 
and dreams of its inhabitants. It stands as a testament to what can be achieved when the galaxy comes together, 
not just to survive, but to thrive. )"""
LOCAL = """

    Nestled in the bustling heart of Lumina Astra, a mega city on the Third Ring of the 5th World Station, 
    lies the Cosmos Cantina. Renowned for its unique blend of interstellar cultures and flavors, this establishment 
    stands as a testament to the advanced society that thrives within the station's confines.

In a world where scarcity is but a distant memory, the staff of Cosmos Cantina are entirely robotic, 
a choice reflecting the station's post-scarcity economy and its commitment to technological innovation. These robots, 
ranging from mixologists with an encyclopedic knowledge of cosmic cocktails to servers who glide silently between 
tables, are not just functional; they are a spectacle. Each is designed with a flair that mirrors the diverse 
aesthetics of the station's inhabitants, from sleek and minimalist forms inspired by the Core's technological 
wonders, to more ornate and whimsical designs paying homage to the Artisan Ring's creative spirit.

The cantina itself is a marvel of design, combining elements from the myriad cultures that make up the 5th World. Its 
walls are adorned with holographic murals that shift and change, telling the ancient tales of distant worlds and the 
shared history of the station's many peoples. The ceiling, a transparent dome, offers a view of the cosmos that is 
both humbling and exhilarating, reminding patrons of the vastness of the universe they share.

At the heart of the cantina's appeal is its menu, a culinary journey through the galaxy. The robotic chefs prepare 
dishes that are as diverse as the station's population, catering to the tastes and nutritional requirements of every 
species. From the delicately flavored vapor cuisines favored by the gas giants' denizens to the rich, spiced stews 
beloved by martian cultures, every dish is a masterpiece.

The bar, a long, curving expanse of luminescent material that seems to float without support, is where the cantina's 
robotic mixologists truly shine. These machines craft beverages that are more than just drinks; they are experiences. 
Ingredients from across the galaxy, some rare and others commonplace in the vastness of space, are combined in ways 
that delight and surprise. It's not uncommon to see patrons sipping on a cocktail that simmers with cold fire, 
or sharing a bowl of punch that shifts flavors as it moves around the table.

But Cosmos Cantina is more than just a place to eat and drink; it's a community hub. It's where deals are struck over 
a shared meal, where travelers from distant stars share stories of their journeys, and where the residents of Lumina 
Astra come to unwind. The staff, though robotic, are programmed with a deep understanding of the social fabric of the 
station, facilitating interactions and creating an atmosphere that is welcoming and inclusive.

In this era of post-scarcity, the Cosmos Cantina stands as a beacon of what society can achieve. It's a space where 
the technological and the cultural intertwine, where the past and the future meld, and where every visit is a 
reminder of the 5th World Station's place in the tapestry of the cosmos..

"""

INST = """Objective: Generate dialogue for characters in a narrative-driven game. The output should 
    strictly represent spoken words by the game character, suitable for direct conversion to speech in an interactive 
    environment. The dialogue will be voiced by a text-to-speech model and played back in the game, representing the 
    character's verbal responses.

Instructions for the LLM:

Focus on Spoken Dialogue: Your response must only include the exact words that the character would verbally express. 
Imagine writing a script for a voice actor where only the dialogue lines are provided, without any action cues or 
narrative descriptions.

Exclude Non-Verbal Elements: Do not include stage directions, character actions, thoughts, or any descriptive text 
that would not be spoken out loud by the character. The dialogue should be ready for immediate vocalization without 
interpretation or editing.

Avoid Speculative Language: Ensure the dialogue does not speculate about future events, the thoughts of other 
characters, or external circumstances unless directly voiced by the character in a speculative manner as part of 
their spoken dialogue.

Maintain Character Consistency: Tailor the dialogue to the character's established personality, background, 
and current situation as provided in their profile. Consider their linguistic style, cultural background, 
and personal beliefs when crafting their speech.

Context Awareness: Although your response should strictly contain dialogue, it must be relevant to the given 
context—responding appropriately to the situation, the environment (such as the bar in the mega city on the Third 
Ring), and the conversation's flow up to this point.

Clarity and Natural Flow: The dialogue should sound natural and coherent, as if the character is genuinely responding 
to the conversation or situation at hand. Avoid jargon or references that would be out of place for the character or 
setting.

Simplicity and Directness: Aim for simplicity and directness in the dialogue. The character's speech should convey 
their intentions and emotions clearly without requiring extensive background knowledge or inference from the 
audience."""

characters_data = {
    "Axel": {
        "model": "gpt-4",
        "voice": "alloy",
        "dispositions": {"adventure": 0.9, "science": 0.7, "culture": 0.2},
        "background": "Axel, an engineer from the Manufacturing Ring, thrives on innovation and the thrill of discovery. His work on sustainable energy sources has gained widespread attention."
    },
    "Briar": {
        "model": "gpt-4",
        "voice": "echo",
        "dispositions": {"politics": -0.8, "history": 0.5, "economy": 0.4},
        "background": "Briar is a political activist known for her fiery speeches and dedication to workers' rights. Her influence is growing, much to the concern of the station's elite."
    },
    "Cleo": {
        "model": "gpt-4",
        "voice": "fable",
        "dispositions": {"art": 0.8, "technology": -0.3, "environment": 0.7},
        "background": "A celebrated artist from the Artisan Ring, Cleo's installations challenge viewers to see the beauty in recycled materials, blending environmental activism with art."
    },
    "Dex": {
        "model": "gpt-4",
        "voice": "shimmer",
        "dispositions": {"sports": 0.9, "gambling": 0.6, "culture": -0.4},
        "background": "Dex, a former athlete turned sports commentator, is beloved for his insightful, albeit controversial, takes on the station's sporting events and betting pools."
    },
    "Eve": {
        "model": "gpt-4",
        "voice": "nova",
        "dispositions": {"science": 0.8, "politics": 0.4, "adventure": 0.5},
        "background": "Eve is a scientist whose research on artificial ecosystems has put her at odds with several powerful factions, yet her discoveries could revolutionize life on the station."
    },
    "Finn": {
        "model": "gpt-4",
        "voice": "onyx",
        "dispositions": {"economy": 0.9, "history": -0.2, "technology": 0.4},
        "background": "As a financial analyst, Finn's predictions have a near-mystical accuracy, making him a sought-after advisor for the station's most influential traders and investors."
    },
    "Gia": {
        "model": "gpt-4",
        "voice": "alloy",
        "dispositions": {"environment": 0.9, "art": 0.6, "science": -0.5},
        "background": "Gia leads the station's largest environmental advocacy group, fighting tirelessly to maintain the 5th World's ecosystems against unchecked technological expansion."
    },
    "Holt": {
        "model": "gpt-4",
        "voice": "echo",
        "dispositions": {"technology": 0.8, "sports": -0.7, "adventure": 0.6},
        "background": "A tech entrepreneur whose startup is on the brink of launching a game-changing transportation technology, Holt is as adventurous in business as he is in life."
    },
    "Isla": {
        "model": "gpt-4",
        "voice": "fable",
        "dispositions": {"culture": 0.9, "economy": -0.5, "politics": 0.3},
        "background": "Isla, a cultural anthropologist, has spent years documenting the diverse societies of the 5th World, offering invaluable insights into its complex social fabric."
    },
    "Jude": {
        "model": "gpt-4",
        "voice": "shimmer",
        "dispositions": {"history": 0.8, "art": 0.7, "science": -0.4},
        "background": "An historian specializing in the 5th World's formation and growth, Jude's works are essential reading for anyone looking to understand the station's place in the cosmos."
    },
    "Zara": {
        "model": "gpt-4",
        "voice": "nova",
        "dispositions": {"politics": -0.7, "technology": 0.5, "economy": 0.4, "environment": 0.9, "art": 0.3},
        "background": "Zara is a passionate environmental activist from the Artisan Ring, dedicated to promoting "
                      "sustainability and green technology across the station. She's often seen at the forefront of "
                      "demonstrations, pushing for eco-friendly policies."
    },
    "Milo": {
        "model": "gpt-4",
        "voice": "shimmer",
        "dispositions": {"politics": 0.6, "technology": -0.2, "economy": -0.5, "environment": -0.8, "art": 0.7},
        "background": "Milo, a renowned artist, uses his art to comment on the station's political landscape. His "
                      "controversial pieces often spark debates on governance and freedom, reflecting his complex "
                      "relationship with the station's authorities."
    },
    "Juno": {
        "model": "gpt-4",
        "voice": "echo",
        "dispositions": {"politics": 0.3, "technology": 0.8, "economy": 0.2, "environment": 0.1, "art": -0.6},
        "background": "Juno is a tech entrepreneur, known for her startup that revolutionizes waste management "
                      "through advanced recycling technologies. She's a pragmatic visionary, seeing the station's "
                      "growth and tech development as key to its future."
    },
    "Kai": {
        "model": "gpt-4",
        "voice": "onyx",
        "dispositions": {"politics": -0.4, "technology": 0.6, "economy": 0.8, "environment": 0.4, "art": -0.1},
        "background": "Kai operates one of the most successful trading companies on the station, dealing in rare "
                      "materials. His deep understanding of the economy and sharp business acumen make him a "
                      "respected figure in the trading community."
    },
    "Lena": {
        "model": "gpt-4",
        "voice": "fable",
        "dispositions": {"politics": 0.5, "technology": 0.3, "economy": -0.7, "environment": 0.6, "art": 0.8},
        "background": "Lena, a curator at the station's Museum of Galactic History, is passionate about preserving "
                      "the artistic and cultural heritage of different civilizations. She believes in art as a medium "
                      "to foster peace and understanding."
    },
    "Rex": {
        "model": "gpt-4",
        "voice": "alloy",
        "dispositions": {"politics": 0.2, "technology": -0.5, "economy": 0.7, "environment": -0.2, "art": -0.4},
        "background": "Rex is a seasoned bartender at the cantina, having served drinks and stories for decades. His "
                      "insights into the station's history and the dynamics of its inhabitants make him a beloved "
                      "figure among regulars."
    }
}


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
        personal_context = npc.background + " " + ". ".join([f"{topic} disposition: {score}" for topic, score in npc.dispositions.items()])
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

def main():
    global_context = GLOBAL
    local_context = LOCAL
    instructions = INST
    #choose 3 random characters from the list
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
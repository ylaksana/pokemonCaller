# This example requires the 'message_content' intent.

import discord
import requests

from dotenv import dotenv_values

config = dotenv_values(".env")


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$pikachu'):
        pokeRequests = requests.get("https://pokeapi.co/api/v2/pokemon/pikachu/").json()
        await message.channel.send(f'my data -> {pokeRequests["abilities"][0]["ability"]}')
    

client.run(config["TOKEN"])


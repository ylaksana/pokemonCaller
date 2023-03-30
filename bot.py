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
async def on_message(message: str):
    if message.author == client.user:
        return

    if message.content.startswith('$pokeCaller'):
        # =====================================================================
        # SETUP ===============================================================
        # =====================================================================
        channel = client.get_channel(770741092474683452)

        # Initialize an Embed
        embed = discord.Embed()

        words = message.content.split()
        # Lookup "python ternary" for explanation
        pokemonName = words[1].lower() if len(words) > 1 else None

        if not pokemonName:
            await message.channel.send(f'You must supply a Pokemon name.')

        # Get the information from our external API and store it
        try:
            pokeInfo: dict = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemonName}/").json()
        except Exception:
            await message.channel.send(f'Error trying to retrieve Pokemon information.')
            raise

        level: bool = 5
        # [{ability:1, is_hidden:true}, {ability:2, is_hidden:true}, {ability:3, is_hidden:true}]
        pokeAbilities: list[dict] = pokeInfo['abilities']
        pokeMoves: list[dict] = pokeInfo['moves']
        pokeStats: list[dict] = pokeInfo['stats']

        # =====================================================================
        # PROCESS =============================================================
        # =====================================================================
        pokemonMessage = f'Pokemon: {pokeInfo["species"]["name"].capitalize()}\n'
        levelMessage = f'Level: {level}\n'
        abilitiesMessage = ''
        movesMessage = ''
        statsMessage = ''
        line = "-----------------------------------------------------------\n"

        # Building Stats string
        for statData in pokeStats:
            statsMessage += f'{statData["stat"]["name"].upper()} | {statData["base_stat"]}\n'
            

        # Building Moves string
        count = 0
        for moveData in pokeMoves:
            if 0 < moveData["version_group_details"][0]["level_learned_at"] <= 5:
                movesMessage += f'{moveData["move"]["name"].upper()}'
                moveInfo = requests.get(moveData["move"]["url"]).json()
                movesMessage += f' | {moveInfo["pp"]} PP \n'
                count += 1
            if count == 4:
                break

        typeMessage = f'Type: {pokeInfo["types"][0]["type"]["name"].capitalize()}\
{" / " + pokeInfo["types"][1]["type"]["name"].capitalize()if len(pokeInfo["types"]) > 1 else ""} \n'

        # Abilities are more complicated because we need to make a separate request to get the info
        for i, abilityData in enumerate(pokeAbilities, start=1):
            abilityInfo = requests.get(abilityData["ability"]["url"]).json()
            abilitiesMessage += f'Pokemon Ability {i}: **{abilityData["ability"]["name"].capitalize()}**\n'

            # Make sure we only get English info
            for entry in abilityInfo["effect_entries"]:
                if entry['language']['name'] == 'en':
                    abilitiesMessage += f'{entry["effect"]}\n\n'

        embed.set_image(url=pokeInfo["sprites"]["other"]
                        ["official-artwork"]["front_default"])

        # =====================================================================
        # OUTPUT ==============================================================
        # =====================================================================
        # Finally, send the Embed
        await channel.send(embed=embed)
        # TODO: Replace this message with the embed
        await message.channel.send(pokemonMessage + typeMessage + levelMessage + abilitiesMessage + "**STATS**\n" + line + statsMessage + "\n" + "**MOVES**" + "\n" + line + movesMessage)

client.run(config["TOKEN"])

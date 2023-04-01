# This example requires the 'message_content' intent.

# from discord.ext import commands
import discord
import requests
import random
import asyncio
import asyncpg

from dotenv import dotenv_values

config = dotenv_values(".env")

# DEFAULT_PREFIX = '!'

# async def get_prefix(bot, message):
#     if not message.guild:
#         return commands.when_mentioned_or(DEFAULT_PREFIX)(bot,message)
    
#     prefix = await bot.db.fetch('SELECT prefix FROM pokeData WHERE "pokeID" = $1', message.guild.id)
#     if len(prefix) == 0:
#         await bot.db.execute('INSERT INTO pokeData("pokeID", prefix) VALUES ($1, $2)', message.guild.id, DEFAULT_PREFIX)
#     else:
#         prefix = prefix[0].get("prefix")
#     return commands.when_mentioned_or(prefix)(bot,message)

# bot = commands.Bot(command_prefix = get_prefix)

# async def create_db_pool():
#     bot.db = await asyncpg.create_pool(database = "pokeBattler", user = "postgres", password = "")
#     print("Connection successful")

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

    if message.content.startswith('$db'):
        conn = await asyncpg.connect(user='postgres', password='DL6SL9!23', database='pokeBattler', host='127.0.0.1')
        values = await conn.fetch('SELECT * FROM pokeData;',10)
        print("testing")
        await channel.send(values)
        await conn.close()
    # loop = asyncio.get_event_loop()
    

    if message.content.startswith('$pokeCaller'):
        # =====================================================================
        # SETUP ===============================================================
        # =====================================================================
        channel = client.get_channel(770741092474683452)

        words = message.content.split()
        # Lookup "python ternary" for explanation
        pokemonName = words[1].lower() if len(words) > 1 else None

        if not pokemonName:
            await message.channel.send(f'You must supply a Pokemon name.')

        # Get the information from our external API and store it
        try:
            pokeInfo: dict = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemonName}/").json()
            pokeNature: dict = requests.get(f'https://pokeapi.co/api/v2/nature').json()
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
        pokemonMessage = f'Pokemon #{pokeInfo["id"]}\n\nPokemon: {pokeInfo["species"]["name"].capitalize()}\n\n'
        levelMessage = f'Level: {level}\n'
        abilitiesMessage = ''
        movesMessage = ''
        statsMessage = ''
        natureMessage = ''
        line = "----------------------------------------------------\n"

        # Building Nature string
        natureNum = random.randrange(0, len(pokeNature["results"]))
        natureInfo = requests.get(pokeNature["results"][natureNum]["url"]).json()
        natureMessage += f'Nature: **{pokeNature["results"][natureNum]["name"].capitalize()}**\n'
        statUp = natureInfo["increased_stat"]
        statDown = natureInfo["decreased_stat"]
        if(isinstance(statUp, dict) and isinstance(statDown, dict)):
            natureMessage += f'{natureInfo["increased_stat"]["name"].upper()} **UP**, {natureInfo["decreased_stat"]["name"].upper()} **DOWN**\n\n'
        else:
            natureMessage += f'No effect on stats.\n\n'

        # Building Stats string
        for statData in pokeStats:
            statsMessage += f'{statData["stat"]["name"].upper()} | {statData["base_stat"]}\n'
            

        # Building Moves string
        count = 0
        for moveData in pokeMoves:
            if 0 < moveData["version_group_details"][0]["level_learned_at"] <= 5:
                movesMessage += f'{moveData["move"]["name"].upper()}'
                moveInfo = requests.get(moveData["move"]["url"]).json()
                acc = moveInfo["accuracy"]
                if isinstance(acc, int):
                    acc = moveInfo["accuracy"]
                else:
                    acc = "--"
                movesMessage += f' | {moveInfo["damage_class"]["name"].capitalize()} | Accuracy: {acc} | {moveInfo["pp"]} PP \n'
                count += 1
            if count == 4:
                break

        typeMessage = f'Type: {pokeInfo["types"][0]["type"]["name"].capitalize()}\
{" / " + pokeInfo["types"][1]["type"]["name"].capitalize()if len(pokeInfo["types"]) > 1 else ""} \n'

        # Abilities are more complicated because we need to make a separate request to get the info
        for i, abilityData in enumerate(pokeAbilities, start=1):
            abilityInfo = requests.get(abilityData["ability"]["url"]).json()
            if abilityData["is_hidden"] == False:
                abilitiesMessage += f'Pokemon Ability {i}: **{abilityData["ability"]["name"].capitalize()}**\n'
            elif abilityData["is_hidden"] == True:
                abilitiesMessage += f'Hidden Ability: **{abilityData["ability"]["name"].capitalize()}**\n'

            # Make sure we only get English info
            for entry in abilityInfo["effect_entries"]:
                if entry['language']['name'] == 'en':
                    abilitiesMessage += f'{entry["effect"]}\n\n'
        

        # =====================================================================
        # OUTPUT ==============================================================
        # =====================================================================s
        # Finally, send the Embed
        # Initialize an Embed
        shinyNum = random.randrange(1, 8193)
        print(shinyNum)
        embed = discord.Embed(description = pokemonMessage + natureMessage + typeMessage + levelMessage + abilitiesMessage + "**STATS**\n" + line + statsMessage + "\n" + "**MOVES**" + "\n" + line + movesMessage)
        if 1 < shinyNum < 8193:
            embed.set_image(url=pokeInfo["sprites"]["other"]["official-artwork"]["front_default"])
        else:
            embed.set_image(url=pokeInfo["sprites"]["other"]["official-artwork"]["front_shiny"])
            embed.set_footer(text = "CONGRATS! YOU GOT A SHINY!")
        await channel.send(embed=embed)


# @bot.command(aliases=['setpre'])
# @commands.has_permissions(administrator=True)
# async def setprefix(ctx, new_prefix):
#     await bot.db.execute('UPDATE guilds SET prefix = $1 WHERE "guild_id" = $2', new_prefix, ctx.guild.id)
#     await ctx.send("Prefix updated!")
    
# bot.loop.run_until_complete(create_db_pool())
client.run(config["TOKEN"])

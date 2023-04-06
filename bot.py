# This example requires the 'message_content' intent.

# from discord.ext import commands
import discord
import requests
import random
import asyncio
import asyncpg

from dotenv import dotenv_values

config = dotenv_values(".env")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# TODO: Fix this, it's bad
class Database:
    connection = None
db = Database()


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

    try:
        print('Attempting to connect to database')
        db.connection = await asyncpg.connect(config["DATABASE_STRING"])
        print('Successfully connected to database')
    except Exception as e:
        print('Error connecting to database: ', e)
        raise



@client.event
async def on_message(message: str):
    if message.author == client.user:
        return

    if message.content.startswith('$release'):
        channel = client.get_channel(770741092474683452)

        words = message.content.split()
        pokemon = words[1].capitalize()

        print(pokemon)

        deleteCommand = f"DELETE FROM pokedata WHERE pokename='{pokemon}';"
    
        try:
            print('Releasing Pokemon...')
            records: list[asyncpg.Record] = await db.connection.execute(deleteCommand)
            await channel.send(f'{pokemon} was released.\nBye-Bye, {pokemon}!')
        except Exception as e:
            print(e)
            raise

    if message.content.startswith('$viewParty'):
        channel = client.get_channel(770741092474683452)
    
        records: list[asyncpg.Record] = await db.connection.fetch('''
            SELECT * FROM pokedata;
        ''')
        trainers: list[asyncpg.Record] = await db.connection.fetch('''
            SELECT * FROM trainer;
        ''')

        #================================================================
        # CHECK IF TRAINER HAS BEEN REGISTERED
        #================================================================

        foundTrainer = False
        nameMessage = ''
        userID = client.user.id
        for trainer in trainers:
            if(trainer["ID"] == userID):
                foundTrainer = True
                trainerName = trainer["name"]
                break
        print(print)
        #================================================================
        # OUTPUT EACH POKEMON ENTRY FROM THE TABLE
        #================================================================

        if(foundTrainer):
            await channel.send(f"{trainerName}'s Party:")
            count = 1
            for record in records:  # https://magicstack.github.io/asyncpg/current/api/index.html?highlight=record#asyncpg.Record
                if record["trainerid"] == userID:
                    nameMessage += f'Pokemon {count}: **{record["pokename"]}**\n'
                    nameMessage += f'HP: {record["currenthp"]}'
                    nameMessage += f' | Status: {record["status"]}\n'
                    nameMessage += f'Nature: {record["pokenature"]} | Ability: {record["ability"]}\n\n'
                    nameMessage += f'STATS\n-------------------------------\n'
                    nameMessage += f'HP {record["hp"]} | ATK {record["atk"]} | DEF {record["def"]}\n'
                    nameMessage += f'SPATK {record["spatk"]} | SPDEF {record["spdef"]} | SPD {record["speed"]}\n\n'
                    nameMessage += f'MOVES\n-------------------------------\n'
                    nameMessage += f'{record["move1"]} (PP {record["move1pp"]}/{record["move1pp"]}) | {record["move2"]} (PP {record["move2pp"]}/{record["move2pp"]})\n'
                    nameMessage += f'{record["move3"]} (PP {record["move3pp"]}/{record["move3pp"]}) | {record["move4"]} (PP {record["move4pp"]}/{record["move4pp"]})\n\n\n\n'
                    count += 1

        else:
            nameMessage += f"Currently, you have no Pokemon that belongs to you."
            await channel.send(nameMessage)

        embed = discord.Embed(description = nameMessage)
        await channel.send(embed=embed)
        

    if message.content.startswith('$catch'):
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
        pokeNature: dict = requests.get(f'https://pokeapi.co/api/v2/nature').json()

        # Add the pokemon to the database

        POKEID = pokeInfo["id"]
        NAME = pokeInfo["species"]["name"].capitalize()
        abilityNum = random.randrange(0, len(pokeAbilities))
        ABILITY = pokeAbilities[abilityNum]["ability"]["name"].capitalize()
        natureNum = random.randrange(0, len(pokeNature["results"]))
        NATURE = pokeNature["results"][natureNum]["name"].capitalize()
        STATUS = "None"
        CURRENTHP = pokeInfo["stats"][0]["base_stat"]
        HP = pokeInfo["stats"][0]["base_stat"]
        ATTACK = pokeInfo["stats"][1]["base_stat"]
        DEF = pokeInfo["stats"][2]["base_stat"]
        SPATK = pokeInfo["stats"][3]["base_stat"]
        SPDEF = pokeInfo["stats"][4]["base_stat"]
        SPEED = pokeInfo["stats"][5]["base_stat"]
        MOVE1PP = 30
        MOVE2PP = 25
        MOVE3PP = 0
        MOVE4PP = 0
        TRAINERID = client.user.id

        
        command = f"INSERT INTO pokedata(pokeid, pokename, pokenature, ability, status, currenthp, hp, atk, def, spatk, spdef, speed, move1, move1pp, move2, move2pp, move3, move3pp, move4, move4pp, trainerid)\
 VALUES ({POKEID}, '{NAME}', '{NATURE}', '{ABILITY}', '{STATUS}', {CURRENTHP}, {HP}, {ATTACK}, {DEF}, {SPATK}, {SPDEF}, {SPEED}, 'MOVE1', {MOVE1PP}, 'MOVE2', {MOVE2PP}, 'MOVE3', {MOVE3PP}, 'MOVE4', {MOVE4PP}, {TRAINERID});"

        print(command)

        # command.replace('POKENAME', f'{NAME}')

        try:
            print('Adding new entry to database')
            records: list[asyncpg.Record] = await db.connection.execute(command)
            await message.channel.send(f'Successfully caught {NAME}!')
        except Exception as e:
            print(e)
            raise
        
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

import discord
from discord.ext import commands
from os import environ
import random
import json
import time

client = commands.Bot(command_prefix=">")
token = environ.get("token")


@client.event
async def on_ready():
    print('Logged in')
    await client.change_presence(status=discord.Status.online, activity=discord.Game(">start"))


@commands.command()
async def start(ctx):

    # checking some things
    user = ctx.author
    guild = ctx.guild
    channel = ctx.channel
    vcs = guild.voice_channels
    vc = None

    if user.bot:
        return

    for i in vcs:
        if user in i.members:
            vc = i

    if vc is None:
        embed = discord.Embed(title="Error", color=discord.Colour.red())
        embed.add_field(name="You are not in a vc!",
                        value="You can't play without being connected to a vc! You need to connect to a vc to play.")
        await channel.send(embed=embed)
        return

    players = vc.members

    if len(players) < 2:
        embed = discord.Embed(title="Error", color=discord.Colour.red())
        embed.add_field(name="To little users!",
                        value="There are too little users in the voice channel! You need at least 3 people to play.")
        await channel.send(embed=embed)
        return

    await guild.change_voice_state(channel=vc, self_deaf=True, self_mute=True)

    # selecting impostor(s) TODO: add settings so you can select number of impostors
    crewmates = list(players)
    impostors = [players[random.randint(0, len(players)-1)]]

    for i in impostors:
        crewmates.remove(i)

    # print(f"crew: {crewmates}")
    # print(f"impostors: {impostors}")

    # selecting a question TODO: make some example questions
    questions = json.load(open("questions.json"))

    q_number = len(questions["crewmate"])
    i_q_number = len(questions["impostor"])

    if q_number != i_q_number:
        if q_number > i_q_number:
            q_number = i_q_number

    n = random.randint(0, q_number-1)
    c_q = questions["crewmate"][n]
    i_q = questions["impostor"][n]

    # announcing roles TODO: make it pretty with embed messages with images
    for i in crewmates:
        m = guild.get_member(i.id)

        if m.dm_channel is None:
            await m.create_dm()

        await m.dm_channel.send("You are a Crewmate!")
        await m.dm_channel.send(c_q)

    for i in impostors:
        m = guild.get_member(i.id)

        if m.dm_channel is None:
            await m.create_dm()

        await m.dm_channel.send("You are The Impostor!")
        await m.dm_channel.send(i_q)

    # creating the game channel
    chan_name = f"yiay-us-{random.randint(1000, 9999)}"
    game_role = await guild.create_role(name=chan_name)  # TODO: change it to specific users rather than a role
    print(f"Starting {chan_name} game")

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False, add_reactions=False),
        game_role: discord.PermissionOverwrite(read_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    game_channel = await guild.create_text_channel(chan_name, overwrites=overwrites)

    for i in players:
        await i.add_roles(game_role)

    # answering phase TODO: maybe change it to dms so you cant change your mind based on other answers
    messages = []
    for i in players:
        temp_msg = await game_channel.send(f"{i.mention} it's your turn! You have 60 seconds to answer.")

        def answer_check(msg):
            return msg.channel == game_channel and msg.author == i

        message = await client.wait_for('message', check=answer_check, timeout=60)
        messages.append(message)
        await temp_msg.delete()

    # voting phase TODO: say who is voted out and overwrite so dead people can't talk
    await game_channel.send(f"The question was: {c_q}")
    vote_announce = await game_channel.send(f"Voting starts in 20 seconds {game_role.mention}")
    time.sleep(20)
    await vote_announce.delete()

    not_voted = list(players)
    votes = {}

    skip_msg = await game_channel.send("Skip vote")
    messages.append(skip_msg)
    for i in messages:
        await i.add_reaction("✅")
    await game_channel.send(f"You can now vote! Remember that you can't change your vote!")

    def vote_check(reaction, user):
        return not user.bot

    while not_voted:
        reaction, user = await client.wait_for("reaction_add", check=vote_check, timeout=90)

        if reaction.message.channel == game_channel and str(reaction.emoji) == "✅" and user in not_voted:
            not_voted.remove(user)

            if reaction.message.author in votes.keys():
                votes[reaction.message.author] += 1
            else:
                votes[reaction.message.author] = 1

            await game_channel.send(f"{user.mention} has voted!")
            await reaction.remove(user)

        else:
            await reaction.delete()

    # voting results TODO: add list who voted for what
    await game_channel.send("Voting results:")
    for i in votes.keys():
        if i != client.user:
            await game_channel.send(f"{i.mention} got {votes[i]} votes")
        else:
            await game_channel.send(f"Skipped: {votes[i]}")

    # TODO: make game longer than one round
    time.sleep(30)
    # cleaning after the end of the game
    print(f"Cleaning {chan_name} game")
    await guild.change_voice_state(channel=None)
    for i in players:
        await i.remove_roles(game_role)
    await game_role.delete()

    # await game_channel.delete() TODO: make it so you need to confirm to delete the channel


client.add_command(start)
client.run(token)

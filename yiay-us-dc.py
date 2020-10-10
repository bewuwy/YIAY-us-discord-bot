import discord
from discord.ext import commands
from os import environ
import random
import json

client = commands.Bot(command_prefix=">")
token = environ.get("token")


@client.event
async def on_ready():
    print('Logged in')
    await client.change_presence(status=discord.Status.online, activity=discord.Game(">start"))


@commands.command()
async def start(ctx):

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

    await guild.change_voice_state(channel=vc, self_deaf=True, self_mute=True)

    if len(players) < 2:
        embed = discord.Embed(title="Error", color=discord.Colour.red())
        embed.add_field(name="To little users!",
                        value="There are too little users in the voice channel! You need at least 3 people to play.")
        await channel.send(embed=embed)

        return

    crewmates = list(players)
    impostors = [players[random.randint(0, len(players)-1)]]

    for i in impostors:
        crewmates.remove(i)

    # print(f"crew: {crewmates}")
    # print(f"impostors: {impostors}")
    questions = json.load(open("questions.json"))

    q_number = len(questions["crewmate"])
    i_q_number = len(questions["impostor"])

    if q_number != i_q_number:
        if q_number > i_q_number:
            q_number = i_q_number

    n = random.randint(0, q_number-1)
    c_q = questions["crewmate"][n]
    i_q = questions["impostor"][n]

    for i in crewmates:
        await i.create_dm()
        await i.dm_channel.send("You are a Crewmate!")
        await i.dm_channel.send(c_q)

    for i in impostors:
        await i.create_dm()
        await i.dm_channel.send("You are The Impostor!")
        await i.dm_channel.send(i_q)


client.add_command(start)
client.run(token)

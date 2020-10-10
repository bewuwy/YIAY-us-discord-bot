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

    chan_name = f"yiay-us-{random.randint(1000, 9999)}"
    game_role = await guild.create_role(name=chan_name)
    print(f"Starting {chan_name} game")

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        game_role: discord.PermissionOverwrite(read_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    game_channel = await guild.create_text_channel(chan_name, overwrites=overwrites)

    for i in players:
        await i.add_roles(game_role)

    for i in players:
        temp_msg = await game_channel.send(f"{i.mention} it's your turn! You have 60 seconds to answer.")

        def answer_check(msg):
            return msg.channel == game_channel and msg.author == i

        message = await client.wait_for('message', check=answer_check, timeout=60)
        await message.add_reaction("✅")
        await temp_msg.delete()

    time.sleep(20)
    await guild.change_voice_state(channel=None)
    for i in players:
        await i.remove_roles(game_role)
    await game_channel.delete()
    await game_role.delete()


client.add_command(start)
client.run(token)

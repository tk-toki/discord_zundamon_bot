import asyncio
import json
import re
import wave
from xmlrpc.client import Boolean

import psycopg2
import requests
import discord
from discord.ext import commands

#VOICEVOXエンジンの接続ポート
host = 'localhost'
port = 50021

#DISCORD情報
intents = discord.Intents.default()
client = discord.Client(intents=intents)
bot = commands.Bot()
token = ""
vclist = {}

#音声ファイル番号
count = 0
is_read_name = False

@client.event
async def on_ready():
    is_initialize_speaker = requests.get(
        f'http://{host}:{port}/is_initialize_speaker'
    )
    if is_initialize_speaker == False:
        initialize_speaker = requests.post(
            f'http://{host}:{port}/initialize_speaker'
        )
    print("起動したのだ")

@client.event
async def on_message(message):
    voice = discord.utils.get(bot.voice_clients, guild=message.guild)

    if voice and voice.is_connected and message.channel.id == vclist[message.guild.id]:
        pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
        pattern_emoji = "\<.+?\>"

        output = re.sub(pattern, "URL省略なのだ", message.content)
        output = re.sub(pattern_emoji, "", output)
        if is_read_name and not message.author.bot:
            output = message.author.display_name + "." + output
        if len(output) > 50:
            sur = len(output) - 50
            output = output[:len(output) - sur]
            output += "以下略なのだ"
        print(output)

        while message.guild.voice_client.is_playing():
            await asyncio.sleep(0.1)
        source = discord.FFmpegPCMAudio(generate_wav(output))
        message.guild.voice_client.play(source)
        return
    else:
        return

@client.event
async def on_voice_state_update(member, before, after):
    voicestate = member.guild.voice_client
    if voicestate is None:
        return
    if len(voicestate.channel.members) == 1:
        await voicestate.disconnect()

@bot.slash_command(description='ずんだもんをボイスチャンネルから切断するのだ')
async def zu_e(ctx):
    if ctx.guild.voice_client is not None:
        await ctx.guild.voice_client.disconnect()
        await ctx.respond("切断したのだ")
        return
    else:
        await ctx.respond("切断しようとしたときに何らかの問題が発生したのだ")
        return

@bot.slash_command(description='ずんだもんをボイスチャンネルに接続するのだ')
async def zu_s(ctx):
    if ctx.author.voice is None:
        await ctx.respond("音声チャンネルに入っていないから操作できないのだ")
        return
    if ctx.guild.voice_client is not None:
        del vclist[ctx.guild.id]
        await ctx.guild.voice_client.disconnect()
        await ctx.respond("切断したのだ")
        return
    else:
        vclist[ctx.guild.id] = ctx.channel.id
        await ctx.author.voice.channel.connect()
        await ctx.respond("読み上げを開始するのだ")
        return

@bot.slash_command(description='ずんだもんが名前を呼ぶか設定できるのだ 読む="y" or "1", 読まない="n" or "0"')
async def zu_readname(ctx, is_enable:str):
    global is_read_name
    if is_enable in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
        is_read_name = True
        await ctx.respond("名前を呼ぶようにするのだ")
        return
    elif is_enable in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
        is_read_name = False
        await ctx.respond("名前を呼ばないようにするのだ")
        return
    else:
        await ctx.respond("指定する文字を間違えているのだ")
        return

#音声データの作成
def generate_wav(text):
    #作成するボイス情報
    params = (
        ('text', text),
        ('speaker', 1), #ずんだもん
    )

    #最初にsynthesis宛用のパラメータを生成する
    audioquery = requests.post(
        f'http://{host}:{port}/audio_query',
        params=params
    )

    #synthesisに渡して音声データを作る
    synthesis = requests.post(
        f'http://{host}:{port}/synthesis',
        headers = {'Content-Type': 'application/json', },
        params=params,
        data=json.dumps(audioquery.json())
    )

    #ファイル名
    global count
    count += 1
    if (count > 5):
        count = 1
    filepath = f'./temp{count}.wav'

    #音声データの各種設定
    wf = wave.open(filepath, 'wb')
    wf.setnchannels(1) #モノラル
    wf.setsampwidth(2) #1サンプルあたり2bytes(16bit)
    wf.setframerate(24000)
    wf.writeframes(synthesis.content)
    wf.close()

    return filepath

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    client.run(token)
# See PyCharm help at https://www.jetbrains.com/help/pycharm/

import discord
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv

def run_bot():
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in .env file")
        return

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    queues = {}
    voice_clients = {}
    yt_dl_options = {
        "format": "bestaudio/best",
        "cookiesfrombrowser": "chrome"
    }
    ytdl = yt_dlp.YoutubeDL(yt_dl_options)

    ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn -filter:a "volume=0.25"'}

    @client.event
    async def on_ready():
        print(f'{client.user} is now jamming')

    @client.event
    async def on_message(message):
        if message.content.startswith("?play"):
            if message.author.voice is None:
                print("User is not connected to a voice channel.")
                await message.channel.send("You need to be in a voice channel to use this command.")
                return

            try:
                voice_client = await message.author.voice.channel.connect()
                voice_clients[voice_client.guild.id] = voice_client
                print(f"Connected to voice channel: {message.author.voice.channel}")
            except discord.ClientException as e:
                print(f"ClientException: {e}")
                await message.channel.send("Bot is already connected to a voice channel.")
            except discord.opus.OpusNotLoaded as e:
                print(f"OpusNotLoaded: {e}")
                await message.channel.send("Opus library is not loaded.")
            except Exception as e:
                print(f"Error connecting to voice channel: {e}")
                await message.channel.send(f"Error connecting to voice channel: {e}")
                return

            try:
                parts = message.content.split(" ", 1)
                if len(parts) < 2 or not parts[1].strip():
                    await message.channel.send("Please provide a valid URL to play.")
                    return

                url = parts[1].strip()
                print(f"URL to play: {url}")

                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
                print(f"Extracted data: {data}")

                song = data['url']
                player = discord.FFmpegPCMAudio(song, **ffmpeg_options)
                print(f"Playing song: {song}")

                voice_clients[message.guild.id].play(player)
            except Exception as e:
                print(f"Error playing song: {e}")
                await message.channel.send(f"Error playing song: {e}")

        if message.content.startswith("?pause"):
            try:
                voice_clients[message.guild.id].pause()
            except Exception as e:
                print(e)

        if message.content.startswith("?resume"):
            try:
                voice_clients[message.guild.id].resume()
            except Exception as e:
                print(e)

        if message.content.startswith("?stop"):
            try:
                voice_clients[message.guild.id].stop()
                await voice_clients[message.guild.id].disconnect()
            except Exception as e:
                print(e)

    print("Running the bot...")
    client.run(TOKEN)
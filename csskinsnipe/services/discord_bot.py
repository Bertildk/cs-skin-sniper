# This example requires the 'message_content' intent.
import asyncio
import threading
from datetime import datetime

import discord
from discord.ext import commands
from discord.ext.commands import bot
from dotenv import load_dotenv
import os
from csskinsnipe.services import scanner
import re

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


def run_discord_bot():
    client.run(TOKEN)


async def shutdown(context):
    await client.close()


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    skin_snipe = client.get_channel(1337196801744306237)
    new_items = client.get_channel(1337196820455227453)
    if skin_snipe and new_items is None:
        print("Channel not found or bot does not have access to it.")
    else:
        print("Channel found:", skin_snipe, new_items)


async def alert_users(message):
    print("Attempting to send message in Skin-sniper channel")
    skin_snipe = client.get_channel(1337196801744306237)
    if 'Scan completed' in message:
        client.loop.create_task(skin_snipe.send(f"{message}"))
    else:
        client.loop.create_task(skin_snipe.send(f"@everyone {message}"))


async def alert_new_item(message):
    print("Attempting to send message in New-items channel")
    new_items = client.get_channel(1337196820455227453)
    client.loop.create_task(new_items.send(f"@everyone{message}\n{datetime.now().hour}:{datetime.now().minute}"))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!?'):
        await message.channel.send('Im Awake!')

    if message.content.startswith('!get crafts'):
        await get_crafts(message, True)
    if message.content.startswith('!get deals'):
        await get_deals(message)
    if message.content.startswith('!help'):
        await message.channel.send('**Commands** :\n'
                                   '".!" : Check if bot is awake'
                                   '\n"!get crafts <amount>" : Get the best crafts'
                                   '\n"!get deals <amount>" : Get the best deals')


def create_msg(items, key, counter):
    sending_message = ""
    sending_message += f"**{counter}: {items[key]['skin_name']}**\n"
    sending_message += f"Skin Price: {items[key]['skin_price']}$\n"
    sending_message += f"Total Sticker Price: {items[key]['totalStickerPrice']}$\n"
    sending_message += f"Sticker Value: {items[key]['sticker_value']}\n"
    sending_message += f"Stickers: \n"

    for sticker in items[key]['stickers']:
        sending_message += f"   -{sticker['name']}, {sticker['price']}$\n"

    return sending_message


async def get_deals(message):
    amount = re.search(r'\d+', message.content)
    amount = int(amount.group())
    print(amount)
    sorted_skins = scanner.load_sorted_skins()
    items = sorted_skins.get('items')

    counter = 1
    for index, key in enumerate(items):
        if index < amount:
            sending_message = create_msg(items, key, counter)
            print(sending_message)
            counter += 1
            await message.channel.send(sending_message)

        if index + 1 == amount:
            break


async def get_crafts(message, isCraft):
    amount = re.search(r'\d+', message.content)
    amount = int(amount.group())
    sorted_skins = scanner.load_sorted_skins()
    items = sorted_skins.get('items')
    counter = 1
    for index, key in enumerate(items):
        sending_message = ""
        if index < amount and items[key]['sticker_craft'] is isCraft:
            sending_message = create_msg(items, key, counter)

            counter += 1
            await message.channel.send(sending_message)

        if items[key]['sticker_craft'] is False:
            amount += 1

        if index + 1 == amount:
            break

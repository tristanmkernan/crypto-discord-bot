import aiohttp
import json
import os

from asyncio import Lock, sleep
from discord.ext import commands
from random import choice


MESSAGE_INTERVAL_MINUTES = 60

with open("cryptocoins.json") as fp:
    CRYPTO_DB = json.load(fp)


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()


bot = commands.Bot("!")


@bot.command()
async def crypto(ctx, ticker):
    async with aiohttp.ClientSession() as session:
        # example
        # https://api.coingecko.com/api/v3/coins/bitcoin?localization=false
        datum = await fetch(
            session,
            f"https://api.coingecko.com/api/v3/coins/{ticker}?localization=false",
        )

        await ctx.send(
            f"{datum['symbol']}/{datum['name']} - CURRENT ${datum['market_data']['current_price']['usd']}"
            f" - CHANGE 24hrs ${datum['market_data']['price_change_24h']}"
        )


lock = Lock()


@bot.listen()
async def on_message(message):

    if bot.user == message.author:
        return

    if bot.user in message.mentions:
        await message.channel.send("https://www.youtube.com/watch?v=fSETHWC8R5U")
        return

    # set of ids for API retrieval
    matches = []

    for potential in CRYPTO_DB:
        if potential["symbol"] in message.content.lower():
            matches.append(potential["id"])

    if len(matches) == 0:
        return

    if lock.locked():
        return

    # select only 1 ticker at random
    matches = [choice(matches)]

    async with lock:
        async with aiohttp.ClientSession() as session:
            crypto_ids = ",".join(match for match in matches)

            # example
            # https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=01coin,0chain
            data = await fetch(
                session,
                f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={crypto_ids}",
            )

            for datum in data:
                await message.channel.send(
                    f"{datum['symbol']}/{datum['name']} - CURRENT ${datum['current_price']}"
                    f" - CHANGE 24hrs ${datum['price_change_24h']}"
                )

        await sleep(MESSAGE_INTERVAL_MINUTES)


bot.run(os.environ.get("BOT_PASSWORD"))

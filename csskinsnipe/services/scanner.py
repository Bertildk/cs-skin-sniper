import os
import random
from datetime import datetime

import requests
import json
import asyncio  # Core Python library for asynchronous programming
import aiohttp  # For making asynchronous HTTP requests
from aiohttp import ClientResponseError
from django.conf import settings
import time

from django.http import JsonResponse

'''
Galil AR | Sandstorm patterns search URL for pirateswap
https://web.pirateswap.com/inventory/ExchangerInventory/groups?orderBy=lowestPrice&sortOrder=DESC&page=1&results=40&pattern=761&pattern=583&pattern=739&pattern=178&pattern=844&pattern=231&pattern=555&pattern=449&pattern=873&pattern=352&pattern=177&pattern=807&pattern=786&pattern=783&pattern=774&priceTo=7.67&searchPhrase=Galil+AR+%7C+Sandstorm&marketHashNameHashCodes=-593427553&marketHashNameHashCodes=-1183325041&marketHashNameHashCodes=-1657302649&marketHashNameHashCodes=-1828659712&marketHashNameHashCodes=-93381993&marketHashNameHashCodes=1230582889&marketHashNameHashCodes=762805584&marketHashNameHashCodes=673331220&itemWithSticker=false
'''


def get_posts(url):
    try:
        response = requests.get(url)

        if response.status_code == 200:
            posts = response.json()
            return posts
        else:
            print('Error:', response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        return None


def construct_url(page, maxPrice):
    """
    Constructs the URL for the given page number.
    """
    return f"https://web.pirateswap.com/inventory/ExchangerInventory?orderBy=price&sortOrder=DESC&page={page}&results=100&priceTo={maxPrice}&itemWithSticker=true"


async def fetch_page(session, url):
    try:
        async with session.get(url) as response:
            print(f"Fetching page: {url}")
            if response.status == 403:
                print(f"Access forbidden for URL: {url}")
                return None
            if response.content_type != 'application/json':
                print(f"Unexpected content type: {response.content_type} for URL: {url}")
                return None
            return await response.json()
    except ClientResponseError as e:
        print(f"Client response error: {e}")
        return None


async def scan_pages_pirateswap(maxPrice, minTotalStickerPrice):
    amount_of_new_items_found = 0
    new_items_found = []
    list_of_all_items_scanned = {}
    last_list_of_skins = load_all_items()
    fetched_urls = []
    start_time = time.time()
    sticker_price_dictionary = load_sticker_price_dictionary()
    skin_sticker_value = {}
    lowest_skin_price = maxPrice
    amount_of_api_calls = 0
    total_items = 0
    empty = False
    amount_of_duplicates = 0

    print("Scanning started, please wait...")
    print(f"{lowest_skin_price}$ lowest skin price at start")
    # Create all fetch tasks
    while empty is False:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for page in range(50):
                url = construct_url(page + 1, lowest_skin_price)
                amount_of_api_calls += 1
                if url not in fetched_urls:
                    fetched_urls.append(url)
                    tasks.append(fetch_page(session, url))
                else:
                    lowest_skin_price -= 0.01

            # Fetch all pages concurrently
            all_pages = await asyncio.gather(*tasks)

        for page in all_pages:
            if page.get('empty', False):
                empty = True
                continue
            all_items_on_page = page.get('items', [])
            for item in all_items_on_page:
                total_items += 1
                sticker_craft = False
                total_sticker_price = 0
                skin_name = item.get('marketHashName', 'Unknown Skin')
                if 'Souvenir' in skin_name:
                    continue
                price = item.get('price', 'N/A')
                stickers = item.get('stickers', [])
                sticker_details = []
                for sticker in stickers:
                    sticker_name = sticker.get('name', 'Unknown Sticker')
                    sticker_price = sticker_price_dictionary.get(sticker_name, 0)
                    total_sticker_price += sticker_price

                    sticker_details.append({
                        "name": sticker_name,
                        "price": sticker_price,
                        "slot": sticker.get('slot', 'N/A')
                    })

                if len(sticker_details) >= 4 and sticker_details[0].get('name') == sticker_details[1].get('name') == \
                        sticker_details[2].get('name') == sticker_details[3].get('name'):
                    sticker_craft = True

                if item['id'] in list_of_all_items_scanned:
                    amount_of_duplicates += 1
                else:
                    skin_key = item['id']
                    list_of_all_items_scanned[skin_key] = {
                        "skin_name": skin_name,
                        "skin_price": price,
                        "total_sticker_price": total_sticker_price,
                        "sticker_value": round(total_sticker_price / price, 2),
                        "stickers": sticker_details,
                        "sticker_craft": sticker_craft
                    }

                if item['id'] not in last_list_of_skins:
                    amount_of_new_items_found += 1
                    new_items_found.append(item['id'])

                try:
                    price = float(price)
                except ValueError:
                    print(f"Price is not a number: {price}")
                    continue

                if price < lowest_skin_price:
                    lowest_skin_price = price

                if total_sticker_price > minTotalStickerPrice:
                    skin_key = item['id']
                    skin_sticker_value[skin_key] = {
                        "skin_name": skin_name,
                        "skin_price": price,
                        "totalStickerPrice": round(total_sticker_price, 2),
                        "stickers": sticker_details,
                        "sticker_value": round(total_sticker_price / price, 2),
                        "sticker_craft": sticker_craft
                    }

    sorted_skin_sticker_value = dict(
        sorted(
            skin_sticker_value.items(),  # Extracts (key, value) pairs
            key=lambda item: item[1]["sticker_value"],  # Sort by "sticker_value" in the value
            reverse=True,  # Optional: Set to True for descending order, False for ascending
        )
    )

    output_data = {"items": sorted_skin_sticker_value}

    with open('csskinsnipe/services/sorted_skins.json', 'w') as json_file:
        json.dump(output_data, json_file, indent=4)
        print("JSON file created: sorted_skins.json")

    with open('csskinsnipe/services/all_items_scanned.json', 'w') as json_file:
        json.dump(list_of_all_items_scanned, json_file, indent=4)
        print("JSON file created: all_items_scanned.json")

    end_time = time.time()
    message = (f"Scan completed at: **{datetime.now().hour}:{datetime.now().minute}**."
               f" Found **{len(sorted_skin_sticker_value)}** skins, with a total sticker price over **{minTotalStickerPrice}**."
               f" Lowest skin price {lowest_skin_price}$."
               f" Maximal skin price {maxPrice}$."
               f" Amount of Api calls made: **{amount_of_api_calls}**, in **{end_time - start_time:.2f}** seconds. ."
               f" Total skins sorted through: **{total_items}**."
               f" Amount of duplicates found: **{amount_of_duplicates}**."
               f" Amount of unique items found: **{len(list_of_all_items_scanned)}**."
               f" Amount of new items found: **{amount_of_new_items_found}**.")
    create_data_entry(amount_of_new_items_found)
    await print_new_items_found(new_items_found)
    return {"message": message}


def create_data_entry(amount_of_new_items_found):
    with open('csskinsnipe/services/data_entries.json', 'r') as json_file:
        try:
            data_entries = json.load(json_file)
        except json.decoder.JSONDecodeError:
            data_entries = []
    data_entries.append({
        "time": f"{datetime.now().hour}:{datetime.now().minute}",
        "amount_of_new_items_found": amount_of_new_items_found
    })
    with open('csskinsnipe/services/data_entries.json', 'w') as json_file:
        json.dump(data_entries, json_file, indent=4)
        print("JSON file created: data_entries.json")


def create_sticker_price_dictionary():
    sticker_price_dictionary = {}
    currentPage = 1
    url = 'https://web.pirateswap.com/inventory/Stickers?orderBy=id&sortOrder=ASC&WithSticker=True&page=' + str(
        currentPage) + '&results=100'
    posts = get_posts(url)
    totalResults = posts.get('totalResults', 'totalResultsNotFound!')
    totalPages = posts.get('totalPages', 'totalPagesNotFound')

    stickers_found = 0

    while currentPage < totalPages:
        url = 'https://web.pirateswap.com/inventory/Stickers?orderBy=id&sortOrder=ASC&WithSticker=True&page=' + str(
            currentPage) + '&results=100'
        posts = get_posts(url)

        currentPage += 1
        for index, sticker in enumerate(posts.get('items')):
            sticker_price = sticker.get('price', 'N/A')
            if sticker_price is None:
                continue
            else:
                stickers_found += 1
                sticker_name = sticker.get('name', 'Unknown name')
                cleaned_sticker_name = sticker_name.replace("Sticker | ", "")

                sticker_price_dictionary[cleaned_sticker_name] = sticker_price
                # print(f"Sticker name: {cleaned_sticker_name}, Sticker price: {sticker_price}")
                # print(sticker_price_dictionary.get(sticker_name))

    print(
        f"Current page: {currentPage}, Total pages: {totalPages}, Total stickers: {totalResults}, Stickers found with Prices: {stickers_found}")

    output_data = {"items": sticker_price_dictionary}

    with open('sticker_prices.json', 'w') as json_file:
        json.dump(sticker_price_dictionary, json_file, indent=4)
        print("JSON file created: sticker_prices.json")


def load_sticker_price_dictionary():
    with open(os.path.join(settings.BASE_DIR, 'csskinsnipe/services/sticker_prices.json'), 'r') as json_file:
        sticker_price_dictionary = json.load(json_file)
    return sticker_price_dictionary


def load_sorted_skins():
    print("Loading started")
    with open(os.path.join(settings.BASE_DIR, 'csskinsnipe/services/sorted_skins.json'), 'r') as json_file:
        sorted_skins = json.load(json_file)
    return sorted_skins


def load_all_items():
    with open(os.path.join(settings.BASE_DIR, 'csskinsnipe/services/all_items_scanned.json'), 'r') as json_file:
        all_items = json.load(json_file)
    return all_items


async def print_new_items_found(new_items_found):
    from csskinsnipe.services.discord_bot import alert_new_item
    all_items = load_all_items()
    for item in new_items_found:

        skin = all_items.get(item)
        if ((skin.get('sticker_value') >= 10 and skin.get(item).get('skin_price') >= 3) or
                (skin.get('sticker_craft') and skin.get('sticker_value') >= 1.5 and skin.get('skin_price') >= 3)):
            message = create_msg(skin)
            await alert_new_item(message)


def create_msg(skin):
    message = (f"New item found: **{skin.get('skin_name')}**\n"
               f"Skin price: **{skin.get('skin_price')}$**\n"
               f"Total sticker price: **{skin.get('total_sticker_price')}$**\n"
               f"Sticker value: **{skin.get('sticker_value')}**\n")
    for sticker in skin.get('stickers'):
        message += f"   -{sticker['name']}, **{sticker['price']}**$\n"
    return message

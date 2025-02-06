import asyncio
import threading
from datetime import datetime
import json
import geocoder
import requests
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from csskinsnipe.services import scanner
from csskinsnipe.services.discord_bot import alert_users, client, run_discord_bot
import time

# Create your views here.
threading.Thread(target=run_discord_bot).start()


def main(request):
    template = loader.get_template("index.html")
    return HttpResponse(template.render({}, request))


@csrf_exempt
async def scan(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        maxPrice = int(data.get('maxPrice', 1000))
        minTotalStickerPrice = int(data.get('minTotalStickerPrice', 1))
        result = await scanner.scan_pages_pirateswap(maxPrice, minTotalStickerPrice)
        print(result.get("message"))
        return JsonResponse({"status": "success", "message": result.get("message")}, status=200)
    return JsonResponse({"status": "failed"}, status=400)


@csrf_exempt
async def discord_notify(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        await alert_users(data.get('message'))
        return JsonResponse({"status": "success"}, status=200)
    return JsonResponse({"status": "failed"}, status=400)


def refresh(request):
    try:
        print("Refreshing skins")
        sorted_skins = scanner.load_sorted_skins()
        return JsonResponse(sorted_skins, safe=False)
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"status": "failed"}, status=400)

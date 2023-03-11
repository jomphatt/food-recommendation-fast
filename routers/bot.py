import os
import random
from dotenv import load_dotenv, find_dotenv

# FastAPI
from fastapi import APIRouter, Depends, HTTPException, Request, Header

# Line-Bot SDK
from linebot import *
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextMessage, MessageEvent, TextSendMessage, StickerMessage, \
    StickerSendMessage, ImageMessage, FlexSendMessage

router = APIRouter(
    prefix="/bot",
    tags=["bot"],
    responses={404: {"description": "Not found"}}
)

# Load .env variables
load_dotenv(find_dotenv())

# Initiate LineBot & Webhook
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))

# List of all menus
menu_file = open("../menus.txt", "r")
menu_list = menu_file.readlines()

# One flex message's template
flex_template = """{
    "type": "bubble",
    "hero": {
        "type": "image",
        "url": "{menu_image}",
        "size": "full",
        "aspectRatio": "20:13",
        "aspectMode": "cover"
    },
    "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": "{menu_name}",
                "weight": "bold",
                "size": "xl"
            },
            {
                "type": "box",
                "layout": "vertical",
                "margin": "lg",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "box",
                        "layout": "baseline",
                        "spacing": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": "Calorie",
                                "color": "#aaaaaa",
                                "size": "md",
                                "flex": 2
                            },
                            {
                                "type": "text",
                                "text": "{menu_calorie}",
                                "wrap": True,
                                "color": "#666666",
                                "size": "md",
                                "flex": 5
                            }
                        ]
                    }
                ]
            }
        ]
    }
}"""


@router.get("/")
async def root_bot():
    return {'message': 'Root Bot'}

@router.post("/callback")
async def callback(request: Request, x_line_signature=Header(None)):
    body = await request.body()
    print(body)
    try:
        handler.handle(body.decode("utf-8"), x_line_signature)

    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="InvalidSignatureError")

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    print(event)
    if event.message.text == "Give me food recommendations.":
        recommended_menus = random.sample(menu_list, 5) # Replace this with an actual code for recommendation model
        content = []
        for rm in recommended_menus:
            menu_flex = flex_template.format(
                menu_image = "https://en.wikipedia.org/wiki/Pikachu#/media/File:Pok%C3%A9mon_Pikachu_art.png", 
                menu_name = rm, 
                menu_calorie = 500
            )
            content.append(menu_flex)
        flex_message = FlexSendMessage(
            alt_text='recommended_menus',
            contents={
                "type": "carousel",
                "contents": content
            }
        )
        line_bot_api.reply_message(
            event.reply_token,
            flex_message
        )
    else:
        pass

@handler.add(MessageEvent, message=StickerMessage)
def sticker_text(event):
    # Judge condition
    line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(package_id='6136', sticker_id='10551379')
    )

@handler.add(MessageEvent, message=ImageMessage)
def sticker_text(event):
    pass


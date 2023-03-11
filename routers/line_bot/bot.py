import os
import random
import json
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
menu_file = open("./menus.txt", "r")
menu_list = menu_file.readlines()


def get_template(menu_image: str, menu_name: str, menu_calorie: str) -> dict:
    return (
        {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": menu_image,
            "size": "full",
            "aspectRatio": "3:4",
            "aspectMode": "cover"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": menu_name,
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
                                    "text": menu_calorie,
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
    }
    )


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
        # Replace this with an actual code for recommendation model
        recommended_menus = random.sample(menu_list, 5)
        content = []
        for rm in recommended_menus:
            menu_flex = get_template(
                menu_image="https://thumbs.dreamstime.com/b/people-eating-healthy-meals-wooden-table-top-view-food-delivery-people-eating-healthy-meals-wooden-table-food-delivery-160387494.jpg",
                menu_name=rm,
                menu_calorie=str(500)
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

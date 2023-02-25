import os
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
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )

@handler.add(MessageEvent, message=StickerMessage)
def sticker_text(event):
    # Judge condition
    line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(package_id='6136', sticker_id='10551379')
    )

@handler.add(MessageEvent, message=ImageMessage)
def sticker_text(event):
    flex_message = FlexSendMessage(
        alt_text='hello',
        contents={
            "type": "carousel",
            "contents": [
                {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "text",
                        "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
                        "wrap": True
                    }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                        "type": "uri",
                        "label": "Go",
                        "uri": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_1_cafe.png"
                        }
                    }
                    ]
                }
                },
                {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "text",
                        "text": "Hello, World!",
                        "wrap": True
                    }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                        "type": "uri",
                        "label": "Go",
                        "uri": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_1_cafe.png"
                        }
                    }
                    ]
                }
                }
            ]
        }
    )
    line_bot_api.reply_message(
        event.reply_token,
        flex_message
    )


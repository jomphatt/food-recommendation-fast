import os
import random
import string
import requests
import pandas as pd
from dotenv import load_dotenv, find_dotenv

# FastAPI
from fastapi import APIRouter, Depends, HTTPException, Request, Header

# Line-Bot SDK
from linebot import *
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, StickerMessage, \
    ImageMessage, StickerSendMessage, TextSendMessage, FlexSendMessage
    
# Import food recognition class
from routers.line_bot.food_recognition import FoodRecognition

# Import Firebase Storage class
from routers.line_bot.firebase_storage import FirebaseStorage


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

firebase_storage = FirebaseStorage()
food_recognition = FoodRecognition()

# List of all menus
# menu_file = open("./assets/menus.txt", "r")
# menu_list = menu_file.readlines()
menu_df = pd.read_csv("./assets/menus.csv")
menu_ids = menu_df["id"].values.tolist()

BASE_DB_URL = "https://22c6-2405-9800-bc00-15b4-830-190b-c10d-5dd.ap.ngrok.io/"
MENU_DB_URL = BASE_DB_URL + "menus/"


def get_template(menu_image: str, menu_name: str, menu_calorie: str) -> dict:
    return (
        {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": menu_image,
            "size": "full",
            "aspectRatio": "10:9",
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
                    "size": "xl",
                    "wrap": True
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
        # recommended_menus = random.sample(menu_list, 5)
        recommended_menu_ids = random.sample(menu_ids, 5)
        r = requests.get(MENU_DB_URL)
        menu_db = r.json()
        contents = []
        for rm_id in recommended_menu_ids:
            img_url = firebase_storage.get_image_urls(f"flex_images/{rm_id}.jpeg")
            # menu = menu_df[menu_df['id'] == rm_id]
            # menu_calorie = menu['calorie'].values[0]
            # menu_name = menu['name'].values[0]
            menu = menu_db[str(rm_id)]
            menu_calorie = menu['calorie']
            menu_name = menu['name']
            
            menu_flex = get_template(
                menu_image=img_url,
                menu_name=string.capwords(menu_name),
                menu_calorie=str(int(menu_calorie))
            )
            contents.append(menu_flex)
        flex_message = FlexSendMessage(
            alt_text='Check out our recommended menus!',
            contents={
                "type": "carousel",
                "contents": contents
            }
        )
        line_bot_api.reply_message(
            event.reply_token,
            flex_message
        )
    else:
        pass

  
@handler.add(MessageEvent, message=ImageMessage)
def image_text(event):
    
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    
    img_path = f"./assets/inputs/{message_id}.jpg"
    with open(img_path, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)

    prediction = food_recognition.predict(img_path)
    # menu = menu_df[menu_df['id'] == rm]
    # menu_calorie = menu['calorie'].values[0]
    # menu_name = menu['name'].values[0]
    firebase_storage.upload_retrain_image(prediction, img_path)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=prediction) 
    )
    
    if os.path.exists(img_path):
        os.remove(img_path)
    else:
        print("The file does not exist.")


@handler.add(MessageEvent, message=StickerMessage)
def sticker_text(event):
    pass


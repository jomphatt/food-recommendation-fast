# Import general libraries
import os
import random
import string
import requests
import pandas as pd
from dotenv import load_dotenv, find_dotenv

# Import FastAPI
from fastapi import APIRouter, Depends, HTTPException, Request, Header

# Import LINE Messaging API SDK
from linebot import *
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, StickerMessage, \
    ImageMessage, StickerSendMessage, TextSendMessage, FlexSendMessage

# Import custom classes
from routers.line_bot.food_recommendation import FoodRecommendation
from routers.line_bot.food_recognition import FoodRecognition
from routers.line_bot.firebase_storage import FirebaseStorage


# Load environment variables
load_dotenv(find_dotenv())

# Declare LINE bot and webhook
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))

# Declare database URLs
# TODO: 
# Put the databases in a directory, e.g. /databases/menus. 
# And put the base URL in .env.
BASE_DB_URL = "https://c6b0-171-98-30-190.ap.ngrok.io/"
MENU_DB_URL = BASE_DB_URL + "menus/"
ORDER_DB_URL = BASE_DB_URL + "orders/"
USER_DB_URL = BASE_DB_URL + "users/"

# Declare LINE bot API router
router = APIRouter(
    prefix="/bot",
    tags=["bot"],
    responses={404: {"description": "Not found"}}
)

# Declare custom classes
firebase_storage = FirebaseStorage()
food_recognition = FoodRecognition()


# TODO:
# Replace the codes that randoms recommended menus with the food recommendation model
# and move the function to a new class named "FoodRecommendation".
def recommend_menus() -> list:
    """Recommend menus.

    Returns:
        recommended_menus (list): List of recommended menus. Each menu is a dictionary.
    """
    r = requests.get(MENU_DB_URL)
    menu_db = r.json()
    menu_ids = [id for id in menu_db.keys()]
    recommended_menu_ids = random.sample(menu_ids, 5)
    recommended_menus = [menu_db[id] for id in recommended_menu_ids]
    return recommended_menus

def create_menu_bubble(menu_image_url: str, menu_name: str, menu_calorie: str) -> dict:
    """Create a bubble message of a menu to be added to a carousel.

    Args:
        menu_image_url (str): Firebase URL of the menu image.
        menu_name (str): Menu name.
        menu_calorie (str): Menu calorie.

    Returns:
        menu_bubble (dict): Bubble message of a menu.
    """
    
    menu_bubble = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": menu_image_url,
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
    
    return menu_bubble

def create_menu_carousel(menus: list) -> dict:
    """Create a carousel message of menus.

    Args:
        menus (list): List of menus. Each menu is a dictionary.

    Returns:
        menu_carousel (dict): Carousel message of menus.
    """
    menu_carousel = []
    for menu in menus:
        menu_id = list(menu.keys())[0]
        menu_image_url = firebase_storage.get_image_urls(f"flex_images/{menu_id}.jpeg")
        menu_calorie = menu[menu_id]['calorie']
        menu_name = menu[menu_id]['name']
        
        menu_bubble = create_menu_bubble(
            menu_image_url=menu_image_url,
            menu_name=string.capwords(menu_name),
            menu_calorie=str(int(menu_calorie))
        )
        menu_carousel.append(menu_bubble)
        
    return menu_carousel


@router.get("/")
async def root():
    reponse = {"message": "OK"}
    return reponse


@router.post("/callback")
async def callback(request: Request, x_line_signature=Header(None)):
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), x_line_signature)
    
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="InvalidSignatureError")
    response = {"message": "OK"}
    return response


@handler.add(MessageEvent, message=TextMessage)
def text_message(event):
    """Handle text messages, including requests for food recommendations sent by users.

    Args:
        event (MessageEvent): LINE text message event.
    """
    if event.message.text == "Give me food recommendations.":
        # Get a list of recommended menus
        recommended_menus = recommend_menus()
        
        # Create a carousel message of recommended menus
        menu_carousel = create_menu_carousel(recommended_menus)
        
        # Send the carousel message to the user
        flex_message = FlexSendMessage(
            alt_text='Check out our recommended menus!',
            contents={
                "type": "carousel",
                "contents": menu_carousel
            }
        )
        line_bot_api.reply_message(
            event.reply_token, 
            flex_message
        )
    else:
        pass

  
@handler.add(MessageEvent, message=ImageMessage)
def image_message(event):
    """Handle image messages by recognizing the menu of the food in the image.

    Args:
        event (MessageEvent): LINE image message event.
    """
    
    # Save the image to the local storage
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    img_path = f"./assets/inputs/{message_id}.jpg"
    with open(img_path, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)

    # Check if the image contains food
    is_food = food_recognition.is_food(img_path)
    if is_food:
        # Recognize the menu
        prediction = food_recognition.recognize_menu(img_path)
        
        # Upload the image to Firebase Storage for retraining
        # firebase_storage.upload_retrain_image(prediction, img_path)
        
        # Send the prediction to the user
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=prediction) 
        )
    else:
        # Send a warning message to the user
        # TODO: Modify the warning message
        warning_msg = "The image does not contain food."
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=warning_msg) 
        )

    # Delete the image from the local storage
    if os.path.exists(img_path):
        os.remove(img_path)
    else:
        print(f'The image path "{img_path}" does not exist.')


@handler.add(MessageEvent, message=StickerMessage)
def sticker_message(event):
    pass


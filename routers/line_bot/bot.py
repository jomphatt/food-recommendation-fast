# Import general libraries
import io
import os
import string
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from datetime import datetime

# Import FastAPI
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import FileResponse

# Import LINE Messaging API SDK
from linebot import *
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, StickerMessage, \
    ImageMessage, StickerSendMessage, TextSendMessage, FlexSendMessage

# Import custom classes
from routers.line_bot.food_recommendation import FoodRecommendation
from routers.line_bot.food_recognition import FoodRecognition
from routers.line_bot.firebase_storage import FirebaseStorage

# Import database 
import database
import routers.menu.crud as menu_crud
import routers.order.crud as order_crud
import routers.user.crud as user_crud
import routers.user_feature.crud as user_feature_crud


# Load environment variables
load_dotenv(find_dotenv())

# Declare LINE bot and webhook
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))

# Declare LINE bot API router
router = APIRouter(
    prefix="/bot",
    tags=["bot"],
    responses={404: {"description": "Not found"}}
)

# Declare custom classes
food_recommendation = FoodRecommendation()
food_recognition = FoodRecognition()
firebase_storage = FirebaseStorage()

# Initialize database session
db = database.SessionLocal()


# TODO: (OPTIONAL) Add a store number to the menu table
def __create_menu_bubble(menu: any) -> dict:
    """Create a bubble message of a menu to be added to a carousel."""
    
    # Declare menu name and selected attributes
    menu_name = menu.name
    selected_attrs = ['calorie', 'protein', 'fat', 'carbohydrate']
    
    # TODO: Get the image URL from our API endpoint of Firebase Storage
    # Get menu image URL from Firebase Storage
    menu_image_url = firebase_storage.get_image_urls(f"flex_images/{menu.id}.jpg")

    # Create menu nutrition contents to be added to the bubble
    menu_nutrition_contents = []
    for attr in selected_attrs:
        
        if attr == 'calorie':
            unit = 'kcal'
        else:
            unit = 'g'
        
        menu_nutrition_contents.append(
            {
                "type": "box",
                "layout": "baseline",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": f"{string.capwords(attr)} ({unit})",
                        "color": "#111111",
                        "size": "sm",
                        "flex": 4
                    },
                    {
                        "type": "text",
                        "text": str(getattr(menu, attr)),
                        "wrap": True,
                        "color": "#555555",
                        "size": "sm",
                        "flex": 1
                    }
                ]
            }
        )
    
    menu_bubble = {
        "type": "bubble",
        "size": "kilo",
        "hero": {
            "type": "image",
            "url": menu_image_url,
            "size": "full",
            "aspectRatio": "4:3",
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
                    "size": "lg",
                    "wrap": True
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "sm",
                    "contents": menu_nutrition_contents
                }
            ]
        }
    }
    
    return menu_bubble

def create_menu_carousel(menus: list) -> dict:
    """Create a carousel message of menus."""
    
    bubbles = []
    for menu in menus:
        
        # Create a bubble message of a menu
        bubble = __create_menu_bubble(menu=menu)
        
        # Add the bubble message to the carousel
        bubbles.append(bubble)
    
    menu_carousel = {
        "type": "carousel",
        "contents": bubbles
    }
        
    return menu_carousel

def create_recognition_bubble(menu: any) -> dict:
    """Create a bubble message of a menu to be returned as a recognition result."""
    
    # Create a bubble message of a menu
    menu_bubble = __create_menu_bubble(menu=menu)
    
    # Add a footer that receives a feedback from the user to the bubble message
    menu_bubble['footer'] = {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "contents": [
            {
                "type": "button",
                "style": "primary",
                "height": "sm",
                "action": {
                    "type": "message",
                    "label": "Correct",
                    "text": "Yes, the prediction is correct."
                }
            },
            {
                "type": "button",
                "style": "secondary",
                "height": "sm",
                "action": {
                    "type": "message",
                    "label": "Incorrect",
                    "text": "No, the prediction is not correct." # TODO: Change type to uri and add a "uri" key with the value of the LIFF URL
                }
            }
        ]
    }
    
    recognition_bubble = menu_bubble
    
    return recognition_bubble

def create_daily_summary_bubble(daily_summary: dict) -> dict:
    """Create a bubble message of the daily summary.

    Returns:
        daily_summary_bubble (dict): Bubble message of the daily summary.
    """

    if len(daily_summary) == 0:
        daily_summary_bubble = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "EATWISE",
                        "weight": "bold",
                        "color": "#1DB446",
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": "NUTRITION SUMMARY",
                        "weight": "bold",
                        "size": "xl",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "Summary of nutrient consumed since start of day",
                        "size": "xxs",
                        "color": "#aaaaaa",
                        "wrap": True
                    },
                    {
                        "type": "separator",
                        "margin": "xxl"
                    },
                    {
                        "type": "text",
                        "text": "No order history has been found. Please order a menu first.",
                        "weight": "regular",
                        "size": "md",
                        "margin": "md",
                        "wrap": True
                    }
                ]
            },
            "styles": {
                "footer": {
                    "separator": True
                }
            }
        }
    
        return daily_summary_bubble

    # Count the number of each menu in the menu IDs of the daily summary
    set_menu_id = daily_summary["set_menu_id"]

    menu_count = {}
    for menu_id in set_menu_id:
        if menu_id in menu_count:
            menu_count[menu_id] += 1
        else:
            menu_count[menu_id] = 1

    # Initialize the contents of the order history with the headers
    order_history_contents = [
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": "Menu",
                    "size": "sm",
                    "color": "#111111",
                    "flex": 4,
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": "Calorie",
                    "size": "sm",
                    "color": "#555555",
                    "align": "end",
                    "flex": 1,
                    "weight": "bold"
                }
            ]
        }
    ]
    
    # Add order template of each menu to the order history contents
    for menu_id in menu_count:
        
        menu = menu_crud.get_menu(db, menu_id=menu_id)
        menu_quantity = menu_count[menu_id]

        order_template = {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": f"{menu_quantity}x {menu.name}",
                    "size": "sm",
                    "color": "#111111",
                    "flex": 4,
                    "wrap": True
                },
                {
                    "type": "text",
                    "text": str(menu.calorie * menu_quantity),
                    "size": "sm",
                    "color": "#555555",
                    "align": "end",
                    "flex": 1
                }
            ]
        }
        order_history_contents.append(order_template)
    
    # Loop through nutrient attributes to create the nutrient contents
    nutrient_contents = []
    for attr in daily_summary:
        
        if attr == 'set_menu_id':
            title = 'Meals'
            value = str(len(daily_summary[attr]))
        else:
            title = string.capwords(attr.replace('_', ' '))
            unit = 'kcal' if attr == 'total_calorie' else 'g'
            title = f'{title} ({unit})'
            value = str(daily_summary[attr])
        
        weight = 'bold' if attr == 'total_calorie' else 'regular'
            
        nutrient_contents.append(
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": title,
                        "size": "sm",
                        "color": "#111111",
                        "weight": weight,
                        "flex": 4
                    },
                    {
                        "type": "text",
                        "text": value,
                        "size": "sm",
                        "color": "#555555",
                        "align": "end",
                        "weight": weight,
                        "flex": 1
                    }
                ]
            }
        )   
    
    daily_summary_bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "EATWISE",
                    "weight": "bold",
                    "color": "#1DB446",
                    "size": "sm"
                },
                {
                    "type": "text",
                    "text": "NUTRITION SUMMARY",
                    "weight": "bold",
                    "size": "xl",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "Summary of nutrient consumed since start of day",
                    "size": "xxs",
                    "color": "#aaaaaa",
                    "wrap": True
                },
                {
                    "type": "separator",
                    "margin": "xxl"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "xxl",
                    "spacing": "sm",
                    "contents": order_history_contents
                },
                {
                    "type": "separator",
                    "margin": "xxl"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "xxl",
                    "spacing": "sm",
                    "contents": nutrient_contents  
                }
            ]
        },
        "styles": {
            "footer": {
                "separator": True
            }
        }
    }
    
    return daily_summary_bubble

# TODO: Implement this function instead of using "get_image_url" function of Firebase Storage, 
# so we can get the image URL directly from our API endpoint instead of Firebase Storage
def get_flex_image_url(menu_id: int) -> str:
    flex_image_url = f"https://OUR-AZURE-DOMAIN/assets/images/flex_images/{menu_id}.jpg" #TODO: Change the domain 
    return flex_image_url

def handle_unregistered_user_event(event: any):

    # Get database connection from global variable
    global db
    global line_bot_api

    # Get user state by LINE ID
    line_user_id = event.source.user_id
    user_state = user_crud.get_user_state_by_line_id(db=db, line_id=line_user_id)

    # If user state is not found which means the user has not registered yet, send a message to ask the user to register first.
    if user_state:
        text_message = TextSendMessage(
            text='EatWise could not find your account. Please register by pushing the "EATWISE PROFILE" button in the rich menu.'
        )
        line_bot_api.reply_message(
            event.reply_token, 
            text_message
        )
        return user_state

    return user_state

def get_meal():
    current_hour = datetime.now().hour
    if current_hour >= 3 and current_hour < 11:
        return 'breakfast'
    elif current_hour >= 11 and current_hour < 17:
        return 'lunch'
    elif current_hour >= 17 or current_hour < 3:
        return 'dinner'


@router.get("/")
async def root():
    reponse = {"message": "OK"}
    return reponse

@router.get("/assets/images/flex_images/{image_name}")
async def get_flex_image(image_name: str):
    image_path = Path(f"assets/images/flex_images/{image_name}")
    if image_path.is_file():
        response = FileResponse(image_path)
    else:
        response = {"error": "Image not found"}
    return response

@router.post("/callback")
async def callback(request: Request, x_line_signature=Header(None)):
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), x_line_signature)
    
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="InvalidSignatureError")
    response = {"message": "OK"}
    return response

@router.post("/recognition_feedback")
async def recognition_feedback(request: Request):
    
    # Get LINE ID, then use it to get user state
    body = await request.body()
    body = body.decode("utf-8")
    line_user_id = body["line_user_id"]
    user_state = user_crud.get_user_state_by_line_id(line_id=line_user_id)
    
    # # Check state of user
    # if user_state == 'TODO: FILL THE CORRECT STATE HERE.':
    #     pass
    # else:
    #     return
    
    # correct_class = body
    
    return


@handler.add(MessageEvent, message=TextMessage)
def text_message(event):
    """Handle text messages, including requests for food recommendations sent by users.

    Args:
        event (MessageEvent): LINE text message event.
    """

    # Handle unregistered user event, get user state, and return if user does not exist
    user_state = handle_unregistered_user_event(event=event)
    if not user_state:
        return

    if event.message.text == "Give me food recommendations.":

        # If user state is "start", the user has not requested for food recommendations yet.
        if user_state == "start":
            # User features
            users = user_crud.get_users(db=db)
            user_preferences = user_feature_crud.get_user_features_flag(db=db)

            # Food features
            menu_features = menu_crud.get_menu_features(db=db)

            # Interaction Matrix
            interaction_matrix = order_crud.get_orders(db=db)

            # Get food nutrition data
            nutritional_data = menu_crud.get_menus_for_recommendation(db=db)

            # Nutritional goal left
            line_user_id = event.source.user_id
            user_id = [user.id for user in users if user.line_id == line_user_id][0]

            # Retrieve summarized nutrition values from the database
            query_result = order_crud.get_daily_summary(db=db, user_id=user_id)

            # Check if there is any order history since start of day
            if len(query_result) == 0:
                daily_summary = {}
            else:
                # Store result in dictionary
                daily_summary = {
                    "Protein": query_result[0][1],
                    "Carbs": query_result[0][2],
                    "Fat": query_result[0][3],
                    "Calories": query_result[0][4]
                }

            nutritional_goal_left = {
                "Protein": 50 - daily_summary["Protein"],
                "Carbs": 300 - daily_summary["Carbs"],
                "Fat": 70 - daily_summary["Fat"],
                "Calories": 2000 - daily_summary["Calories"]
            }

            # Previous food 
            previous_food = order_crud.get_lastest_order(db=db, user_id=user_id)

            # Meal time
            meal_time = get_meal()

            
            
            
            # Get a list of recommended menus
            recommended_menus = food_recommendation.recommend_menus()
            # print(food_recommendation.get_food_features())
            
            # Create a carousel message of recommended menus
            menu_carousel = create_menu_carousel(menus=recommended_menus)

            # Prepare messages to be sent to the user
            flex_message = FlexSendMessage(
                alt_text='Check out our recommended menus!',
                contents=menu_carousel
            )
            text_message = TextSendMessage(
                text='Here are our recommended menus for you! Once you have ordered your food, please take a picture of it and send it to us.'
            )

            # Send reply messages to the user
            line_bot_api.reply_message(
                event.reply_token, 
                [flex_message, text_message]
            ) 

            # Update user state
            user_crud.update_user_state_by_line_id(
                db=db,
                line_id=event.source.user_id,
                state="recommendation_sent"
            )

        else:
            
            # Send an error message when the user has already requested for food recommendations for the next meal
            error_message = TextSendMessage(
                text='You have already requested for food recommendations for your next meal. Please take a picture of your food and send it to us.'
            )
            line_bot_api.reply_message(
                event.reply_token, 
                error_message
            )
            
    elif event.message.text == "Give me a nutrition summary.":
        
        # Get user ID from LINE user ID
        line_user_id = event.source.user_id
        user_id = user_crud.get_user_by_line_id(db=db, line_id=line_user_id).id
        
        # Retrieve summarized nutrition values from the database
        query_result = order_crud.get_daily_summary(db=db, user_id=user_id)
        
        # Check if there is any order history since start of day
        if len(query_result) == 0:
            daily_summary = {}
        else:
            # Store result in dictionary
            daily_summary = {
                "set_menu_id": query_result[0][0],
                "total_protein": query_result[0][1],
                "total_carbohydrate": query_result[0][2],
                "total_fat": query_result[0][3],
                "total_calorie": query_result[0][4]
            }
    
        # Create a bubble message of the daily summary
        daily_summary_bubble = create_daily_summary_bubble(daily_summary=daily_summary)
        flex_message = FlexSendMessage(
            alt_text='Check out your today nutrition summary!',
            contents=daily_summary_bubble
        )

        # Send the flex message to the user
        line_bot_api.reply_message(
            event.reply_token, 
            flex_message
        )

    else:
        # Send an error message when message is not recognized
        error_message = TextSendMessage(
            text='Sorry, EatWise does not understand what you mean. Please interact with me via rich menu or flex messages.'
        )
        line_bot_api.reply_message(
            event.reply_token, 
            error_message
        )
        

@handler.add(MessageEvent, message=ImageMessage)
def image_message(event):
    """Handle image messages by recognizing the menu of the food in the image.

    Args:
        event (MessageEvent): LINE image message event.
    """

    # Handle unregistered user event, get user state, and return if user does not exist
    user_state = handle_unregistered_user_event(event=event)
    if not user_state:
        return
    
    # 
    if user_state == "recommendation_sent":

        # Get the image content
        message_id = event.message.id
        message_content = line_bot_api.get_message_content(message_id)

        # TODO: Delete the code block below after testing firebase_storage.upload_preprocessed_image()
        # # Save the image to the local storage
        # img_path = f"./assets/inputs/{message_id}.jpg"
        # with open(img_path, 'wb') as fd:
        #     for chunk in message_content.iter_content():
        #         fd.write(chunk)

        # Save image as a byte array
        img_byte = io.BytesIO(message_content.content)

        # Check if the image contains food
        is_food = food_recognition.is_food(img_byte)
        if is_food:
            # Recognize the menu
            predicted_menu_id = food_recognition.recognize_menu(img_byte)
            predicted_menu = menu_crud.get_menu(db=db, menu_id=predicted_menu_id)
            
            # TODO:
            # 1. Save the preprocessed image to Firebase Storage in a folder named "uncategorized" where the image name is f"{USER ID}_{UUID or TIMESTAMP}.jpg".
            # 2. Include the menu ID in the postback data of the "Correct" button in recognition bubble.
            # 3. Create a postback event handler. Also send a message back to the user once a postback event is received.
            # 4. Once received a postback event, categorize the image uploaded in step 1.
            # 5. Apply the same approach with the "Incorrect" button. But we have to create a router instead of a postback event handler.

            # Create a bubble message of the recognized menu
            recognition_bubble = create_recognition_bubble(menu=predicted_menu)
            
            # Create a flex message of the recognized menu
            flex_message = FlexSendMessage(
                alt_text='Check out the menu prediction by EatWise!',
                contents=recognition_bubble
            )
            
            # Send the flex message containing the prediction bubble to the user
            line_bot_api.reply_message(
                event.reply_token, 
                flex_message
            )

            # Update user state
            user_crud.update_user_state_by_line_id(
                db=db,
                line_id=event.source.user_id,
                state="menu_recognized"
            )

        else:
            # Send an error message when the bot cannot detect food in the image
            error_message = "EatWise cannot detect food in the image. Please try again."
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=error_message) 
            )

        # TODO: Delete the code block below after testing firebase_storage.upload_preprocessed_image()
        # # Delete the image from the local storage
        # if os.path.exists(img_path):
        #     os.remove(img_path)
        # else:
        #     print(f'The image path "{img_path}" does not exist.')
    
    else:
        # Send an error message when the user sends an image at the wrong state
        error_message = TextSendMessage(
            text='Sorry. It seems like you have not requested for food recommendations for your next meal. Please push the "RECOMMEND" button in the rich menu.'
        )
        line_bot_api.reply_message(
            event.reply_token, 
            error_message
        )


@handler.add(MessageEvent, message=StickerMessage)
def sticker_message(event):
    pass


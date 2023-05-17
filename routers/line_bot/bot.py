# Import general libraries
import io
import os
import json
import string
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timedelta
from scipy.sparse import csr_matrix, hstack
from sklearn.preprocessing import MinMaxScaler
import pandas as pd

# Import FastAPI
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import FileResponse

# Import LINE Messaging API SDK
from linebot import *
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextMessage, ImageMessage, StickerMessage, \
    TextSendMessage, FlexSendMessage, StickerSendMessage, \
    MessageEvent, PostbackEvent

# Import custom classes
from routers.line_bot.food_recommendation import FoodRecommendation
from routers.line_bot.food_recognition import FoodRecognition
from routers.line_bot.firebase_storage import FirebaseStorage
from schemas import OrderCreate

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
                    "type": "postback",
                    "label": "Correct",
                    "data": f"{{\"is_correct\":true,\"menu_id\":{menu.id}}}",
                    "displayText": "Yes, the prediction is correct."
                }
            },
            {
                "type": "button",
                "style": "secondary",
                "height": "sm",
                "action": {
                    "type": "uri",
                    "label": "Incorrect",
                    "uri": "https://liff.line.me/1660664500-JQB11po2/foods"
                }
            }
        ]
    }
    
    recognition_bubble = menu_bubble
    
    return recognition_bubble

def create_rating_bubble(menu_id: int) -> dict:
    """Create a rating bubble message to be returned after a recognition result."""

    rating_bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "Let's rate your food!",
                    "weight": "bold",
                    "size": "lg",
                    "align": "start"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "1",
                                "data": f"{{\"menu_id\":{menu_id},\"rating\":1}}",
                                "displayText": "1"
                            },
                            "style": "primary",
                            "color": "#A6E3D6",
                            "height": "md"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "2",
                                "data": f"{{\"menu_id\":{menu_id},\"rating\":2}}",
                                "displayText": "2"
                            },
                            "style": "primary",
                            "color": "#7BCEB8"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "3",
                                "data": f"{{\"menu_id\":{menu_id},\"rating\":3}}",
                                "displayText": "3"
                            },
                            "style": "primary",
                            "color": "#50B99A"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "4",
                                "data": f"{{\"menu_id\":{menu_id},\"rating\":4}}",
                                "displayText": "4"
                            },
                            "style": "primary",
                            "color": "#0E8A6A"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "5",
                                "data": f"{{\"menu_id\":{menu_id},\"rating\":5}}",
                                "displayText": "5"
                            },
                            "style": "primary",
                            "color": "#06C755"
                        }
                    ],
                    "spacing": "sm",
                    "margin": "md"
                }
            ]
        }
    }
    
    return rating_bubble

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

    # Get user state by LINE ID
    line_user_id = event.source.user_id
    user_state = user_crud.get_user_state_by_line_id(db=db, line_id=line_user_id)

    # If user state is not found which means the user has not registered yet, send a message to ask the user to register first.
    if not user_state:
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
    current_time_utc = datetime.utcnow()
    current_time_gmt_7 = current_time_utc + timedelta(hours=7)
    current_hour = current_time_gmt_7.hour
    
    if current_hour >= 3 and current_hour < 11:
        return 'Breakfast'
    elif current_hour >= 11 and current_hour < 17:
        return 'Lunch'
    elif current_hour >= 17 or current_hour < 3:
        return 'Dinner'


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

@router.get("/nutrition_summary/{line_id}")
async def nutrition_summary_by_line_id(line_id: str):
    
    user_id = (user_crud.get_user_by_line_id(db=db, line_id=line_id)).id
    query_result = order_crud.get_daily_summary(db=db, user_id=user_id)
    
    if query_result:
        nutrition_summary = {
            "total_protein": query_result[0][1],
            "total_carbohydrate": query_result[0][2],
            "total_fat": query_result[0][3],
            "total_calorie": query_result[0][4]
        }
    else:
        nutrition_summary = {
            "total_protein": 0.0,
            "total_carbohydrate": 0.0,
            "total_fat": 0.0,
            "total_calorie": 0.0
        }
    
    return nutrition_summary

@router.get("/top_menus_by_user/{line_id}")
async def top_menus_by_user(line_id: str):
    
    user_id = (user_crud.get_user_by_line_id(db=db, line_id=line_id)).id    
    query_result = order_crud.get_top_menus_by_user(db=db, user_id=user_id, top_n=3)
    
    if query_result:
        top_orders_by_user = [
            {'menu_name': r[0], 'menu_calorie': r[1], 'order_count': r[2]} for r in query_result
        ]
    else:
        top_orders_by_user = []

    return top_orders_by_user


@handler.add(PostbackEvent)
def postback_event(event):
    
    # Handle unregistered user event, get user state, and return if user does not exist
    user_state = handle_unregistered_user_event(event=event)
    if not user_state:
        return
    
    # Get data from postback event
    line_user_id = event.source.user_id
    postback_data = event.postback.data
    postback_data = json.loads(postback_data)
    menu_id = postback_data["menu_id"]
    
    # If user state is "menu_recognized", a recognition feedback is expected from the user.
    if user_state.state == "menu_recognized":
    
        # Categorize uploaded image
        firebase_storage.categorize_image(line_user_id=line_user_id, menu_id=menu_id)
    
        # Update user state to "image_categorized"
        user_crud.update_user_state_by_line_id(db=db, line_id=line_user_id, state="image_categorized")
        
        # Send a flex message to ask the user to rate the food
        rating_bubble = create_rating_bubble(menu_id=menu_id)
        flex_message = FlexSendMessage(
            alt_text="Let's rate your food!",
            contents=rating_bubble
        )
        line_bot_api.reply_message(
            event.reply_token, 
            flex_message
        )
    
    # If user state is "image_categorized", a rating feedback is expected from the user.
    elif user_state.state == "image_categorized":
        
        # Get rating from postback data
        rating = postback_data["rating"]
        
        # Get user ID from LINE ID
        user_id = user_crud.get_user_by_line_id(db=db, line_id=line_user_id).id
        
        # Get current time in GMT+7
        current_time_utc = datetime.utcnow()
        current_time_gmt_7 = current_time_utc + timedelta(hours=7)
        
        # Add an order of the correct menu to user's order history
        new_order = OrderCreate(
            user_id=user_id,
            menu_id=menu_id,
            rating=rating,
            create_at=current_time_gmt_7
        )

        order_crud.create_order(
            db=db,
            order=new_order
        )
        
        # Send a text message to thank the user for rating the food
        text_message = TextSendMessage(
            text="Thank you for rating the food!"
        )
        line_bot_api.reply_message(
            event.reply_token, 
            text_message
        )
        
        # Update user state to "registered"
        user_crud.update_user_state_by_line_id(db=db, line_id=line_user_id, state="registered")
        
    else:
        return None
        
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

    # Get LINE user ID
    line_user_id = event.source.user_id

    if event.message.text == "Give me food recommendations.":

        # If user state is "registered", the user has not requested for food recommendations yet.
        if user_state.state == "registered":

            gender_mapping = {
                "Male": (0, 1),
                "Female": (1, 0),
                "Other": (0, 0),
                "Prefer not to say": (0, 0)
            }

            sc = MinMaxScaler()

            # User features
            users = user_crud.get_users(db=db)
            user_age_height_weight_norm = list(map(tuple, sc.fit_transform([[2023 - user.birth_date.year, user.height, user.weight] for user in users])))

            user_preferences = user_feature_crud.get_user_features_flag(db=db)
            user_predference_features = [(x.cheap, x.chicken, x.fried, x.pork, x.salty, x.soup, x.spicy, x.steam, x.sweet, x.vegetable) for x in user_preferences]

            user_features_sparse = csr_matrix([numerical + (gender_mapping[user.gender]) + prefer for numerical, prefer, user in zip(user_age_height_weight_norm, user_predference_features, users)])

            # Food features
            menu_features = menu_crud.get_menu_features(db=db)
            menu_features_sparse = csr_matrix([(menu.spicy, menu.high_sugar, menu.high_fat, menu.high_calorie, menu.is_light, menu.is_fried, menu.contain_water, menu.has_vegetable, menu.high_sodium, menu.high_protein, menu.high_carbohydrate, menu.high_cholesterol, menu.has_chicken, menu.has_pork, menu.has_noodle, menu.high_price) for menu in menu_features])

            # Interaction Matrix
            interaction_matrix = order_crud.get_orders(db=db)

            interaction_user = [order.user_id for order in interaction_matrix]
            fill_in_user = [user_id for user_id in range(0, len(users)) if user_id not in interaction_user]
            interaction_user = interaction_user + fill_in_user

            interaction_menu = [order.menu_id for order in interaction_matrix] + ([0.0] * len(fill_in_user))

            interaction_rating = [order.rating for order in interaction_matrix] + ([0.0] * len(fill_in_user))

            interaction_matrix_sparse = csr_matrix(pd.crosstab(interaction_user, interaction_menu, values=interaction_rating, aggfunc='mean').fillna(0))

            # Get food nutrition data
            nutritional_data = menu_crud.get_menus_for_recommendation(db=db)
            
            # Menu names
            menu_names = list(nutritional_data.keys())

            # Nutritional goal left
            user_id = [user.id for user in users if user.line_id == line_user_id][0]

            # Retrieve summarized nutrition values from the database
            query_result = order_crud.get_daily_summary(db=db, user_id=user_id)

            # Check if there is any order history since start of day
            if len(query_result) == 0:
                daily_summary = {
                    "Protein": 0.0,
                    "Carbs": 0.0,
                    "Fat": 0.0,
                    "Calories": 0.0
                }
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
            previous_food_id = previous_food.menu_id if previous_food else -1

            # Meal time
            meal_time = get_meal()
            
            # Load model
            model = food_recommendation.load_model()
            
            # "recommendation_result" is a dictionary that has a menu name as keys
            recommendation_result = food_recommendation.dynamic_food_recommend(
                model,
                interaction_matrix_sparse,
                user_id,
                user_features_sparse,
                previous_food_id,
                menu_names,
                menu_features_sparse,
                nutritional_data,
                nutritional_goal_left,
                meal_time=meal_time
            )
            
            # Get a list of recommended menu objects and store them in "recommended_menus" list
            recommended_menus = []
            for menu_name in recommendation_result:
                # Get Menu object from menu name
                menu = menu_crud.get_menu_by_name(db=db, name=menu_name)
                recommended_menus.append(menu)
    
            # # Get a mock list of recommended menus
            # recommended_menus = food_recommendation.mock_recommend_menus()
            
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
            
            if user_state.state == "recommendation_sent":
                error_text = "Please take a picture of your food to proceed further."
                
            elif user_state.state == "menu_recognized":
                error_text = "Please provide feedback on the menu prediction to proceed further."
                
            elif user_state.state == "image_categorized":
                error_text = "Please rate your food to proceed further."
            
            # Send an error message when the user has already requested for food recommendations
            error_message = TextSendMessage(
                text=error_text
            )
            line_bot_api.reply_message(
                event.reply_token, 
                error_message
            )

    # If the recognition result is wrong, and the user uses LIFF to send the correct menu name
    elif user_state.state == "menu_recognized" and (event.message.text).startswith("The correct menu is"):
        
        # Extract menu name from the message
        menu_name = (event.message.text).split("\n")[1]
        menu_name = menu_name.rstrip(".")
        
        # Get menu ID from menu name
        menu_id = (menu_crud.get_menu_by_name(db=db, name=menu_name)).id
        
        # Categorize uploaded image
        firebase_storage.categorize_image(line_user_id=line_user_id, menu_id=menu_id)
    
        # Update user state to "image_categorized"
        user_crud.update_user_state_by_line_id(db=db, line_id=line_user_id, state="image_categorized")
        
        # Send a flex message showing the correct menu
        correct_menu = menu_crud.get_menu(db=db, menu_id=menu_id)
        correct_menu_bubble = __create_menu_bubble(menu=correct_menu)
        correct_menu_flex = FlexSendMessage(
            alt_text="Let's rate your food!",
            contents=correct_menu_bubble
        )
        
        # Send a flex message to ask the user to rate the food
        rating_bubble = create_rating_bubble(menu_id=menu_id)
        rating_flex = FlexSendMessage(
            alt_text="Let's rate your food!",
            contents=rating_bubble
        )
        line_bot_api.reply_message(
            event.reply_token, 
            [correct_menu_flex, rating_flex]
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
            text='Sorry, EatWise does not understand what you mean. Please interact with us via rich menu or flex messages.'
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
    
    # If the user has already requested for food recommendations
    if user_state.state == "recommendation_sent":

        # Get the image content
        message_id = event.message.id
        message_content = line_bot_api.get_message_content(message_id)

        # Save image as a byte array
        img_byte = io.BytesIO(message_content.content)

        # Check if the image contains food
        is_food = food_recognition.is_food(img_byte)
        if is_food:
            
            # Recognize the menu
            predicted_menu_id, preprocessed_img_byte = food_recognition.recognize_menu(img_byte)
            predicted_menu = menu_crud.get_menu(db=db, menu_id=predicted_menu_id)
            
            # Save uncategorized image to Firebase Storage
            firebase_storage.upload_uncategorized_image(
                line_user_id=event.source.user_id,
                img_byte=preprocessed_img_byte
            )

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

    else:
        
        if user_state.state == "registered":
            error_text = "Please push the \"RECOMMEND\" button in the rich menu before sending your food image."
            
        elif user_state.state == "menu_recognized":
            error_text = "Please provide feedback on the menu prediction to proceed further."
            
        elif user_state.state == "image_categorized":
            error_text = "Please rate your food to proceed further."
        
        # Send an error message when the user sends an image at the wrong state
        error_message = TextSendMessage(
            text=error_text
        )
        line_bot_api.reply_message(
            event.reply_token, 
            error_message
        )


@handler.add(MessageEvent, message=StickerMessage)
def sticker_message(event):
    
    sticker_message = StickerSendMessage(
        package_id='789',
        sticker_id='10865'
    )
    line_bot_api.reply_message(
        event.reply_token, 
        sticker_message
    )


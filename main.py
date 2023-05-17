# FastAPI
from fastapi import FastAPI, Header, HTTPException, Depends, status, Response, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Line-Bot SDK
from linebot import *

# Router
from routers.line_bot import bot
from routers.user import user
from routers.menu import menu
from routers.order import order
from routers.feature import feature
from routers.user_feature import user_feature
from routers.recommend import recommend

# Initiate Fast App
app = FastAPI()

# CORS
origins = [
    "https://62d4-2405-9800-bc00-2f1-d4ca-7e6d-7688-a19b.ngrok-free.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router to Fast App
app.include_router(bot.router)
app.include_router(user.router)
app.include_router(menu.router)
app.include_router(order.router)
app.include_router(feature.router)
app.include_router(user_feature.router)
app.include_router(recommend.router)


@app.get('/')
async def root():
    return {'message': 'Hellooooo'}

@app.get("/liff", response_class=HTMLResponse)
async def read_item(request: Request):
    return """
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        <body>
            <h1>Look ma! HTML!</h1>
        </body>
    </html>
    """

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
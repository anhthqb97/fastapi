from fastapi import (
    Security,
    Response,
    status,
    Body,
    Depends,
    FastAPI,
    BackgroundTasks,
    Request,
    HTTPException
)
from typing import (
    Annotated,
    Union,
    Set,
    List
)
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
    HTTPBasic,
    HTTPBasicCredentials
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.routing import APIRoute
from pydantic import BaseModel, ValidationError

import yaml
import secrets

from dataclasses import dataclass

from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse, UJSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timedelta, timezone

from dependencies import get_query_token, get_token_header
from internal import admin
from routers import items, users

tags_metadata = [
    {
        "name": "users",
        "description": "Operations with users. The **login** logic is also here.",
    },
    {
        "name": "items",
        "description": "Manage items. So _fancy_ they have their own docs.",
        "externalDocs": {
            "description": "Items external docs",
            "url": "https://fastapi.tiangolo.com/",
        },
    },
]
app = FastAPI(
    openapi_tags=tags_metadata,
    dependencies=[Depends(get_query_token)]
)

security = HTTPBasic()


# app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(users.router)
app.include_router(items.router)
app.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_token_header)],
    responses={418: {"description": "I'm a teapot"}},
)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}

def write_notification(email: str, message: ""):
    with open("log.txt", "a") as email_file:
        content = f"Notification for {email}: {message}\n"
        email_file.write(content)

def write_notification_tow(email: str, message: str):
    with open("log.txt", "a") as email_file:
        content = f"Baby Shark Notification for {email}: {message}\n"
        email_file.write(content)

@app.post("/send-notification/{email}")
async def send_notification_two(
        email: str,
        background_tasks: BackgroundTasks,
        message: str
):
    background_tasks.add_task(write_notification, email, message)
    background_tasks.add_task(write_log, message)
    return {"message": "Notification send in the background"}

def write_log(message: str):
    with open("log2.txt", "a") as log:
        log.write(message)

def get_query(background_tasks: BackgroundTasks, q: Union[str, None] = None):
    if q:
        message = f"Query for {q}: {q}"
        background_tasks.add_task(write_log, message)
    return q

@app.post("/send-notification2/{email}")
async def send_notification(
        email: str,
        background_tasks: BackgroundTasks,
        q: Annotated[str, Depends(get_query)]
):
    message = f"Message to {email}\n"
    background_tasks.add_task(write_log, message)
    return {"message": "Message sent in the background"}

@app.get(
    "/items",
    operation_id="get_items",
    include_in_schema=False
)
async def read_items():
    return {"items": "Foo"}

### Path Operation Advanced Configuration
def magic_data_reader(raw_body: bytes):
    return {
        "size": len(raw_body),
        "content": {
            "name": "Maaaagic",
            "price": 42,
            "description": "Just kidding, no magic here"
        }
    }

@app.post(
    "/baby-shark",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "required": ["name", "price"],
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "price": {"type": "number"},
                            "description": {"type": "string"},
                        }
                    }
                }
            },
            "required": True,
        }
    }
)
async def baby_shark(request: Request):
    raw_body = await request.body()
    data = magic_data_reader(raw_body)
    return data

class Item(BaseModel):
    name: str
    tags: List[str]

@app.post(
    "/baby-chill",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/x-yaml": {
                    "schema": Item.model_json_schema()
                }
            }
        }
    }
)
async def baby_chill(request: Request):
    raw_body = await request.body()

    try:
        data = yaml.safe_load(raw_body)
    except yaml.YAMLError:
        raise HTTPException(
            status_code=422,
            detail="Invalid YAML"
        )

    try:
        item = Item.model_validate(data)
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=e.errors(include_url=False)
        )

    return item

### ADDITIONAL STATUS CODE
items = {
    "foo": {
        "name": "Fighters",
        "size": 6
    },
    "bar": {
        "name": "Tenders",
        "size": 3
    }
}

@app.put("/baby-dont-chill")
async def upsert_item(
    item_id: str,
    name: Annotated[Union[str, None], Body()] = None,
    size: Annotated[Union[str, None], Body()] = None,
):
    if item_id in items:
        item = items[item_id]
        item["size"] = size
        item["name"] = name
        return item
    else:
        item = {
            "name": name,
            "size": size
        }
        items[item_id] = item
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=item
        )

#### Return a response directly
class  ItemNew(BaseModel):
    title: str
    timestamp: datetime
    description: Union[str, None] = None

@app.put("/king/{id}")
async def update_item(
    id: str,
    item_new: ItemNew
):
    json_compatible_item_data = jsonable_encoder(item_new)
    return JSONResponse(content=json_compatible_item_data, status_code=status.HTTP_200_OK)

@app.get("/legacy")
def get_legacy_data():
    data = """<?xml version="1.0" encoding="UTF-8"?>
        <shampoo>
        <Header>
            Apply shampoo here.
        </Header>
        <Body>
            You'll have to use soap here.
        </Body>
        </shampoo>
    """
    return Response(
        content=data,
        status_code=status.HTTP_200_OK,
        media_type="application/xml"
    )

### HTMLResponse
def generate_html_response():
    html_content = """
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        <body>
            <h1>Look ma! HTML!</h1>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.get(
    "/generate_html_response",
    response_class=HTMLResponse
)
def generate_html_response():
    return generate_html_response()

@app.get("/test_plan_text", response_class=PlainTextResponse)
async def main():
    return "Hello World"

@app.get("/test_ujson_response", response_class=UJSONResponse)
async def read_items():
    return [{"item_id": "Foo"}]

### Additional Responses in OpenAPI
class Baby(BaseModel):
    id: str
    value: str

class Message(BaseModel):
    message: str

responses = {
    404: {"description": "Item not found"},
    302: {"description": "The item was moved"},
    403: {"description": "Not enough privileges"},
}

@app.get(
    "/test_addition_response/{item_id}",
    response_model = Baby,
    responses={
        **responses,
        200: {"content": {"image/png": {}}}
    }
)
async def read_item(item_id: str):
    if item_id == "Foo":
        return {
            "id": "foo",
            "value": "there goes my hero"
        }
    return JSONResponse(
        status_code=404,
        content={"message": "Item not found"}
    )

@app.post("/cookie/")
def create_cookie():
    content = {"message": "Come to the dark side, we have cookies"}
    response = JSONResponse(content=content)
    response.set_cookie(key="fakesession", value="fake-cookie-session-value")
    return response

@app.get("/headers-and-object/")
def get_headers(response: Response):
    response.headers["X-Cat-Dog"] = "Alone in the world"
    return {"X-Cat-Dog": "Alone in the world"}

@app.get("/headers")
def get_headers():
    content = {"message": "Hello World"}
    headers = {"X-Cat-Dog": "Alone in the world", "Content-Language": "en-US"}
    return JSONResponse(content=content, headers=headers)

tasks = {
    "foo": "Listen to the Bar Fighters"
}
@app.put("/get-or-create-task/{task_id}", status_code=200)
def get_or_create_task(task_id: str, response: Response):
    if task_id not in tasks:
        tasks[task_id] = "This didn't exist before"
        response.status_code = status.HTTP_201_CREATED
    return tasks[task_id]

# Advanced Dependencies
class FixedContentQueryChecker:
    def __init__(self, fixed_content: str):
        self.fixed_content = fixed_content

    def __call__(self, q:str = ""):
        if q:
            return self.fixed_content in q
        return False

checker = FixedContentQueryChecker("bar")
@app.get("/query-checker")
async def query_checker(
    fixed_content_included: Annotated[bool, Depends(checker)]
):
    return {"fixed_content": fixed_content_included}

### Security
### HTTP BASIC
def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
):
    current_username_bytes = credentials.username.encode("utf-8")
    correct_username_bytes = b"lucas"
    is_correct_username = secrets.compare_digest(
        current_username_bytes,
        correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf-8")
    correct_password_bytes = b"passLucas"
    is_correct_password = secrets.compare_digest(
        current_password_bytes,
        correct_password_bytes
    )
    if not (is_correct_username or is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"}
        )
    return credentials.username

@app.get("/users/m4u")
def read_current_user(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)],
        request: Request
):
    client_host = request.client.host
    return {
        "username": credentials.username,
        "password": credentials.password,
        "client_host": client_host
    }

@dataclass
# class FakeBabyClass(BaseModel):
class FakeBabyClass():
    name: str
    price: float
    description: Union[str, None] = None
    tax: Union[int, None] = None

@app.post("/fakeeeeeeeeeeeeeeeeeee/",
    response_model=FakeBabyClass
)
async def create_item(item: FakeBabyClass):
    return item


### TEMPLATES
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates/")

@app.get("/templates/{id}", response_class=HTMLResponse)
async def read_templates(request: Request, id: str):
    return templates.TemplateResponse(
        request=request,
        name="item.html",
        context={
            "id": id,
            "value": "HERE"
        }
    )
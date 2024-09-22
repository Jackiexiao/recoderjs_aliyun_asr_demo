"""
平替 NodeJsServer_asr.aliyun.short.js
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import os
import time
import hmac
import hashlib
import base64
import uuid
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger
import traceback
from fastapi import Form
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Add this near the top of the file, after loading environment variables
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class Config:
    ACCESS_KEY = os.getenv("ALIYUN_ACCESSKEY")
    SECRET = os.getenv("ALIYUN_SECRET")
    LANGS = {
        "普通话": os.getenv("ALIYUN_APPKEY"),
        # Add other languages as needed
    }

class TokenResponse(BaseModel):
    c: int # 0: success, 1: error
    m: str # message
    v: Dict[str, str] # value: {"appkey": str, "token": str}

class AccessToken(BaseModel):
    Id: str
    ExpireTime: int

# Cache for AccessToken (In-memory cache, consider using Redis for production)
access_token_cache: Optional[AccessToken] = None

async def new_access_token() -> AccessToken:
    params = {
        "AccessKeyId": Config.ACCESS_KEY,
        "Action": "CreateToken",
        "Version": "2019-02-28",
        "Format": "JSON",
        "RegionId": "cn-shanghai",
        "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "SignatureMethod": "HMAC-SHA1",
        "SignatureVersion": "1.0",
        "SignatureNonce": str(uuid.uuid4()),
    }

    # Sort parameters
    sorted_params = sorted(params.items())
    canonicalized_query_string = "&".join(f"{k}={requests.utils.quote(v)}" for k, v in sorted_params)

    # Create string to sign
    string_to_sign = f"GET&%2F&{requests.utils.quote(canonicalized_query_string)}"

    # Create signature
    hmac_obj = hmac.new(f"{Config.SECRET}&".encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha1)
    signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')

    # Add signature to parameters
    params["Signature"] = signature

    # Make request
    response = requests.get("http://nls-meta.cn-shanghai.aliyuncs.com/", params=params)
    data = response.json()

    if "Token" not in data:
        raise HTTPException(status_code=500, detail=f"Failed to get token: {data.get('Code')} - {data.get('Message')}")

    return AccessToken(**data["Token"])

@app.get("/token", response_model=TokenResponse)
async def get_asr_token(lang: str):
    try:
        global access_token_cache

        if not Config.ACCESS_KEY or not Config.SECRET:
            raise HTTPException(status_code=500, detail="AccessKey not configured")

        appkey = Config.LANGS.get(lang)
        if not appkey:
            raise HTTPException(status_code=400, detail=f"Lang '{lang}' not configured. Available langs: {list(Config.LANGS.keys())}")

        # Check if token is cached and valid
        if not access_token_cache or access_token_cache.ExpireTime - int(time.time()) < 60:
            access_token_cache = await new_access_token()

        return TokenResponse(c=0, m="", v={"appkey": appkey, "token": access_token_cache.Id})
    except HTTPException as e:
        return TokenResponse(c=1, m=str(e.detail), v={})
    except Exception as e:
        logger.error(f"Unexpected error in get_asr_token: {str(e)}")
        return TokenResponse(c=1, m="An unexpected error occurred", v={})

@app.post("/token", response_model=TokenResponse)
async def post_asr_token(lang: str = Form(...)):
    return await get_asr_token(lang)

@app.get("/")
async def root():
    return {"message": "Aliyun ASR Token API service is running..."}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = f"Global exception: {exc}"
    error_trace = traceback.format_exc()
    logger.error(f"{error_msg}\n{error_trace}")
    return JSONResponse(
        status_code=500,
        content=TokenResponse(c=1, m="An unexpected error occurred", v={}).dict()
    )

@app.post("/polish", response_model=TokenResponse)
async def polish_text(text: str = Form(...)):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是文本润色助手。请润色提供的文本，使其更加简洁、清晰，并去除冗余词汇，尽量保持原文的风格。返回一个润色后的文本。"},
                {"role": "user", "content": text},
            ],
            temperature=0.0,
            stream=False
        )
        polished_text = response.choices[0].message.content
        return TokenResponse(c=0, m="", v={"polished_text": polished_text})
    except Exception as e:
        logger.error(f"Error in polish_text: {str(e)}")
        return TokenResponse(c=1, m="An error occurred while polishing the text", v={})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9527)
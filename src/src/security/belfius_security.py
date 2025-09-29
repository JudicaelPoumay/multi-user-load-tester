import traceback
from collections import OrderedDict
from security.belfius_sso_azure import azure, token_store
from msal import ConfidentialClientApplication, TokenCache
import jwt
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import os
import json
import logging
from flask import session

if os.environ.get('DOTENV_LOCATION') is not None:
    print("Loading configuration from " + os.environ.get('DOTENV_LOCATION'))
    load_dotenv(os.environ.get('DOTENV_LOCATION'))
else:
    load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.debug("Loading confidential client")

client_id = os.environ.get("BACKEND_APPLICATION_ID")
client_secret = os.environ.get("BACKEND_APPLICATION_SECRET")
tenant_id = "83ba98e9-2851-416c-9d81-c0bee20bb7f3"

msal_client = ConfidentialClientApplication(
    client_id=os.environ.get("BACKEND_APPLICATION_ID"),
    authority="https://login.microsoftonline.com/83ba98e9-2851-416c-9d81-c0bee20bb7f3",
    client_credential=os.environ.get("BACKEND_APPLICATION_SECRET")
)


forceUseAppTokens = False
if "FORCE_USE_APP_TOKENS" in os.environ and os.environ["FORCE_USE_APP_TOKENS"] == "True":
    forceUseAppTokens = True

def get_token()  -> str:
    return session['access_token']

def get_userinfo() -> dict:
    if not azure.authorized:
        return None

    token = token_store.get(session['user_id'])

    id_claims = jwt.decode(token.get('id_token'),
                        options={"verify_signature": False})
    return {
        'userid': id_claims.get("mailnickname"),
        'fullname': (id_claims.get("name") or '').replace('(Belfius)', '').strip(),
        'lang': (id_claims.get("extensionattribute7") or '').upper()
    }

def get_user_groups_memberships() -> list:
    if not azure.authorized:
        return None

    token = token_store.get(session['user_id'])
    id_token = jwt.decode(token.get('id_token'),options={"verify_signature": False}) 
    return id_token.get("roles", [])

def get_current_userid() -> str:
    if not azure.authorized:
        return None
    return session["user_id"]


def get_user_token_for(scopes) -> str:
    if not azure.authorized:
        return None
    user = get_userinfo()["userid"]
    return get_new_token_for(scopes, user)


def get_new_token_for(scopes, user: str) -> str:
    current_token = session['access_token']
    tokenresponse = msal_client.acquire_token_on_behalf_of(user_assertion=current_token, scopes=[*scopes]) \
        if not forceUseAppTokens else msal_client.acquire_token_for_client(scopes=[*scopes])
    print(tokenresponse,flush=True)
    print(scopes,flush=True)
    print(current_token,flush=True)
    if tokenresponse is not None:
        try:
            token = tokenresponse.get("access_token")
            return token
        except KeyError:
            logger.error("Could not get an access token ",
                          tokenresponse.get("error"))
    return None



def get_app_token(scopes: list[str]) -> str:
    token_response = msal_client.acquire_token_for_client(scopes=[*scopes])
    token = token_response.get("access_token")
    if token is None : 
        return token, token_response
    return token, None
    

def get_userinfo_for_geus() -> dict:
    if not azure.authorized:
        return None

    token = token_store.get(session['user_id'])
    id_claims = jwt.decode(token.get('id_token'),
                           options={"verify_signature": False})
    return {
        'userid': id_claims.get("mailnickname"),
        'fullname': (id_claims.get("name") or '').replace('(Belfius)', '').strip(),
        'lang': (id_claims.get("extensionattribute7") or '').lower(), 
        'tid' : id_claims.get("tid"),
    }


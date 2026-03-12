import logging

import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
import truststore

#from app.keycloak_oauth import KeycloakOAuth2
from keycloak_py.keycloak_login import KeycloakOAuth2
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.deps import get_db
from app.api.main import api_router
from app.core.config import settings
from app.crud import create_oauth_user, get_user_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

truststore.inject_into_ssl()

def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

base_url = ''
if settings.ENVIRONMENT == "local":
    base_url = settings.keycloak.base_url_local
elif settings.ENVIRONMENT == "staging":
    base_url = settings.keycloak.base_url_staging
elif settings.ENVIRONMENT == "production":
    base_url = settings.keycloak.base_url_staging
else:
    raise Exception("Enviroment type (local, staging, production) not set")

keycloak = KeycloakOAuth2(
    get_session=get_db,
    get_user_id=get_user_id,
    create_user=create_oauth_user,
    client_id=settings.keycloak.client_id,
    client_secret=settings.keycloak.client_secret,
    base_url=base_url,
    authorize_path=str(settings.keycloak.authorize_path),
    access_token_path=str(settings.keycloak.access_token_path),
    server_metadata_path=str(settings.keycloak.server_metadata_path),
    logout_path=str(settings.keycloak.logout_path),
    client_kwargs=settings.keycloak.client_kwargs,
)

# print('keycloak', settings.keycloak)

# create router and register API endpoints

keycloak.setup_fastapi_routes()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,  # ty:ignore[invalid-argument-type] Pycharm lint bug: https://github.com/fastapi/fastapi/discussions/10968#discussioncomment-11004407
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

api_router.include_router(keycloak.router)
app.include_router(api_router, prefix=settings.API_V1_STR)
app.add_middleware(SessionMiddleware, secret_key=settings.keycloak.client_secret) # ty:ignore[invalid-argument-type] TODO: client_secret?

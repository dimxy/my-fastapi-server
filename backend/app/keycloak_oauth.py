# based on https://github.com/bakdata/python-keycloak-oauth.git
import logging
import ssl
from pathlib import Path
from typing import Any

from authlib.common.security import generate_token
from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from authlib.jose import JsonWebKey, JsonWebToken, JWTClaims
from authlib.oauth2.rfc7523 import PrivateKeyJWT
from starlette import status
from starlette.datastructures import URL
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.models import UserCreate, UserKC

logger = logging.getLogger(__name__)

class KeycloakOAuth2:
    def __init__(
        self,
        *,
        client_id: str,
        get_session,
        get_user_id,
        create_user,
        client_secret: str | bytes | None,
        base_url: str, # base oauth provider url
        authorize_path: str,
        server_metadata_path: str,
        access_token_path: str,
        logout_path: str,
        client_kwargs: dict[str, Any],
        login_target: str = "/",
        logout_target: str = "/",
    ) -> None:
        self.code_verifier = generate_token(48)
        self._login_target = login_target # where to redirect after successful login
        self._logout_path = logout_path # logout path in oauth provider
        self._logout_target = logout_target # where to redirect after logout
        self._client_id = client_id
        self._base_url = base_url
        self._get_session = get_session
        self._get_user_id = get_user_id
        self._create_user = create_user

        oauth = OAuth()

        # HACK: load custom certificate including default certifi cacert chain
        if verify := client_kwargs.get("verify"):
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23, verify=verify)
            client_kwargs["verify"] = ssl_context

        oauth.register(
            name="keycloak",
            # client_id and client_secret are created in keycloak
            client_id=client_id,
            client_secret=client_secret,
            authorize_url=self._base_url + authorize_path,
            server_metadata_url=self._base_url + server_metadata_path,
            access_token_url=self._base_url + access_token_path,
            client_kwargs=client_kwargs,
            code_challenge_method="S256",
        )

        assert isinstance(oauth.keycloak, StarletteOAuth2App)
        self.keycloak = oauth.keycloak

    async def setup_signed_jwt(self, keypair: Path, public_key: Path) -> None:
        """Setup client authentication for signed JWT.

        :param keypair: Path to keypair.pem, generated via `openssl genrsa - out keypair.pem 2048`
        :param public_key: Path to publickey.crt, generated via `openssl rsa -in keypair.pem -pubout -out publickey.crt`
        """
        self.keycloak.client_secret = keypair.read_bytes()
        self.pub = JsonWebKey.import_key(
            public_key.read_text(), {"kty": "RSA", "use": "sig"}
        ).as_dict()

        metadata = await self.keycloak.load_server_metadata()
        auth_method = PrivateKeyJWT(metadata["token_endpoint"])
        self.keycloak.client_auth_methods = [auth_method]
        self.keycloak.client_kwargs.update(
            {
                "token_endpoint_auth_method": auth_method.name,
            }
        )

    def setup_fastapi_routes(self) -> None:
        """Create FastAPI router and register API endpoints."""
        import fastapi

        self.router = fastapi.APIRouter(prefix="/auth", tags=["auth"])
        self.router.add_api_route("/login", self.login_page, methods=["GET","POST"])
        self.router.add_api_route("/callback", self.oauth_callback)
        self.router.add_api_route("/logout", self.logout)
        self.router.add_api_route("/certs", self.public_keys)

    async def public_keys(self, request: Request) -> dict[str, Any]:
        return {"keys": [self.pub]}

    async def login_page(
        self, request: Request, redirect_target: str | None = None
    ) -> RedirectResponse:
        """Redirect to Keycloak login page."""

        # where to redirect after successful login
        if login_target := request.query_params.get("redirect_uri"):
            self._login_target = login_target

        # oauth callback uri:
        redirect_uri = (
            URL(redirect_target)
            if redirect_target
            else request.url_for("oauth_callback")  # /auth/callback
        )
        if next := request.query_params.get("next"):
            redirect_uri = redirect_uri.include_query_params(next=next)
        return await self.keycloak.authorize_redirect(
            request, redirect_uri, code_verifier=self.code_verifier
        )

    # Callback where we are sent by oauth provider
    async def oauth_callback(self, request: Request) -> RedirectResponse:
        """Authorize user with Keycloak access token."""
        token = await self.keycloak.authorize_access_token(request)
        claims = await self.parse_claims(token)
        roles :list[str] = []
        roles.extend(claims.get("realm_access", {}).get("roles", []))
        roles.extend(
            claims.get("resource_access", {})
                .get("account", {})
                .get("roles", [])
        )

        if (email := claims.get("email")) is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid auth server token (no email)"
            )
        if (session := self._get_session()) is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cannot access db"
            )

        user_id = self._get_user_id(session=session, email=email)
        # id = db_user.id if db_user is not None else get_new_id()
        user = UserKC(
            name=claims["preferred_username"],
            email=email,
            roles=roles,
            token=token["access_token"],
        )
        if user_id is None:
            user_create=UserCreate(
                password='dummypassword', # TODO: remove passwords
                is_active=True,
                is_superuser=True,
                email=email
            )
            self._create_user(session=session, user_create=user_create)
        else:
            user.id = user_id

        request.session["user"] = user.model_dump(mode="json")
        # Where to redirect after successful login, normally should be set in '../auth/login?redirect_uri=...'
        redirect_uri = request.query_params.get("next") or self._login_target
        return RedirectResponse(redirect_uri)

    async def parse_claims(self, token: dict[str, Any]) -> JWTClaims:
        metadata = await self.keycloak.load_server_metadata()
        alg_values: list[str] = metadata.get(
            "id_token_signing_alg_values_supported"
        ) or ["RS256"]
        jwt = JsonWebToken(alg_values)
        jwk_set = await self.keycloak.fetch_jwk_set()
        claims = jwt.decode(
            token["access_token"],
            key=JsonWebKey.import_key_set(jwk_set),
        )
        return claims

    async def logout(self, request: Request) -> RedirectResponse:
        """Deauthorize user and redirect to logout page."""
        request.session.pop("user", None)
        query_params = { "client_id": self._client_id }
        # TODO: we may also use referrer to construct post_logout_redirect_uri to the home page (if no redirect_uri in the query params)
        if (post_logout_redirect_uri := request.query_params.get("post_logout_redirect_uri")) is not None:
            query_params["post_logout_redirect_uri"] = post_logout_redirect_uri
        if (post_logout_redirect_uri := request.query_params.get("redirect_uri")) is not None: # support redirect_uri query too
            query_params["post_logout_redirect_uri"] = post_logout_redirect_uri
        # TODO: we can first query the metadata server to get end session endpoint url
        logout_uri=URL(self._base_url + self._logout_path).include_query_params(**query_params)
        return RedirectResponse(logout_uri)


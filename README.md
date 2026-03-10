# Added OAuth2/Keycloak support for FastAPI template server

This repo adds OAuth2 authentication support with KeyCloak server as OAuth2 provider for FastAPI template server (Dashboard demo app)

## Install and run

Create a volume for keycloak data in /opt:
```
docker volume create keycloak-opt
```

Start keycloak docker container: 
```
docker run -p 127.0.0.1:8081:8080 -e KC_BOOTSTRAP_ADMIN_USERNAME=<adminuser> -e KC_BOOTSTRAP_ADMIN_PASSWORD=<adminpass> -v keycloak-opt:/opt quay.io/keycloak/keycloak:26.4.7 start-dev
```

In Keycloak add settings:
- add client scope
- add cors settings
- add mail provider
- set header and css for keycloak logon prompt


Clone this repo and checkout keycloak-demo:
```
git clone https://github.com/dimxy/my-fastapi-server.git
cd my-fast-api-server
git checkout keycloak-demo
```

Install fastapi backend:
```
uv venv .venv
source .venv/bin/activate
uv pip install
```

Install fastapi demo frontend
```
npm i
```

Setup the app .env file:
- fix your keycloak base url, client id and secret 


Install postgresql 18

Create postgresql 'app' db:
```
/usr/local/opt/postgresql@18/bin/createdb app
```

Run postgresql:
```
LC_ALL=en_US.UTF-8  /usr/local/opt/postgresql@18/bin/postgres -D /usr/local/var/postgresql@18
```

Run alembic DB install
backend/scripts/prestart.sh


Start backend:
```
cd backend
fastapi run app/main.py
```

Start demo frontend:
```
npm run dev
```

Navigate to the app url, like http://localhost:5173


# Original FastAPI remplate app README
https://github.com/fastapi/full-stack-fastapi-template/blob/master/README.md



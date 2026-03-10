# Added OAuth2/Keycloak support for FastAPI template server

This repo adds OAuth2 authentication support with KeyCloak server as OAuth2 provider for FastAPI template server (Dashboard demo app)

## Install and run

Create a volume for keycloak data in /opt:
```
docker volume create keycloak-opt
```

Start keycloak docker container: 
```
docker run -p 127.0.0.1:8081:8080 -e KC_BOOTSTRAP_ADMIN_USERNAME=admin -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin -v keycloak-opt:/opt quay.io/keycloak/keycloak:26.4.7 start-dev
```

Clone this repo and checkout keycloak-demo:
```
git clone https://github.com/dimxy/my-fastapi-server.git
cd my-fast-api-server
git checkout keycloak-demo
```



Install backend:
```
uv venv .venv
source .venv/bin/activate
uv pip install
```

Install demo frontend


Start backend:
```
cd backend
fastapi run app/main.py
```

Start demo frontend:
```
npm run dev
```

# Original README
https://github.com/fastapi/full-stack-fastapi-template/blob/master/README.md



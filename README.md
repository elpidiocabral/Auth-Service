# Auth-Service

Serviço de autenticação reutilizável com suporte a múltiplos provedores de login (local, Google OAuth2). Construído com FastAPI e PostgreSQL.

## Features

- 🔐 **Autenticação Local**: Login com usuário/senha
- 🌐 **Google OAuth2**: Login simplificado via Google
- 🏗️ **Arquitetura Extensível**: Suporte para adicionar novos provedores
- 🔑 **JWT Tokens**: Autenticação stateless
- 🗄️ **PostgreSQL**: Banco de dados confiável
- 🐳 **Docker**: Containerizado e pronto para produção

## Quick Start

### 1. Pré-requisitos

- Docker e Docker Compose

### 2. Configuração

```bash
# Copiar exemplo de variáveis
cp .env.example .env

# (Opcional) Configurar Google OAuth2
# Edite .env com suas credenciais do Google
```

### 3. Iniciar

```bash
docker-compose up --build
```

A API estará disponível em `http://localhost:8000`

## API Documentation

### Documentação Interativa

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

#### Health Check
```
GET /health
```
Verifica se o serviço está funcionando.

#### Registrar Usuário
```
POST /register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response (201):**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": null,
  "last_name": null,
  "picture_url": null,
  "provider": "local",
  "created_at": "2025-12-17T10:30:00"
}
```

#### Login Local
```
POST /login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": null,
    "last_name": null,
    "picture_url": null,
    "provider": "local",
    "created_at": "2025-12-17T10:30:00"
  }
}
```

#### Login com Google - Iniciar
```
GET /auth/google/login
```

Redireciona para a tela de login do Google. Após autenticação, Google redireciona para o callback.

#### Login com Google - Callback
```
POST /auth/google/callback
Content-Type: application/json

{
  "code": "authorization_code_from_google",
  "state": "state_token"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 2,
    "username": null,
    "email": "user@gmail.com",
    "first_name": "John",
    "last_name": "Doe",
    "picture_url": "https://...",
    "provider": "google",
    "created_at": "2025-12-17T10:35:00"
  }
}
```

#### Obter Perfil
```
GET /profile
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": null,
  "last_name": null,
  "picture_url": null,
  "provider": "local",
  "created_at": "2025-12-17T10:30:00"
}
```

## Integração em Seu Projeto

### Cliente JavaScript

```javascript
import AuthServiceClient from './client.js'

const auth = new AuthServiceClient('http://localhost:8000')

// Login local
await auth.login('username', 'password')

// Ou Google OAuth2
auth.startGoogleLogin()

// Usar token
const profile = await auth.getProfile()
console.log(auth.token) // JWT token
```

### Cliente Python

```python
from client_example import AuthServiceClient

client = AuthServiceClient('http://localhost:8000')

# Login local
result = client.login('username', 'password')
token = client.token

# Usar em requisições
profile = client.get_profile()
```

### Fazer Requisições Autenticadas

```python
import requests

token = "seu_jwt_token_aqui"
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(
    "http://seu-servico/api/protected",
    headers=headers
)
```

## Configuração Google OAuth2

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto
3. Ative Google+ API
4. Crie credencial OAuth2 (Web Application)
5. Configure URIs autorizadas:
   - **Origem**: `http://localhost:8000`
   - **Callback**: `http://localhost:8000/auth/google/callback`
6. Copie Client ID e Secret para `.env`:

```env
GOOGLE_CLIENT_ID=seu-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=seu-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

## Variáveis de Ambiente

Ver [`.env.example`](.env.example) para todas as opções:

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/db

# JWT
SECRET_KEY=sua-chave-secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth2
GOOGLE_CLIENT_ID=seu-id
GOOGLE_CLIENT_SECRET=seu-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Frontend
FRONTEND_URL=http://localhost:3000
```

## Estrutura do Projeto

```
app/
├── __init__.py
├── auth.py           # JWT e password hashing
├── config.py         # Configurações
├── database.py       # Modelos e conexão BD
├── main.py           # Endpoints da API
├── oauth.py          # Provedores OAuth
└── schemas.py        # Modelos Pydantic
```

## Adicionar Novo Provedor OAuth

1. Criar classe em `app/oauth.py`:

```python
class NovoProviderOAuth(OAuthProvider):
    async def get_authorization_url(self, state: str) -> str:
        # Implementar
        pass
    
    async def get_user_info(self, code: str) -> Dict[str, Any]:
        # Implementar
        pass
```

2. Registrar em `oauth_manager`:

```python
oauth_manager.register_provider("novo", NovoProviderOAuth())
```

3. Adicionar endpoint em `main.py`

## Contribuindo

Pull requests são bem-vindos! Por favor:

1. Teste sua implementação
2. Mantenha a cobertura de testes
3. Atualize a documentação

## Licença

MIT

Response (200 OK):
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com"
}
```

## Testing with cURL

### Register a user:
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

### Login:
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

### Get user info (replace TOKEN with actual token):
```bash
curl -X GET "http://localhost:8000/me" \
  -H "Authorization: Bearer TOKEN"
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
DATABASE_URL=postgresql://auth_user:auth_password@db:5432/auth_db
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Resilience Pattern

The service implements a retry pattern using the Tenacity library for database connections:
- **Retry attempts**: 5 attempts
- **Retry strategy**: Exponential backoff (2s min, 10s max)
- **Exception handling**: Retries on `OperationalError`

This ensures the application can handle temporary database connection issues gracefully.

## Development

### Local Development (without Docker)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL and update environment variables

3. Run the application:
```bash
uvicorn app.main:app --reload
```

## Project Structure

```
Auth-Service/
├── app/
│   ├── main.py         # FastAPI application and endpoints
│   ├── database.py     # Database models and connection with retry
│   ├── auth.py         # Authentication utilities (JWT, password hashing)
│   ├── schemas.py      # Pydantic models for request/response
│   └── config.py       # Configuration settings
├── Dockerfile          # Docker configuration for the app
├── docker-compose.yml  # Docker Compose configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables example
├── .gitignore         # Git ignore file
└── README.md          # This file
```

## Security Notes

- Change the `SECRET_KEY` in production
- Use strong passwords for database credentials
- Consider using HTTPS in production
- Implement rate limiting for production use
- Add input validation and sanitization as needed

## License

MIT

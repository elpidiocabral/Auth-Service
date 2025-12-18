# Auth-Service

Serviço de autenticação reutilizável com suporte a múltiplos provedores OAuth. Construído com FastAPI, SQLAlchemy e arquitetura em camadas.

## 🚀 Features

- 🔐 **Autenticação Local**: Registro e login com email/senha
- 🌐 **Google OAuth2**: Login via conta Google
- 🔵 **Facebook OAuth**: Login via conta Facebook
- 🎮 **Discord OAuth**: Login via conta Discord
- 🔑 **Reset de Senha**: Redefinição segura via email
- 🔄 **Retry Pattern**: Resiliência na conexão com banco de dados
- 🏗️ **Arquitetura em Camadas**: Código organizado e extensível
- 🔑 **JWT Tokens**: Autenticação stateless e segura
- 🗄️ **SQLite/PostgreSQL**: Suporte a ambos os bancos
- 🐳 **Docker**: Containerizado e pronto para produção
- 📚 **Documentação Interativa**: Swagger UI integrado

## 📋 Pré-requisitos

**Opção 1 - Docker (Recomendado para produção):**
- Docker
- Docker Compose

**Opção 2 - Local (Desenvolvimento):**
- Python 3.11+
- pip

## ⚡ Quick Start

### Opção 1: Com Docker (PostgreSQL)

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/Auth-Service.git
cd Auth-Service

# 2. Configure variáveis de ambiente (opcional para OAuth)
cp .env.example .env
# Edite .env com suas credenciais OAuth se necessário

# 3. Inicie os serviços
docker-compose up --build

# A API estará disponível em: http://localhost:8000
# Documentação: http://localhost:8000/docs
```

### Opção 2: Desenvolvimento Local (SQLite)

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/Auth-Service.git
cd Auth-Service

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure o .env (SQLite já vem configurado por padrão)
cp .env.example .env

# 4. Execute a aplicação
uvicorn app.main:app --reload

# A API estará disponível em: http://localhost:8000
# Documentação: http://localhost:8000/docs
```

## 📚 Documentação da API

### Documentação Interativa

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Categorias de Endpoints

#### 🔐 Authentication (Local)
- `POST /register` - Registrar novo usuário
- `POST /login` - Login com email/senha

#### 🔑 Password Reset
- `POST /forgot-password` - Solicitar reset de senha
- `POST /reset-password` - Confirmar nova senha

#### 🌐 OAuth - Google
- `GET /auth/google/login` - Iniciar login com Google
- `GET /auth/google/callback` - Callback do Google (automático)

#### 🔵 OAuth - Facebook
- `GET /auth/facebook` - Iniciar login com Facebook
- `GET /auth/facebook/callback` - Callback do Facebook (automático)

#### 🎮 OAuth - Discord
- `GET /auth/discord` - Iniciar login com Discord
- `GET /auth/discord/callback` - Callback do Discord (automático)

#### 👤 User Profile
- `GET /me` - Obter informações do usuário autenticado
- `GET /profile` - Obter perfil do usuário

#### 💚 Health
- `GET /` - Informações da API
- `GET /health` - Status do serviço

## 🔧 Exemplos de Uso

### Registrar Usuário

```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "senha123"
  }'
```

**Response:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": null,
  "last_name": null,
  "provider": "local",
  "created_at": "2025-12-18T10:30:00"
}
```

### Login

```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "senha123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Obter Perfil (Autenticado)

```bash
curl -X GET "http://localhost:8000/me" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### Login com OAuth

Para Google, Facebook ou Discord, basta acessar no navegador:

```
http://localhost:8000/auth/google/login
http://localhost:8000/auth/facebook
http://localhost:8000/auth/discord
```

Você será redirecionado para a página de login do provedor, e após autenticar, receberá um token JWT.

## 🔐 Configuração OAuth

### Google OAuth2

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative a **Google+ API**
4. Vá em **Credenciais > Criar Credenciais > ID do cliente OAuth**
5. Configure:
   - **Tipo**: Aplicativo da Web
   - **URIs de redirecionamento autorizados**: `http://localhost:8000/auth/google/callback`
6. Copie **Client ID** e **Client Secret** para o `.env`:

```env
GOOGLE_CLIENT_ID=seu-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=seu-client-secret
```

### Facebook OAuth

1. Acesse [Facebook Developers](https://developers.facebook.com/apps/)
2. Crie um novo aplicativo
3. Em **Produtos**, adicione **Facebook Login**
4. Configure:
   - **URIs de redirecionamento OAuth válidos**: `http://localhost:8000/auth/facebook/callback`
5. Copie **App ID** e **App Secret** para o `.env`:

```env
FACEBOOK_CLIENT_ID=seu-app-id
FACEBOOK_CLIENT_SECRET=seu-app-secret
```

### Discord OAuth

1. Acesse [Discord Developers](https://discord.com/developers/applications)
2. Crie uma nova aplicação
3. Em **OAuth2 > General**, adicione:
   - **Redirects**: `http://localhost:8000/auth/discord/callback`
4. Copie **Client ID** e **Client Secret** para o `.env`:

```env
DISCORD_CLIENT_ID=seu-client-id
DISCORD_CLIENT_SECRET=seu-client-secret
```

## 🗄️ Banco de Dados

### SQLite (Padrão - Desenvolvimento)

Por padrão, o projeto usa SQLite, perfeito para desenvolvimento e testes:

```env
DATABASE_URL=sqlite:///./test.db
```

Não precisa instalar ou configurar nada!

### PostgreSQL (Produção)

Para produção com Docker, o `docker-compose.yml` já configura PostgreSQL automaticamente:

```env
DATABASE_URL=postgresql://auth_user:auth_password@db:5432/auth_db
```

## 🏗️ Arquitetura

O projeto segue **Arquitetura em Camadas (Layered Architecture)**:

```
┌─────────────────────────────────────┐
│   Presentation Layer (API/Routes)   │  ← main.py
├─────────────────────────────────────┤
│   Business Logic Layer (Services)   │  ← auth.py, oauth.py
├─────────────────────────────────────┤
│   Data Access Layer (Repository)    │  ← database.py
├─────────────────────────────────────┤
│   Domain Models (Entities/DTOs)     │  ← schemas.py, User model
├─────────────────────────────────────┤
│   Configuration Layer                │  ← config.py
└─────────────────────────────────────┘
```

### Estrutura de Arquivos

```
Auth-Service/
├── app/
│   ├── __init__.py
│   ├── main.py           # Endpoints da API (Presentation Layer)
│   ├── auth.py           # Serviços de autenticação JWT/hash
│   ├── oauth.py          # Provedores OAuth (Google, Facebook, Discord)
│   ├── database.py       # Modelos e conexão com banco
│   ├── schemas.py        # DTOs (Pydantic models)
│   └── config.py         # Configurações e variáveis de ambiente
├── docker-compose.yml    # Configuração Docker
├── Dockerfile           # Imagem da aplicação
├── requirements.txt     # Dependências Python
├── .env.example         # Exemplo de variáveis de ambiente
└── README.md           # Este arquivo
```

## 🔄 Padrão de Resiliência

O serviço implementa **Retry Pattern** usando a biblioteca Tenacity para conexões com banco de dados:

- **Tentativas**: 5 tentativas máximas
- **Estratégia**: Backoff exponencial (2s min, 10s max)
- **Exceções**: Retenta apenas em `OperationalError`

Isso garante que a aplicação lide graciosamente com falhas temporárias de conexão.

## 🔧 Variáveis de Ambiente

Exemplo completo (veja [.env.example](.env.example)):

```env
# Database
DATABASE_URL=sqlite:///./test.db

# JWT
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth
GOOGLE_CLIENT_ID=seu-id
GOOGLE_CLIENT_SECRET=seu-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Facebook OAuth
FACEBOOK_CLIENT_ID=seu-app-id
FACEBOOK_CLIENT_SECRET=seu-app-secret
FACEBOOK_REDIRECT_URI=http://localhost:8000/auth/facebook/callback

# Discord OAuth
DISCORD_CLIENT_ID=seu-client-id
DISCORD_CLIENT_SECRET=seu-client-secret
DISCORD_REDIRECT_URI=http://localhost:8000/auth/discord/callback

# Email (SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app

# Frontend
FRONTEND_URL=http://localhost:3000
```

## 🚀 Deploy em Produção

### Alterações necessárias:

1. **Altere SECRET_KEY** para um valor seguro:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

2. **Use PostgreSQL** em vez de SQLite

3. **Configure HTTPS** (obrigatório para OAuth)

4. **Atualize redirect URIs** nos provedores OAuth para suas URLs de produção

5. **Configure CORS** apropriadamente no `main.py`

## 🧪 Testando Endpoints

Use o Swagger UI em `/docs` ou ferramentas como cURL, Postman, Insomnia.

## 🤝 Contribuindo

Pull requests são bem-vindos! Para mudanças maiores:

1. Abra uma issue primeiro
2. Fork o projeto
3. Crie sua feature branch
4. Commit suas mudanças
5. Push para a branch
6. Abra um Pull Request

## 🔗 Links Úteis

- [Documentação FastAPI](https://fastapi.tiangolo.com/)
- [Google OAuth2](https://developers.google.com/identity/protocols/oauth2)
- [Facebook OAuth](https://developers.facebook.com/docs/facebook-login)
- [Discord OAuth2](https://discord.com/developers/docs/topics/oauth2)

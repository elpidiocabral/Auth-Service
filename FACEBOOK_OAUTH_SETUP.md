# Configuração do Facebook OAuth

## Passo 1: Criar um App no Facebook

1. Acesse: https://developers.facebook.com/apps/
2. Clique em **"Create App"** (Criar Aplicativo)
3. Escolha o tipo: **"Consumer"** ou **"Business"**
4. Preencha:
   - **App Name**: Nome do seu app (ex: "Auth Service")
   - **App Contact Email**: Seu email
5. Clique em **"Create App"**

## Passo 2: Configurar Facebook Login

1. No painel do app, clique em **"Add Product"**
2. Encontre **"Facebook Login"** e clique em **"Set Up"**
3. Escolha **"Web"** como plataforma
4. Em **"Site URL"**, adicione: `http://localhost:8000`
5. Salve as configurações

## Passo 3: Configurar OAuth Redirect URIs

1. No menu lateral, vá em **"Facebook Login" > "Settings"**
2. Em **"Valid OAuth Redirect URIs"**, adicione:
   ```
   http://localhost:8000/auth/facebook/callback
   ```
3. Salve as alterações

## Passo 4: Obter Credenciais

1. No menu lateral, vá em **"Settings" > "Basic"**
2. Copie:
   - **App ID** (FACEBOOK_CLIENT_ID)
   - **App Secret** (clique em "Show" para ver - FACEBOOK_CLIENT_SECRET)

## Passo 5: Configurar no .env

Edite o arquivo `.env` e adicione suas credenciais:

```env
FACEBOOK_CLIENT_ID=seu_app_id_aqui
FACEBOOK_CLIENT_SECRET=seu_app_secret_aqui
FACEBOOK_REDIRECT_URI=http://localhost:8000/auth/facebook/callback
```

## Passo 6: Testar

1. Reinicie o servidor:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Acesse no navegador:
   ```
   http://localhost:8000/auth/facebook
   ```

3. Você será redirecionado para o Facebook para fazer login

4. Após autorizar, receberá um token JWT

## Endpoints Disponíveis

### Autenticação Local
- `POST /register` - Registrar usuário com email/senha
- `POST /login` - Login com email/senha
- `GET /me` - Obter informações do usuário autenticado

### Autenticação com Facebook
- `GET /auth/facebook` - Iniciar login com Facebook
- `GET /auth/facebook/callback` - Callback do Facebook (automático)

## Modo de Desenvolvimento

Para testar sem configurar o Facebook, você pode continuar usando os endpoints tradicionais de registro e login.

## Produção

Em produção, altere:
- `FACEBOOK_REDIRECT_URI` para sua URL de produção
- Adicione sua URL de produção nas configurações do Facebook
- Use HTTPS (obrigatório para OAuth em produção)
- Altere `SECRET_KEY` para um valor seguro

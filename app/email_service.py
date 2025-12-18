import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, FRONTEND_URL
from typing import Optional


async def send_reset_password_email(email: str, reset_token: str) -> bool:
    """
    Send password reset email to user.
    
    Args:
        email: User's email address
        reset_token: Password reset token
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"
        
        subject = "Redefinir Senha - Auth Service"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2c3e50;">Solicitação de Redefinição de Senha</h2>
                    
                    <p>Olá,</p>
                    
                    <p>Você solicitou redefinir a sua senha. Clique no botão abaixo para continuar:</p>
                    
                    <div style="margin: 30px 0;">
                        <a href="{reset_url}" style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Redefinir Senha
                        </a>
                    </div>
                    
                    <p>Ou copie e cole o link abaixo no seu navegador:</p>
                    <p style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; word-break: break-all;">
                        {reset_url}
                    </p>
                    
                    <p style="color: #e74c3c;"><strong>Atenção:</strong> Este link é válido por apenas 15 minutos.</p>
                    
                    <p>Se você não solicitou esta redefinição de senha, ignore este email.</p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="font-size: 12px; color: #666;">
                        Este é um email automático, por favor não responda diretamente.
                    </p>
                </div>
            </body>
        </html>
        """
        
        text_body = f"""
        Solicitação de Redefinição de Senha
        
        Você solicitou redefinir a sua senha. Acesse o link abaixo:
        {reset_url}
        
        Este link é válido por apenas 15 minutos.
        
        Se você não solicitou esta redefinição de senha, ignore este email.
        """
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = email
        
        # Attach text and HTML versions
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


async def send_password_changed_email(email: str) -> bool:
    """
    Send confirmation email after password is changed.
    
    Args:
        email: User's email address
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        subject = "Senha Redefinida com Sucesso - Auth Service"
        
        html_body = """
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #27ae60;">Senha Redefinida com Sucesso</h2>
                    
                    <p>Olá,</p>
                    
                    <p>Sua senha foi redefinida com sucesso. Você pode agora fazer login com sua nova senha.</p>
                    
                    <p style="color: #e74c3c;"><strong>Segurança:</strong> Se você não realizou esta ação, altere sua senha imediatamente e entre em contato com nosso suporte.</p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="font-size: 12px; color: #666;">
                        Este é um email automático, por favor não responda diretamente.
                    </p>
                </div>
            </body>
        </html>
        """
        
        text_body = """
        Senha Redefinida com Sucesso
        
        Sua senha foi redefinida com sucesso. Você pode agora fazer login com sua nova senha.
        
        Se você não realizou esta ação, altere sua senha imediatamente.
        """
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = email
        
        # Attach text and HTML versions
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

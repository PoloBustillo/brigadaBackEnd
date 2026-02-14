"""Email service using Resend."""
import resend
from typing import Optional, Dict, Any
from app.core.config import settings


# Configure Resend API
resend.api_key = settings.RESEND_API_KEY


class EmailService:
    """Service for sending emails via Resend."""
    
    @staticmethod
    async def send_activation_email(
        to_email: str,
        full_name: str,
        activation_code: str,
        expires_in_hours: int = 72,
        custom_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send activation code email to user.
        
        Args:
            to_email: Recipient email address
            full_name: User's full name
            activation_code: Plain activation code (6 numeric digits)
            expires_in_hours: Hours until code expires
            custom_message: Optional custom message from admin
            
        Returns:
            Dict with email send status
        """
        subject = "Tu Código de Activación - Brigada"
        
        # Build HTML email
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Código de Activación</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .content {{
            background: #ffffff;
            padding: 30px;
            border: 1px solid #e0e0e0;
            border-radius: 0 0 10px 10px;
        }}
        .code-box {{
            background: #f8f9fa;
            border: 2px dashed #667eea;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin: 30px 0;
        }}
        .code {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            letter-spacing: 4px;
            font-family: 'Courier New', monospace;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #666;
            font-size: 14px;
        }}
        .button {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Brigada</h1>
        <p>Tu cuenta está lista para activarse</p>
    </div>
    
    <div class="content">
        <p>Hola <strong>{full_name}</strong>,</p>
        
        <p>Tu cuenta en Brigada ha sido pre-autorizada. Usa el siguiente código para activar tu cuenta en la aplicación móvil:</p>
        
        <div class="code-box">
            <div style="color: #666; font-size: 14px; margin-bottom: 10px;">TU CÓDIGO DE ACTIVACIÓN</div>
            <div class="code">{activation_code}</div>
        </div>
        
        {f'<p style="background: #e3f2fd; padding: 15px; border-radius: 5px; border-left: 4px solid #2196f3;"><strong>Mensaje del administrador:</strong><br>{custom_message}</p>' if custom_message else ''}
        
        <div class="warning">
            <strong>⏰ Importante:</strong>
            <ul style="margin: 10px 0; padding-left: 20px;">
                <li>Este código expira en <strong>{expires_in_hours} horas</strong></li>
                <li>Solo puede usarse una vez</li>
                <li>No compartas este código con nadie</li>
            </ul>
        </div>
        
        <h3>📱 Pasos para activar tu cuenta:</h3>
        <ol>
            <li>Abre la aplicación móvil de Brigada</li>
            <li>Selecciona "Activar Cuenta"</li>
            <li>Ingresa el código mostrado arriba</li>
            <li>Completa tu información de registro</li>
            <li>¡Listo! Ya puedes empezar a usar Brigada</li>
        </ol>
        
        <p style="margin-top: 30px;">Si tienes problemas o el código ha expirado, contacta a tu administrador.</p>
    </div>
    
    <div class="footer">
        <p>Este es un correo automático, por favor no respondas.</p>
        <p style="color: #999; font-size: 12px;">© 2026 Brigada - Sistema de Gestión</p>
    </div>
</body>
</html>
"""
        
        # Plain text version
        text_content = f"""
Hola {full_name},

Tu cuenta en Brigada ha sido pre-autorizada.

TU CÓDIGO DE ACTIVACIÓN:
{activation_code}

{f'Mensaje del administrador: {custom_message}' if custom_message else ''}

IMPORTANTE:
- Este código expira en {expires_in_hours} horas
- Solo puede usarse una vez
- No compartas este código con nadie

PASOS PARA ACTIVAR:
1. Abre la aplicación móvil de Brigada
2. Selecciona "Activar Cuenta"
3. Ingresa el código: {activation_code}
4. Completa tu información de registro

Si tienes problemas, contacta a tu administrador.

---
Este es un correo automático, por favor no respondas.
© 2026 Brigada
"""
        
        try:
            # Send email via Resend
            response = resend.Emails.send({
                "from": f"{settings.FROM_NAME} <{settings.FROM_EMAIL}>",
                "to": [to_email],
                "subject": subject,
                "html": html_content,
                "text": text_content,
                "tags": [
                    {"name": "category", "value": "activation"},
                    {"name": "environment", "value": settings.ENVIRONMENT}
                ]
            })
            
            return {
                "success": True,
                "email_id": response.get("id"),
                "status": "sent",
                "message": "Email sent successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status": "failed",
                "message": f"Failed to send email: {str(e)}"
            }
    
    @staticmethod
    async def resend_activation_email(
        to_email: str,
        full_name: str,
        activation_code: str,
        expires_in_hours: int = 72
    ) -> Dict[str, Any]:
        """
        Resend activation code email (reminder).
        
        Args:
            to_email: Recipient email address
            full_name: User's full name
            activation_code: Plain activation code
            expires_in_hours: Hours until code expires
            
        Returns:
            Dict with email send status
        """
        return await EmailService.send_activation_email(
            to_email=to_email,
            full_name=full_name,
            activation_code=activation_code,
            expires_in_hours=expires_in_hours,
            custom_message="Este es un recordatorio de tu código de activación."
        )


# Singleton instance
email_service = EmailService()

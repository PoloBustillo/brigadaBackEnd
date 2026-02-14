# Email Service - Resend Integration

## Overview

This service handles all email communications for the Brigada application using [Resend](https://resend.com) as the email provider.

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Email (Resend)
RESEND_API_KEY=re_XHFBq6Va_5xJ4377458VbZSrrhvULsH32
FROM_EMAIL=noreply@psicologopuebla.com
FROM_NAME=Brigada
```

### Installation

The `resend` package is included in `requirements.txt`:

```bash
pip install resend==0.8.0
```

## Usage

### Send Activation Email

```python
from app.services.email_service import email_service

# Send activation code email
result = await email_service.send_activation_email(
    to_email="user@example.com",
    full_name="Juan Pérez",
    activation_code="123456",
    expires_in_hours=72,
    custom_message="Welcome to Brigada!" # Optional
)

if result["success"]:
    print(f"Email sent! ID: {result['email_id']}")
else:
    print(f"Error: {result['error']}")
```

### Resend Activation Email

```python
# Resend with reminder message
result = await email_service.resend_activation_email(
    to_email="user@example.com",
    full_name="Juan Pérez",
    activation_code="123456",
    expires_in_hours=48 # Remaining hours
)
```

## Email Template

The activation email includes:

- **Header**: Brigada branding with gradient background
- **Activation Code**: Large, formatted code in monospace font
- **Custom Message**: Optional message from admin (highlighted)
- **Warning Box**: Expiration time and security notes
- **Instructions**: Step-by-step activation guide
- **Footer**: Company branding and auto-response notice

### HTML Layout

```html
┌─────────────────────────────┐
│  🎯 Brigada                 │ ← Gradient header
│  Tu cuenta está lista       │
├─────────────────────────────┤
│                             │
│  Hola Juan Pérez,          │
│                             │
│  ┌───────────────────────┐ │
│  │  TU CÓDIGO            │ │
│  │  123456               │ │ ← Code box
│  └───────────────────────┘ │
│                             │
│  ⏰ Expira en 72 horas      │ ← Warning
│                             │
│  📱 Pasos para activar:     │
│  1. Abre la app            │
│  2. ...                    │ ← Instructions
│                             │
└─────────────────────────────┘
```

## Response Format

### Success Response

```json
{
  "success": true,
  "email_id": "523e4567-e89b-12d3-a456-426614174000",
  "status": "sent",
  "message": "Email sent successfully"
}
```

### Error Response

```json
{
  "success": false,
  "error": "Invalid API key",
  "status": "failed",
  "message": "Failed to send email: Invalid API key"
}
```

## Integration with Activation Flow

### Phase 2: Code Generation

When an admin generates an activation code:

```python
# In activation endpoint
from app.services.email_service import email_service

# Generate code
activation_code = generate_activation_code()
code_hash = hash_activation_code(activation_code)

# Save to database
db_code = ActivationCode(
    code_hash=code_hash,
    whitelist_id=whitelist.id,
    expires_at=datetime.now() + timedelta(hours=72),
    generated_by=current_admin.id
)
db.add(db_code)
db.commit()

# Send email
if send_email:
    email_result = await email_service.send_activation_email(
        to_email=whitelist.identifier,
        full_name=whitelist.full_name,
        activation_code=activation_code,  # Plain code (only time visible)
        expires_in_hours=72,
        custom_message=request.custom_message
    )
    
    # Log email send attempt
    audit_log = ActivationAuditLog(
        event_type="email_sent",
        activation_code_id=db_code.id,
        success=email_result["success"],
        metadata={"email_id": email_result.get("email_id")}
    )
    db.add(audit_log)
    db.commit()
```

## Resend Features Used

### Email Tagging

Each email is tagged for analytics:

```python
"tags": [
    {"name": "category", "value": "activation"},
    {"name": "environment", "value": "production"}
]
```

View analytics in Resend dashboard:
- Open rate
- Click rate
- Delivery status
- Bounce rate

### Email Tracking

Track email deliverability via Resend webhooks (future enhancement):

```python
@app.post("/webhooks/resend")
async def resend_webhook(payload: dict):
    """
    Handle Resend webhook events:
    - email.sent
    - email.delivered
    - email.bounced
    - email.opened
    - email.clicked
    """
    event_type = payload.get("type")
    email_id = payload.get("data", {}).get("email_id")
    
    # Update email status in audit log
    # ...
```

## Email Content Best Practices

### Spanish Language

All emails are in Spanish to match the target audience:
- "Tu Código de Activación" (Your Activation Code)
- "Hola" instead of "Hello"
- "Expira en X horas" (Expires in X hours)

### Security Messaging

Emphasize security in every email:
- ⏰ "Este código expira en 72 horas"
- 🔒 "Solo puede usarse una vez"
- ⚠️ "No compartas este código con nadie"

### Plain Text Fallback

Every email includes a plain text version for:
- Email clients without HTML support
- Accessibility (screen readers)
- Spam filter compliance

## Testing

### Test Email Sending

```python
import asyncio
from app.services.email_service import email_service

async def test_email():
    result = await email_service.send_activation_email(
        to_email="test@example.com",
        full_name="Test User",
        activation_code="TEST-CODE-1234",
        expires_in_hours=72
    )
    print(result)

asyncio.run(test_email())
```

### Resend Dashboard

Monitor emails in real-time:
1. Go to [resend.com](https://resend.com/logs)
2. View delivery status
3. Check email content preview
4. Debug delivery issues

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid API key` | Wrong or missing `RESEND_API_KEY` | Check `.env` file |
| `Domain not verified` | Email domain not verified in Resend | Verify domain in Resend dashboard |
| `Rate limit exceeded` | Too many emails sent | Implement rate limiting |
| `Invalid email address` | Malformed recipient email | Validate email format before sending |

## Production Considerations

### Rate Limits

Resend free tier limits:
- 100 emails/day
- 3,000 emails/month

For production, upgrade to paid plan for higher limits.

### Domain Verification

**Required for production:**

1. Add your domain in Resend dashboard
2. Add DNS records (SPF, DKIM, DMARC)
3. Wait for verification
4. Update `FROM_EMAIL` to use verified domain

Example DNS records:
```
@ TXT "v=spf1 include:resend.com ~all"
resend._domainkey TXT "k=rsa; p=MIGfMA0GCS..."
_dmarc TXT "v=DMARC1; p=quarantine; rua=mailto:dmarc@psicologopuebla.com"
```

### Monitoring

Set up monitoring for:
- Email delivery rate
- Bounce rate
- Failed send attempts
- API errors

```python
# Add to Prometheus metrics
email_sent_total = Counter(
    'email_sent_total',
    'Total emails sent',
    ['status', 'category']
)

email_sent_total.labels(status='success', category='activation').inc()
```

## Troubleshooting

### Email Not Received

1. **Check Resend logs**: View in dashboard
2. **Verify recipient**: Ensure email exists and is valid
3. **Check spam folder**: May be filtered
4. **Domain reputation**: New domains may have delivery issues

### API Key Issues

```python
# Test API key
import resend
resend.api_key = "re_XHFBq6Va_5xJ4377458VbZSrrhvULsH32"

try:
    response = resend.Emails.send({
        "from": "noreply@psicologopuebla.com",
        "to": ["test@example.com"],
        "subject": "Test",
        "html": "<p>Test</p>"
    })
    print("API key valid!")
except Exception as e:
    print(f"Error: {e}")
```

## Migration from SendGrid

This service replaces previous SendGrid integration. Key differences:

| Feature | SendGrid | Resend |
|---------|----------|--------|
| API simplicity | Complex | Simple |
| Python SDK | `sendgrid` | `resend` |
| Pricing | Higher | Lower |
| Dashboard | Complex | Clean |
| Email Templates | Template IDs | Inline HTML |

Migration steps completed:
- ✅ Installed `resend` package
- ✅ Updated environment variables
- ✅ Created email service
- ✅ Updated documentation

## Resources

- [Resend Documentation](https://resend.com/docs)
- [Resend Python SDK](https://github.com/resendlabs/resend-python)
- [Email Best Practices](https://resend.com/docs/knowledge-base/best-practices)
- [Domain Verification Guide](https://resend.com/docs/dashboard/domains/introduction)

## Support

For issues or questions:
- Check Resend status: [status.resend.com](https://status.resend.com)
- Review logs in Resend dashboard
- Contact Resend support: support@resend.com

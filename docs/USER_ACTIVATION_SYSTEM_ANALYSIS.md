# User Activation System - Architecture Analysis & Implementation Plan

**Date**: February 14, 2026  
**System**: Brigada Survey - Whitelist-based User Activation  
**Status**: Architecture Proposal

---

## Executive Summary

**Current State**: The system currently allows admin-created users with immediate access. No activation workflow exists.

**Gap Analysis**: Missing whitelist mechanism, activation codes, expiration windows, and supervisor assignment during activation.

**Risk Level**: 🟡 Medium - Current implementation would require significant database and API changes.

**Recommendation**: Implement proposed architecture with phased rollout (backend → admin panel → mobile).

---

## 1. Required Database Changes

### 1.1 New Tables

#### **Table: `user_whitelist`**
Pre-authorized users who can activate accounts.

```sql
CREATE TABLE user_whitelist (
    id SERIAL PRIMARY KEY,
    
    -- Identifier (email, phone, or national ID)
    identifier VARCHAR(255) UNIQUE NOT NULL,
    identifier_type VARCHAR(20) NOT NULL, -- 'email', 'phone', 'national_id'
    
    -- Pre-assigned information
    assigned_role VARCHAR(20) NOT NULL,
    assigned_supervisor_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NULL,
    
    -- Activation tracking
    is_activated BOOLEAN DEFAULT FALSE,
    activated_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    activated_at TIMESTAMP WITH TIME ZONE NULL,
    
    -- Metadata
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT NULL,
    
    -- Indexes
    CONSTRAINT check_role CHECK (assigned_role IN ('admin', 'encargado', 'brigadista')),
    CONSTRAINT check_identifier_type CHECK (identifier_type IN ('email', 'phone', 'national_id'))
);

CREATE INDEX idx_whitelist_identifier ON user_whitelist(identifier);
CREATE INDEX idx_whitelist_is_activated ON user_whitelist(is_activated);
CREATE INDEX idx_whitelist_assigned_supervisor ON user_whitelist(assigned_supervisor_id);
```

#### **Table: `activation_codes`**
Time-limited activation codes for whitelist entries.

```sql
CREATE TABLE activation_codes (
    id SERIAL PRIMARY KEY,
    
    -- Code information
    code VARCHAR(12) UNIQUE NOT NULL, -- Format: XXXX-XXXX-XXXX
    whitelist_id INTEGER NOT NULL REFERENCES user_whitelist(id) ON DELETE CASCADE,
    
    -- Expiration
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP WITH TIME ZONE NULL,
    used_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    
    -- Security tracking
    activation_attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE NULL,
    last_attempt_ip VARCHAR(45) NULL,
    
    -- Generation metadata
    generated_by INTEGER NOT NULL REFERENCES users(id),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT check_code_format CHECK (code ~ '^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$')
);

CREATE INDEX idx_activation_code ON activation_codes(code);
CREATE INDEX idx_activation_whitelist ON activation_codes(whitelist_id);
CREATE INDEX idx_activation_expires ON activation_codes(expires_at);
CREATE INDEX idx_activation_is_used ON activation_codes(is_used);
```

#### **Table: `activation_audit_log`**
Security audit trail for all activation attempts.

```sql
CREATE TABLE activation_audit_log (
    id SERIAL PRIMARY KEY,
    
    -- Event information
    event_type VARCHAR(50) NOT NULL, -- 'code_generated', 'attempt_success', 'attempt_failed', 'code_expired'
    activation_code_id INTEGER NULL REFERENCES activation_codes(id) ON DELETE SET NULL,
    whitelist_id INTEGER NULL REFERENCES user_whitelist(id) ON DELETE SET NULL,
    
    -- Request details
    identifier_attempted VARCHAR(255) NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT NULL,
    
    -- Result
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(255) NULL,
    
    -- User created (if successful)
    created_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_event_type ON activation_audit_log(event_type);
CREATE INDEX idx_audit_created_at ON activation_audit_log(created_at);
CREATE INDEX idx_audit_ip ON activation_audit_log(ip_address);
CREATE INDEX idx_audit_success ON activation_audit_log(success);
```

### 1.2 Modify Existing Tables

#### **Table: `users`** (modifications)

```sql
-- Add new columns
ALTER TABLE users ADD COLUMN whitelist_id INTEGER NULL REFERENCES user_whitelist(id) ON DELETE SET NULL;
ALTER TABLE users ADD COLUMN supervisor_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE users ADD COLUMN activated_at TIMESTAMP WITH TIME ZONE NULL;
ALTER TABLE users ADD COLUMN activation_code_id INTEGER NULL REFERENCES activation_codes(id) ON DELETE SET NULL;

-- Add indexes
CREATE INDEX idx_users_whitelist ON users(whitelist_id);
CREATE INDEX idx_users_supervisor ON users(supervisor_id);

-- Add constraint: brigadistas must have a supervisor
ALTER TABLE users ADD CONSTRAINT check_brigadista_supervisor 
    CHECK (role != 'brigadista' OR supervisor_id IS NOT NULL);
```

---

## 2. Required API Endpoints

### 2.1 Admin Panel Endpoints (Backend)

#### **Whitelist Management**

```python
# POST /admin/whitelist
# Create whitelist entry
{
    "identifier": "juan.perez@example.com",
    "identifier_type": "email",
    "assigned_role": "brigadista",
    "assigned_supervisor_id": 5,
    "full_name": "Juan Pérez",
    "phone": "+5215551234567",
    "notes": "Field worker for Zone A"
}

# GET /admin/whitelist?page=1&limit=20&status=pending
# List whitelist entries (paginated, filterable)
Response: {
    "items": [...],
    "total": 150,
    "page": 1,
    "pages": 8
}

# GET /admin/whitelist/{id}
# Get whitelist entry details

# PATCH /admin/whitelist/{id}
# Update whitelist entry (only if not activated)

# DELETE /admin/whitelist/{id}
# Remove whitelist entry (only if not activated)

# POST /admin/whitelist/bulk
# Bulk create whitelist entries (CSV upload)
{
    "entries": [
        {"identifier": "user1@example.com", ...},
        {"identifier": "user2@example.com", ...}
    ]
}
```

#### **Activation Code Management**

```python
# POST /admin/activation-codes/generate
# Generate activation code for whitelist entry
{
    "whitelist_id": 123,
    "expires_in_hours": 72  # Default: 72 hours
}
Response: {
    "code": "A9K7-X2M4-P1Q8",
    "expires_at": "2026-02-17T14:30:00Z",
    "whitelist_entry": {
        "identifier": "juan.perez@example.com",
        "full_name": "Juan Pérez",
        "role": "brigadista"
    }
}

# GET /admin/activation-codes?status=active&whitelist_id=123
# List activation codes (filterable)

# POST /admin/activation-codes/{id}/revoke
# Revoke/invalidate an activation code

# POST /admin/activation-codes/{id}/extend
# Extend expiration date
{
    "additional_hours": 24
}
```

#### **Activation Audit**

```python
# GET /admin/activation-audit?from_date=2026-02-01&to_date=2026-02-14
# Get activation audit logs

# GET /admin/activation-audit/stats
# Get activation statistics
Response: {
    "total_whitelisted": 500,
    "total_activated": 342,
    "pending_activation": 158,
    "failed_attempts_24h": 12,
    "expired_codes": 23,
    "avg_activation_time_hours": 18.5
}
```

### 2.2 Public Activation Endpoints (No Auth Required)

#### **Activation Flow**

```python
# POST /public/activate/validate-code
# Validate activation code and show whitelist info
{
    "code": "A9K7-X2M4-P1Q8"
}
Response: {
    "valid": true,
    "whitelist_entry": {
        "full_name": "Juan Pérez",
        "assigned_role": "brigadista",
        "identifier_type": "email",
        "expires_at": "2026-02-17T14:30:00Z"
    }
}

# POST /public/activate/complete
# Complete activation (create user account)
Request Headers: {
    "X-Device-Info": "...",
    "X-Real-IP": "..."
}
{
    "code": "A9K7-X2M4-P1Q8",
    "identifier": "juan.perez@example.com",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!",
    "phone": "+5215551234567"  # Optional, override whitelist value
}
Response: {
    "success": true,
    "user": {
        "id": 456,
        "email": "juan.perez@example.com",
        "full_name": "Juan Pérez",
        "role": "brigadista",
        "supervisor_id": 5
    },
    "access_token": "eyJ...",
    "token_type": "bearer"
}
```

### 2.3 Rate Limiting Configuration

```python
# Fast API dependencies for rate limiting

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# Apply different limits to different endpoints
@router.post("/public/activate/validate-code")
@limiter.limit("10/minute")  # Allow checking code 10 times per minute
async def validate_code(...): ...

@router.post("/public/activate/complete")
@limiter.limit("3/hour")  # Only 3 activation attempts per hour per IP
async def complete_activation(...): ...

@router.post("/admin/activation-codes/generate")
@limiter.limit("100/hour")  # Admins can generate many codes
async def generate_code(...): ...
```

---

## 3. Security Concerns & Mitigations

### 3.1 High-Risk Vulnerabilities

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Code Brute-Force** | High | Medium | Rate limiting (3 attempts/hour), exponential backoff, CAPTCHA after 3 failures |
| **Identifier Enumeration** | Medium | High | Generic error messages, same response time for valid/invalid codes |
| **Code Sharing** | Medium | Medium | One-time use codes, device fingerprinting, geo-location validation |
| **Expired Code Reuse** | Low | Low | Database constraint prevents used codes, automatic cleanup |
| **SQL Injection** | Critical | Low | Use parameterized queries (SQLAlchemy ORM), input validation |
| **CSV Injection (bulk upload)** | Medium | Low | Sanitize CSV data, validate all fields, sandbox processing |

### 3.2 Security Best Practices

#### **Code Generation**
```python
import secrets
import string

def generate_activation_code() -> str:
    """Generate cryptographically secure activation code."""
    # Use secrets module (not random)
    chars = string.ascii_uppercase + string.digits
    # Exclude ambiguous characters: 0, O, 1, I, L
    chars = chars.replace('0', '').replace('O', '').replace('1', '').replace('I', '').replace('L', '')
    
    segments = []
    for _ in range(3):
        segment = ''.join(secrets.choice(chars) for _ in range(4))
        segments.append(segment)
    
    return '-'.join(segments)  # Format: XXXX-XXXX-XXXX
```

#### **Password Requirements**
```python
from passlib.context import CryptContext
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.
    
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - No common passwords (check against breach database)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    # Check against compromised password list (optional but recommended)
    # Use pwnedpasswords API or local database
    
    return True, "Password is strong"
```

#### **Identifier Verification**
```python
def verify_identifier_match(
    code: str,
    provided_identifier: str,
    whitelist: UserWhitelist
) -> bool:
    """
    Verify provided identifier matches whitelist entry.
    
    Use constant-time comparison to prevent timing attacks.
    """
    import hmac
    
    expected = whitelist.identifier.lower().strip()
    provided = provided_identifier.lower().strip()
    
    # Constant-time comparison
    return hmac.compare_digest(expected, provided)
```

#### **IP-Based Rate Limiting with Redis**
```python
from redis import Redis
from datetime import datetime, timedelta

redis_client = Redis(host='localhost', port=6379, db=0)

def check_rate_limit(ip_address: str, action: str, limit: int, window_seconds: int) -> bool:
    """
    Check if IP has exceeded rate limit for specific action.
    
    Args:
        ip_address: Client IP
        action: Action identifier (e.g., 'activation_attempt')
        limit: Maximum attempts allowed
        window_seconds: Time window in seconds
    
    Returns:
        True if within limit, False if exceeded
    """
    key = f"rate_limit:{action}:{ip_address}"
    
    # Increment counter
    current = redis_client.incr(key)
    
    # Set expiration on first attempt
    if current == 1:
        redis_client.expire(key, window_seconds)
    
    return current <= limit
```

---

## 4. Rate Limiting Strategy

### 4.1 Rate Limit Tiers

| Endpoint | Rate Limit | Window | Scope |
|----------|------------|--------|-------|
| `POST /public/activate/validate-code` | 10 requests | 1 minute | Per IP |
| `POST /public/activate/complete` | 3 requests | 1 hour | Per IP |
| `POST /public/activate/complete` | 5 requests | 24 hours | Per Code |
| `POST /admin/activation-codes/generate` | 100 requests | 1 hour | Per Admin User |
| `POST /admin/whitelist/bulk` | 5 requests | 1 hour | Per Admin User |
| `GET /admin/activation-audit` | 50 requests | 1 minute | Per Admin User |

### 4.2 Graduated Response Strategy

```python
def get_rate_limit_response(
    attempts: int,
    max_attempts: int,
    window_seconds: int
) -> dict:
    """Return appropriate error message based on violation severity."""
    
    remaining_time = calculate_remaining_time(window_seconds)
    
    if attempts >= max_attempts * 2:
        # Severe violation - long lockout
        return {
            "error": "Too many failed attempts",
            "retry_after": remaining_time * 2,  # Double the lockout
            "severity": "high",
            "message": "Your IP has been temporarily blocked. Please contact support."
        }
    elif attempts >= max_attempts:
        # Standard violation
        return {
            "error": "Rate limit exceeded",
            "retry_after": remaining_time,
            "severity": "medium",
            "message": f"Too many attempts. Please try again in {remaining_time // 60} minutes."
        }
    
    # Within limits
    return None
```

### 4.3 CAPTCHA Integration (After Failed Attempts)

```python
from fastapi import Request, HTTPException
import httpx

async def verify_captcha(request: Request, captcha_token: str) -> bool:
    """
    Verify hCaptcha or reCAPTCHA token.
    
    Should be triggered after 3 failed activation attempts from same IP.
    """
    secret_key = settings.CAPTCHA_SECRET_KEY
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://hcaptcha.com/siteverify",
            data={
                "secret": secret_key,
                "response": captcha_token,
                "remoteip": request.client.host
            }
        )
        
        result = response.json()
        return result.get("success", False)

@router.post("/public/activate/complete")
async def complete_activation(
    request: Request,
    data: ActivationRequest,
    captcha_token: Optional[str] = None
):
    """Complete activation with optional CAPTCHA."""
    
    # Check failed attempts
    failed_attempts = get_failed_attempts(request.client.host)
    
    if failed_attempts >= 3:
        if not captcha_token:
            raise HTTPException(
                status_code=428,  # Precondition Required
                detail="CAPTCHA verification required after multiple failed attempts"
            )
        
        if not await verify_captcha(request, captcha_token):
            raise HTTPException(
                status_code=400,
                detail="Invalid CAPTCHA"
            )
    
    # Continue with activation...
```

---

## 5. Admin UI Changes (Next.js)

### 5.1 New Pages Required

#### **`/dashboard/whitelist`** - Whitelist Management

```typescript
// Features:
// - Table with columns: Identifier, Name, Role, Supervisor, Status, Actions
// - Filters: Status (pending/activated), Role, Supervisor
// - Search: By identifier or name
// - Bulk actions: Generate codes, Export CSV, Delete
// - Action buttons: View, Edit, Generate Code, Delete

interface WhitelistEntry {
  id: number;
  identifier: string;
  identifierType: 'email' | 'phone' | 'national_id';
  assignedRole: UserRole;
  supervisorId?: number;
  supervisorName?: string;
  fullName: string;
  phone?: string;
  isActivated: boolean;
  activatedAt?: string;
  activatedUserName?: string;
  createdAt: string;
  notes?: string;
}
```

#### **`/dashboard/whitelist/new`** - Create Whitelist Entry

```typescript
// Form fields:
// - Identifier type (select: Email, Phone, National ID)
// - Identifier (input with validation based on type)
// - Full name (required)
// - Assigned role (select: Admin, Encargado, Brigadista)
// - Assigned supervisor (autocomplete search, required if role=brigadista)
// - Phone number (optional)
// - Notes (textarea)

// Validation:
// - Email: RFC 5322 format
// - Phone: E.164 format (+52...)
// - National ID: Country-specific format
// - Supervisor: Must be admin or encargado
```

#### **`/dashboard/whitelist/bulk-import`** - CSV Bulk Import

```typescript
// Features:
// - CSV template download
// - Drag-and-drop file upload
// - Preview table before import
// - Validation errors display
// - Progress bar during import
// - Results summary (success/failed)

// CSV Format:
// identifier,identifier_type,full_name,assigned_role,supervisor_email,phone,notes
// juan@example.com,email,Juan Pérez,brigadista,supervisor@example.com,+5215551234567,Zone A
```

#### **`/dashboard/activation-codes`** - Activation Code Management

```typescript
// Features:
// - Table: Code, Whitelist Entry, Status, Expires At, Actions
// - Filters: Status (active/expired/used), Expiring soon (next 24h)
// - Bulk generate: Select multiple whitelist entries
// - Action buttons: Copy Code, Send Email, Extend, Revoke

interface ActivationCode {
  id: number;
  code: string;
  whitelistId: number;
  whitelistIdentifier: string;
  whitelistFullName: string;
  expiresAt: string;
  isUsed: boolean;
  usedAt?: string;
  activationAttempts: number;
  generatedBy: string;
  generatedAt: string;
}
```

#### **`/dashboard/activation-audit`** - Audit Log & Analytics

```typescript
// Features:
// - Line chart: Activations over time
// - Statistics cards: Total whitelisted, Total activated, Pending, Failed attempts
// - Audit log table: Event, Details, IP Address, Result, Timestamp
// - Filters: Date range, Event type, Success/Failure
// - Export to CSV

interface AuditLogEntry {
  id: number;
  eventType: 'code_generated' | 'attempt_success' | 'attempt_failed' | 'code_expired';
  identifier: string;
  ipAddress: string;
  userAgent: string;
  success: boolean;
  failureReason?: string;
  createdAt: string;
}
```

### 5.2 Updated Components

#### **Sidebar Navigation** - Add new menu items

```typescript
const navSections = [
  {
    title: "Principal",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/dashboard/users", label: "Usuarios", icon: Users, allowedRoles: ["admin"] },
      { href: "/dashboard/whitelist", label: "Lista Blanca", icon: Shield, allowedRoles: ["admin"] }, // NEW
      { href: "/dashboard/activation-codes", label: "Códigos", icon: Key, allowedRoles: ["admin"] }, // NEW
      { href: "/dashboard/surveys", label: "Encuestas", icon: FileText },
      { href: "/dashboard/assignments", label: "Asignaciones", icon: ClipboardList },
    ],
  },
  {
    title: "Análisis",
    items: [
      { href: "/dashboard/reports", label: "Reportes", icon: BarChart3 },
      { href: "/dashboard/activation-audit", label: "Auditoría Activación", icon: Shield, allowedRoles: ["admin"] }, // NEW
      { href: "/dashboard/system-health", label: "Estado del Sistema", icon: Activity },
    ],
  },
];
```

#### **Email Template Component** - Send activation codes

```typescript
// Component to send activation code via email
interface EmailCodeModalProps {
  whitelistEntry: WhitelistEntry;
  activationCode: string;
  expiresAt: string;
  onClose: () => void;
}

// Features:
// - Preview email template
// - Customize message
// - Send immediately or schedule
// - Track email delivery status
```

---

## 6. Mobile Flow Changes (React Native)

### 6.1 New Screens

#### **`ActivationWelcomeScreen`**

```typescript
// First screen users see
// Features:
// - Welcome message
// - Explanation of activation process
// - "I have an activation code" button
// - "Contact administrator" link

interface ActivationWelcomeScreenProps {
  navigation: NavigationProp<RootStackParamList>;
}
```

#### **`ActivationCodeInputScreen`**

```typescript
// Code input screen
// Features:
// - Formatted input (XXXX-XXXX-XXXX) with auto-formatting
// - Real-time validation
// - Clear error messages
// - "Paste from clipboard" helper
// - Retry count display (after failures)

interface CodeInputState {
  code: string;
  isValidating: boolean;
  error: string | null;
  attempts: number;
  requiresCaptcha: boolean;
}
```

#### **`ActivationDetailsScreen`**

```typescript
// Show whitelist entry details and confirm
// Features:
// - Display: Name, Role, Supervisor (if applicable)
// - Countdown timer for code expiration
// - "This is me" confirmation
// - "Not me" option (reports suspicious activity)

interface ActivationDetails {
  fullName: string;
  assignedRole: string;
  supervisorName?: string;
  expiresAt: string;
  identifierType: string;
}
```

#### **`ActivationRegistrationScreen`**

```typescript
// Complete registration
// Features:
// - Auto-filled fields (email/phone from whitelist)
// - Password input with strength indicator
// - Password confirmation
// - Terms & conditions checkbox
// - Submit button

interface RegistrationForm {
  identifier: string; // Read-only (from whitelist)
  fullName: string;   // Read-only (from whitelist)
  phone?: string;     // Editable (can override whitelist)
  password: string;
  passwordConfirm: string;
  agreedToTerms: boolean;
}
```

#### **`ActivationSuccessScreen`**

```typescript
// Success confirmation
// Features:
// - Success animation
// - Welcome message
// - Display assigned role and supervisor
// - "Start using the app" button (auto-navigates)

interface ActivationSuccessData {
  userName: string;
  role: string;
  supervisorName?: string;
}
```

### 6.2 Navigation Flow

```typescript
// Root Stack Navigator
const RootStack = createNativeStackNavigator();

<RootStack.Navigator>
  {!isAuthenticated ? (
    <>
      <RootStack.Screen name="ActivationWelcome" component={ActivationWelcomeScreen} />
      <RootStack.Screen name="ActivationCodeInput" component={ActivationCodeInputScreen} />
      <RootStack.Screen name="ActivationDetails" component={ActivationDetailsScreen} />
      <RootStack.Screen name="ActivationRegistration" component={ActivationRegistrationScreen} />
      <RootStack.Screen name="ActivationSuccess" component={ActivationSuccessScreen} />
    </>
  ) : (
    <>
      <RootStack.Screen name="Main" component={MainTabNavigator} />
      {/* Existing authenticated screens */}
    </>
  )}
</RootStack.Navigator>
```

### 6.3 Offline Support Strategy

```typescript
// Queue activation attempt for when connection is restored
interface QueuedActivationAttempt {
  id: string;
  code: string;
  identifier: string;
  password: string; // Encrypted locally
  timestamp: number;
  retries: number;
}

// Use AsyncStorage to persist queued attempts
const queueActivationAttempt = async (data: QueuedActivationAttempt) => {
  const queue = await AsyncStorage.getItem('activation_queue');
  const parsed = queue ? JSON.parse(queue) : [];
  parsed.push(data);
  await AsyncStorage.setItem('activation_queue', JSON.stringify(parsed));
};

// Process queue when connection is restored
NetInfo.addEventListener(state => {
  if (state.isConnected) {
    processActivationQueue();
  }
});
```

---

## 7. Risk Analysis

### 7.1 Technical Risks

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| **Database Migration Failure** | Medium | Critical | Test migration on staging, create rollback script, schedule during low-traffic window | Backend Team |
| **Code Generation Collision** | Low | Medium | Use cryptographically secure random generator, collision detection in database constraint | Backend Team |
| **Performance Degradation** | Medium | Medium | Index all foreign keys, paginate admin queries, implement caching for stats | Backend/DevOps |
| **Bulk Import Memory Issues** | Medium | Low | Stream CSV processing, limit batch size to 1000 rows, implement chunking | Backend Team |
| **Email Delivery Failures** | High | Low | Use reliable email service (SendGrid/AWS SES), implement retry queue, provide manual code sharing | Backend Team |

### 7.2 Security Risks

| Risk | Probability | Impact | Mitigation | Priority |
|------|-------------|--------|------------|----------|
| **Activation Code Leakage** | Medium | High | Short expiration (72h), one-time use, audit log all attempts | P0 |
| **Brute Force Attacks** | High | Medium | Rate limiting (3/hour), exponential backoff, IP blocking | P0 |
| **Insider Threat (Admin Abuse)** | Low | High | Audit all whitelist/code operations, require approval for bulk operations, alert on suspicious patterns | P1 |
| **Social Engineering** | Medium | Medium | User education, verify supervisor via in-person code delivery, multi-factor authentication | P2 |
| **Man-in-the-Middle** | Low | Critical | Enforce HTTPS, certificate pinning in mobile app, secure headers | P0 |

### 7.3 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Admin Training Gap** | High | Medium | Create admin user guide, video tutorials, test environment for practice |
| **User Confusion** | Medium | Low | Clear mobile UI, in-app help, FAQ section, support contact |
| **Code Distribution Delays** | Medium | Medium | Multiple delivery methods (email, SMS, WhatsApp), admin can resend |
| **Support Ticket Volume Spike** | High | Medium | Automated email responses, chatbot for common issues, dedicated support team |

---

## 8. Improvements to Prevent Abuse

### 8.1 Multi-Layer Defense Strategy

#### **Layer 1: Database Constraints**

```sql
-- Prevent duplicate activations
CREATE UNIQUE INDEX idx_whitelist_activated_user ON user_whitelist(activated_user_id) 
WHERE activated_user_id IS NOT NULL;

-- Prevent code reuse
ALTER TABLE activation_codes ADD CONSTRAINT check_used_once 
CHECK (NOT (is_used = TRUE AND used_at IS NULL));

-- Enforce activation window
CREATE OR REPLACE FUNCTION check_activation_window()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_used = TRUE AND NEW.expires_at < NOW() THEN
        RAISE EXCEPTION 'Cannot use expired activation code';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_activation_window
BEFORE UPDATE ON activation_codes
FOR EACH ROW EXECUTE FUNCTION check_activation_window();
```

#### **Layer 2: Application Logic**

```python
class ActivationValidator:
    """Multi-stage validation for activation attempts."""
    
    def __init__(self, db: Session, redis_client: Redis):
        self.db = db
        self.redis = redis_client
    
    async def validate_activation(
        self,
        code: str,
        identifier: str,
        ip_address: str,
        user_agent: str
    ) -> tuple[bool, str]:
        """
        Comprehensive validation pipeline.
        
        Returns: (success, error_message)
        """
        
        # 1. Rate limiting check
        if not self.check_rate_limit(ip_address):
            return False, "Too many activation attempts. Please try again later."
        
        # 2. Code format validation
        if not self.validate_code_format(code):
            return False, "Invalid activation code format."
        
        # 3. Code exists and not used
        activation_code = self.db.query(ActivationCode).filter_by(code=code).first()
        if not activation_code:
            await self.log_failed_attempt(code, identifier, ip_address, "code_not_found")
            return False, "Invalid activation code."
        
        if activation_code.is_used:
            await self.log_failed_attempt(code, identifier, ip_address, "code_already_used")
            return False, "This activation code has already been used."
        
        # 4. Expiration check
        if activation_code.expires_at < datetime.now(timezone.utc):
            await self.log_failed_attempt(code, identifier, ip_address, "code_expired")
            return False, "This activation code has expired."
        
        # 5. Identifier match
        whitelist = activation_code.whitelist
        if not self.verify_identifier(identifier, whitelist.identifier):
            await self.log_failed_attempt(code, identifier, ip_address, "identifier_mismatch")
            # Track repeated mismatches (potential attack)
            self.increment_mismatch_count(ip_address)
            return False, "The provided information does not match our records."
        
        # 6. Activation attempts check
        if activation_code.activation_attempts >= 5:
            await self.log_failed_attempt(code, identifier, ip_address, "too_many_attempts")
            return False, "This code has exceeded the maximum number of activation attempts."
        
        # 7. Geo-location check (optional but recommended)
        if settings.ENABLE_GEO_VALIDATION:
            if not await self.validate_geo_location(ip_address, whitelist):
                await self.log_failed_attempt(code, identifier, ip_address, "suspicious_location")
                # Don't block immediately, but flag for admin review
                await self.send_admin_alert("Suspicious activation attempt from unexpected location")
        
        # All checks passed
        return True, ""
    
    def increment_mismatch_count(self, ip_address: str):
        """Track repeated identifier mismatches (potential credential stuffing)."""
        key = f"activation_mismatches:{ip_address}"
        count = self.redis.incr(key)
        self.redis.expire(key, 3600)  # 1 hour window
        
        if count >= 10:
            # Block this IP for 24 hours
            self.redis.setex(f"blocked_ip:{ip_address}", 86400, "1")
            # Send alert to admins
            self.send_admin_alert(f"IP {ip_address} blocked due to repeated validation failures")
```

#### **Layer 3: Behavioral Analysis**

```python
class ActivationAnomalyDetector:
    """Detect unusual activation patterns."""
    
    async def detect_anomalies(self, activation_attempt: dict) -> list[str]:
        """
        Detect suspicious patterns in activation attempts.
        
        Returns: List of detected anomaly types
        """
        anomalies = []
        
        # Pattern 1: Rapid sequential attempts from same IP
        recent_attempts = await self.get_recent_attempts_by_ip(
            activation_attempt['ip_address'],
            minutes=5
        )
        if len(recent_attempts) > 10:
            anomalies.append("rapid_sequential_attempts")
        
        # Pattern 2: Same code attempted from multiple IPs
        code_attempts = await self.get_attempts_by_code(
            activation_attempt['code'],
            hours=1
        )
        unique_ips = set(a['ip_address'] for a in code_attempts)
        if len(unique_ips) > 3:
            anomalies.append("multiple_ip_same_code")
        
        # Pattern 3: Activation outside business hours
        attempt_time = datetime.now(timezone.utc)
        if attempt_time.hour < 6 or attempt_time.hour > 22:
            anomalies.append("unusual_time")
        
        # Pattern 4: User agent mismatch (desktop browser trying to activate mobile-only code)
        if self.is_mobile_only_code(activation_attempt['code']):
            if not self.is_mobile_user_agent(activation_attempt['user_agent']):
                anomalies.append("device_type_mismatch")
        
        # Pattern 5: Geo-velocity impossible travel
        if len(recent_attempts) > 0:
            prev_location = await self.get_geo_location(recent_attempts[-1]['ip_address'])
            curr_location = await self.get_geo_location(activation_attempt['ip_address'])
            
            distance_km = self.calculate_distance(prev_location, curr_location)
            time_diff_hours = (attempt_time - recent_attempts[-1]['timestamp']).total_seconds() / 3600
            velocity_kmh = distance_km / time_diff_hours if time_diff_hours > 0 else 0
            
            # If travel would require >800 km/h (faster than commercial airplane)
            if velocity_kmh > 800:
                anomalies.append("impossible_travel")
        
        return anomalies
```

#### **Layer 4: Post-Activation Monitoring**

```python
class PostActivationMonitor:
    """Monitor new user behavior for suspicious patterns."""
    
    async def monitor_new_user(self, user_id: int, duration_hours: int = 24):
        """
        Monitor newly activated user for first 24 hours.
        
        Red flags:
        - Immediate data export attempts
        - Accessing resources outside assigned area
        - Unusual login patterns (multiple locations)
        - Attempting to access admin functions
        """
        
        # Set temporary enhanced logging flag
        await self.redis.setex(f"monitor_user:{user_id}", duration_hours * 3600, "1")
        
        # Create monitoring task
        await self.create_monitoring_task(user_id, duration_hours)
    
    async def check_suspicious_activity(self, user_id: int, action: str):
        """Check if action is suspicious for a newly activated user."""
        
        is_monitored = await self.redis.exists(f"monitor_user:{user_id}")
        
        if not is_monitored:
            return  # User is past monitoring period
        
        # Define suspicious actions for new users
        suspicious_actions = [
            "bulk_data_export",
            "access_admin_panel",
            "modify_other_user",
            "delete_survey_data",
            "change_role"
        ]
        
        if action in suspicious_actions:
            # Alert admins and temporarily restrict user
            await self.send_admin_alert(
                f"Suspicious activity from newly activated user {user_id}: {action}"
            )
            await self.apply_temporary_restriction(user_id)
```

### 8.2 Admin Monitoring Dashboard

```typescript
// Real-time monitoring component for admins
interface SecurityMonitoringWidget {
  // Live stats
  activeActivationsLast5Min: number;
  failedAttemptsLast1Hour: number;
  blockedIPs: number;
  flaggedAnomalities: AnomalyAlert[];
  
  // Recent suspicious activities
  recentAlerts: SecurityAlert[];
  
  // Actions
  onBlockIP: (ip: string) => void;
  onRevokeCode: (codeId: number) => void;
  onInvestigate: (alertId: number) => void;
}

interface AnomalyAlert {
  id: number;
  type: 'rapid_attempts' | 'multiple_ips' | 'impossible_travel';
  severity: 'low' | 'medium' | 'high';
  details: string;
  timestamp: string;
  autoResolved: boolean;
}
```

### 8.3 Automated Response Actions

```python
class AutomatedSecurityResponse:
    """Automatic responses to detected threats."""
    
    async def handle_threat(self, threat_type: str, context: dict):
        """Execute appropriate response based on threat severity."""
        
        responses = {
            "rapid_sequential_attempts": self.response_rate_limit_violation,
            "multiple_ip_same_code": self.response_distributed_attack,
            "impossible_travel": self.response_credential_sharing,
            "identifier_mismatch_pattern": self.response_credential_stuffing,
        }
        
        handler = responses.get(threat_type)
        if handler:
            await handler(context)
    
    async def response_rate_limit_violation(self, context: dict):
        """Response to rate limit violations."""
        ip = context['ip_address']
        
        # 1. Block IP temporarily
        await self.redis.setex(f"blocked_ip:{ip}", 3600, "1")  # 1 hour
        
        # 2. Log incident
        await self.log_security_incident("rate_limit_violation", context)
        
        # 3. If repeated violations, escalate
        violations = await self.get_violation_count(ip, days=7)
        if violations > 3:
            # Permanent block
            await self.db.execute(
                "INSERT INTO blocked_ips (ip_address, reason, blocked_at) VALUES (?, ?, NOW())",
                (ip, "repeated_rate_limit_violations")
            )
            await self.send_admin_alert(f"IP {ip} permanently blocked")
    
    async def response_distributed_attack(self, context: dict):
        """Response to coordinated attacks from multiple IPs."""
        code = context['code']
        
        # 1. Invalidate the activation code immediately
        await self.db.execute(
            "UPDATE activation_codes SET is_used = TRUE, used_at = NOW() WHERE code = ?",
            (code,)
        )
        
        # 2. Generate new code for legitimate user
        new_code = await self.generate_replacement_code(code)
        
        # 3. Notify whitelist contact
        await self.send_security_notification(
            code,
            "Your activation code was involved in suspicious activity. A new code has been sent."
        )
        
        # 4. Block all involved IPs
        for ip in context['attacking_ips']:
            await self.redis.setex(f"blocked_ip:{ip}", 86400, "1")  # 24 hours
```

---

## 9. Implementation Timeline

### Phase 1: Database & Backend (Week 1-2)

- ✅ Create migration files
- ✅ Implement new models (whitelist, activation_codes, audit_log)
- ✅ Update user model
- ✅ Create repositories
- ✅ Implement services
- ✅ Create API endpoints
- ✅ Add rate limiting
- ✅ Implement security validators
- ✅ Write unit tests

### Phase 2: Admin Panel (Week 3-4)

- ✅ Create whitelist management pages
- ✅ Create activation code management
- ✅ Create audit dashboard
- ✅ Implement CSV bulk import
- ✅ Add email template system
- ✅ Integration testing

### Phase 3: Mobile App (Week 5-6)

- ✅ Create activation flow screens
- ✅ Implement code input with validation
- ✅ Add offline support
- ✅ Implement error handling
- ✅ Add analytics tracking
- ✅ User acceptance testing

### Phase 4: Security & Performance (Week 7)

- ✅ Penetration testing
- ✅ Load testing (1000 concurrent activations)
- ✅ Security audit
- ✅ Performance optimization
- ✅ Documentation finalization

### Phase 5: Deployment (Week 8)

- ✅ Staging deployment
- ✅ Admin training sessions
- ✅ Beta testing with limited users
- ✅ Production deployment
- ✅ Monitoring setup
- ✅ Post-deployment support

---

## 10. Success Metrics

### Key Performance Indicators

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Successful Activation Rate** | >95% | (Successful activations / Total attempts) × 100 |
| **Average Activation Time** | <5 minutes | Time from code generation to account creation |
| **Failed Activation Rate (Legitimate)** | <2% | Failed attempts due to user error |
| **Blocked Malicious Attempts** | >99% | Successfully blocked brute force attacks |
| **Admin Code Generation Time** | <30 seconds | Time to generate and send code |
| **Support Ticket Volume** | <5% of activations | Tickets related to activation issues |
| **Code Expiration Without Use** | <10% | Codes that expire before being used |

### Monitoring & Alerting

```yaml
# Prometheus metrics
activation_attempts_total{status="success|failure", reason="..."}
activation_codes_generated_total{role="..."}
activation_duration_seconds{quantile="0.5|0.9|0.99"}
rate_limit_violations_total{endpoint="..."}
security_incidents_total{type="..."}

# Alert rules
- alert: HighActivationFailureRate
  expr: rate(activation_attempts_total{status="failure"}[5m]) > 0.1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High activation failure rate detected"

- alert: SuspiciousActivationPattern
  expr: increase(security_incidents_total[1h]) > 10
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Potential security breach - multiple incidents"
```

---

## 11. Conclusion & Recommendations

### Current Architecture Assessment

**Score: 6/10**

- ✅ Solid foundation with SQLAlchemy ORM and FastAPI
- ✅ Existing user management and role system
- ✅ JWT authentication already implemented
- ⚠️ No whitelist mechanism exists
- ⚠️ No activation code system
- ⚠️ Limited rate limiting
- ❌ No audit logging for security events

### Implementation Priority

**Priority 1 (Critical)**:
1. Database migrations (whitelist, activation_codes tables)
2. Backend endpoints for activation flow
3. Rate limiting and security validators
4. Audit logging

**Priority 2 (High)**:
1. Admin UI for whitelist management
2. Activation code generation and management
3. Mobile app activation flow

**Priority 3 (Medium)**:
1. Security monitoring dashboard
2. Automated threat response
3. Analytics and reporting

**Priority 4 (Low)**:
1. Email template customization
2. SMS delivery option
3. Multi-language support

### Risk Mitigation Strategy

1. **Gradual Rollout**: Deploy to staging → beta users (50) → production (all users)
2. **Feature Flags**: Use feature toggles to enable/disable activation system
3. **Fallback Plan**: Keep admin-created users as backup during transition
4. **Training**: Extensive admin training before full rollout
5. **Support**: Dedicated support team for first 2 weeks post-launch

### Final Recommendation

**✅ PROCEED WITH IMPLEMENTATION**

The proposed architecture is comprehensive, secure, and scalable. The 8-week timeline is realistic with proper resource allocation. The multi-layer security approach adequately addresses potential abuse vectors.

**Estimated Effort**: 
- Backend: 120 hours
- Frontend (Admin): 80 hours
- Mobile: 60 hours
- Testing & QA: 40 hours
- **Total**: ~300 hours (6-8 weeks with 2 developers)

**Budget Impact**: Low - Primarily development time, no new infrastructure required except Redis for rate limiting (already recommended for caching).

---

**Document Version**: 1.0  
**Last Updated**: February 14, 2026  
**Next Review**: After Phase 1 completion

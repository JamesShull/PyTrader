# Authentication API

PyTrader uses JWT (JSON Web Tokens) for secure authentication.

## Authentication Flow

1. **Login Request** - User submits credentials to `/token`
2. **Token Generation** - Server validates credentials and returns JWT
3. **Token Storage** - Token stored in HTTP-only cookie
4. **Protected Access** - Token required for accessing protected routes

## Endpoints

### POST /token

Authenticate user and receive access token.

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### GET /home

Protected route that requires valid authentication.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```html
<!-- Protected HTML page -->
```

## User Model

```python
class UserInDB:
    username: str
    full_name: str
    email: str
    hashed_password: str
    disabled: bool
    scopes: List[str]
```

## Security Features

- **Password Hashing** - Bcrypt for secure password storage
- **JWT Tokens** - Short-lived tokens with expiration
- **HTTP-Only Cookies** - Prevents XSS token theft
- **Scope-Based Authorization** - Role-based access control

## Token Configuration

- **Algorithm:** HS256
- **Expiration:** 30 minutes
- **Type:** Bearer token

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 400 Bad Request
```json
{
  "detail": "Inactive user"
}
```
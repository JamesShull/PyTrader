# API Endpoints

Complete reference for all PyTrader API endpoints.

## Public Endpoints

### GET /
- **Description:** Root endpoint, redirects to login
- **Authentication:** None required
- **Response:** 302 redirect to `/login`

### GET /login
- **Description:** Login form page
- **Authentication:** None required
- **Response:** HTML login form

## Authentication Endpoints

### POST /token
- **Description:** User authentication
- **Authentication:** None required
- **Content-Type:** `application/x-www-form-urlencoded`
- **Request Body:**
  ```
  username=admin&password=admin
  ```
- **Response:** JWT token or error

## Protected Endpoints

### GET /home
- **Description:** Protected welcome page
- **Authentication:** Required (JWT token)
- **Response:** HTML welcome page with user information

## Static File Endpoints

### GET /static/{file_path}
- **Description:** Serve static assets (CSS, images)
- **Authentication:** None required
- **Examples:**
  - `/static/css/styles.css`
  - `/static/img/login-icon.svg`

## Response Formats

### Success Response
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Error Response
```json
{
  "detail": "Error message description"
}
```

## HTTP Status Codes

- **200 OK** - Successful request
- **302 Found** - Redirect response
- **400 Bad Request** - Invalid request format
- **401 Unauthorized** - Authentication required/failed
- **404 Not Found** - Endpoint not found
- **422 Unprocessable Entity** - Validation error

## Request Headers

### For Protected Routes
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### For Form Submissions
```
Content-Type: application/x-www-form-urlencoded
```
# Pruebas de API con JWT
# Usar en PowerShell, CMD o Postman

### Variables
$API_URL = "http://localhost:8000/api"

### 1. LOGIN
# Obtener tokens de autenticación
$loginResponse = Invoke-RestMethod -Uri "$API_URL/auth/login/" -Method POST -ContentType "application/json" -Body '{
  "username": "admin",
  "password": "admin123"
}'

# Guardar el token
$token = $loginResponse.access_token
$refreshToken = $loginResponse.refresh_token

Write-Host "Access Token: $token"
Write-Host "User: $($loginResponse.user.username) - Role: $($loginResponse.user.role)"

### 2. OBTENER USUARIOS (requiere token de admin)
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$users = Invoke-RestMethod -Uri "$API_URL/users/" -Method GET -Headers $headers
Write-Host "Total de usuarios: $($users.total)"
$users.usuarios | Format-Table

### 3. CREAR USUARIO (solo admin)
$newUser = @{
    username = "test_user"
    password = "password123"
    role = "user"
} | ConvertTo-Json

$createdUser = Invoke-RestMethod -Uri "$API_URL/users/create/" -Method POST -Headers $headers -Body $newUser
Write-Host "Usuario creado: $($createdUser.username)"

### 4. ACTUALIZAR USUARIO
$updateData = @{
    username = "test_user_updated"
    role = "admin"
} | ConvertTo-Json

$updatedUser = Invoke-RestMethod -Uri "$API_URL/users/update/$($createdUser.id)/" -Method PUT -Headers $headers -Body $updateData
Write-Host "Usuario actualizado: $($updatedUser.username)"

### 5. VERIFICAR TOKEN
$verifyResponse = Invoke-RestMethod -Uri "$API_URL/auth/verify/" -Method POST -Headers $headers
Write-Host "Token válido para: $($verifyResponse.user.username)"

### 6. RENOVAR TOKEN (cuando el access token expire)
$refreshData = @{
    refresh_token = $refreshToken
} | ConvertTo-Json

$newToken = Invoke-RestMethod -Uri "$API_URL/auth/refresh/" -Method POST -ContentType "application/json" -Body $refreshData
$token = $newToken.access_token
Write-Host "Nuevo access token: $token"

### 7. ELIMINAR USUARIO
$deleteResponse = Invoke-RestMethod -Uri "$API_URL/users/delete/$($createdUser.id)/" -Method DELETE -Headers $headers
Write-Host $deleteResponse.mensaje

### 8. LOGOUT
$logoutResponse = Invoke-RestMethod -Uri "$API_URL/auth/logout/" -Method POST -Headers $headers
Write-Host $logoutResponse.message


# ========================================
# EJEMPLOS PARA CURL (Linux/Mac/Git Bash)
# ========================================

<#

# 1. LOGIN
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Guardar el token en una variable
TOKEN="tu_token_aqui"

# 2. OBTENER USUARIOS
curl -X GET http://localhost:8000/api/users/ \
  -H "Authorization: Bearer $TOKEN"

# 3. CREAR USUARIO
curl -X POST http://localhost:8000/api/users/create/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "nuevo_usuario", "password": "password123", "role": "user"}'

# 4. ACTUALIZAR USUARIO
curl -X PUT http://localhost:8000/api/users/update/1/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "usuario_actualizado", "role": "admin"}'

# 5. VERIFICAR TOKEN
curl -X POST http://localhost:8000/api/auth/verify/ \
  -H "Authorization: Bearer $TOKEN"

# 6. RENOVAR TOKEN
REFRESH_TOKEN="tu_refresh_token_aqui"
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"

# 7. ELIMINAR USUARIO
curl -X DELETE http://localhost:8000/api/users/delete/1/ \
  -H "Authorization: Bearer $TOKEN"

# 8. LOGOUT
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer $TOKEN"

#>


# ========================================
# COLECCIÓN POSTMAN (JSON)
# Importar en Postman > Import > Raw Text
# ========================================

<#
{
  "info": {
    "name": "Django JWT API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{access_token}}",
        "type": "string"
      }
    ]
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000/api"
    },
    {
      "key": "access_token",
      "value": ""
    },
    {
      "key": "refresh_token",
      "value": ""
    }
  ],
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Login",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "const response = pm.response.json();",
                  "pm.collectionVariables.set('access_token', response.access_token);",
                  "pm.collectionVariables.set('refresh_token', response.refresh_token);"
                ]
              }
            }
          ],
          "request": {
            "auth": {
              "type": "noauth"
            },
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"username\": \"admin\",\n  \"password\": \"admin123\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": "{{base_url}}/auth/login/"
          }
        },
        {
          "name": "Refresh Token",
          "request": {
            "auth": {
              "type": "noauth"
            },
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"refresh_token\": \"{{refresh_token}}\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": "{{base_url}}/auth/refresh/"
          }
        },
        {
          "name": "Verify Token",
          "request": {
            "method": "POST",
            "header": [],
            "url": "{{base_url}}/auth/verify/"
          }
        },
        {
          "name": "Logout",
          "request": {
            "method": "POST",
            "header": [],
            "url": "{{base_url}}/auth/logout/"
          }
        }
      ]
    },
    {
      "name": "Users",
      "item": [
        {
          "name": "Get Users",
          "request": {
            "method": "GET",
            "header": [],
            "url": "{{base_url}}/users/"
          }
        },
        {
          "name": "Create User",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"username\": \"nuevo_usuario\",\n  \"password\": \"password123\",\n  \"role\": \"user\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": "{{base_url}}/users/create/"
          }
        },
        {
          "name": "Update User",
          "request": {
            "method": "PUT",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"username\": \"usuario_actualizado\",\n  \"role\": \"admin\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": "{{base_url}}/users/update/1/"
          }
        },
        {
          "name": "Delete User",
          "request": {
            "method": "DELETE",
            "header": [],
            "url": "{{base_url}}/users/delete/1/"
          }
        }
      ]
    }
  ]
}
#>

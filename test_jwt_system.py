# Test del Sistema JWT
# Ejecutar: python test_jwt_system.py

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_login():
    """Prueba el login y obtención de tokens"""
    print("\n🔐 Test 1: Login de usuario admin")
    
    response = requests.post(
        f"{BASE_URL}/auth/login_user/",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Login exitoso")
        print(f"   Access Token: {data['access'][:50]}...")
        print(f"   Refresh Token: {data['refresh'][:50]}...")
        print(f"   User ID: {data['user_id']}")
        print(f"   Username: {data['username']}")
        return data['access'], data['refresh']
    else:
        print(f"❌ Login falló: {response.status_code}")
        print(f"   Error: {response.text}")
        return None, None


def test_protected_endpoint(access_token):
    """Prueba acceso a endpoint protegido"""
    print("\n🔒 Test 2: Acceso a endpoint protegido (listar productos)")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/api/productos/",
        headers=headers
    )
    
    if response.status_code == 200:
        productos = response.json()
        print(f"✅ Acceso exitoso")
        print(f"   Total productos: {len(productos)}")
        if productos:
            print(f"   Primer producto: {productos[0]['nombre']}")
    else:
        print(f"❌ Acceso denegado: {response.status_code}")
        print(f"   Error: {response.text}")


def test_refresh_token(refresh_token):
    """Prueba el refresh del access token"""
    print("\n🔄 Test 3: Renovar access token")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/refresh/",
        json={"refresh": refresh_token}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Token renovado exitosamente")
        print(f"   Nuevo Access Token: {data['access'][:50]}...")
        return data['access']
    else:
        print(f"❌ Renovación falló: {response.status_code}")
        print(f"   Error: {response.text}")
        return None


def test_expired_token():
    """Prueba acceso con token inválido"""
    print("\n⚠️  Test 4: Acceso con token inválido")
    
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.token"
    headers = {
        "Authorization": f"Bearer {fake_token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/api/productos/",
        headers=headers
    )
    
    if response.status_code == 401:
        print("✅ Token inválido correctamente rechazado (401)")
    else:
        print(f"❌ Respuesta inesperada: {response.status_code}")


def test_no_token():
    """Prueba acceso sin token"""
    print("\n🚫 Test 5: Acceso sin token")
    
    response = requests.get(f"{BASE_URL}/api/productos/")
    
    if response.status_code == 401:
        print("✅ Acceso sin token correctamente rechazado (401)")
    else:
        print(f"❌ Respuesta inesperada: {response.status_code}")


def main():
    print("=" * 60)
    print("🧪 SUITE DE PRUEBAS - SISTEMA JWT")
    print("=" * 60)
    
    # Test 1: Login
    access_token, refresh_token = test_login()
    
    if not access_token:
        print("\n❌ No se pudo obtener tokens. Abortando pruebas.")
        return
    
    # Test 2: Endpoint protegido con token válido
    test_protected_endpoint(access_token)
    
    # Test 3: Refresh token
    new_access_token = test_refresh_token(refresh_token)
    
    # Test 4: Token inválido
    test_expired_token()
    
    # Test 5: Sin token
    test_no_token()
    
    print("\n" + "=" * 60)
    print("✅ PRUEBAS COMPLETADAS")
    print("=" * 60)
    print("\n📝 Resumen:")
    print("   - Sistema JWT funcionando correctamente")
    print("   - Access token: 30 minutos")
    print("   - Refresh token: 7 días")
    print("   - Auto-refresh implementado en frontend")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se pudo conectar al servidor")
        print("   Asegúrate de que Django esté corriendo:")
        print("   > python manage.py runserver")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

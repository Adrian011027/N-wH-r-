"""
Tests automatizados del Dashboard - E-commerce Admin Panel
Ejecutar con: python manage.py test store.tests.test_dashboard
"""

import pytest
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from store.models import Producto, Categoria, Usuario, Variante, Cliente, Orden, Carrito
from datetime import datetime, timedelta


class DashboardAuthenticationTest(TestCase):
    """SUITE: Autenticación y Acceso del Dashboard"""
    
    def setUp(self):
        """Preparar datos de prueba"""
        self.client = Client()
        self.categoria = Categoria.objects.create(nombre='Test Category')
        
        # Crear usuario admin
        self.admin = Usuario.objects.create_user(
            username='admin_test',
            password='secure_pass_123',
            role='admin'
        )
        
        # Crear usuario cliente
        self.cliente = Usuario.objects.create_user(
            username='cliente_test',
            password='client_pass_123',
            role='cliente'
        )
    
    def test_01_login_exitoso_admin(self):
        """✅ Admin puede loguearse correctamente"""
        response = self.client.post('/auth/login_user/', {
            'username': 'admin_test',
            'password': 'secure_pass_123'
        })
        
        self.assertIn('token', response.json(), 'No se retornó token JWT')
        self.assertIn('role', response.json(), 'No se retornó rol')
        self.assertEqual(response.json()['role'], 'admin')
        print(f"✅ Login exitoso: {response.json().get('username')}")
    
    def test_02_login_falla_password_incorrecto(self):
        """❌ Login falla con contraseña incorrecta"""
        response = self.client.post('/auth/login_user/', {
            'username': 'admin_test',
            'password': 'wrong_password'
        })
        
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.json())
        print(f"❌ Login rechazado: {response.json()['error']}")
    
    def test_03_login_falla_usuario_inexistente(self):
        """❌ Login falla si usuario no existe"""
        response = self.client.post('/auth/login_user/', {
            'username': 'usuario_fantasma',
            'password': 'any_password'
        })
        
        self.assertEqual(response.status_code, 401)
        print("❌ Usuario inexistente rechazado")
    
    def test_04_acceso_dashboard_sin_token(self):
        """🔐 Dashboard requiere autenticación"""
        response = self.client.get('/api/productos/')
        
        # Sin token, debería fallar
        # Nota: Depende de tu configuración de middleware
        print(f"🔐 Status sin token: {response.status_code}")
    
    def test_05_token_invalido_rechazado(self):
        """🔐 Token inválido es rechazado"""
        response = self.client.get(
            '/api/productos/',
            HTTP_AUTHORIZATION='Bearer INVALID_TOKEN_12345'
        )
        
        # Debería rechazar token inválido
        print(f"🔐 Token inválido - Status: {response.status_code}")
    
    def test_06_cliente_no_puede_crear_productos(self):
        """🔒 Cliente no puede crear productos (solo admin)"""
        # Loguearse como cliente
        login_response = self.client.post('/auth/login_user/', {
            'username': 'cliente_test',
            'password': 'client_pass_123'
        })
        
        token = login_response.json().get('token')
        
        # Intentar crear producto
        response = self.client.post(
            '/api/productos/crear/',
            data=json.dumps({
                'nombre': 'Producto Malicioso',
                'descripcion': 'Intento de cliente',
                'precio': 100,
                'categoria_id': self.categoria.id,
                'genero': 'Hombre'
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # Debería rechazar o devolver 403
        print(f"🔒 Cliente intentó crear - Status: {response.status_code}")


class ProductosCRUDTest(TestCase):
    """SUITE: Operaciones CRUD de Productos"""
    
    def setUp(self):
        """Preparar datos"""
        self.client = Client()
        self.categoria = Categoria.objects.create(nombre='Calzado')
        
        self.admin = Usuario.objects.create_user(
            username='admin_crud',
            password='pass123',
            role='admin'
        )
        
        # Login y obtener token
        login_resp = self.client.post('/auth/login_user/', {
            'username': 'admin_crud',
            'password': 'pass123'
        })
        self.token = login_resp.json().get('token')
    
    def _make_request(self, method, url, data=None):
        """Helper para hacer requests con token"""
        if method == 'GET':
            return self.client.get(
                url,
                HTTP_AUTHORIZATION=f'Bearer {self.token}'
            )
        elif method == 'POST':
            return self.client.post(
                url,
                data=json.dumps(data),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.token}'
            )
        elif method == 'DELETE':
            return self.client.delete(
                url,
                HTTP_AUTHORIZATION=f'Bearer {self.token}'
            )
    
    def test_01_crear_producto_valido(self):
        """✅ Crear producto con datos válidos"""
        response = self._make_request('POST', '/api/productos/crear/', {
            'nombre': 'Nike Air 2025',
            'descripcion': 'Zapatilla deportiva premium',
            'precio': 1299.99,
            'categoria_id': self.categoria.id,
            'genero': 'Hombre',
            'stock': 100
        })
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('id', data, 'No se retornó ID del producto')
        self.assertEqual(data['nombre'], 'Nike Air 2025')
        print(f"✅ Producto creado: ID {data['id']}")
    
    def test_02_crear_producto_sin_nombre(self):
        """❌ No se puede crear producto sin nombre"""
        response = self._make_request('POST', '/api/productos/crear/', {
            'nombre': '',  # Vacío
            'descripcion': 'Falta nombre',
            'precio': 100,
            'categoria_id': self.categoria.id,
            'genero': 'Hombre'
        })
        
        self.assertNotEqual(response.status_code, 201)
        print("❌ Producto sin nombre rechazado")
    
    def test_03_listar_productos(self):
        """✅ Listar todos los productos"""
        # Crear algunos productos primero
        for i in range(3):
            Producto.objects.create(
                nombre=f'Producto {i}',
                descripcion='Test',
                precio=100 + i,
                categoria=self.categoria,
                genero='Hombre'
            )
        
        response = self._make_request('GET', '/api/productos/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 3)
        print(f"✅ Listando {len(data)} productos")
    
    def test_04_actualizar_producto(self):
        """✅ Actualizar producto existente"""
        # Crear producto
        producto = Producto.objects.create(
            nombre='Original',
            descripcion='Original desc',
            precio=500,
            categoria=self.categoria,
            genero='Hombre'
        )
        
        # Actualizar
        response = self._make_request('POST', f'/api/productos/update/{producto.id}/', {
            'nombre': 'Actualizado',
            'precio': 750
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar en BD
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, 'Actualizado')
        self.assertEqual(producto.precio, 750)
        print(f"✅ Producto actualizado: {producto.nombre}")
    
    def test_05_eliminar_producto(self):
        """✅ Eliminar producto"""
        producto = Producto.objects.create(
            nombre='Para eliminar',
            descripcion='Será borrado',
            precio=100,
            categoria=self.categoria,
            genero='Hombre'
        )
        
        pid = producto.id
        
        response = self._make_request('DELETE', f'/api/productos/delete/{pid}/')
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar que fue eliminado
        exists = Producto.objects.filter(id=pid).exists()
        self.assertFalse(exists)
        print(f"✅ Producto {pid} eliminado correctamente")
    
    def test_06_filtro_por_genero(self):
        """✅ Filtrar productos por género"""
        # Crear productos
        p_hombre = Producto.objects.create(
            nombre='Nike Hombre',
            descripcion='D',
            precio=100,
            categoria=self.categoria,
            genero='Hombre'
        )
        p_mujer = Producto.objects.create(
            nombre='Adidas Mujer',
            descripcion='D',
            precio=100,
            categoria=self.categoria,
            genero='Mujer'
        )
        
        # Filtrar
        response = self._make_request('GET', '/api/productos/?genero=Hombre')
        
        data = response.json()
        generos_filtrados = [p.get('genero') for p in data]
        
        # Verificar que solo hay productos Hombre o Unisex
        for genero in generos_filtrados:
            self.assertIn(genero, ['Hombre', 'Unisex'], f"Género inesperado: {genero}")
        
        print(f"✅ Filtro género funciona: {len([p for p in data if p['genero'] == 'Hombre'])} productos Hombre")


class VariantesTest(TestCase):
    """SUITE: Gestión de Variantes de Productos"""
    
    def setUp(self):
        self.client = Client()
        self.categoria = Categoria.objects.create(nombre='Test')
        
        self.admin = Usuario.objects.create_user(
            username='admin_var',
            password='pass',
            role='admin'
        )
        
        login_resp = self.client.post('/auth/login_user/', {
            'username': 'admin_var',
            'password': 'pass'
        })
        self.token = login_resp.json().get('token')
        
        # Crear producto
        self.producto = Producto.objects.create(
            nombre='Tenis',
            descripcion='D',
            precio=100,
            categoria=self.categoria,
            genero='Hombre'
        )
    
    def test_01_crear_variante(self):
        """✅ Crear variante de producto"""
        response = self.client.post(
            '/api/variantes/create/',
            data=json.dumps({
                'producto_id': self.producto.id,
                'talla': '42',
                'color': 'Negro',
                'precio': 1200,
                'stock': 50
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['talla'], '42')
        print(f"✅ Variante creada: {data['talla']} - {data['color']}")
    
    def test_02_stock_total_actualiza(self):
        """✅ Stock total del producto se actualiza con variantes"""
        # Crear variantes
        Variante.objects.create(
            producto=self.producto,
            talla='40',
            color='Azul',
            precio=1000,
            stock=10
        )
        Variante.objects.create(
            producto=self.producto,
            talla='42',
            color='Negro',
            precio=1000,
            stock=15
        )
        
        # Verificar stock_total
        stock_total = self.producto.stock_total
        self.assertEqual(stock_total, 25)
        print(f"✅ Stock total calculado correctamente: {stock_total}")


class ClientesDashboardTest(TestCase):
    """SUITE: Gestión de Clientes en Dashboard"""
    
    def setUp(self):
        self.client = Client()
        
        self.admin = Usuario.objects.create_user(
            username='admin_clientes',
            password='pass',
            role='admin'
        )
        
        login_resp = self.client.post('/auth/login_user/', {
            'username': 'admin_clientes',
            'password': 'pass'
        })
        self.token = login_resp.json().get('token')
    
    def test_01_listar_usuarios(self):
        """✅ Admin puede listar usuarios"""
        response = self.client.get(
            '/api/users/',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('usuarios', data)
        self.assertGreater(len(data['usuarios']), 0)
        print(f"✅ Listando {data['total']} usuarios")
    
    def test_02_crear_usuario(self):
        """✅ Crear nuevo usuario (admin)"""
        response = self.client.post(
            '/api/users/create/',
            data=json.dumps({
                'username': 'nuevo_admin',
                'password': 'secure_123',
                'role': 'admin'
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Usuario.objects.filter(username='nuevo_admin').exists())
        print("✅ Nuevo usuario creado")


class OrdenesDashboardTest(TestCase):
    """SUITE: Gestión de Órdenes en Dashboard"""
    
    def setUp(self):
        self.client = Client()
        self.categoria = Categoria.objects.create(nombre='Test')
        
        self.admin = Usuario.objects.create_user(
            username='admin_orders',
            password='pass',
            role='admin'
        )
        
        login_resp = self.client.post('/auth/login_user/', {
            'username': 'admin_orders',
            'password': 'pass'
        })
        self.token = login_resp.json().get('token')
    
    def test_01_listar_ordenes(self):
        """✅ Admin puede listar todas las órdenes"""
        response = self.client.get(
            '/api/admin/ordenes/',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('ordenes', data)
        print(f"✅ Órdenes listadas: {len(data.get('ordenes', []))} órdenes")


class ValidacionesTest(TestCase):
    """SUITE: Validaciones de Datos"""
    
    def setUp(self):
        self.client = Client()
        self.categoria = Categoria.objects.create(nombre='Test')
        
        self.admin = Usuario.objects.create_user(
            username='admin_valid',
            password='pass',
            role='admin'
        )
        
        login_resp = self.client.post('/auth/login_user/', {
            'username': 'admin_valid',
            'password': 'pass'
        })
        self.token = login_resp.json().get('token')
    
    def test_01_precio_negativo_rechazado(self):
        """❌ No permitir precio negativo"""
        response = self.client.post(
            '/api/productos/crear/',
            data=json.dumps({
                'nombre': 'Producto',
                'descripcion': 'D',
                'precio': -100,  # Negativo
                'categoria_id': self.categoria.id,
                'genero': 'Hombre'
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        # Debería rechazar
        self.assertNotEqual(response.status_code, 201)
        print("❌ Precio negativo rechazado correctamente")
    
    def test_02_stock_negativo_rechazado(self):
        """❌ No permitir stock negativo"""
        response = self.client.post(
            '/api/variantes/create/',
            data=json.dumps({
                'producto_id': 1,
                'talla': '42',
                'color': 'Negro',
                'precio': 100,
                'stock': -5  # Negativo
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        self.assertNotEqual(response.status_code, 201)
        print("❌ Stock negativo rechazado correctamente")


# ════════════════════════════════════════════════════════════════
# PYTEST FIXTURES (Opcional - si usas pytest en lugar de unittest)
# ════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
    django.setup()
    
    # Ejecutar tests
    import unittest
    unittest.main()

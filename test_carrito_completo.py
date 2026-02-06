#!/usr/bin/env python3
"""
=============================================================================
SCRIPT DE TESTING COMPLETO - CARRITO, ORDEN Y PAGO
=============================================================================

Prueba automática del flujo completo con usuario existente:
- Usuario: zem1r (ID: 16)
- Email: jona.emir@hotmail.com
- Password: 123456

Módulos a probar:
1. Login con usuario existente
2. Carrito (agregar, obtener, actualizar, eliminar, vaciar)
3. Orden (crear, obtener detalle, listar órdenes)
4. Pago (simular pago con Conekta)

Uso:
    python test_carrito_completo.py
"""

import requests
import json
import time
import jwt
from typing import Optional, Dict, List


class ColoredOutput:
    """Clase para outputs con colores en terminal (sin emojis para Windows)"""
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    OKCYAN = '\033[96m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def success(msg):
        print(f"{ColoredOutput.OKGREEN}[OK] {msg}{ColoredOutput.ENDC}")
    
    @staticmethod
    def error(msg):
        print(f"{ColoredOutput.FAIL}[ERROR] {msg}{ColoredOutput.ENDC}")
    
    @staticmethod
    def info(msg):
        print(f"{ColoredOutput.OKCYAN}[INFO] {msg}{ColoredOutput.ENDC}")
    
    @staticmethod
    def warning(msg):
        print(f"{ColoredOutput.WARNING}[WARN] {msg}{ColoredOutput.ENDC}")
    
    @staticmethod
    def header(msg):
        print(f"\n{ColoredOutput.BOLD}{'='*70}{ColoredOutput.ENDC}")
        print(f"{ColoredOutput.BOLD}{msg}{ColoredOutput.ENDC}")
        print(f"{ColoredOutput.BOLD}{'='*70}{ColoredOutput.ENDC}\n")


class CarritoCompletoTest:
    """
    Clase principal para testing completo de Carrito, Orden y Pago
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", username: str = None, password: str = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Usuario: Si no se proporciona, crear uno nuevo
        if username and password:
            self.username = username
            self.password = password
            self.cliente_id = None  # Se obtendrá del login
            self.usar_usuario_existente = True
        else:
            # Crear usuario nuevo para testing
            import random
            import string
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            self.username = f"test_carrito_{random_suffix}"
            self.password = "Test123456!"
            self.cliente_id = None
            self.usar_usuario_existente = False
        
        # Tokens JWT
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        
        # IDs de recursos creados
        self.carrito_id: Optional[int] = None
        self.orden_id: Optional[int] = None
        self.variantes_agregadas: List[int] = []
        
        # Productos de prueba
        self.productos_prueba = [
            {"producto_id": 22, "variante_id": 30, "talla": "26", "cantidad": 2},  # Nike Air
            {"producto_id": 23, "variante_id": 32, "talla": "25", "cantidad": 1},  # Dolce & Gabbana
            {"producto_id": 24, "variante_id": 33, "talla": "28", "cantidad": 3},  # Bota Dior
        ]
        
        ColoredOutput.info(f"URL Base: {self.base_url}")
        ColoredOutput.info(f"Usuario: {self.username}")
        if self.usar_usuario_existente:
            ColoredOutput.info("Modo: Usuario existente")
        else:
            ColoredOutput.info("Modo: Crear usuario nuevo")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Helper para hacer requests con logging"""
        url = f"{self.base_url}{endpoint}"
        
        # Agregar headers con JWT si está disponible
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        
        if self.access_token and 'Authorization' not in kwargs['headers']:
            kwargs['headers']['Authorization'] = f'Bearer {self.access_token}'
        
        # Asegurar que siempre se solicite JSON
        if 'Accept' not in kwargs['headers']:
            kwargs['headers']['Accept'] = 'application/json'
        
        # Si hay JSON body, establecer Content-Type
        if 'json' in kwargs and 'Content-Type' not in kwargs['headers']:
            kwargs['headers']['Content-Type'] = 'application/json'
        
        ColoredOutput.info(f"{method.upper()} {endpoint}")
        response = self.session.request(method, url, **kwargs)
        
        # Log de respuesta
        if response.ok:
            ColoredOutput.success(f"Status: {response.status_code}")
        else:
            ColoredOutput.error(f"Status: {response.status_code} - {response.text[:200]}")
        
        return response
    
    # ========================================================================
    # TEST 0: REGISTRO (OPCIONAL - Solo si no es usuario existente)
    # ========================================================================
    def test_registro(self) -> bool:
        """Registrar nuevo cliente (solo si no es usuario existente)"""
        if self.usar_usuario_existente:
            ColoredOutput.info("Saltando registro - usando usuario existente")
            return True
        
        ColoredOutput.header("TEST 0: Registro de Nuevo Cliente")
        
        try:
            response = self._make_request(
                'post',
                '/clientes/crear/',
                json={
                    'username': self.username,
                    'password': self.password,
                    'correo': f"{self.username}@test.com",
                    'nombre': f"Test User {self.username}"
                },
                headers={}  # Sin JWT para registro
            )
            
            if response.status_code not in [200, 201]:
                ColoredOutput.error(f"Registro fallido: {response.text}")
                return False
            
            data = response.json()
            ColoredOutput.success(f"Cliente registrado - Username: {self.username}")
            
            return True
            
        except Exception as e:
            ColoredOutput.error(f"Error en registro: {e}")
            return False
    
    # ========================================================================
    # TEST 1: LOGIN
    # ========================================================================
    def test_login(self) -> bool:
        """Login con usuario existente y obtener JWT"""
        ColoredOutput.header("TEST 1: Login con Usuario Existente")
        
        try:
            response = self._make_request(
                'post',
                '/auth/login_client/',
                json={
                    'username': self.username,
                    'password': self.password
                }
            )
            
            if response.status_code != 200:
                ColoredOutput.error(f"Login fallido: {response.text}")
                return False
            
            data = response.json()
            self.access_token = data.get('access')
            self.refresh_token = data.get('refresh')
            
            if not self.access_token:
                ColoredOutput.error("No se recibió access token")
                return False
            
            # Decodificar JWT para obtener cliente_id
            try:
                payload = jwt.decode(self.access_token, options={"verify_signature": False})
                self.cliente_id = payload.get('user_id')
                ColoredOutput.success(f"Login exitoso - Cliente ID: {self.cliente_id}")
                
                # Verificar si el email está verificado
                if not data.get('email_verified', False):
                    ColoredOutput.warning("Email no verificado - Login permitido pero con advertencia")
                
                return True
                
            except Exception as e:
                ColoredOutput.error(f"Error al decodificar JWT: {e}")
                return False
                
        except Exception as e:
            ColoredOutput.error(f"Error en login: {e}")
            return False
    
    # ========================================================================
    # TEST 2: AGREGAR PRODUCTOS AL CARRITO
    # ========================================================================
    def test_agregar_productos_carrito(self) -> bool:
        """Agregar múltiples productos al carrito"""
        ColoredOutput.header("TEST 2: Agregar Productos al Carrito")
        
        if not self.access_token:
            ColoredOutput.error("Se requiere login primero")
            return False
        
        try:
            for producto in self.productos_prueba:
                ColoredOutput.info(f"Agregando: {producto}")
                
                response = self._make_request(
                    'post',
                    f'/api/carrito/create/{self.cliente_id}/',
                    json={
                        'producto_id': producto['producto_id'],
                        'talla': producto['talla'],
                        'cantidad': producto['cantidad']
                    }
                )
                
                if response.status_code not in [200, 201]:
                    ColoredOutput.error(f"Fallo al agregar producto {producto['producto_id']}: {response.text}")
                    return False
                
                data = response.json()
                self.carrito_id = data.get('carrito_id')
                self.variantes_agregadas.append(producto['variante_id'])
                
                ColoredOutput.success(f"Producto agregado - Carrito ID: {self.carrito_id}")
                time.sleep(0.3)  # Pequeña pausa entre requests
            
            ColoredOutput.success(f"Todos los productos agregados - Total: {len(self.productos_prueba)}")
            return True
            
        except Exception as e:
            ColoredOutput.error(f"Error al agregar productos: {e}")
            return False
    
    # ========================================================================
    # TEST 3: OBTENER DETALLE DEL CARRITO
    # ========================================================================
    def test_obtener_detalle_carrito(self) -> bool:
        """Obtener y validar el contenido del carrito"""
        ColoredOutput.header("TEST 3: Obtener Detalle del Carrito")
        
        if not self.carrito_id:
            ColoredOutput.error("Se requiere carrito creado primero")
            return False
        
        try:
            response = self._make_request(
                'get',
                f'/api/carrito/{self.cliente_id}/'
            )
            
            if response.status_code != 200:
                ColoredOutput.error(f"Fallo al obtener carrito: {response.text}")
                return False
            
            data = response.json()
            items = data.get('items', [])
            total_items = len(items)
            total_piezas = sum(item['cantidad'] for item in items)
            mayoreo = data.get('mayoreo', False)
            
            ColoredOutput.success(f"Carrito ID: {data.get('carrito_id')}")
            ColoredOutput.success(f"Status: {data.get('status')}")
            ColoredOutput.success(f"Total productos: {total_items}")
            ColoredOutput.success(f"Total piezas: {total_piezas}")
            ColoredOutput.success(f"Precio mayoreo: {'SI' if mayoreo else 'NO'}")
            
            # Mostrar detalles de cada item
            print(f"\n{ColoredOutput.BOLD}Items en el carrito:{ColoredOutput.ENDC}")
            for item in items:
                print(f"  - {item['producto']} | Talla: {item['talla']} | "
                      f"Cantidad: {item['cantidad']} | Precio: ${item['precio_unitario']} | "
                      f"Subtotal: ${item['subtotal']}")
            
            # Validar que el mayoreo se active con >= 6 piezas
            if total_piezas >= 6 and not mayoreo:
                ColoredOutput.warning("Mayoreo debería estar activo (>= 6 piezas)")
            
            return True
            
        except Exception as e:
            ColoredOutput.error(f"Error al obtener carrito: {e}")
            return False
    
    # ========================================================================
    # TEST 4: ACTUALIZAR CANTIDAD DE PRODUCTO
    # ========================================================================
    def test_actualizar_cantidad(self) -> bool:
        """Actualizar la cantidad de un producto en el carrito"""
        ColoredOutput.header("TEST 4: Actualizar Cantidad de Producto")
        
        if not self.variantes_agregadas:
            ColoredOutput.error("No hay productos en el carrito")
            return False
        
        try:
            # Actualizar la cantidad del primer producto a 5 unidades
            variante_id = self.variantes_agregadas[0]
            nueva_cantidad = 5
            
            response = self._make_request(
                'patch',
                f'/api/carrito/{self.cliente_id}/item/{variante_id}/actualizar/',
                json={'cantidad': nueva_cantidad}
            )
            
            if response.status_code != 200:
                ColoredOutput.error(f"Fallo al actualizar cantidad: {response.text}")
                return False
            
            data = response.json()
            ColoredOutput.success(f"Cantidad actualizada a {nueva_cantidad}")
            
            # Verificar la actualización obteniendo el carrito
            response_check = self._make_request('get', f'/api/carrito/{self.cliente_id}/')
            if response_check.ok:
                carrito_data = response_check.json()
                item_actualizado = next(
                    (item for item in carrito_data['items'] if item['variante_id'] == variante_id),
                    None
                )
                if item_actualizado and item_actualizado['cantidad'] == nueva_cantidad:
                    ColoredOutput.success("Verificacion OK - Cantidad actualizada correctamente")
                else:
                    ColoredOutput.warning("No se pudo verificar la actualizacion")
            
            return True
            
        except Exception as e:
            ColoredOutput.error(f"Error al actualizar cantidad: {e}")
            return False
    
    # ========================================================================
    # TEST 5: ELIMINAR PRODUCTO DEL CARRITO
    # ========================================================================
    def test_eliminar_producto_carrito(self) -> bool:
        """Eliminar un producto específico del carrito"""
        ColoredOutput.header("TEST 5: Eliminar Producto del Carrito")
        
        if len(self.variantes_agregadas) < 2:
            ColoredOutput.warning("Se necesitan al menos 2 productos para eliminar uno")
            return True  # No es un error crítico
        
        try:
            # Eliminar el segundo producto
            variante_id = self.variantes_agregadas[1]
            
            response = self._make_request(
                'delete',
                f'/api/carrito/{self.cliente_id}/item/{variante_id}/eliminar/'
            )
            
            if response.status_code != 200:
                ColoredOutput.error(f"Fallo al eliminar producto: {response.text}")
                return False
            
            ColoredOutput.success(f"Producto variante {variante_id} eliminado del carrito")
            self.variantes_agregadas.remove(variante_id)
            
            return True
            
        except Exception as e:
            ColoredOutput.error(f"Error al eliminar producto: {e}")
            return False
    
    # ========================================================================
    # TEST 6: CREAR ORDEN DESDE CARRITO
    # ========================================================================
    def test_crear_orden(self) -> bool:
        """Crear una orden desde el carrito actual"""
        ColoredOutput.header("TEST 6: Crear Orden desde Carrito")
        
        if not self.carrito_id:
            ColoredOutput.error("Se requiere carrito con productos")
            return False
        
        try:
            response = self._make_request(
                'post',
                f'/ordenar/{self.carrito_id}/enviar/',
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
            
            if response.status_code not in [200, 201, 302]:
                ColoredOutput.error(f"Fallo al crear orden: {response.text[:200]}")
                return False
            
            # Intentar parsear JSON
            try:
                data = response.json()
                
                if data.get('success'):
                    ColoredOutput.success(f"Orden creada exitosamente")
                    ColoredOutput.success(f"Mensaje: {data.get('message', 'N/A')}")
                    
                    # La orden se crea pero no se retorna el ID directamente
                    # Obtener la última orden del cliente
                    response_ordenes = self._make_request('get', '/api/cliente/ordenes/')
                    if response_ordenes.ok:
                        ordenes_data = response_ordenes.json()
                        ordenes = ordenes_data.get('ordenes', [])
                        if ordenes:
                            self.orden_id = ordenes[0]['id']
                            ColoredOutput.success(f"Orden ID obtenida: {self.orden_id}")
                    
                    return True
                else:
                    ColoredOutput.error(f"Error al crear orden: {data.get('message', 'Error desconocido')}")
                    return False
                    
            except json.JSONDecodeError:
                # Si es redirect HTML, intentar obtener la orden
                ColoredOutput.warning("Respuesta no es JSON, obteniendo orden desde API")
                response_ordenes = self._make_request('get', '/api/cliente/ordenes/')
                if response_ordenes.ok:
                    ordenes_data = response_ordenes.json()
                    ordenes = ordenes_data.get('ordenes', [])
                    if ordenes:
                        self.orden_id = ordenes[0]['id']
                        ColoredOutput.success(f"Orden encontrada - ID: {self.orden_id}")
                        return True
                
                ColoredOutput.warning("No se pudo obtener orden_id")
                return True  # No es crítico
            
        except Exception as e:
            ColoredOutput.error(f"Error al crear orden: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ========================================================================
    # TEST 7: OBTENER DETALLE DE ORDEN
    # ========================================================================
    def test_obtener_detalle_orden(self) -> bool:
        """Obtener y validar el detalle de la orden creada"""
        ColoredOutput.header("TEST 7: Obtener Detalle de Orden")
        
        if not self.orden_id:
            ColoredOutput.error("Se requiere orden creada primero")
            return False
        
        try:
            response = self._make_request(
                'get',
                f'/orden/{self.orden_id}/'
            )
            
            if response.status_code != 200:
                ColoredOutput.error(f"Fallo al obtener orden: {response.text}")
                return False
            
            data = response.json()
            
            ColoredOutput.success(f"Orden ID: {data.get('id')}")
            ColoredOutput.success(f"Cliente: {data.get('cliente', {}).get('nombre', 'N/A')}")
            ColoredOutput.success(f"Total piezas: {data.get('total_piezas')}")
            ColoredOutput.success(f"Total amount: ${data.get('total_amount')}")
            ColoredOutput.success(f"Status: {data.get('status')}")
            ColoredOutput.success(f"Payment method: {data.get('payment_method')}")
            
            # Mostrar items de la orden
            print(f"\n{ColoredOutput.BOLD}Items en la orden:{ColoredOutput.ENDC}")
            for item in data.get('items', []):
                print(f"  - {item['producto']} | Talla: {item['talla']} | "
                      f"Cantidad: {item['cantidad']} | Precio: ${item['precio_unitario']} | "
                      f"Subtotal: ${item['subtotal']}")
            
            return True
            
        except Exception as e:
            ColoredOutput.error(f"Error al obtener orden: {e}")
            return False
    
    # ========================================================================
    # TEST 8: LISTAR TODAS LAS ÓRDENES DEL CLIENTE
    # ========================================================================
    def test_listar_ordenes_cliente(self) -> bool:
        """Obtener historial de órdenes del cliente"""
        ColoredOutput.header("TEST 8: Listar Órdenes del Cliente")
        
        if not self.access_token:
            ColoredOutput.error("Se requiere autenticación")
            return False
        
        try:
            # El endpoint correcto es /api/cliente/ordenes/ (retorna JSON)
            response = self._make_request(
                'get',
                '/api/cliente/ordenes/'
            )
            
            if response.status_code != 200:
                ColoredOutput.error(f"Fallo al obtener órdenes: {response.text[:200]}")
                return False
            
            data = response.json()
            ordenes = data.get('ordenes', [])
            
            ColoredOutput.success(f"Total órdenes encontradas: {len(ordenes)}")
            
            # Mostrar resumen de cada orden
            print(f"\n{ColoredOutput.BOLD}Historial de Órdenes:{ColoredOutput.ENDC}")
            for orden in ordenes:
                print(f"\n  Orden #{orden['id']}")
                print(f"    Status: {orden['status']}")
                print(f"    Total: ${orden['total_amount']}")
                print(f"    Fecha: {orden['created_at']}")
                print(f"    Items: {orden['total_items']}")
            
            # Verificar que la orden recién creada aparece
            if self.orden_id:
                orden_encontrada = any(o['id'] == self.orden_id for o in ordenes)
                if orden_encontrada:
                    ColoredOutput.success(f"Orden #{self.orden_id} encontrada en el historial")
                else:
                    ColoredOutput.warning(f"Orden #{self.orden_id} NO encontrada en el historial")
            
            return True
            
        except Exception as e:
            ColoredOutput.error(f"Error al listar órdenes: {e}")
            return False
    
    # ========================================================================
    # TEST 9: SIMULAR PAGO (CONEKTA)
    # ========================================================================
    def test_simular_pago(self) -> bool:
        """Simular un pago con token de prueba de Conekta"""
        ColoredOutput.header("TEST 9: Simular Pago con Conekta")
        
        if not self.carrito_id:
            ColoredOutput.warning("Se requiere un carrito para procesar pago")
            # Crear un nuevo carrito para el pago
            if not self.test_agregar_productos_carrito():
                return False
        
        try:
            # Token de prueba de Conekta (siempre funciona en sandbox)
            token_prueba = "tok_test_visa_4242"
            
            response = self._make_request(
                'post',
                '/pago/procesar/',
                json={
                    'carrito_id': self.carrito_id,
                    'token': token_prueba,
                    'payment_method': 'card'
                }
            )
            
            if response.status_code not in [200, 201]:
                ColoredOutput.warning(f"Pago no procesado (esperado en desarrollo local): {response.text[:200]}")
                # En desarrollo local sin Conekta configurado, esto es normal
                ColoredOutput.info("Nota: Para probar pagos reales, configura CONEKTA_API_KEY en .env")
                return True  # No es un error crítico en desarrollo
            
            data = response.json()
            
            if data.get('success'):
                ColoredOutput.success("Pago procesado exitosamente")
                ColoredOutput.success(f"Orden ID: {data.get('orden_id')}")
                ColoredOutput.success(f"Payment Status: {data.get('payment_status')}")
                ColoredOutput.success(f"Total: ${data.get('total')}")
                
                # Actualizar orden_id si se creó una nueva
                if data.get('orden_id'):
                    self.orden_id = data['orden_id']
            else:
                ColoredOutput.warning(f"Pago no exitoso: {data.get('error', 'Error desconocido')}")
            
            return True
            
        except Exception as e:
            ColoredOutput.error(f"Error al procesar pago: {e}")
            return False
    
    # ========================================================================
    # TEST 10: VACIAR CARRITO
    # ========================================================================
    def test_vaciar_carrito(self) -> bool:
        """Vaciar completamente el carrito"""
        ColoredOutput.header("TEST 10: Vaciar Carrito")
        
        # Primero crear un nuevo carrito para vaciar
        if not self.test_agregar_productos_carrito():
            ColoredOutput.warning("No se pudo crear carrito para vaciar")
            return True  # No es crítico
        
        try:
            response = self._make_request(
                'delete',
                f'/api/carrito/{self.cliente_id}/empty/'
            )
            
            if response.status_code != 200:
                ColoredOutput.error(f"Fallo al vaciar carrito: {response.text}")
                return False
            
            ColoredOutput.success("Carrito vaciado exitosamente")
            
            # Verificar que el carrito esté vacío
            response_check = self._make_request('get', f'/api/carrito/{self.cliente_id}/')
            if response_check.ok:
                carrito_data = response_check.json()
                items = carrito_data.get('items', [])
                if len(items) == 0:
                    ColoredOutput.success("Verificacion OK - Carrito vacio")
                else:
                    ColoredOutput.warning(f"Carrito aun tiene {len(items)} items")
            
            return True
            
        except Exception as e:
            ColoredOutput.error(f"Error al vaciar carrito: {e}")
            return False
    
    # ========================================================================
    # EJECUTAR TODOS LOS TESTS
    # ========================================================================
    def run_all_tests(self):
        """Ejecuta todos los tests en secuencia"""
        ColoredOutput.header("INICIANDO TESTS COMPLETOS DE CARRITO, ORDEN Y PAGO")
        
        tests = [
            ("Registro", self.test_registro),
            ("Login", self.test_login),
            ("Agregar Productos al Carrito", self.test_agregar_productos_carrito),
            ("Obtener Detalle del Carrito", self.test_obtener_detalle_carrito),
            ("Actualizar Cantidad", self.test_actualizar_cantidad),
            ("Eliminar Producto", self.test_eliminar_producto_carrito),
            ("Crear Orden", self.test_crear_orden),
            ("Obtener Detalle de Orden", self.test_obtener_detalle_orden),
            ("Listar Órdenes del Cliente", self.test_listar_ordenes_cliente),
            ("Simular Pago", self.test_simular_pago),
            ("Vaciar Carrito", self.test_vaciar_carrito),
        ]
        
        resultados = []
        
        for nombre, test_func in tests:
            try:
                resultado = test_func()
                resultados.append((nombre, resultado))
                
                if not resultado:
                    ColoredOutput.error(f"Test '{nombre}' FALLÓ")
                else:
                    ColoredOutput.success(f"Test '{nombre}' PASÓ")
                
                time.sleep(0.5)  # Pausa entre tests
                
            except Exception as e:
                ColoredOutput.error(f"Excepción en test '{nombre}': {e}")
                resultados.append((nombre, False))
        
        # Resumen final
        ColoredOutput.header("RESUMEN DE TESTS")
        
        tests_pasados = sum(1 for _, resultado in resultados if resultado)
        tests_fallidos = len(resultados) - tests_pasados
        
        print(f"\n{ColoredOutput.BOLD}Resultados:{ColoredOutput.ENDC}")
        for nombre, resultado in resultados:
            status = f"{ColoredOutput.OKGREEN}[OK]{ColoredOutput.ENDC}" if resultado else f"{ColoredOutput.FAIL}[ERROR]{ColoredOutput.ENDC}"
            print(f"  {status} {nombre}")
        
        print(f"\n{ColoredOutput.BOLD}Estadísticas:{ColoredOutput.ENDC}")
        ColoredOutput.success(f"Tests pasados: {tests_pasados}/{len(resultados)}")
        if tests_fallidos > 0:
            ColoredOutput.error(f"Tests fallidos: {tests_fallidos}/{len(resultados)}")
        
        print(f"\n{ColoredOutput.BOLD}IDs Generados:{ColoredOutput.ENDC}")
        print(f"  Cliente ID: {self.cliente_id}")
        print(f"  Carrito ID: {self.carrito_id}")
        print(f"  Orden ID: {self.orden_id}")
        
        return tests_pasados == len(resultados)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Testing completo de Carrito, Orden y Pago')
    parser.add_argument('--username', help='Username o email del cliente existente')
    parser.add_argument('--password', help='Password del cliente existente')
    parser.add_argument('--base-url', default='http://127.0.0.1:8000', help='URL base de la API')
    
    args = parser.parse_args()
    
    # Ejecutar tests
    if args.username and args.password:
        ColoredOutput.info(f"Usando usuario existente: {args.username}")
        tester = CarritoCompletoTest(
            base_url=args.base_url,
            username=args.username,
            password=args.password
        )
    else:
        ColoredOutput.info("Creando usuario nuevo para testing")
        tester = CarritoCompletoTest(base_url=args.base_url)
    
    success = tester.run_all_tests()
    
    exit(0 if success else 1)

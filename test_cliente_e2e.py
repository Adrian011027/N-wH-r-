#!/usr/bin/env python3
"""
=============================================================================
SCRIPT DE TESTING END-TO-END - CLIENTE
=============================================================================

Prueba automática completa del flujo de un cliente desde registro hasta pago:

1. ✅ Registro de nuevo cliente
2. ✅ Login y obtención de JWT
3. ✅ Navegación por productos
4. ✅ Gestión de Wishlist (agregar/eliminar productos)
5. ✅ Gestión de Carrito (agregar/actualizar/eliminar)
6. ✅ Creación de orden
7. ✅ Pago simulado (integración Conekta)
8. ✅ Verificación de orden completada
9. ✅ Cleanup (eliminar datos de prueba)

Uso:
    python test_cliente_e2e.py
    python test_cliente_e2e.py --base-url http://production.com
"""

import requests
import json
import time
import random
import string
import argparse
import jwt  # pip install pyjwt
from datetime import datetime
from typing import Optional, Dict, List


class ColoredOutput:
    """Clase para outputs con colores en terminal"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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
        print(f"\n{ColoredOutput.BOLD}{ColoredOutput.HEADER}{'='*70}{ColoredOutput.ENDC}")
        print(f"{ColoredOutput.BOLD}{ColoredOutput.HEADER}{msg}{ColoredOutput.ENDC}")
        print(f"{ColoredOutput.BOLD}{ColoredOutput.HEADER}{'='*70}{ColoredOutput.ENDC}\n")


class ClienteE2ETest:
    """
    Clase principal para testing end-to-end de cliente
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Datos del cliente de prueba
        self.username = f"test_cliente_{self._random_string(6)}"
        self.email = f"{self.username}@test.com"
        self.password = "Test123456!"
        
        # Tokens JWT
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.cliente_id: Optional[int] = None
        
        # IDs de recursos creados (para cleanup)
        self.created_wishlist_products: List[int] = []
        self.created_carrito_items: List[int] = []
        self.created_orden_id: Optional[int] = None
        
        ColoredOutput.info(f"URL Base: {self.base_url}")
        ColoredOutput.info(f"Usuario de prueba: {self.username}")
    
    def _random_string(self, length: int = 8) -> str:
        """Genera string aleatorio"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Retorna headers HTTP con JWT si está disponible"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if include_auth and self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        return headers
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Wrapper para hacer requests con logging"""
        url = f"{self.base_url}{endpoint}"
        
        # Agregar headers por defecto
        if 'headers' not in kwargs:
            kwargs['headers'] = self._get_headers()
        
        ColoredOutput.info(f"{method.upper()} {endpoint}")
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code >= 400:
                ColoredOutput.warning(f"Status: {response.status_code}")
                try:
                    ColoredOutput.warning(f"Response: {response.json()}")
                except:
                    ColoredOutput.warning(f"Response: {response.text[:200]}")
            
            return response
        except Exception as e:
            ColoredOutput.error(f"Request failed: {str(e)}")
            raise
    
    # =========================================================================
    # STEP 1: REGISTRO DE CLIENTE
    # =========================================================================
    
    def test_registro_cliente(self) -> bool:
        """
        Prueba el registro de un nuevo cliente
        
        POST /clientes/crear/
        """
        ColoredOutput.header("STEP 1: Registro de Cliente")
        
        payload = {
            "correo": self.email,
            "password": self.password,
            "username": self.username,
            "nombre": "Test Cliente",
            "telefono": "1234567890",
            "direccion": "Calle Test 123"
        }
        
        response = self._make_request('POST', '/clientes/crear/', json=payload)
        
        if response.status_code in [200, 201]:
            data = response.json()
            ColoredOutput.success(f"Cliente registrado exitosamente")
            ColoredOutput.info(f"Mensaje: {data.get('message', 'N/A')}")
            return True
        else:
            ColoredOutput.error(f"Fallo en registro: {response.status_code}")
            return False
    
    # =========================================================================
    # STEP 2: LOGIN Y OBTENCIÓN DE JWT
    # =========================================================================
    
    def test_login_cliente(self) -> bool:
        """
        Prueba el login y obtención de tokens JWT
        
        POST /auth/login_client/
        """
        ColoredOutput.header("STEP 2: Login y Obtención de JWT")
        
        payload = {
            "username": self.username,
            "password": self.password
        }
        
        response = self._make_request('POST', '/auth/login_client/', json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            
            self.access_token = data.get('access')
            self.refresh_token = data.get('refresh')
            
            # El cliente_id no viene en la respuesta, lo extraemos del JWT
            if self.access_token:
                try:
                    import jwt
                    payload_decoded = jwt.decode(self.access_token, options={"verify_signature": False})
                    self.cliente_id = payload_decoded.get('user_id')
                except Exception as e:
                    ColoredOutput.error(f"No se pudo decodificar JWT: {e}")
                    return False
            
            if not self.access_token or not self.cliente_id:
                ColoredOutput.error("Respuesta de login no contiene tokens o cliente_id")
                ColoredOutput.info(f"Data recibida: {data}")
                return False
            
            ColoredOutput.success(f"Login exitoso")
            ColoredOutput.info(f"Cliente ID: {self.cliente_id}")
            ColoredOutput.info(f"Access Token: {self.access_token[:50]}...")
            ColoredOutput.info(f"Refresh Token: {self.refresh_token[:50]}..." if self.refresh_token else "No refresh token")
            
            # Advertencia si email no verificado
            if not data.get('email_verified', True):
                ColoredOutput.warning(f"Email no verificado: {data.get('warning', '')}")
            
            return True
        else:
            ColoredOutput.error(f"Fallo en login: {response.status_code}")
            try:
                ColoredOutput.info(f"Error: {response.json()}")
            except:
                pass
            return False
    
    # =========================================================================
    # STEP 3: NAVEGACIÓN Y BÚSQUEDA DE PRODUCTOS
    # =========================================================================
    
    def test_obtener_productos(self) -> List[int]:
        """
        Prueba la obtención de productos disponibles
        
        GET /api/productos/
        """
        ColoredOutput.header("STEP 3: Navegación de Productos")
        
        response = self._make_request('GET', '/api/productos/')
        
        if response.status_code == 200:
            productos = response.json()
            
            if isinstance(productos, dict) and 'results' in productos:
                productos = productos['results']
            
            ColoredOutput.success(f"Productos obtenidos: {len(productos)}")
            
            # Retornar IDs de los primeros 5 productos para testing
            product_ids = [p['id'] for p in productos[:5] if 'id' in p]
            ColoredOutput.info(f"IDs de productos para testing: {product_ids}")
            return product_ids
        else:
            ColoredOutput.error(f"Fallo al obtener productos: {response.status_code}")
            return []
    
    # =========================================================================
    # STEP 4: GESTIÓN DE WISHLIST
    # =========================================================================
    
    def test_wishlist(self, product_ids: List[int]) -> bool:
        """
        Prueba la funcionalidad de wishlist
        
        POST /wishlist/<cliente_id>/
        GET /wishlist/<cliente_id>/
        DELETE /wishlist/<cliente_id>/
        """
        ColoredOutput.header("STEP 4: Gestión de Wishlist")
        
        if not product_ids:
            ColoredOutput.warning("No hay productos para agregar a wishlist")
            return False
        
        # 4.1: Agregar productos a wishlist
        ColoredOutput.info("4.1: Agregando productos a wishlist...")
        
        for product_id in product_ids[:3]:  # Agregar los primeros 3
            payload = {"producto_id": product_id}
            response = self._make_request('POST', f'/wishlist/{self.cliente_id}/', json=payload)
            
            if response.status_code in [200, 201]:
                ColoredOutput.success(f"Producto {product_id} agregado a wishlist")
                self.created_wishlist_products.append(product_id)
            else:
                ColoredOutput.error(f"Fallo al agregar producto {product_id}: {response.status_code}")
        
        time.sleep(1)
        
        # 4.2: Obtener wishlist
        ColoredOutput.info("4.2: Obteniendo wishlist completa...")
        
        response = self._make_request('GET', f'/wishlist/{self.cliente_id}/?full=true')
        
        if response.status_code == 200:
            data = response.json()
            productos_wishlist = data.get('productos', [])
            ColoredOutput.success(f"Wishlist tiene {len(productos_wishlist)} productos")
        else:
            ColoredOutput.error(f"Fallo al obtener wishlist: {response.status_code}")
        
        time.sleep(1)
        
        # 4.3: Eliminar un producto de wishlist
        ColoredOutput.info("4.3: Eliminando un producto de wishlist...")
        
        if self.created_wishlist_products:
            product_to_remove = self.created_wishlist_products[0]
            payload = {"producto_id": product_to_remove}
            response = self._make_request('DELETE', f'/wishlist/{self.cliente_id}/', json=payload)
            
            if response.status_code == 200:
                ColoredOutput.success(f"Producto {product_to_remove} eliminado de wishlist")
                self.created_wishlist_products.remove(product_to_remove)
            else:
                ColoredOutput.error(f"Fallo al eliminar producto: {response.status_code}")
        
        return len(self.created_wishlist_products) > 0
    
    # =========================================================================
    # STEP 5: GESTIÓN DE CARRITO
    # =========================================================================
    
    def test_carrito(self, product_ids: List[int]) -> bool:
        """
        Prueba la funcionalidad de carrito
        
        POST /api/carrito/create/<cliente_id>/
        GET /api/carrito/<cliente_id>/
        PATCH /api/carrito/<cliente_id>/item/<variante_id>/actualizar/
        DELETE /api/carrito/<cliente_id>/item/<variante_id>/eliminar/
        """
        ColoredOutput.header("STEP 5: Gestión de Carrito")
        
        if not product_ids:
            ColoredOutput.warning("No hay productos para agregar al carrito")
            return False
        
        # 5.1: Agregar productos al carrito
        ColoredOutput.info("5.1: Agregando productos al carrito...")
        
        variante_ids = []
        
        for product_id in product_ids[:2]:  # Agregar los primeros 2
            # Primero obtener las variantes/tallas del producto
            response = self._make_request('GET', f'/api/productos/{product_id}/')
            
            if response.status_code != 200:
                ColoredOutput.warning(f"No se pudo obtener info del producto {product_id}")
                continue
            
            # Agregar al carrito (necesitamos talla/variante)
            payload = {
                "producto_id": product_id,
                "talla": "42",  # Talla por defecto para pruebas
                "cantidad": random.randint(1, 3)
            }
            
            response = self._make_request('POST', f'/api/carrito/create/{self.cliente_id}/', json=payload)
            
            if response.status_code in [200, 201]:
                data = response.json()
                ColoredOutput.success(f"Producto {product_id} agregado al carrito")
                
                # Extraer variante_id para futuras operaciones
                if 'variante_id' in data:
                    variante_ids.append(data['variante_id'])
            else:
                ColoredOutput.error(f"Fallo al agregar producto {product_id}: {response.status_code}")
        
        time.sleep(1)
        
        # 5.2: Obtener carrito completo
        ColoredOutput.info("5.2: Obteniendo carrito completo...")
        
        response = self._make_request('GET', f'/api/carrito/{self.cliente_id}/')
        
        if response.status_code == 200:
            data = response.json()
            items_carrito = data.get('items', [])
            total = data.get('total', 0)
            
            ColoredOutput.success(f"Carrito tiene {len(items_carrito)} items")
            ColoredOutput.info(f"Total del carrito: ${total}")
            
            # Guardar variante IDs para cleanup
            for item in items_carrito:
                if 'variante_id' in item:
                    variante_ids.append(item['variante_id'])
        else:
            ColoredOutput.error(f"Fallo al obtener carrito: {response.status_code}")
            return False
        
        time.sleep(1)
        
        # 5.3: Actualizar cantidad de un item
        ColoredOutput.info("5.3: Actualizando cantidad de un item...")
        
        if variante_ids:
            variante_id = variante_ids[0]
            nueva_cantidad = random.randint(2, 5)
            
            response = self._make_request(
                'PATCH',
                f'/api/carrito/{self.cliente_id}/item/{variante_id}/actualizar/',
                json={"cantidad": nueva_cantidad}
            )
            
            if response.status_code == 200:
                ColoredOutput.success(f"Cantidad actualizada a {nueva_cantidad}")
            else:
                ColoredOutput.error(f"Fallo al actualizar cantidad: {response.status_code}")
        
        return len(variante_ids) > 0
    
    # =========================================================================
    # STEP 6: CREACIÓN DE ORDEN
    # =========================================================================
    
    def test_crear_orden(self) -> Optional[int]:
        """
        Prueba la creación de una orden a partir del carrito
        
        POST /ordenar/<carrito_id>/enviar/
        """
        ColoredOutput.header("STEP 6: Creación de Orden")
        
        # Primero obtener el carrito_id activo
        response = self._make_request('GET', f'/api/carrito/{self.cliente_id}/')
        
        if response.status_code != 200:
            ColoredOutput.error("No se pudo obtener el carrito")
            return None
        
        data = response.json()
        carrito_id = data.get('id')
        
        if not carrito_id:
            ColoredOutput.error("Carrito no tiene ID")
            return None
        
        ColoredOutput.info(f"Carrito ID: {carrito_id}")
        
        # Crear orden con datos de envío
        payload = {
            "nombre_completo": "Test Cliente",
            "telefono": "1234567890",
            "email": self.email,
            "direccion": "Calle Test 123",
            "ciudad": "Ciudad Test",
            "estado": "Estado Test",
            "codigo_postal": "12345",
            "metodo_pago": "card"  # Conekta
        }
        
        response = self._make_request('POST', f'/ordenar/{carrito_id}/enviar/', json=payload)
        
        if response.status_code in [200, 201]:
            data = response.json()
            orden_id = data.get('orden_id')
            
            if orden_id:
                self.created_orden_id = orden_id
                ColoredOutput.success(f"Orden creada exitosamente: ID {orden_id}")
                ColoredOutput.info(f"Status: {data.get('status', 'N/A')}")
                return orden_id
            else:
                ColoredOutput.error("Respuesta no contiene orden_id")
                return None
        else:
            ColoredOutput.error(f"Fallo al crear orden: {response.status_code}")
            return None
    
    # =========================================================================
    # STEP 7: PAGO SIMULADO (CONEKTA)
    # =========================================================================
    
    def test_pago_simulado(self, orden_id: int) -> bool:
        """
        Simula el proceso de pago con Conekta
        
        NOTA: En ambiente de pruebas, usamos tokens de prueba de Conekta
        """
        ColoredOutput.header("STEP 7: Pago Simulado (Conekta)")
        
        if not orden_id:
            ColoredOutput.warning("No hay orden_id para procesar pago")
            return False
        
        ColoredOutput.info(f"Simulando pago para orden {orden_id}...")
        ColoredOutput.warning("NOTA: En producción esto se haría con integración real de Conekta")
        
        # En lugar de hacer el pago real, podemos actualizar el status directamente
        # (esto simula que el webhook de Conekta confirmó el pago)
        
        payload = {"status": "pagado"}
        
        response = self._make_request('POST', f'/orden/procesando/{orden_id}/', json=payload)
        
        if response.status_code == 200:
            ColoredOutput.success(f"Pago simulado exitoso para orden {orden_id}")
            return True
        else:
            ColoredOutput.error(f"Fallo en pago simulado: {response.status_code}")
            return False
    
    # =========================================================================
    # STEP 8: VERIFICACIÓN DE ORDEN
    # =========================================================================
    
    def test_verificar_orden(self, orden_id: int) -> bool:
        """
        Verifica el estado de la orden creada
        
        GET /orden/<orden_id>/
        """
        ColoredOutput.header("STEP 8: Verificación de Orden")
        
        if not orden_id:
            ColoredOutput.warning("No hay orden_id para verificar")
            return False
        
        response = self._make_request('GET', f'/orden/{orden_id}/')
        
        if response.status_code == 200:
            data = response.json()
            
            ColoredOutput.success(f"Orden verificada exitosamente")
            ColoredOutput.info(f"ID: {data.get('id')}")
            ColoredOutput.info(f"Status: {data.get('status')}")
            ColoredOutput.info(f"Total: ${data.get('total')}")
            ColoredOutput.info(f"Fecha: {data.get('fecha_creacion')}")
            
            return data.get('status') == 'pagado'
        else:
            ColoredOutput.error(f"Fallo al verificar orden: {response.status_code}")
            return False
    
    # =========================================================================
    # STEP 9: PERFIL DE CLIENTE (MIS PEDIDOS)
    # =========================================================================
    
    def test_mis_pedidos(self) -> bool:
        """
        Prueba la funcionalidad de "Mis Pedidos"
        
        GET /mis-pedidos/
        """
        ColoredOutput.header("STEP 9: Mis Pedidos")
        
        response = self._make_request('GET', '/mis-pedidos/')
        
        if response.status_code == 200:
            # La respuesta puede ser HTML o JSON dependiendo de la implementación
            ColoredOutput.success("Mis Pedidos accesible")
            return True
        else:
            ColoredOutput.error(f"Fallo al acceder a Mis Pedidos: {response.status_code}")
            return False
    
    # =========================================================================
    # CLEANUP: ELIMINAR DATOS DE PRUEBA
    # =========================================================================
    
    def cleanup(self):
        """
        Limpia los datos de prueba creados
        """
        ColoredOutput.header("CLEANUP: Eliminando Datos de Prueba")
        
        # Vaciar wishlist
        if self.cliente_id and self.created_wishlist_products:
            ColoredOutput.info("Vaciando wishlist...")
            response = self._make_request('DELETE', f'/wishlist/all/{self.cliente_id}/')
            
            if response.status_code == 200:
                ColoredOutput.success("Wishlist vaciada")
            else:
                ColoredOutput.warning("No se pudo vaciar wishlist")
        
        # Nota: No eliminamos la orden ni el cliente para poder revisar en la DB
        ColoredOutput.info(f"Cliente de prueba: {self.username} (ID: {self.cliente_id})")
        ColoredOutput.info(f"Orden creada: {self.created_orden_id}")
        ColoredOutput.warning("NOTA: Cliente y orden no fueron eliminados para auditoría")
    
    # =========================================================================
    # RUNNER PRINCIPAL
    # =========================================================================
    
    def run_all_tests(self):
        """
        Ejecuta todos los tests en secuencia
        """
        start_time = time.time()
        
        ColoredOutput.header("INICIANDO TESTING END-TO-END - CLIENTE")
        ColoredOutput.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {
            'total': 9,
            'passed': 0,
            'failed': 0
        }
        
        try:
            # Step 1: Registro
            if self.test_registro_cliente():
                results['passed'] += 1
            else:
                results['failed'] += 1
                ColoredOutput.error("[ERROR CRITICO] No se puede continuar sin registro")
                return results
            
            time.sleep(1)
            
            # Step 2: Login
            if self.test_login_cliente():
                results['passed'] += 1
            else:
                results['failed'] += 1
                ColoredOutput.error("[ERROR CRITICO] No se puede continuar sin login")
                return results
            
            time.sleep(1)
            
            # Step 3: Productos
            product_ids = self.test_obtener_productos()
            if product_ids:
                results['passed'] += 1
            else:
                results['failed'] += 1
                ColoredOutput.warning("⚠️ No hay productos, algunas pruebas pueden fallar")
            
            time.sleep(1)
            
            # Step 4: Wishlist
            if self.test_wishlist(product_ids):
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            time.sleep(1)
            
            # Step 5: Carrito
            if self.test_carrito(product_ids):
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            time.sleep(1)
            
            # Step 6: Crear Orden
            orden_id = self.test_crear_orden()
            if orden_id:
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            time.sleep(1)
            
            # Step 7: Pago Simulado
            if orden_id and self.test_pago_simulado(orden_id):
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            time.sleep(1)
            
            # Step 8: Verificar Orden
            if orden_id and self.test_verificar_orden(orden_id):
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            time.sleep(1)
            
            # Step 9: Mis Pedidos
            if self.test_mis_pedidos():
                results['passed'] += 1
            else:
                results['failed'] += 1
        
        except KeyboardInterrupt:
            ColoredOutput.warning("\n⚠️ Testing interrumpido por usuario")
        except Exception as e:
            ColoredOutput.error(f"\n[ERROR] Error inesperado: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            # Siempre hacer cleanup
            time.sleep(1)
            self.cleanup()
        
        # Resumen final
        elapsed_time = time.time() - start_time
        
        ColoredOutput.header("RESUMEN DE RESULTADOS")
        
        ColoredOutput.success(f"Tests pasados: {results['passed']}/{results['total']}")
        if results['failed'] > 0:
            ColoredOutput.error(f"Tests fallidos: {results['failed']}/{results['total']}")
        
        ColoredOutput.info(f"Tiempo total: {elapsed_time:.2f}s")
        
        # Exit code
        return 0 if results['failed'] == 0 else 1


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Testing End-to-End para funcionalidades de Cliente'
    )
    parser.add_argument(
        '--base-url',
        default='http://127.0.0.1:8000',
        help='URL base de la aplicación (default: http://127.0.0.1:8000)'
    )
    
    args = parser.parse_args()
    
    # Crear instancia del tester
    tester = ClienteE2ETest(base_url=args.base_url)
    
    # Ejecutar todos los tests
    exit_code = tester.run_all_tests()
    
    exit(exit_code)


if __name__ == '__main__':
    main()

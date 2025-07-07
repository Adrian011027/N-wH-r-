# store/urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# ─────────── Reset password ───────────
from .views.reset_password import (
    solicitar_reset, reset_password_confirm, reset_password_submit,
)

# ─────────── Vistas públicas / dashboard ───────────
from .views.views import (
    index, genero_view, registrarse,
    alta, lista_productos, editar_producto,
    get_categorias,
    login_user, logout_user,
    login_client, logout_client, create_categoria,
    dashboard_clientes, editar_cliente, perfil_cliente,
)

# ─────────── Carrito ───────────
from .views.carrito import (
    create_carrito,
    detalle_carrito_cliente,
    delete_producto_carrito,
    vaciar_carrito,
    carrito_cliente,      # protegida (cliente logueado)
    carrito_publico,      # pública (guest + logueado)
    finalizar_compra,
    actualizar_cantidad_producto, 
    detalle_carrito_session, 
    vaciar_carrito_guest,
    actualizar_cantidad_guest,
    eliminar_item_guest,
)

# ─────────── Clientes ───────────
from .views.client import (
    detalle_client, get_all_clients,
    create_client, update_client, delete_client,
    send_contact,
)

# ─────────── Usuarios ───────────
from .views.users import (
    create_user, get_user, update_user, delete_user,
)

# ─────────── Productos ───────────
from .views.products import (
    detalle_producto,
    get_all_products, create_product,
    update_productos, update_variant,
    delete_productos, delete_all_productos,
)

# ─────────── Wishlist ───────────
from .views.wishlist import (
    wishlist_detail, wishlist_all,
    get_cliente_id, producto_tallas, productos_por_ids,
)


# ─────────── Orden ─────────── 
from .views.orden import get_orden
# ───────────────────────── URLPATTERNS ─────────────────────────
urlpatterns = [
    # ---------- Recuperación de contraseña ----------
    path("recuperar/",                         solicitar_reset,        name="cliente_solicitar_reset"),
    path("recuperar/<uidb64>/<token>/",        reset_password_confirm,  name="cliente_reset_password_confirm"),
    path("recuperar/<uidb64>/<token>/submit/", reset_password_submit,   name="cliente_reset_password_submit"),

    # ---------- Front-end ----------

    path("",                           index,          name="index"),
    path("coleccion/<str:genero>/",    genero_view,    name="coleccion_genero"),
    path("registrarse/",               registrarse,    name="registrarse"),

    # Sesión cliente
    path("login-client/",   login_client,    name="login_client"),
    path("logout-client/",  logout_client,   name="logout_client"),
    path("perfil/",         perfil_cliente,  name="perfil_cliente"),

    # ---------- Carrito páginas ----------

    path("carrito/",             carrito_publico,  name="ver_carrito"),      # pública
    path("carrito/cliente/",     carrito_cliente,  name="carrito_cliente"),  # protegida opcional
    #path("carrito/finalizar/",   finalizar_compra, name="finalizar_compra"),

    # ---------- Carrito API ----------
    path('api/carrito/guest/',            detalle_carrito_session, name='detalle_carrito_session'),  # 
    path('api/carrito/guest/empty/',     vaciar_carrito_guest,  name='vaciar_carrito_guest'),
    path('api/carrito/guest/item/<int:variante_id>/actualizar/', actualizar_cantidad_guest, name='actualizar_cantidad_guest'),
    path('api/carrito/guest/item/<int:variante_id>/eliminar/', eliminar_item_guest, name='eliminar_item_guest'),

    path("api/carrito/create/<int:cliente_id>/",                                   create_carrito,            name="create_carrito"),
    path("api/carrito/<int:cliente_id>/",                                          detalle_carrito_cliente,   name="detalle_carrito"),
    path("api/carrito/<int:cliente_id>/empty/",                                    vaciar_carrito,            name="vaciar_carrito"),
    path("api/carrito/<int:cliente_id>/item/<int:variante_id>/actualizar/",        actualizar_cantidad_producto, name="actualizar_cantidad_producto"),
    path("api/carrito/<int:cliente_id>/item/<int:variante_id>/eliminar/",          delete_producto_carrito,      name="delete_producto_carrito"),

    path('create-client/', create_client, name='create_client'),

    # ---------- Dashboard ----------
    path("dashboard/login/",   login_user,            name="login_user"),
    path("dashboard/logout/",  logout_user,           name="logout_user"),
    path("dashboard/productos/",                 lista_productos,    name="dashboard_productos"),
    path("dashboard/productos/crear/",           alta,               name="dashboard_alta"),
    path("dashboard/productos/editar/<int:id>/", editar_producto,    name="editar_producto"),

    path("dashboard/clientes/",                  dashboard_clientes, name="dashboard_clientes"),
    path("dashboard/clientes/editar/<int:id>/",  editar_cliente,     name="editar_cliente"),

    # ---------- Productos ----------
    path("producto/<int:id>/",                      detalle_producto,  name="detalle_producto"),
    path("api/productos/",                          get_all_products,  name="get_all_products"),
    path("api/productos/crear/",                    create_product,    name="create_product"),
    path("api/productos/update/<int:id>/",          update_productos,  name="update_product"),
    path("api/productos/delete/<int:id>/",          delete_productos,  name="delete_product"),
    path("api/productos/delete/all/",               delete_all_productos, name="delete_all_productos"),
    path("api/variantes/update/<int:variante_id>/", update_variant,    name="update_variant"),

    path("api/categorias/",       get_categorias,   name="get_categorias"),
    path("api/categorias/crear/", create_categoria, name="create_categoria"),

    # ---------- Clientes ----------
    path("clientes/",                get_all_clients, name="get_all_clients"),
    path("clientes/<int:id>/",       detalle_client,  name="detalle_client"),
    path("clientes/crear/",          create_client,   name="create_client"),
    path("clientes/update/<int:id>/", update_client,  name="update_client"),
    path("clientes/delete/<int:id>/", delete_client,  name="delete_client"),
    path("api/cliente_id/<str:username>/", get_cliente_id, name="get_cliente_id"),
    path("contact/send/<int:id>/",         send_contact,   name="send_contact"),

    # ---------- Usuarios ----------
    path("user/get/",             get_user,    name="get_user"),
    path("user/create/",          create_user, name="create_user"),
    path("user/update/<int:id>/", update_user, name="update_user"),
    path("user/delete/<int:id>/", delete_user, name="delete_user"),

    # ---------- Wishlist ----------

    path("wishlist/<int:id_cliente>/",       wishlist_detail, name="wishlist_detail"),
    path("wishlist/all/<int:id_cliente>/",   wishlist_all,    name="wishlist_all"),
    path("api/productos/<int:id_producto>/", producto_tallas, name="producto_tallas"),
    path("api/productos_por_ids/",           productos_por_ids, name="productos_por_ids"),

    # ---------- Alias antiguo ----------
    path("registro/", alta, name="alta"),

    #-------------------- Orden ---------------------
    #path('orden/<int:id_producto>/', orden, name='orden'),
    path('ordenar/<int:carrito_id>/', finalizar_compra, name='finalizar_compra'),
    path('orden/<int:id>/', get_orden, name='get_orden'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

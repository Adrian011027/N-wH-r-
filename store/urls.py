from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# ─────────── Reset password ───────────
from .views.reset_password import (
    solicitar_reset, reset_password_confirm, reset_password_submit,
)

# ─────────── Email Verification ───────────
from .views.email_verification import (
    verificar_email, reenviar_verificacion, estado_verificacion
)

# ─────────── Auth con JWT ───────────
from .views import auth
from .views.views import (
    index, genero_view, registrarse,logout_client,logout_user,
    login_user, login_client, refresh_token, create_categoria, get_categorias, update_categoria, delete_categoria,
    categorias_por_genero, producto_aleatorio_subcategoria
)

# ─────────── Carrito ───────────
from .views.carrito import (
    create_carrito, detalle_carrito_cliente, delete_producto_carrito,
    vaciar_carrito, carrito_cliente, carrito_publico, finalizar_compra,
    actualizar_cantidad_producto, detalle_carrito_session,
    vaciar_carrito_guest, actualizar_cantidad_guest, eliminar_item_guest,
    mostrar_confirmacion_compra, mostrar_formulario_confirmacion,
    enviar_ticket_whatsapp, enviar_ticket_email,
)

# ─────────── Clientes ───────────
from .views.client import (
    detalle_client, get_all_clients,
    create_client, update_client, delete_client, send_contact,
    editar_perfil, mis_pedidos,
)

# ─────────── Usuarios (admin) ───────────
from .views.users import create_user, get_user, update_user, delete_user

# ─────────── Productos ───────────
from .views.products import (
    detalle_producto, get_all_products, create_product,
    update_productos, update_variant, create_variant,
    delete_productos, delete_all_productos,
)

# ─────────── Wishlist ───────────
from .views.wishlist import (
    wishlist_detail, wishlist_all,
    get_cliente_id, producto_tallas, productos_por_ids,
)

# ─────────── Orden ───────────
from .views.orden import (
    eliminar_orden, get_orden, update_status, procesar_por_link, eliminar_producto, dashboard_ordenes,
    get_all_ordenes, cambiar_estado_orden
)

# ─────────── Pago (Conekta) ───────────
from .views.payment import (
    mostrar_formulario_pago_conekta, procesar_pago_conekta, webhook_conekta,
    pago_exitoso, pago_cancelado, crear_checkout_conekta, verificar_orden_creada
)

# ─────────── Subcategorías ───────────
from .views.subcategorias import (
    get_subcategorias, create_subcategoria, update_subcategoria, delete_subcategoria, 
    get_subcategorias_por_categoria, subcategorias_por_categoria_query
)


# ─────────── Dashboard ───────────
from .views.views import (
    lista_productos, alta, editar_producto,
    dashboard_clientes, editar_cliente, dashboard_categorias, login_user_page, dashboard_subcategorias,
)

# ─────────── Búsqueda y Filtros ───────────
from .views.search import (
    search_products, get_filter_options, search_page
)

# ───────────────────────── URLPATTERNS ─────────────────────────
urlpatterns = [
    # ---------- Recuperación de contraseña ----------
    path("recuperar/",                         solicitar_reset,        name="cliente_solicitar_reset"),
    path("recuperar/<uidb64>/<token>/",        reset_password_confirm, name="cliente_reset_password_confirm"),
    path("recuperar/<uidb64>/<token>/submit/", reset_password_submit,  name="cliente_reset_password_submit"),

    # ---------- Email Verification ----------
    path("verificar-email/<str:token>/",       verificar_email,       name="verificar_email"),
    path("api/auth/reenviar-verificacion/",    reenviar_verificacion, name="reenviar_verificacion"),
    path("api/auth/estado-verificacion/",      estado_verificacion,   name="estado_verificacion"),

    # ---------- Front-end público ----------
    path("",                           index,          name="index"),
    path("coleccion/<str:genero>/",    genero_view,    name="coleccion_genero"),
    path("registrarse/",               registrarse,    name="registrarse"),
    path("buscar/",                    search_page,    name="search_page"),

    # ---------- Categorías y Subcategorías API ----------
    path("api/categorias-por-genero/",           categorias_por_genero,    name="categorias_por_genero"),
    path("api/producto-aleatorio-subcategoria/", producto_aleatorio_subcategoria, name="producto_aleatorio_subcategoria"),
    path("api/categorias/",                      get_categorias,           name="get_categorias"),
    path("api/categorias/crear/",                create_categoria,         name="create_categoria"),
    path("api/categorias/actualizar/<int:id>/",  update_categoria,         name="update_categoria"),
    path("api/categorias/eliminar/<int:id>/",    delete_categoria,         name="delete_categoria"),
    path("api/subcategorias/",                   get_subcategorias,        name="get_subcategorias"),
    path("api/subcategorias/crear/",             create_subcategoria,      name="create_subcategoria"),
    path("api/subcategorias/actualizar/<int:id>/", update_subcategoria,    name="update_subcategoria"),
    path("api/subcategorias/eliminar/<int:id>/", delete_subcategoria,      name="delete_subcategoria"),
    path("api/subcategorias-por-categoria/", subcategorias_por_categoria_query, name="subcategorias_por_categoria_query"),
    path("api/subcategorias-por-categoria/<int:categoria_id>/", get_subcategorias_por_categoria, name="get_subcategorias_por_categoria"),
    path("api/search/",                search_products,     name="search_products"),
    path("api/search/filters/",        get_filter_options,  name="filter_options"),

    # ---------- Auth (JWT) ----------
    path("api/auth/login/",   auth.login,          name="api_login"),
    path("api/auth/refresh/", auth.refresh_token,  name="api_refresh_token"),
    path("api/auth/logout/",  auth.logout,         name="api_logout"),
    path("api/auth/verify/",  auth.verify_token,   name="api_verify_token"),
    
    # Auth antiguo (compatibilidad)
    path("auth/login_user/",   login_user,    name="login_user"),
    path("auth/login_client/", login_client,  name="login_client"),
    path("auth/refresh/",      refresh_token, name="refresh_token"),
    path("auth/logout_client/", logout_client, name="logout_client"),   
    path("auth/logout_user/",   logout_user,   name="logout_user"),



    # ---------- Categorías API ----------
    path("api/categorias/",                     get_categorias,    name="get_categorias"),
    path("api/categorias/crear/",               create_categoria,  name="create_categoria"),
    path("api/categorias/actualizar/<int:id>/", update_categoria,  name="update_categoria"),
    path("api/categorias/eliminar/<int:id>/",   delete_categoria,  name="delete_categoria"),

    # ---------- Carrito (páginas públicas) ----------
    path("carrito/",         carrito_publico,  name="ver_carrito"),
    path("carrito/cliente/", carrito_cliente,  name="carrito_cliente"),

    # ---------- Carrito API ----------
    path("api/carrito/guest/",                                  detalle_carrito_session,        name="detalle_carrito_session"),
    path("api/carrito/guest/empty/",                            vaciar_carrito_guest,           name="vaciar_carrito_guest"),
    path("api/carrito/guest/item/<int:variante_id>/actualizar/", actualizar_cantidad_guest,     name="actualizar_cantidad_guest"),
    path("api/carrito/guest/item/<int:variante_id>/eliminar/",   eliminar_item_guest,           name="eliminar_item_guest"),
    path("api/carrito/create/<int:cliente_id>/",                 create_carrito,                name="create_carrito"),
    path("api/carrito/<int:cliente_id>/",                        detalle_carrito_cliente,       name="detalle_carrito"),
    path("api/carrito/<int:cliente_id>/empty/",                  vaciar_carrito,                name="vaciar_carrito"),
    path("api/carrito/<int:cliente_id>/item/<int:variante_id>/actualizar/", actualizar_cantidad_producto, name="actualizar_cantidad_producto"),
    path("api/carrito/<int:cliente_id>/item/<int:variante_id>/eliminar/",   delete_producto_carrito,     name="delete_producto_carrito"),

    # ---------- Clientes ----------
    path("clientes/",                 get_all_clients, name="get_all_clients"),
    path("clientes/<int:id>/",        detalle_client,  name="detalle_client"),
    path("clientes/crear/",           create_client,   name="create_client"),
    path("clientes/update/<int:id>/", update_client,   name="update_client"),
    path("clientes/delete/<int:id>/", delete_client,   name="delete_client"),
    path("perfil/<int:id>/",          editar_perfil,   name="editar_perfil"),
    path("mis-pedidos/",              mis_pedidos,     name="mis_pedidos"),
    path("api/cliente_id/<str:username>/", get_cliente_id, name="get_cliente_id"),
    path("contact/send/<int:id>/",         send_contact,   name="send_contact"),

    # ---------- Usuarios (solo admin JWT) ----------
    path("api/users/",                  get_user,    name="get_user"),
    path("api/users/create/",           create_user, name="create_user"),
    path("api/users/update/<int:id>/",  update_user, name="update_user"),
    path("api/users/delete/<int:id>/",  delete_user, name="delete_user"),

    # ---------- Productos ----------
    path("producto/<int:id>/",                      detalle_producto,  name="detalle_producto"),
    path("api/productos/",                          get_all_products,  name="get_all_products"),
    path("api/productos/crear/",                    create_product,    name="create_product"),
    path("api/productos/update/<int:id>/",          update_productos,  name="update_product"),
    path("api/productos/delete/<int:id>/",          delete_productos,  name="delete_product"),
    path("api/productos/delete/all/",               delete_all_productos, name="delete_all_productos"),
    path("api/variantes/create/",                   create_variant,    name="create_variant"),
    path("api/variantes/update/<int:variante_id>/", update_variant,    name="update_variant"),

    # ---------- Wishlist ----------
    path("wishlist/<int:id_cliente>/",       wishlist_detail, name="wishlist_detail"),
    path("wishlist/all/<int:id_cliente>/",   wishlist_all,    name="wishlist_all"),
    path("api/productos/<int:id_producto>/", producto_tallas, name="producto_tallas"),
    path("api/productos_por_ids/",           productos_por_ids, name="productos_por_ids"),

    # ---------- Orden ----------
    path("ordenar/<int:carrito_id>/",           mostrar_formulario_confirmacion, name="mostrar_formulario_confirmacion"),
    path("ordenar/<int:carrito_id>/enviar/",    finalizar_compra,                name="finalizar_compra"),
    path("ordenar/<int:carrito_id>/exito/",     mostrar_confirmacion_compra,     name="mostrar_confirmacion_compra"),
    path("ordenar/<int:carrito_id>/",           mostrar_confirmacion_compra,     name="confirmar_compra"),
    path("orden/<int:id>/",                     get_orden,                       name="get_orden"),
    path("orden/procesando/<int:id>/",          update_status,                   name="update_status"),
    path("orden/procesando/link/<str:token>/",  procesar_por_link,               name="procesar_por_link"),
    path("orden/delete/<int:id>/",              eliminar_orden,                  name="eliminar_orden"),
    path("orden/delete/<int:orden_id>/<int:producto_id>", eliminar_producto,     name="eliminar_producto"),
    
    # ---------- API Órdenes (Admin) ----------
    path("api/admin/ordenes/",                         get_all_ordenes,      name="api_get_all_ordenes"),
    path("api/admin/ordenes/<int:id>/estado/",         cambiar_estado_orden, name="api_cambiar_estado_orden"),
    
    # ---------- Pago con Conekta ----------
    path("pago/crear-checkout/",                     crear_checkout_conekta,          name="crear_checkout_conekta"),
    path("pago/formulario/<int:carrito_id>/",          mostrar_formulario_pago_conekta, name="formulario_pago_conekta"),
    path("pago/procesar/",                             procesar_pago_conekta,           name="procesar_pago_conekta"),
    path("pago/webhook/conekta/",                      webhook_conekta,                 name="webhook_conekta"),
    path("pago/verificar-orden/",                      verificar_orden_creada,          name="verificar_orden_creada"),
    path("pago/exitoso/",                              pago_exitoso,                    name="pago_exitoso"),
    path("pago/cancelado/",                            pago_cancelado,                  name="pago_cancelado"),
    
    # ---------- Envío de Tickets ----------
    path("api/orden/<int:carrito_id>/ticket/whatsapp/", enviar_ticket_whatsapp, name="enviar_ticket_whatsapp"),
    path("api/orden/<int:carrito_id>/ticket/email/",    enviar_ticket_email,    name="enviar_ticket_email"),

       # ---------- Dashboard ----------
    path("dashboard/login/",                     login_user_page,           name="login_user"),
    path("dashboard/productos/",                 lista_productos,      name="dashboard_productos"),
    path("dashboard/productos/crear/",           alta,                 name="dashboard_alta"),
    path("dashboard/productos/editar/<int:id>/", editar_producto,      name="editar_producto"),
    path("dashboard/clientes/",                  dashboard_clientes,   name="dashboard_clientes"),
    path("dashboard/clientes/editar/<int:id>/",  editar_cliente,       name="editar_cliente"),
    path("dashboard/categorias/",                dashboard_categorias, name="dashboard_categorias"),  # NUEVO PANEL
    path("dashboard/subcategorias/",             dashboard_subcategorias, name="dashboard_subcategorias"),
    path("dashboard/ordenes/",                   dashboard_ordenes, name="dashboard_ordenes"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

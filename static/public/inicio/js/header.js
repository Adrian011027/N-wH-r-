// header.js
function decodeJWT(token) {
  try {
    const payload = token.split(".")[1];
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
  } catch {
    return {};
  }
}

export function setupHeaderScroll() {
  const header = document.querySelector("header");
  const logo = document.getElementById("Logo");
  
  window.addEventListener("scroll", () => {
    const scrollY = window.scrollY;
    
    // Toggle clase scrolled
    header.classList.toggle("scrolled", scrollY > 10);
    
    // ReducciÃ³n gradual del logo SOLO EN WEB (desktop)
    if (logo && window.innerWidth > 768) {
      const maxScroll = 200;
      const minSize = 130;
      const maxSize = 200;
      
      if (scrollY <= maxScroll) {
        const progress = scrollY / maxScroll;
        const newSize = maxSize - (progress * (maxSize - minSize));
        logo.style.width = `${newSize}px`;
      } else {
        logo.style.width = `${minSize}px`;
      }
    }
    // En mobile y tablet, no aplicar ningÃºn cambio de tamaÃ±o (usa el CSS)
  });
}

export function setupHeaderPanels() {
  document.addEventListener("DOMContentLoaded", () => {
    const overlay       = document.querySelector(".page-overlay");
    const clientePanel  = document.getElementById("cliente-panel");
    const loginPanel    = document.getElementById("login-panel");
    const wishlistPanel = document.getElementById("wishlist-panel");
    const contactPanel  = document.getElementById("contact-panel");

    const btnLogin   = document.getElementById("btn-login");
    const btnUser    = document.getElementById("btn-user-menu");
    const userSpan   = document.getElementById("cliente-username");

    const closeAllPanels = () => {
      document.querySelectorAll(".login-panel").forEach(p => p.classList.remove("open"));
      overlay.classList.remove("active");
      document.body.classList.remove("no-scroll");
      
      // Resetear vistas de cascada a su estado inicial
      // Login/Registro
      document.getElementById('view-login')?.classList.add('active');
      document.getElementById('view-register')?.classList.remove('active');
      // Cliente: Main/Pedidos/Perfil/Carrito/Wishlist/Contacto
      document.getElementById('view-cliente-main')?.classList.add('active');
      document.getElementById('view-cliente-pedidos')?.classList.remove('active');
      document.getElementById('view-cliente-perfil')?.classList.remove('active');
      document.getElementById('view-cliente-carrito')?.classList.remove('active');
      document.getElementById('view-cliente-wishlist')?.classList.remove('active');
      document.getElementById('view-cliente-contacto')?.classList.remove('active');
    };

    const openPanel = (panel) => {
      closeAllPanels();
      if (panel) {
        panel.classList.add("open");
        overlay.classList.add("active");
        document.body.classList.add("no-scroll");
      }
    };

    // --- Mostrar botones segÃºn JWT ---
    const access = localStorage.getItem("access");
    if (access) {
      const decoded = decodeJWT(access);
      if (btnLogin) btnLogin.style.display = "none";
      if (btnUser) btnUser.style.display = "inline-flex";
      if (userSpan) userSpan.textContent = decoded.username || `Cliente #${decoded.user_id}`;
    } else {
      if (btnLogin) btnLogin.style.display = "inline-flex";
      if (btnUser) btnUser.style.display = "none";
    }

    // Abrir login panel al click en "btn-login"
    btnLogin?.addEventListener("click", (e) => {
      e.preventDefault();
      openPanel(loginPanel);
    });

    // Abrir cliente panel al click en "btn-user-menu"
    btnUser?.addEventListener("click", (e) => {
      e.preventDefault();
      openPanel(clientePanel);
    });

    // Wishlist - ahora abre cascada dentro del panel cliente
    document.getElementById("link-wishlist")?.addEventListener("click", (e) => {
      e.preventDefault();
      // Si estamos en el panel cliente, mostrar cascada
      if (clientePanel?.classList.contains('open')) {
        viewClienteMain.classList.remove('active');
        document.getElementById('view-cliente-wishlist')?.classList.add('active');
        window.renderWishlistPanel?.();
      } else {
        // Fallback: abrir panel cliente y luego wishlist
        openPanel(clientePanel);
        setTimeout(() => {
          viewClienteMain.classList.remove('active');
          document.getElementById('view-cliente-wishlist')?.classList.add('active');
          window.renderWishlistPanel?.();
        }, 100);
      }
    });

    // Contacto - cascada
    document.getElementById("link-contacto")?.addEventListener("click", (e) => {
      e.preventDefault();
      viewClienteMain.classList.remove('active');
      document.getElementById('view-cliente-contacto')?.classList.add('active');
    });

    // Carrito - cascada
    document.getElementById("link-carrito")?.addEventListener("click", (e) => {
      e.preventDefault();
      viewClienteMain.classList.remove('active');
      document.getElementById('view-cliente-carrito')?.classList.add('active');
      cargarCarritoCascada();
    });

    // --- 🔙 BACK BUTTONS CARRITO, WISHLIST Y CONTACTO ---
    // Volver desde carrito
    document.getElementById('btn-back-carrito')?.addEventListener('click', () => {
      document.getElementById('view-cliente-carrito')?.classList.remove('active');
      viewClienteMain.classList.add('active');
    });

    // Cerrar panel desde carrito
    document.getElementById('close-carrito-panel')?.addEventListener('click', () => {
      closeAllPanels();
    });

    // Volver desde wishlist
    document.getElementById('btn-back-wishlist')?.addEventListener('click', () => {
      document.getElementById('view-cliente-wishlist')?.classList.remove('active');
      viewClienteMain.classList.add('active');
    });

    // Cerrar panel desde wishlist
    document.getElementById('close-wishlist-panel')?.addEventListener('click', () => {
      closeAllPanels();
    });

    // Volver desde contacto
    document.getElementById('btn-back-contacto')?.addEventListener('click', () => {
      document.getElementById('view-cliente-contacto')?.classList.remove('active');
      viewClienteMain.classList.add('active');
    });

    // Cerrar panel desde contacto
    document.getElementById('close-contacto-panel')?.addEventListener('click', () => {
      closeAllPanels();
    });

    // --- 🛒 CARGAR CARRITO EN CASCADA ---
    async function cargarCarritoCascada() {
      const container = document.getElementById('carrito-items-container');
      const countEl = document.getElementById('carrito-items-count');
      const mayoreoMsg = document.getElementById('carrito-mayoreo-msg');
      const checkoutBtn = document.getElementById('btn-checkout');
      const vaciarBtn = document.getElementById('btn-vaciar-carrito');
      const resumenSection = document.querySelector('#view-cliente-carrito .carrito-resumen');
      const actionsSection = document.querySelector('#view-cliente-carrito .carrito-actions');
      const counterSection = document.querySelector('#view-cliente-carrito .carrito-counter');
      const productsHeader = document.querySelector('#view-cliente-carrito .carrito-section-header');
      
      if (!container) return;
      
      container.innerHTML = '<p class="carrito-loading">Cargando tu carrito...</p>';
      
      const token = localStorage.getItem('access');
      const userId = localStorage.getItem('user_id');
      
      // Función para ocultar todo cuando está vacío
      const ocultarElementos = () => {
        if (resumenSection) resumenSection.style.display = 'none';
        if (actionsSection) actionsSection.style.display = 'none';
        if (counterSection) counterSection.style.display = 'none';
        if (productsHeader) productsHeader.style.display = 'none';
        if (mayoreoMsg) mayoreoMsg.style.display = 'none';
      };
      
      // Función para mostrar todo cuando hay items
      const mostrarElementos = () => {
        if (resumenSection) resumenSection.style.display = 'block';
        if (actionsSection) actionsSection.style.display = 'block';
        if (counterSection) counterSection.style.display = 'block';
        if (productsHeader) productsHeader.style.display = 'flex';
      };
      
      if (!token || !userId) {
        container.innerHTML = `
          <div class="carrito-empty">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="1.5">
              <circle cx="9" cy="21" r="1"/>
              <circle cx="20" cy="21" r="1"/>
              <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
            </svg>
            <h3>Tu carrito está vacío</h3>
            <p>Inicia sesión para ver tu carrito</p>
          </div>`;
        ocultarElementos();
        return;
      }
      
      try {
        const res = await fetch(`/api/carrito/${userId}/`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!res.ok) throw new Error('Error al cargar carrito');
        
        const data = await res.json();
        const items = data.items || [];
        const esMayoreo = data.mayoreo || false;
        
        if (items.length === 0) {
          container.innerHTML = `
            <div class="carrito-empty">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="1.5">
                <circle cx="9" cy="21" r="1"/>
                <circle cx="20" cy="21" r="1"/>
                <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
              </svg>
              <h3>Tu carrito está vacío</h3>
              <p>¡Explora nuestros productos!</p>
            </div>`;
          ocultarElementos();
          return;
        }
        
        // Mostrar elementos cuando hay items
        mostrarElementos();
        
        // Mostrar mensaje de mayoreo si aplica
        if (mayoreoMsg) {
          mayoreoMsg.style.display = esMayoreo ? 'flex' : 'none';
        }
        if (vaciarBtn) vaciarBtn.style.display = 'flex';
        
        // Calcular totales
        const totalItems = items.reduce((sum, item) => sum + item.cantidad, 0);
        const total = items.reduce((sum, item) => sum + Number(item.subtotal || 0), 0);
        
        // Actualizar contadores
        if (countEl) countEl.textContent = `${totalItems} producto${totalItems !== 1 ? 's' : ''}`;
        document.getElementById('carrito-subtotal').textContent = `$${total.toLocaleString('es-MX')}`;
        document.getElementById('carrito-total-final').textContent = `$${total.toLocaleString('es-MX')}`;
        
        // Renderizar items
        let html = '';
        items.forEach(item => {
          const variantText = [item.talla, item.color].filter(Boolean).join(' / ');
          html += `
            <div class="carrito-item" data-variante="${item.variante_id}">
              <img src="${item.imagen || '/static/images/placeholder.png'}" alt="${item.producto}" class="carrito-item-img">
              <div class="carrito-item-info">
                <span class="carrito-item-name">${item.producto}</span>
                ${variantText ? `<span class="carrito-item-variant">${variantText}</span>` : ''}
                <div class="carrito-item-bottom">
                  <div class="carrito-item-qty-control">
                    <button type="button" class="qty-btn qty-minus" data-variante="${item.variante_id}">−</button>
                    <span class="qty-value">${item.cantidad}</span>
                    <button type="button" class="qty-btn qty-plus" data-variante="${item.variante_id}">+</button>
                  </div>
                  <span class="carrito-item-price">$${Number(item.subtotal).toLocaleString('es-MX')}</span>
                </div>
              </div>
              <button type="button" class="carrito-item-remove" data-variante="${item.variante_id}" title="Eliminar">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>`;
        });
        
        container.innerHTML = html;
        
        // Event listeners para cantidad y eliminar
        container.querySelectorAll('.qty-minus').forEach(btn => {
          btn.addEventListener('click', () => actualizarCantidadCarrito(btn.dataset.variante, -1));
        });
        container.querySelectorAll('.qty-plus').forEach(btn => {
          btn.addEventListener('click', () => actualizarCantidadCarrito(btn.dataset.variante, 1));
        });
        container.querySelectorAll('.carrito-item-remove').forEach(btn => {
          btn.addEventListener('click', () => eliminarItemCarrito(btn.dataset.variante));
        });
        
      } catch (err) {
        console.error('Error cargando carrito:', err);
        container.innerHTML = '<p class="carrito-error">Error al cargar el carrito</p>';
      }
    }
    
    // Actualizar cantidad de item
    async function actualizarCantidadCarrito(varianteId, delta) {
      const token = localStorage.getItem('access');
      const userId = localStorage.getItem('user_id');
      if (!token || !userId) return;
      
      try {
        const res = await fetch(`/api/carrito/${userId}/item/${varianteId}/actualizar/`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ delta })
        });
        
        if (res.ok) {
          cargarCarritoCascada(); // Recargar
        }
      } catch (err) {
        console.error('Error actualizando cantidad:', err);
      }
    }
    
    // Eliminar item del carrito
    async function eliminarItemCarrito(varianteId) {
      const token = localStorage.getItem('access');
      const userId = localStorage.getItem('user_id');
      if (!token || !userId) return;
      
      try {
        const res = await fetch(`/api/carrito/${userId}/item/${varianteId}/eliminar/`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.ok) {
          cargarCarritoCascada(); // Recargar
        }
      } catch (err) {
        console.error('Error eliminando item:', err);
      }
    }
    
    // Vaciar carrito completo
    document.getElementById('btn-vaciar-carrito')?.addEventListener('click', async () => {
      if (!confirm('¿Vaciar todo el carrito?')) return;
      
      const token = localStorage.getItem('access');
      const userId = localStorage.getItem('user_id');
      if (!token || !userId) return;
      
      try {
        const res = await fetch(`/api/carrito/${userId}/empty/`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.ok) {
          cargarCarritoCascada();
        }
      } catch (err) {
        console.error('Error vaciando carrito:', err);
      }
    });

 
    // --- ï¿½ðŸ”‘ LOGIN con JWT ---
    document.getElementById("loginForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.getElementById("username").value;
      const password = document.getElementById("password").value;
      const errorEl  = document.getElementById("login-error");

      try {
        const res = await fetch("/auth/login_client/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });

        if (!res.ok) throw new Error("Credenciales invalidas");
        const data = await res.json();

        // Guardamos tokens
        localStorage.setItem("access", data.access);
        localStorage.setItem("refresh", data.refresh);

        const decoded = decodeJWT(data.access);
        if (decoded) {
          localStorage.setItem("user_id", decoded.user_id || "");
          localStorage.setItem("role", decoded.role || "cliente");
        }
        
        // Guardar username, nombre y correo si vienen en la respuesta
        if (data.username) {
          localStorage.setItem("username", data.username);
        }
        if (data.nombre) {
          localStorage.setItem("nombre", data.nombre);
        }
        if (data.correo) {
          localStorage.setItem("correo", data.correo);
        }

        closeAllPanels();
        window.location.reload();
      } catch (err) {
        if (errorEl) errorEl.textContent = err.message;
      }
    });

    // --- ï¿½ CASCADA LOGIN/REGISTRO ---
    const viewLogin = document.getElementById('view-login');
    const viewRegister = document.getElementById('view-register');
    const btnShowRegister = document.getElementById('btn-show-register');
    const btnBackLogin = document.getElementById('btn-back-login');
    const closeRegisterPanel = document.getElementById('close-register-panel');

    // Mostrar vista de registro
    btnShowRegister?.addEventListener('click', () => {
      viewLogin.classList.remove('active');
      viewRegister.classList.add('active');
    });

    // Volver a login
    btnBackLogin?.addEventListener('click', () => {
      viewRegister.classList.remove('active');
      viewLogin.classList.add('active');
      // Limpiar mensajes
      document.getElementById('register-error').textContent = '';
      document.getElementById('register-success').textContent = '';
    });

    // Cerrar panel desde registro
    closeRegisterPanel?.addEventListener('click', () => {
      closeAllPanels();
      // Resetear a vista login
      viewRegister.classList.remove('active');
      viewLogin.classList.add('active');
    });

    // --- ðŸ“ REGISTRO ---
    document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const email = document.getElementById('reg-email').value.trim().toLowerCase();
      const pwd = document.getElementById('reg-pwd').value;
      const pwd2 = document.getElementById('reg-pwd2').value;
      const errorEl = document.getElementById('register-error');
      const successEl = document.getElementById('register-success');
      const submitBtn = e.target.querySelector('.register-submit-btn');
      const btnText = submitBtn.querySelector('.btn-text');
      const btnLoading = submitBtn.querySelector('.btn-loading');

      // Limpiar mensajes
      errorEl.textContent = '';
      successEl.textContent = '';

      // Validaciones
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        errorEl.textContent = 'Ingresa un correo electrÃ³nico vÃ¡lido';
        return;
      }
      if (pwd.length < 8) {
        errorEl.textContent = 'La contraseÃ±a debe tener al menos 8 caracteres';
        return;
      }
      if (pwd !== pwd2) {
        errorEl.textContent = 'Las contraseÃ±as no coinciden';
        return;
      }

      // Mostrar loading
      btnText.style.display = 'none';
      btnLoading.style.display = 'inline';
      submitBtn.disabled = true;

      try {
        const res = await fetch('/clientes/crear/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ correo: email, password: pwd }),
        });

        const data = await res.json();

        if (res.ok) {
          successEl.textContent = 'Â¡Cuenta creada! Revisa tu correo para verificarla.';
          // Limpiar formulario
          e.target.reset();
          document.querySelector('#regPwdStrength .strength-bar').className = 'strength-bar';
          document.querySelector('#regPwdStrength .strength-text').textContent = '';
          
          // DespuÃ©s de 2 segundos, volver al login
          setTimeout(() => {
            viewRegister.classList.remove('active');
            viewLogin.classList.add('active');
            successEl.textContent = '';
          }, 2500);
        } else {
          errorEl.textContent = data.error || 'Error al crear la cuenta';
        }
      } catch (err) {
        errorEl.textContent = 'Error de conexiÃ³n. Intenta de nuevo.';
      } finally {
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
        submitBtn.disabled = false;
      }
    });

    // Indicador de fuerza de contraseÃ±a
    document.getElementById('reg-pwd')?.addEventListener('input', (e) => {
      const password = e.target.value;
      const strengthContainer = document.getElementById('regPwdStrength');
      const bar = strengthContainer?.querySelector('.strength-bar');
      const text = strengthContainer?.querySelector('.strength-text');
      
      if (!bar || !text) return;

      if (!password) {
        bar.className = 'strength-bar';
        text.className = 'strength-text';
        text.textContent = '';
        return;
      }

      let strength = 0;
      if (password.length >= 8) strength++;
      if (password.length >= 12) strength++;
      if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
      if (/\d/.test(password)) strength++;
      if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++;

      let level = 'weak';
      let msg = 'ContraseÃ±a dÃ©bil';
      if (strength > 3) { level = 'strong'; msg = 'ContraseÃ±a fuerte'; }
      else if (strength > 2) { level = 'medium'; msg = 'ContraseÃ±a media'; }

      bar.className = `strength-bar ${level}`;
      text.className = `strength-text ${level}`;
      text.textContent = msg;
    });

    // Toggle password en formulario de registro
    document.querySelectorAll('#view-register .toggle-password').forEach(btn => {
      btn.addEventListener('click', () => {
        const wrapper = btn.closest('.password-wrapper');
        const input = wrapper.querySelector('input');
        const icon = btn.querySelector('i');
        
        if (input.type === 'password') {
          input.type = 'text';
          icon.classList.remove('fa-eye');
          icon.classList.add('fa-eye-slash');
        } else {
          input.type = 'password';
          icon.classList.remove('fa-eye-slash');
          icon.classList.add('fa-eye');
        }
      });
    });
    // --- ðŸ“¦ CASCADA CLIENTE: MIS PEDIDOS ---
    const viewClienteMain = document.getElementById('view-cliente-main');
    const viewClientePedidos = document.getElementById('view-cliente-pedidos');
    const linkMisPedidos = document.getElementById('link-mis-pedidos');
    const btnBackCliente = document.getElementById('btn-back-cliente');
    const closePedidosPanel = document.getElementById('close-pedidos-panel');

    // Mostrar vista de pedidos
    linkMisPedidos?.addEventListener('click', async (e) => {
      e.preventDefault();
      viewClienteMain.classList.remove('active');
      viewClientePedidos.classList.add('active');
      
      // Cargar pedidos
      await cargarPedidosResumen();
    });

    // Volver al menÃº principal
    btnBackCliente?.addEventListener('click', () => {
      viewClientePedidos.classList.remove('active');
      viewClienteMain.classList.add('active');
    });

    // Cerrar panel desde pedidos
    closePedidosPanel?.addEventListener('click', () => {
      closeAllPanels();
      // Resetear a vista principal
      viewClientePedidos.classList.remove('active');
      viewClienteMain.classList.add('active');
    });

    // FunciÃ³n para cargar los pedidos
    async function cargarPedidosResumen() {
      const loadingEl = document.getElementById('pedidos-loading');
      const emptyEl = document.getElementById('pedidos-empty');
      const listaEl = document.getElementById('pedidos-lista');
      const verMasEl = document.getElementById('pedidos-ver-mas');
      
      loadingEl.style.display = 'block';
      emptyEl.style.display = 'none';
      listaEl.innerHTML = '';
      verMasEl.style.display = 'none';

      const token = localStorage.getItem('access');
      if (!token) {
        loadingEl.style.display = 'none';
        emptyEl.style.display = 'block';
        return;
      }

      try {
        const res = await fetch('/api/cliente/ordenes/', {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!res.ok) throw new Error('Error al cargar pedidos');
        
        const data = await res.json();
        const ordenes = data.ordenes || [];

        loadingEl.style.display = 'none';

        if (ordenes.length === 0) {
          emptyEl.style.display = 'block';
          return;
        }

        // Mostrar solo los Ãºltimos 3 pedidos
        const recientes = ordenes.slice(0, 3);
        
        recientes.forEach(orden => {
          const card = crearPedidoCard(orden);
          listaEl.appendChild(card);
        });

        // Mostrar botÃ³n "Ver mÃ¡s" si hay mÃ¡s pedidos
        if (ordenes.length > 3) {
          verMasEl.style.display = 'block';
        }

      } catch (err) {
        console.error('Error cargando pedidos:', err);
        loadingEl.style.display = 'none';
        emptyEl.querySelector('p').textContent = 'Error al cargar pedidos';
        emptyEl.style.display = 'block';
      }
    }

    // Crear card de pedido
    function crearPedidoCard(orden) {
      const card = document.createElement('div');
      card.className = 'pedido-card';
      
      // Mapeo de estados
      const statusMap = {
        'pending': { text: 'Pendiente', class: 'pendiente' },
        'processing': { text: 'Procesando', class: 'procesando' },
        'shipped': { text: 'Enviado', class: 'enviado' },
        'delivered': { text: 'Entregado', class: 'entregado' },
        'cancelled': { text: 'Cancelado', class: 'cancelado' }
      };
      const status = statusMap[orden.status] || { text: orden.status, class: '' };
      
      // Crear thumbnails de productos (mÃ¡ximo 3)
      const items = orden.items || [];
      let thumbsHTML = items.slice(0, 3).map(item => 
        `<img src="${item.producto_imagen || '/static/images/placeholder.jpg'}" 
              alt="${item.producto_nombre}" 
              class="pedido-item-thumb">`
      ).join('');
      
      if (items.length > 3) {
        thumbsHTML += `<span class="pedido-items-more">+${items.length - 3}</span>`;
      }

      card.innerHTML = `
        <div class="pedido-card-header">
          <div>
            <div class="pedido-numero">Pedido #${orden.id}</div>
            <div class="pedido-fecha">${orden.created_at}</div>
          </div>
          <span class="pedido-status ${status.class}">${status.text}</span>
        </div>
        <div class="pedido-items">
          ${thumbsHTML}
        </div>
        <div class="pedido-card-footer">
          <div class="pedido-total">
            $${orden.total_amount.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
            <small>(${orden.total_items} ${orden.total_items === 1 ? 'artículo' : 'artículos'})</small>
          </div>
        </div>
      `;

      return card;
    }

    // --- ðŸ‘¤ CASCADA CLIENTE: EDITAR PERFIL ---
    const viewClientePerfil = document.getElementById('view-cliente-perfil');
    const linkEditarPerfil = document.getElementById('link-editar-perfil');
    const btnBackPerfil = document.getElementById('btn-back-perfil');
    const closePerfilPanel = document.getElementById('close-perfil-panel');
    let perfilDataOriginal = {};

    // Mostrar vista de perfil
    linkEditarPerfil?.addEventListener('click', async (e) => {
      e.preventDefault();
      viewClienteMain.classList.remove('active');
      viewClientePerfil.classList.add('active');
      await cargarDatosPerfil();
    });

    // Volver al menÃº principal desde perfil
    btnBackPerfil?.addEventListener('click', () => {
      viewClientePerfil.classList.remove('active');
      viewClienteMain.classList.add('active');
      resetearPerfilTabs();
    });

    // Cerrar panel desde perfil
    closePerfilPanel?.addEventListener('click', () => {
      closeAllPanels();
      viewClientePerfil.classList.remove('active');
      viewClienteMain.classList.add('active');
      resetearPerfilTabs();
    });

    // Tabs del perfil
    document.querySelectorAll('.perfil-tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const tabId = btn.dataset.perfilTab;
        // Desactivar todos
        document.querySelectorAll('.perfil-tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.perfil-tab-content').forEach(c => c.classList.remove('active'));
        // Activar seleccionado
        btn.classList.add('active');
        document.getElementById(`perfil-tab-${tabId}`)?.classList.add('active');
      });
    });

    function resetearPerfilTabs() {
      document.querySelectorAll('.perfil-tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.perfil-tab-content').forEach(c => c.classList.remove('active'));
      document.querySelector('.perfil-tab-btn')?.classList.add('active');
      document.getElementById('perfil-tab-info')?.classList.add('active');
    }

    // Cargar datos del perfil
    async function cargarDatosPerfil() {
      const token = localStorage.getItem('access');
      const userId = localStorage.getItem('user_id');
      if (!token || !userId) return;

      try {
        const res = await fetch(`/clientes/${userId}/`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Error al cargar perfil');
        
        const cliente = await res.json();
        perfilDataOriginal = { ...cliente };

        // Info - mostrar valores o placeholder invitando a completar
        document.getElementById('perfil-nombre').value = cliente.nombre || '';
        document.getElementById('perfil-nombre').placeholder = cliente.nombre ? '' : 'Agrega tu nombre completo';
        
        document.getElementById('perfil-username').value = cliente.username || '';
        document.getElementById('perfil-correo').value = cliente.correo || '';
        
        document.getElementById('perfil-telefono').value = cliente.telefono || '';
        document.getElementById('perfil-telefono').placeholder = cliente.telefono ? '' : 'Agrega tu teléfono';
        
        // Badge de verificación
        const badge = document.getElementById('email-verified-badge');
        if (cliente.email_verified) {
          badge.textContent = 'Verificado';
          badge.className = 'perfil-badge verified';
        } else {
          badge.textContent = 'Pendiente';
          badge.className = 'perfil-badge unverified';
        }

        // Dirección
        document.getElementById('perfil-calle').value = cliente.calle || '';
        document.getElementById('perfil-colonia').value = cliente.colonia || '';
        document.getElementById('perfil-cp').value = cliente.codigo_postal || '';
        document.getElementById('perfil-ciudad').value = cliente.ciudad || '';
        document.getElementById('perfil-estado').value = cliente.estado || '';
        document.getElementById('perfil-referencias').value = cliente.referencias || '';

        // Actualizar texto de botones según si hay datos o no
        actualizarBotonEditar('info', cliente);
        actualizarBotonEditar('direccion', cliente);
        
        // Mostrar mensaje si el perfil está incompleto
        const perfilIncompleto = !cliente.nombre || !cliente.telefono || !cliente.calle;
        const msgEl = document.getElementById('perfil-completar-msg');
        if (msgEl) {
          msgEl.style.display = perfilIncompleto ? 'flex' : 'none';
        }

      } catch (err) {
        console.error('Error cargando perfil:', err);
        document.getElementById('perfil-error').textContent = 'Error al cargar datos';
      }
    }

    // Actualizar botón "Editar" o "Agregar" según si hay datos
    function actualizarBotonEditar(section, cliente) {
      const btn = document.getElementById(`btn-edit-${section}`);
      if (!btn) return;

      let isEmpty = false;
      
      if (section === 'info') {
        // Si no tiene nombre o teléfono, mostrar "Completar"
        isEmpty = !cliente.nombre || !cliente.telefono;
      } else if (section === 'direccion') {
        // Si no tiene ningún dato de dirección
        isEmpty = !cliente.calle && !cliente.colonia && !cliente.ciudad;
      }

      if (isEmpty) {
        btn.textContent = 'Agregar';
        btn.classList.add('inviting');
      } else {
        btn.textContent = 'Editar';
        btn.classList.remove('inviting');
      }
    }

    // Botones de editar
    document.getElementById('btn-edit-info')?.addEventListener('click', function() {
      toggleEdicion('info', this);
    });
    document.getElementById('btn-edit-direccion')?.addEventListener('click', function() {
      toggleEdicion('direccion', this);
    });

    function toggleEdicion(section, btn) {
      const form = document.getElementById(`form-${section}`);
      const actions = document.getElementById(`actions-${section}`);
      const inputs = form.querySelectorAll('input, select, textarea');
      const isEditing = btn.classList.contains('editing');
      const originalText = btn.textContent;

      if (isEditing) {
        // Cancelar ediciÃ³n
        inputs.forEach(i => i.disabled = true);
        btn.classList.remove('editing');
        // Restaurar texto original basado en si hay datos
        actualizarBotonEditar(section, perfilDataOriginal);
        actions.style.display = 'none';
        // Restaurar valores originales
        restaurarValores(section);
      } else {
        // Activar ediciÃ³n
        inputs.forEach(i => {
          // El correo no se puede editar directamente
          if (i.id !== 'perfil-correo') {
            i.disabled = false;
          }
        });
        btn.classList.add('editing');
        btn.textContent = 'Cancelar';
        actions.style.display = 'flex';
      }
    }

    function restaurarValores(section) {
      if (section === 'info') {
        document.getElementById('perfil-nombre').value = perfilDataOriginal.nombre || '';
        document.getElementById('perfil-username').value = perfilDataOriginal.username || '';
        document.getElementById('perfil-telefono').value = perfilDataOriginal.telefono || '';
      } else if (section === 'direccion') {
        document.getElementById('perfil-calle').value = perfilDataOriginal.calle || '';
        document.getElementById('perfil-colonia').value = perfilDataOriginal.colonia || '';
        document.getElementById('perfil-cp').value = perfilDataOriginal.codigo_postal || '';
        document.getElementById('perfil-ciudad').value = perfilDataOriginal.ciudad || '';
        document.getElementById('perfil-estado').value = perfilDataOriginal.estado || '';
        document.getElementById('perfil-referencias').value = perfilDataOriginal.referencias || '';
      }
    }

    // Cancelar ediciÃ³n (funciÃ³n global)
    window.cancelarEdicionPerfil = function(section) {
      const btn = document.getElementById(`btn-edit-${section}`);
      toggleEdicion(section, btn);
    };

    // Guardar info personal
    document.getElementById('form-info')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      await guardarSeccion('info', {
        nombre: document.getElementById('perfil-nombre').value,
        username: document.getElementById('perfil-username').value,
        telefono: document.getElementById('perfil-telefono').value
      });
    });

    // Guardar direcciÃ³n
    document.getElementById('form-direccion')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      await guardarSeccion('direccion', {
        calle: document.getElementById('perfil-calle').value,
        colonia: document.getElementById('perfil-colonia').value,
        codigo_postal: document.getElementById('perfil-cp').value,
        ciudad: document.getElementById('perfil-ciudad').value,
        estado: document.getElementById('perfil-estado').value,
        referencias: document.getElementById('perfil-referencias').value
      });
    });

    async function guardarSeccion(section, data) {
      const token = localStorage.getItem('access');
      const userId = localStorage.getItem('user_id');
      const errorEl = document.getElementById('perfil-error');
      const successEl = document.getElementById('perfil-success');
      const btn = document.querySelector(`#form-${section} .perfil-btn-save`);

      errorEl.textContent = '';
      successEl.textContent = '';
      btn.disabled = true;
      btn.textContent = 'Guardando...';

      try {
        const res = await fetch(`/clientes/update/${userId}/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(data)
        });

        const result = await res.json();

        if (res.ok) {
          successEl.textContent = 'Â¡Cambios guardados!';
          perfilDataOriginal = { ...perfilDataOriginal, ...data };
          // Desactivar ediciÃ³n
          const editBtn = document.getElementById(`btn-edit-${section}`);
          toggleEdicion(section, editBtn);
          
          // Actualizar nombre en localStorage si cambiÃ³
          if (data.nombre) {
            localStorage.setItem('nombre', data.nombre);
          }
          if (data.username) {
            localStorage.setItem('username', data.username);
            document.getElementById('cliente-username').textContent = data.username;
          }

          setTimeout(() => successEl.textContent = '', 3000);
        } else {
          errorEl.textContent = result.error || 'Error al guardar';
        }
      } catch (err) {
        errorEl.textContent = 'Error de conexiÃ³n';
      } finally {
        btn.disabled = false;
        btn.textContent = 'Guardar';
      }
    }

    // Cambiar contraseÃ±a
    document.getElementById('form-seguridad')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const actual = document.getElementById('perfil-pwd-actual').value;
      const nueva = document.getElementById('perfil-pwd-nueva').value;
      const confirmar = document.getElementById('perfil-pwd-confirmar').value;
      const errorEl = document.getElementById('seguridad-error');
      const successEl = document.getElementById('seguridad-success');
      const btn = e.target.querySelector('.perfil-btn-save');

      errorEl.textContent = '';
      successEl.textContent = '';

      if (nueva.length < 8) {
        errorEl.textContent = 'La contraseÃ±a debe tener al menos 8 caracteres';
        return;
      }
      if (nueva !== confirmar) {
        errorEl.textContent = 'Las contraseÃ±as no coinciden';
        return;
      }

      btn.disabled = true;
      btn.textContent = 'Cambiando...';

      const token = localStorage.getItem('access');
      const userId = localStorage.getItem('user_id');

      try {
        const res = await fetch(`/clientes/update/${userId}/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            current_password: actual,
            new_password: nueva
          })
        });

        const result = await res.json();

        if (res.ok) {
          successEl.textContent = 'Â¡ContraseÃ±a cambiada correctamente!';
          e.target.reset();
          document.querySelector('#perfilPwdStrength .strength-bar').className = 'strength-bar';
          document.querySelector('#perfilPwdStrength .strength-text').textContent = '';
        } else {
          errorEl.textContent = result.error || 'Error al cambiar contraseÃ±a';
        }
      } catch (err) {
        errorEl.textContent = 'Error de conexiÃ³n';
      } finally {
        btn.disabled = false;
        btn.textContent = 'Cambiar ContraseÃ±a';
      }
    });

    // Indicador de fuerza de contraseÃ±a en perfil
    document.getElementById('perfil-pwd-nueva')?.addEventListener('input', (e) => {
      const password = e.target.value;
      const bar = document.querySelector('#perfilPwdStrength .strength-bar');
      const text = document.querySelector('#perfilPwdStrength .strength-text');
      
      if (!password) {
        bar.className = 'strength-bar';
        text.className = 'strength-text';
        text.textContent = '';
        return;
      }

      let strength = 0;
      if (password.length >= 8) strength++;
      if (password.length >= 12) strength++;
      if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
      if (/\d/.test(password)) strength++;
      if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++;

      let level = 'weak', msg = 'DÃ©bil';
      if (strength > 3) { level = 'strong'; msg = 'Fuerte'; }
      else if (strength > 2) { level = 'medium'; msg = 'Media'; }

      bar.className = `strength-bar ${level}`;
      text.className = `strength-text ${level}`;
      text.textContent = msg;
    });

    // Toggle password en perfil
    document.querySelectorAll('#view-cliente-perfil .toggle-password').forEach(btn => {
      btn.addEventListener('click', () => {
        const wrapper = btn.closest('.password-wrapper');
        const input = wrapper.querySelector('input');
        const icon = btn.querySelector('i');
        
        if (input.type === 'password') {
          input.type = 'text';
          icon.classList.replace('fa-eye', 'fa-eye-slash');
        } else {
          input.type = 'password';
          icon.classList.replace('fa-eye-slash', 'fa-eye');
        }
      });
    });

    // --- ðŸ”‘ LOGOUT con JWT ---
    document.getElementById("link-logout")?.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        localStorage.clear();
      } finally {
        window.location.href = "/";
      }
    });
  });
}



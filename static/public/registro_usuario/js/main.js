function getCSRFToken() {
  const el = document.querySelector('input[name="csrfmiddlewaretoken"]');
  return el ? el.value : '';
}

// Función para mostrar mensajes amigables
function showMessage(message, type = 'error') {
  // Remover mensaje anterior si existe
  const existingMsg = document.querySelector('.form-message');
  if (existingMsg) existingMsg.remove();

  const msgDiv = document.createElement('div');
  msgDiv.className = `form-message form-message-${type}`;
  msgDiv.innerHTML = `<span>${message}</span><button type="button" class="close-msg">&times;</button>`;
  
  const form = document.getElementById('registroForm');
  form.insertBefore(msgDiv, form.firstChild);
  
  // Scroll al mensaje
  msgDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
  
  // Auto-cerrar después de 5 segundos
  setTimeout(() => msgDiv.remove(), 5000);
  
  // Botón de cerrar
  msgDiv.querySelector('.close-msg').addEventListener('click', () => msgDiv.remove());
}

// Variables globales para Google Maps
let map = null;
let marker = null;
let autocomplete = null;
let autocompleteMap = null;
let selectedAddress = '';
let geocoder = null;

// Función de inicialización de Google Maps (llamada por el callback de la API)
window.initGoogleMaps = function() {
  // Inicializar geocoder
  geocoder = new google.maps.Geocoder();
  
  // Autocompletado en el campo de dirección del formulario
  const addressInput = document.getElementById('direccion');
  if (addressInput) {
    autocomplete = new google.maps.places.Autocomplete(addressInput, {
      types: ['address'],
      componentRestrictions: { country: 'mx' } // Restringir a México
    });
    
    autocomplete.addListener('place_changed', () => {
      const place = autocomplete.getPlace();
      if (place.formatted_address) {
        addressInput.value = place.formatted_address;
      }
    });
  }
  
  // Configurar modal del mapa
  setupMapModal();
};

function setupMapModal() {
  const mapModal = document.getElementById('mapModal');
  const btnOpenMap = document.getElementById('btnOpenMap');
  const closeMapModal = document.getElementById('closeMapModal');
  const btnCancelMap = document.getElementById('btnCancelMap');
  const btnConfirmMap = document.getElementById('btnConfirmMap');
  const mapSearchInput = document.getElementById('mapSearchInput');
  const selectedAddressEl = document.getElementById('selectedAddress');
  
  if (!mapModal || !btnOpenMap) return;
  
  // Abrir modal
  btnOpenMap.addEventListener('click', () => {
    mapModal.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Inicializar mapa si no existe
    if (!map) {
      initMap();
    }
    
    // Centrar en ubicación del usuario si está disponible
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const pos = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          map.setCenter(pos);
          map.setZoom(16);
          placeMarker(pos);
          reverseGeocode(pos);
        },
        () => {
          // Si no tiene permisos, centrar en Guadalajara
          map.setCenter({ lat: 20.6597, lng: -103.3496 });
        }
      );
    }
  });
  
  // Cerrar modal
  const closeModal = () => {
    mapModal.classList.remove('active');
    document.body.style.overflow = '';
  };
  
  closeMapModal.addEventListener('click', closeModal);
  btnCancelMap.addEventListener('click', closeModal);
  
  // Cerrar con Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && mapModal.classList.contains('active')) {
      closeModal();
    }
  });
  
  // Cerrar al hacer clic fuera del contenido
  mapModal.addEventListener('click', (e) => {
    if (e.target === mapModal) {
      closeModal();
    }
  });
  
  // Confirmar ubicación
  btnConfirmMap.addEventListener('click', () => {
    if (selectedAddress) {
      document.getElementById('direccion').value = selectedAddress;
      closeModal();
    } else {
      alert('Por favor selecciona una ubicación en el mapa');
    }
  });
  
  // Autocompletado en búsqueda del mapa
  if (mapSearchInput) {
    autocompleteMap = new google.maps.places.Autocomplete(mapSearchInput, {
      types: ['address'],
      componentRestrictions: { country: 'mx' }
    });
    
    autocompleteMap.addListener('place_changed', () => {
      const place = autocompleteMap.getPlace();
      if (place.geometry) {
        const pos = {
          lat: place.geometry.location.lat(),
          lng: place.geometry.location.lng()
        };
        map.setCenter(pos);
        map.setZoom(17);
        placeMarker(pos);
        selectedAddress = place.formatted_address;
        selectedAddressEl.textContent = selectedAddress;
        selectedAddressEl.style.color = '#333';
      }
    });
  }
}

function initMap() {
  const mapContainer = document.getElementById('map');
  if (!mapContainer) return;
  
  // Guadalajara como ubicación por defecto
  const defaultLocation = { lat: 20.6597, lng: -103.3496 };
  
  map = new google.maps.Map(mapContainer, {
    center: defaultLocation,
    zoom: 13,
    styles: [
      {
        featureType: 'poi',
        elementType: 'labels',
        stylers: [{ visibility: 'off' }]
      }
    ],
    mapTypeControl: false,
    streetViewControl: false,
    fullscreenControl: true
  });
  
  // Permitir seleccionar ubicación con clic
  map.addListener('click', (e) => {
    const pos = {
      lat: e.latLng.lat(),
      lng: e.latLng.lng()
    };
    placeMarker(pos);
    reverseGeocode(pos);
  });
}

function placeMarker(position) {
  if (marker) {
    marker.setPosition(position);
  } else {
    marker = new google.maps.Marker({
      position: position,
      map: map,
      draggable: true,
      animation: google.maps.Animation.DROP
    });
    
    // Permitir arrastrar el marcador
    marker.addListener('dragend', () => {
      const pos = {
        lat: marker.getPosition().lat(),
        lng: marker.getPosition().lng()
      };
      reverseGeocode(pos);
    });
  }
}

function reverseGeocode(position) {
  const selectedAddressEl = document.getElementById('selectedAddress');
  
  if (!geocoder) {
    geocoder = new google.maps.Geocoder();
  }
  
  geocoder.geocode({ location: position }, (results, status) => {
    if (status === 'OK' && results[0]) {
      selectedAddress = results[0].formatted_address;
      selectedAddressEl.textContent = selectedAddress;
      selectedAddressEl.style.color = '#333';
    } else {
      selectedAddressEl.textContent = 'No se pudo obtener la dirección';
      selectedAddressEl.style.color = '#ef4444';
    }
  });
}

// Función para evaluar fuerza de contraseña
function checkPasswordStrength(password) {
  let strength = 0;
  
  if (password.length >= 8) strength++;
  if (password.length >= 12) strength++;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
  if (/\d/.test(password)) strength++;
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++;
  
  if (strength <= 2) return 'weak';
  if (strength <= 3) return 'medium';
  return 'strong';
}

function updatePasswordStrength(password) {
  const strengthContainer = document.getElementById('pwdStrength');
  if (!strengthContainer) return;
  
  const bar = strengthContainer.querySelector('.strength-bar');
  const text = strengthContainer.querySelector('.strength-text');
  
  if (!password) {
    bar.className = 'strength-bar';
    text.className = 'strength-text';
    text.textContent = '';
    return;
  }
  
  const strength = checkPasswordStrength(password);
  bar.className = `strength-bar ${strength}`;
  text.className = `strength-text ${strength}`;
  
  const messages = {
    weak: 'Contraseña débil',
    medium: 'Contraseña media',
    strong: 'Contraseña fuerte'
  };
  text.textContent = messages[strength];
}

document.addEventListener("DOMContentLoaded", () => {
  /* ----------  A. MOSTRAR / OCULTAR CONTRASEÑA  ---------- */
  document.querySelectorAll('.pwd-wrapper').forEach(wrapper => {
    const pwdInput = wrapper.querySelector('input[type="password"]');
    const toggleBtn = wrapper.querySelector('.toggle-pwd');
    if (pwdInput && toggleBtn) {
      const icon = toggleBtn.querySelector('i');
      toggleBtn.addEventListener('click', () => {
        const oculto = pwdInput.type === 'password';
        pwdInput.type = oculto ? 'text' : 'password';
        icon.classList.toggle('fa-eye');
        icon.classList.toggle('fa-eye-slash');
        toggleBtn.setAttribute('aria-label', oculto ? 'Ocultar contraseña' : 'Mostrar contraseña');
      });
    }
  });

  /* ----------  B. INDICADOR DE FUERZA DE CONTRASEÑA  ---------- */
  const pwdInput = document.getElementById('pwd');
  if (pwdInput) {
    pwdInput.addEventListener('input', (e) => {
      updatePasswordStrength(e.target.value);
    });
  }

  /* ----------  C. ENVÍO DEL FORMULARIO  ---------- */
  const form = document.getElementById('registroForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const username  = form.username.value.trim();
    const email     = form.email.value.trim().toLowerCase();
    const email2    = form.email2.value.trim().toLowerCase();
    const pwd       = form.pwd.value;
    const pwd2      = form.pwd2.value;
    const nombre    = form.nombre.value.trim();
    const telefono  = form.telefono.value.trim();
    const direccion = form.direccion.value.trim();

    // Validaciones con mensajes amigables
    if (!username) {
      showMessage('Por favor, ingresa un nombre de usuario', 'error');
      form.username.focus();
      return;
    }
    if (username.length < 4) {
      showMessage('El nombre de usuario debe tener al menos 4 caracteres', 'error');
      form.username.focus();
      return;
    }
    if (!email || !email2) {
      showMessage('Por favor, ingresa tu correo electrónico y confírmalo', 'error');
      return;
    }
    if (email !== email2) {
      showMessage('Los correos electrónicos no coinciden. Verifica que sean iguales', 'error');
      form.email2.focus();
      return;
    }
    if (!pwd || !pwd2) {
      showMessage('Por favor, ingresa tu contraseña y confírmala', 'error');
      return;
    }
    if (pwd.length < 8) {
      showMessage('La contraseña debe tener al menos 8 caracteres', 'error');
      form.pwd.focus();
      return;
    }
    if (pwd !== pwd2) {
      showMessage('Las contraseñas no coinciden. Verifica que sean iguales', 'error');
      form.pwd2.focus();
      return;
    }

    const datos = {
      username: username,
      password: pwd,
      correo  : email,
    };
    if (nombre)    datos.nombre    = nombre;
    if (telefono)  datos.telefono  = telefono;
    if (direccion) datos.direccion = direccion;

    try {
      // ℹ️ NOTA: /create-client/ es un endpoint PÚBLICO, no requiere JWT
      const res = await fetch('/create-client/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken' : getCSRFToken(),
        },
        body: JSON.stringify(datos),
      });

      const data = await res.json().catch(() => ({}));

      if (res.ok) {
        showMessage('¡Cuenta creada exitosamente! Redirigiendo...', 'success');
        setTimeout(() => window.location.href = '/', 1500);
      } else {
        showMessage(data.error || 'Error al crear la cuenta. Intenta de nuevo.', 'error');
      }
    } catch (err) {
      showMessage('Error de conexión. Verifica tu internet e intenta de nuevo.', 'error');
    }
  });
});

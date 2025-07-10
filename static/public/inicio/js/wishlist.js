/**
 * initWishlist – invitado + multi-usuario
 * (versión con selector de tallas y carrito invitado)
 * --------------------------------------------------------------------------
 *  Invitado  → localStorage (wishlist_ids_guest)
 *  Login     → migra guest → wishlist_ids_<userId> y sincroniza backend
 *  Logout    → nukeAllKeys() borra TODAS las claves wishlist_ids_*
 */
export function initWishlist({
  selector          = '.wishlist-btn',
  storageKey        = 'wishlist_ids',
  backendURL        = '/api/wishlist/',          //  /<id_cliente>/
  csrfToken         = null,
  isAuthenticated   = false,
  fetchProductoURL  = '/api/productos_por_ids/?ids=',
  clienteId         = null
} = {}) {



/* ────────────────────────── 0. helpers de LS ────────────────────────── */
const IS_GUEST_ID   = 0;                     // 🟢 id ficticio para invitados
const safeClienteId = clienteId ?? IS_GUEST_ID;

const keyUser = isAuthenticated && clienteId
  ? `${storageKey}_${clienteId}` : `${storageKey}_guest`;

const getList = () => {
  try { return JSON.parse(localStorage.getItem(keyUser)) || []; }
  catch { return []; }
};
const setList = list => {
  localStorage.setItem(keyUser, JSON.stringify(list));
  updateHeaderUI(list);
};

/* ─────────────────── 1. migración guest → user + sync ───────────────── */
if (isAuthenticated && clienteId){
  try{
    const guestRaw = localStorage.getItem(`${storageKey}_guest`);
    const userRaw  = localStorage.getItem(keyUser);
    const merged   = [...new Set([
      ...(JSON.parse(userRaw  || '[]')),
      ...(JSON.parse(guestRaw || '[]'))
    ])];
    localStorage.setItem(keyUser, JSON.stringify(merged));
    localStorage.removeItem(`${storageKey}_guest`);

    /* sube likes heredados */
    if (guestRaw){
      for (const id of JSON.parse(guestRaw)){
        fetch(`${backendURL}${clienteId}/`,{
          method : 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(csrfToken && { 'X-CSRFToken': csrfToken })
          },
          body: JSON.stringify({ producto_id: id })
        }).catch(console.error);
      }
    }
  }catch{/* ignore */}
}else{
  /* invitado: borra listas de otros usuarios */
  Object.keys(localStorage)
        .filter(k=>k.startsWith(storageKey) && !k.endsWith('_guest'))
        .forEach(k=>localStorage.removeItem(k));
}

/* ────────────────────────── 2. refs DOM ─────────────────────────────── */
const wishlistPanel   = document.getElementById('wishlist-panel');
const wishlistContent = wishlistPanel?.querySelector('.wishlist-content');
const overlay         = document.querySelector('.page-overlay');
const wishlistBtn     = document.getElementById('btn-wishlist-panel');
const closeBtn        = document.getElementById('close-wishlist-panel');
const wishlistIcon    = document.querySelector('#btn-wishlist-panel i');
const wishlistCount   = document.querySelector('#btn-wishlist-panel .wishlist-count');

/* ────────────────────────── 3. utilidades UI ───────────────────────── */
const toggleBtn = (btn,on)=>{
  btn.classList.toggle('active',on);
  const ic=btn.querySelector('i');
  ic?.classList.toggle('fa-solid',on);
  ic?.classList.toggle('fa-regular',!on);
};
const updateHeaderUI = l=>{
  wishlistIcon?.classList.toggle('fa-solid',!!l.length);
  wishlistIcon?.classList.toggle('fa-regular',!l.length);
  wishlistIcon && (wishlistIcon.style.color = l.length ? '#ff4d6d':'');
  if (wishlistCount){ wishlistCount.textContent=l.length;
                      wishlistCount.hidden=!l.length; }
};

/* ────────── 4. hydrate inicial (pull servidor si login) ─────────────── */
let hydrateDoneResolve;
const hydrateDone = new Promise(resolve => hydrateDoneResolve = resolve);

(async () => {
  if (isAuthenticated && clienteId){
    try {
      const r = await fetch(`${backendURL}${clienteId}/`);
      if (r.ok) {
        const { productos = [] } = await r.json();
        setList([...new Set([...getList(), ...productos.map(String)])]);
      }
    } catch (err) {
      console.error('[Wishlist] pull', err);
    }
  }

  const idsSet = new Set(getList());
  document.querySelectorAll(selector)
          .forEach(btn => toggleBtn(btn, idsSet.has(btn.dataset.productId)));

  hydrateDoneResolve(); // ✅ Finaliza correctamente
})();


/* ───────────────────────── 5. show / hide panel ─────────────────────── */
const showWishlist = async ()=>{
  await hydrateDone;
  renderWishlistPanel();
  wishlistPanel.classList.add('open');
  overlay.classList.add('active');
};
const hideWishlist = ()=>{
  closeSizePicker(wishlistPanel.querySelector('.size-picker'),'side');
  wishlistPanel.classList.remove('open');
  overlay.classList.remove('active');
};
wishlistBtn ?.addEventListener('click',showWishlist);
closeBtn    ?.addEventListener('click',hideWishlist);
overlay     ?.addEventListener('click',hideWishlist);

/* ───────────────── 6. corazones en catálogo (LS + backend) ──────────── */
document.body.addEventListener('click', e=>{
  const heart=e.target.closest(selector);
  if(!heart) return;

  const id=heart.dataset.productId;
  let l=getList();
  const add=!heart.classList.contains('active');

  toggleBtn(heart,add);
  add?l.push(id):l=l.filter(x=>x!==id);
  setList(l);

  if(!isAuthenticated) return;
  fetch(`${backendURL}${clienteId}/`,{
    method : add?'POST':'DELETE',
    headers: {
      'Content-Type':'application/json',
      ...(csrfToken && {'X-CSRFToken':csrfToken})
    },
    body: JSON.stringify({producto_id:id})
  }).catch(console.error);
});

/* ─────────── 7. panel: add-to-cart + selector de talla ─────────────── */
wishlistPanel?.addEventListener('click', async e=>{

  /* 7-A · Cierre automático si hace clic en cualquier zona “no picker” */
  const pickerOpen = wishlistPanel.querySelector('.size-picker');
  if (pickerOpen && !e.target.closest('.size-picker') &&
                    !e.target.matches('.btn-carrito-mini')){
    closeSizePicker(pickerOpen,'down');
  }

  /* 7-B · Botón “Agregar” (abre el picker) */
  if (e.target.matches('.btn-carrito-mini')){

    const pid=e.target.dataset.id;
    if (pickerOpen && pickerOpen.dataset.productId===pid){
      closeSizePicker(pickerOpen,'down'); return;
    }
    pickerOpen && closeSizePicker(pickerOpen,'down');

    let tallas=[];
    try{ const r=await fetch(`/api/productos/${pid}/`);
         tallas=(await r.json()).tallas||['Única']; }
    catch{ tallas=['Única']; }

    const picker=document.createElement('div');
    picker.className='size-picker slide-up-full';
    picker.dataset.productId=pid;
    picker.innerHTML=`
      <div class="size-picker-inner">
        <h3>Selecciona tu talla</h3>
        <div class="size-options">
          ${tallas.map(t=>`<button class="size-option" data-size="${t}">${t}</button>`).join('')}
        </div>
        <button class="close-size-picker">✕</button>
      </div>`;
    wishlistPanel.appendChild(picker);

    /* posición y efecto blur */
    const r=wishlistPanel.getBoundingClientRect();
    picker.style.left=`${r.left}px`;
    picker.style.width=`${r.width}px`;
    wishlistPanel.dataset.prevOverflow = wishlistPanel.style.overflowY||'';
    wishlistPanel.style.overflowY='hidden';
    wishlistContent.classList.add('blurred');
  }

  /* 7-C · Clic en talla */
  if (e.target.matches('.size-option')){
    const talla=e.target.dataset.size;
    const pid  =e.target.closest('.size-picker').dataset.productId;
    e.target.classList.add('chosen');
    await addToCart(pid,talla,1);
    setTimeout(()=>closeSizePicker(
      e.target.closest('.size-picker'),'down'),160);
  }

  /* 7-D · Botón ✕ dentro del picker */
  if (e.target.matches('.close-size-picker')){
    closeSizePicker(e.target.closest('.size-picker'),'down');
  }
});



function showToast(msg) {
  const toast = document.createElement('div');
  toast.className = 'toast-message';
  toast.textContent = msg;
  document.body.appendChild(toast);

  setTimeout(() => toast.classList.add('show'), 100);
  setTimeout(() => toast.classList.remove('show'), 2500);
  setTimeout(() => toast.remove(), 3000);
}

/* POST carrito */
async function addToCart(pid, talla, cant = 1) {
  try {
    const r = await fetch(`/api/carrito/create/${safeClienteId}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(csrfToken && { 'X-CSRFToken': csrfToken })
      },
      body: JSON.stringify({ producto_id: pid, talla, cantidad: cant })
    });

    if (!r.ok) throw new Error(await r.text());
    console.log('🛒', await r.json());

    const card = wishlistPanel.querySelector(`.wishlist-item .btn-carrito-mini[data-id="${pid}"]`)?.closest('.wishlist-item');
    if (card) {
      const actions = card.querySelector('.wishlist-actions');
      const btn = actions.querySelector('.btn-carrito-mini');

      if (btn) {
        btn.classList.add('fade-out');
        btn.addEventListener('animationend', () => {
          btn.remove();
          const span = document.createElement('span');
          span.className = 'in-cart-note fade-in';
          span.textContent = 'Ya en carrito';
          actions.appendChild(span);
        }, { once: true });
      }
    }

    showToast('Producto agregado al carrito');

    // 🔔 Actualiza carrito en vivo
    document.dispatchEvent(new CustomEvent('carrito-actualizado'));

  } catch (err) {
    alert('No se pudo agregar.\n' + err.message);
  }
}


/* util: cierra selector con animación */
function closeSizePicker(node,dir='down'){
  if(!node) return;
  node.classList.add(dir==='side'?'fade-out-side':'fade-out-down');
  wishlistPanel.style.overflowY =
    wishlistPanel.dataset.prevOverflow || 'auto';
  delete wishlistPanel.dataset.prevOverflow;
  wishlistContent.classList.remove('blurred');
  node.addEventListener('animationend',()=>node.remove(),{once:true});
}

/* ─────────── 8. render panel con nota “Ya en carrito” ─────────────── */
async function getCartIds(){
  if(!isAuthenticated) return new Set();
  try{
    const r=await fetch(`/api/carrito/${clienteId}/`,{credentials:'same-origin'});
    if(!r.ok) throw new Error(r.status);
    const {items=[]}=await r.json();
    return new Set(items.map(it=>String(it.producto_id)));
  }catch(err){ console.error(err); return new Set(); }
}

async function renderWishlistPanel(){
  const ids=getList();
  if(!ids.length){
    wishlistContent.textContent='No tienes productos en tu wishlist.';
    if(!isAuthenticated) injectHint();       // 🟢 invitado, muestra hint
    return;
  }

  try{
    wishlistContent.textContent='Cargando…';
    const url=isAuthenticated
      ?`${backendURL}${clienteId}/?full=true`
      :`${fetchProductoURL}${ids.join(',')}`;
    const {productos=[]}=await (await fetch(url)).json();
    const inCart=await getCartIds();
    wishlistContent.innerHTML = productos.length
      ? buildCards(productos,inCart)
      : 'No tienes productos en tu wishlist.';
  }catch(err){
    wishlistContent.textContent='Error al cargar tu wishlist.';
  }
  if(!isAuthenticated) injectHint();         // 🟢 siempre al final
}

const buildCards=(arr,set=new Set())=>arr.map(p=>`
  <div class="wishlist-item">
    <img src="${p.imagen||'/static/img/no-image.jpg'}" alt="${p.nombre}">
    <div class="wishlist-details">
      <h4>${p.nombre}</h4><span class="precio">$${p.precio}</span>
    </div>
    <div class="wishlist-actions">
      ${set.has(String(p.id))?'<span class="in-cart-note">Ya en carrito</span>':''}
      <button class="btn-carrito-mini" data-id="${p.id}">Agregar al carrito</button>
    </div>
  </div>`).join('');

/* Aviso para invitados */
function injectHint(){
  wishlistContent.insertAdjacentHTML('beforeend', `
    <div class="wishlist-hint">
      ¿Quieres conservar tus favoritos?
      <a href="#" id="open-login-hint">Inicia sesión</a> o
      <a href="/registrarse/">crea una cuenta</a>.
    </div>`);
}

/* abrir login desde aviso */
document.body.addEventListener('click',e=>{
  if(e.target.id==='open-login-hint'){ e.preventDefault(); window.mostrarLoginPanel?.();}
});

/* ───────────────────────── 9. nuevas utilidades ────────────────────── */
function clearWishlist(){
  const ids = getList();
  localStorage.removeItem(keyUser);
  updateHeaderUI([]);
  wishlistContent && (wishlistContent.textContent = 'No tienes productos en tu wishlist.');

  if (isAuthenticated && clienteId && ids.length){
    ids.forEach(id=>{
      fetch(`${backendURL}${clienteId}/`,{
        method : 'DELETE',
        headers: {
          'Content-Type':'application/json',
          ...(csrfToken && {'X-CSRFToken':csrfToken})
        },
        body: JSON.stringify({producto_id:id})
      }).catch(console.error);
    });
  }
}

function nukeAllKeys(){
  Object.keys(localStorage)
        .filter(k=>k.startsWith(storageKey))
        .forEach(k=>localStorage.removeItem(k));
  updateHeaderUI([]);
}


// ✅ Expone la función global para que pueda usarse fuera
window.renderWishlistPanel = renderWishlistPanel;

/* ─────────────────────── export API público ──────────────────────── */
const api = { clearWishlist, nukeAllKeys };
window.__wishlistAPI = api;
return api;
}

// ✅ Ahora sí, cuando ya existe renderWishlistPanel
if (!window.__wishlistCarritoListenerRegistered) {
  window.__wishlistCarritoListenerRegistered = true;

  document.addEventListener('carrito-actualizado', async () => {
    const panel = document.getElementById('wishlist-panel');
    if (
      panel?.classList.contains('open') &&
      typeof window.renderWishlistPanel === 'function'
    ) {
      await window.renderWishlistPanel();
    }
  });
}


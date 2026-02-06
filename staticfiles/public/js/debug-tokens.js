// Debug script para revisar estado de tokens
console.log('=== DEBUG: Token Status ===');

// 1. Verificar tokens en localStorage
const accessToken = localStorage.getItem('access');
const refreshToken = localStorage.getItem('refresh');
const userId = localStorage.getItem('user_id');
const username = localStorage.getItem('username');

console.log('Access Token:', accessToken ? accessToken.substring(0, 50) + '...' : 'NOT SET');
console.log('Refresh Token:', refreshToken ? refreshToken.substring(0, 50) + '...' : 'NOT SET');
console.log('User ID:', userId);
console.log('Username:', username);

// 2. Decodificar tokens (sin validar firma)
function decodeJWT(token) {
    if (!token) return null;
    try {
        const parts = token.split('.');
        if (parts.length !== 3) return null;
        const payload = JSON.parse(atob(parts[1]));
        return payload;
    } catch (e) {
        return null;
    }
}

const accessPayload = decodeJWT(accessToken);
const refreshPayload = decodeJWT(refreshToken);

console.log('=== Access Token Payload ===');
console.log(accessPayload);
if (accessPayload) {
    const now = Math.floor(Date.now() / 1000);
    const expiresIn = accessPayload.exp - now;
    console.log('Expires in:', expiresIn, 'seconds');
    console.log('Is expired:', expiresIn < 0 ? 'YES' : 'NO');
}

console.log('=== Refresh Token Payload ===');
console.log(refreshPayload);
if (refreshPayload) {
    const now = Math.floor(Date.now() / 1000);
    const expiresIn = refreshPayload.exp - now;
    console.log('Expires in:', expiresIn, 'seconds');
    console.log('Is expired:', expiresIn < 0 ? 'YES' : 'NO');
}

// 3. Test refresh endpoint
console.log('=== Testing Refresh Endpoint ===');
async function testRefresh() {
    if (!refreshToken) {
        console.log('❌ No refresh token available');
        return;
    }
    
    try {
        const response = await fetch('/api/auth/refresh/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh: refreshToken }),
        });
        
        console.log('Refresh Response Status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Refresh successful!');
            console.log('New access token:', data.access ? data.access.substring(0, 50) + '...' : 'ERROR');
        } else {
            const error = await response.json();
            console.log('❌ Refresh failed:', error);
        }
    } catch (err) {
        console.log('❌ Refresh error:', err.message);
    }
}

await testRefresh();

// 4. Test wishlist endpoint
console.log('=== Testing Wishlist Endpoint ===');
async function testWishlist() {
    if (!userId) {
        console.log('❌ No user ID available');
        return;
    }
    
    try {
        const response = await fetch(`/api/wishlist/${userId}/?full=true`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
        });
        
        console.log('Wishlist Response Status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Wishlist fetch successful!');
            console.log('Productos:', data.productos.length);
        } else {
            const error = await response.json();
            console.log('❌ Wishlist fetch failed:', error);
        }
    } catch (err) {
        console.log('❌ Wishlist error:', err.message);
    }
}

await testWishlist();

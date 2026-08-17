// ═══════════════════════════════════════════
// EcoFuel Connect AI - API Helper
// ═══════════════════════════════════════════
const API_BASE = 'http://localhost:5000/api';

function getToken() {
  return localStorage.getItem('ecofuel_token');
}

function setToken(token) {
  localStorage.setItem('ecofuel_token', token);
}

function getUser() {
  try {
    return JSON.parse(localStorage.getItem('ecofuel_user') || 'null');
  } catch { return null; }
}

function setUser(user) {
  localStorage.setItem('ecofuel_user', JSON.stringify(user));
}

function logout() {
  localStorage.removeItem('ecofuel_token');
  localStorage.removeItem('ecofuel_user');
  window.location.href = '/login.html';
}

async function apiRequest(endpoint, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || `Request failed: ${response.status}`);
  }
  return data;
}

const api = {
  // Auth
  signup: (data) => apiRequest('/auth/signup', { method: 'POST', body: JSON.stringify(data) }),
  login: (data) => apiRequest('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  me: () => apiRequest('/auth/me'),

  // Products
  getProducts: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/products${qs ? '?' + qs : ''}`);
  },
  getProduct: (id) => apiRequest(`/products/${id}`),
  createProduct: (data) => apiRequest('/products', { method: 'POST', body: JSON.stringify(data) }),
  updateProduct: (id, data) => apiRequest(`/products/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteProduct: (id) => apiRequest(`/products/${id}`, { method: 'DELETE' }),

  // Orders
  placeOrder: (data) => apiRequest('/orders', { method: 'POST', body: JSON.stringify(data) }),
  buyerOrders: () => apiRequest('/orders/buyer'),
  sellerOrders: () => apiRequest('/orders/seller'),
  updateOrderStatus: (id, status) => apiRequest(`/orders/${id}/status`, { method: 'PUT', body: JSON.stringify({ status }) }),

  // AI
  recommend: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/ai/recommend${qs ? '?' + qs : ''}`);
  },
  savings: (productId, quantity) => apiRequest(`/ai/savings/${productId}?quantity=${quantity}`),
  savingsForProduct: (productId, quantity) => apiRequest(`/ai/savings/${productId}?quantity=${quantity}`),
  demandForecast: () => apiRequest('/ai/demand-forecast'),
  searchBehavior: () => apiRequest('/ai/search-behavior'),

  // New AI endpoints
  carbonCalculator: (data) => apiRequest('/ai/carbon-calculator', { method: 'POST', body: JSON.stringify(data) }),
  wasteToEnergy: (data) => apiRequest('/ai/waste-to-energy', { method: 'POST', body: JSON.stringify(data) }),
  costComparison: (use_case, monthly_usage) => apiRequest(`/ai/cost-comparison?use_case=${use_case}&monthly_usage=${monthly_usage}`),
  pricePrediction: (fuel_type, city) => apiRequest(`/ai/price-prediction?fuel_type=${fuel_type}&city=${city||''}`),
  areaIntelligence: () => apiRequest('/ai/area-intelligence'),
  energyInsights: () => apiRequest('/ai/energy-insights'),
  fraudDetection: () => apiRequest('/ai/fraud-detection'),
  classifyProduct: (data) => apiRequest('/ai/classify-product', { method: 'POST', body: JSON.stringify(data) }),
  chatbot: (message, conversation) => apiRequest('/chatbot/message', { method: 'POST', body: JSON.stringify({ message, conversation }) }),

  // Analytics
  demand: () => apiRequest('/analytics/demand'),
  popularFuels: () => apiRequest('/analytics/popular'),
  aggregateSavings: () => apiRequest('/analytics/savings'),
  supplyGap: () => apiRequest('/analytics/supply-gap'),
  dashboardStats: () => apiRequest('/analytics/dashboard'),

  // Admin
  adminStats: () => apiRequest('/admin/stats'),
  adminUsers: () => apiRequest('/admin/users'),
  adminSellers: () => apiRequest('/admin/sellers'),
  adminProducts: () => apiRequest('/admin/products'),
  verifySeller: (id, verified) => apiRequest(`/admin/sellers/${id}/verify`, { method: 'PUT', body: JSON.stringify({ verified }) }),
};


// ── Toast Notifications ──
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || '📢'}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(100%)'; setTimeout(() => toast.remove(), 300); }, 3500);
}

// ── Fuel helpers ──
const FUEL_IMAGES = {
  biogas:   '/images/biogas.png',
  'bio-cng': '/images/bio-cng.png',
  biofuel:  '/images/biofuel.png',
  biomass:  '/images/biomass.png'
};
const FUEL_LABELS = { biogas: 'Biogas', 'bio-cng': 'Bio-CNG', biofuel: 'Biofuel', biomass: 'Biomass' };

function getFuelImg(type) {
  const src = FUEL_IMAGES[type] || '/images/biogas.png';
  return `<img src="${src}" alt="${FUEL_LABELS[type] || type}" style="width:100%;height:100%;object-fit:contain;padding:16px">`;
}

// Keep for legacy places that call getFuelIcon
function getFuelIcon(type) { return FUEL_LABELS[type]?.[0] || '⚡'; }

function getFuelLabel(type) { return FUEL_LABELS[type] || type; }

function renderFuelBadge(fuelType) {
  const cls = `badge-${fuelType}`;
  return `<span class="fuel-badge ${cls}">${getFuelLabel(fuelType)}</span>`;
}

function renderStars(rating) {
  let stars = '';
  for (let i = 1; i <= 5; i++) {
    stars += `<span style="color:${i <= rating ? '#f59e0b' : 'var(--clr-text-3)'}">★</span>`;
  }
  return stars;
}

function formatINR(amount) {
  return '₹' + Number(amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 60) return `${m}min ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

// ── Navbar auth state ──
function updateNavbar() {
  const user = getUser();
  const loginBtn = document.getElementById('nav-login');
  const userMenu = document.getElementById('nav-user');
  const sellerLink = document.getElementById('nav-seller');
  const adminLink = document.getElementById('nav-admin');
  const deliveryLink = document.getElementById('nav-delivery');

  if (user && loginBtn) loginBtn.style.display = 'none';
  if (user && userMenu) {
    userMenu.style.display = 'flex';
    const nameEl = document.getElementById('nav-username');
    if (nameEl) nameEl.textContent = user.name.split(' ')[0];
  }
  if (user && user.role === 'seller' && sellerLink) sellerLink.style.display = 'flex';
  if (user && user.role === 'admin') {
    if (adminLink) adminLink.style.display = 'flex';
    if (deliveryLink) deliveryLink.style.display = 'flex';
  }
  if (user && user.role === 'agent' && deliveryLink) deliveryLink.style.display = 'flex';
}

// ── Product card template (compact square) ──
function renderProductCard(p) {
  return `
    <div class="product-card" onclick="window.location.href='product.html?id=${p.id}'" style="cursor:pointer">
      <div class="product-card-img">${getFuelImg(p.fuel_type)}</div>
      <div class="product-card-body">
        <div class="flex-between mb-6">
          ${renderFuelBadge(p.fuel_type)}
          <span class="tag" style="font-size:0.7rem">${p.city}</span>
        </div>
        <h3 class="font-head" style="font-size:0.92rem;font-weight:700;margin:6px 0 4px;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">${p.name}</h3>
        <div class="flex-between mt-10">
          <div>
            <span class="price-tag" style="font-size:1.2rem">${formatINR(p.price)}</span>
            <span class="price-unit">/${p.unit}</span>
          </div>
          <div style="font-size:0.78rem;color:#f59e0b">${renderStars(Math.round(p.avg_rating))}</div>
        </div>
        <div class="flex-between mt-6">
          <span class="text-xs text-muted">Stock: ${p.quantity_available} ${p.unit}</span>
          ${p.seller_verified ? '<span class="tag" style="color:var(--clr-primary);font-size:0.68rem;border-color:rgba(22,163,74,0.3);padding:2px 7px">✓ Verified</span>' : ''}
        </div>
        <button class="btn btn-primary w-full mt-12 btn-sm" onclick="event.stopPropagation();window.location.href='product.html?id=${p.id}'">
          View Details →
        </button>
      </div>
    </div>
  `;
}

document.addEventListener('DOMContentLoaded', updateNavbar);

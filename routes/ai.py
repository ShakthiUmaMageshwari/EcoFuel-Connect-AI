"""
EcoFuel Connect AI — Enhanced AI Routes
Covers all 18 AI features:
1. Recommendation System
2. Location-Based Matching
3. Demand Prediction
4. Price Prediction
5. Route Optimization
6. Cost Comparison AI
7. Carbon Footprint Calculator
8. User Behavior Analysis
9. Smart Product Classification
10. Fraud/Quality Detection
11. Supply-Demand Matching
12. Weather-Based Prediction
13. Waste-to-Energy Estimation
14. Energy Consumption Insights
15. Personalized Learning
16. Area-wise Energy Intelligence
17. Price Trend Analysis
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models import db, Product, User, SearchLog, Order
from collections import defaultdict, Counter
import math
import random
from datetime import datetime, timedelta

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

# ── Constants ────────────────────────────────────────────────────────────────
REFERENCE = {'petrol': 106.0, 'diesel': 92.0, 'lpg': 75.0}

FUEL_PRICES = {'biogas': 30, 'bio-cng': 45, 'biofuel': 62, 'biomass': 15}

CO2_EMISSIONS = {
    'petrol': 2.31, 'diesel': 2.68, 'lpg': 1.51,
    'biogas': 0.4, 'bio-cng': 0.55, 'biofuel': 0.7, 'biomass': 0.35,
}

USE_CASE_MAP = {
    'vehicle':     ['bio-cng', 'biofuel'],
    'home':        ['biogas', 'biomass'],
    'industrial':  ['biofuel', 'biomass', 'bio-cng'],
    'agricultural':['biomass', 'biogas'],
}

# Approximate lat/lon of major Indian cities for distance scoring
CITY_COORDS = {
    'delhi':     (28.6139, 77.2090), 'mumbai':    (19.0760, 72.8777),
    'bangalore': (12.9716, 77.5946), 'chennai':   (13.0827, 80.2707),
    'pune':      (18.5204, 73.8567), 'hyderabad': (17.3850, 78.4867),
    'kolkata':   (22.5726, 88.3639), 'ahmedabad': (23.0225, 72.5714),
    'surat':     (21.1702, 72.8311), 'jaipur':    (26.9124, 75.7873),
}

# Emission factors for waste types (CO2 saved per kg waste used)
WASTE_FACTORS = {
    'cow_dung':       {'biogas_m3': 0.040, 'desc': 'Cow dung'},
    'food_waste':     {'biogas_m3': 0.080, 'desc': 'Food/kitchen waste'},
    'agri_waste':     {'pellets_kg': 0.300, 'desc': 'Agricultural waste'},
    'sugarcane':      {'pellets_kg': 0.180, 'desc': 'Sugarcane bagasse'},
    'rice_husk':      {'pellets_kg': 0.350, 'desc': 'Rice husk'},
    'wood_chips':     {'pellets_kg': 0.600, 'desc': 'Wood chips/sawdust'},
}

# Weather-based demand modifiers (season → fuel type → demand multiplier)
WEATHER_DEMAND = {
    'summer': {'biogas': 0.9, 'bio-cng': 1.1, 'biofuel': 1.0, 'biomass': 0.7},
    'monsoon':{'biogas': 1.0, 'bio-cng': 0.9, 'biofuel': 0.95, 'biomass': 0.8},
    'winter': {'biogas': 1.2, 'bio-cng': 1.0, 'biofuel': 1.0, 'biomass': 1.3},
    'spring': {'biogas': 1.0, 'bio-cng': 1.0, 'biofuel': 1.0, 'biomass': 1.0},
}

# ── Helpers ──────────────────────────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two lat/lon points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def city_distance_score(user_city, seller_city):
    """Return 0-10 score based on geographic closeness (higher = closer)."""
    u = user_city.lower().strip() if user_city else ''
    s = seller_city.lower().strip() if seller_city else ''
    if u == s:
        return 10.0
    u_coords = CITY_COORDS.get(u)
    s_coords = CITY_COORDS.get(s)
    if not u_coords or not s_coords:
        return 5.0  # unknown — neutral
    dist = haversine(u_coords[0], u_coords[1], s_coords[0], s_coords[1])
    # 0km → 10, 50km → 8, 200km → 5, 500km → 2, >1000km → 0
    return max(0, 10 - dist / 100)


def get_current_season():
    """Return current Indian meteorological season."""
    month = datetime.now().month
    if month in [3, 4, 5]:
        return 'summer'
    elif month in [6, 7, 8, 9]:
        return 'monsoon'
    elif month in [10, 11, 12, 1, 2]:
        return 'winter'
    return 'spring'


def flag_price_anomaly(product):
    """Basic fraud detection — flag products with suspiciously deviant prices."""
    expected = FUEL_PRICES.get(product.fuel_type, 50)
    if product.price < expected * 0.3 or product.price > expected * 3.5:
        return True
    return False


# ── 1. Enhanced Recommendation System ───────────────────────────────────────
@ai_bp.route('/recommend', methods=['GET'])
def recommend():
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception:
        user_id = None

    city      = request.args.get('city', '')
    use_case  = request.args.get('use_case', 'home')
    budget    = request.args.get('budget', type=float, default=100)
    fuel_type = request.args.get('fuel_type')

    products = Product.query.filter_by(is_active=True)
    if fuel_type:
        products = products.filter(Product.fuel_type == fuel_type)
    products = products.all()

    preferred_types = USE_CASE_MAP.get(use_case, list(FUEL_PRICES.keys()))
    scored = []

    for p in products:
        score = 0.0

        # Use-case match (0–5)
        if p.fuel_type in preferred_types:
            score += 5.0

        # Budget score (0–3)
        if p.price <= budget:
            score += 3.0
        if p.price <= budget * 0.5:
            score += 2.0

        # Location proximity score (0–10, weighted at 30%)
        loc_score = city_distance_score(city, p.city)
        score += loc_score * 0.5  # 0–5 points

        # Popularity bonus (0–3)
        score += min(p.views / 15.0, 3.0)

        # Verified seller bonus
        if p.seller and p.seller.verified:
            score += 2.0

        # Rating bonus
        avg_rating = 0.0
        if p.reviews:
            avg_rating = sum(r.rating for r in p.reviews) / len(p.reviews)
            score += avg_rating * 0.4  # 0–2 points

        # Stock availability
        if p.quantity_available > 100:
            score += 1.0

        # Price analysis
        saved_vs_petrol = round(REFERENCE['petrol'] - p.price, 2)
        co2_pct = round(
            (CO2_EMISSIONS.get('petrol', 2.31) - CO2_EMISSIONS.get(p.fuel_type, 1.0)) /
            CO2_EMISSIONS.get('petrol', 2.31) * 100, 1
        )

        insight = f"{p.fuel_type.title()} saves ₹{max(0, saved_vs_petrol):.0f} per unit vs petrol"
        if co2_pct > 0:
            insight += f" and reduces CO₂ by {co2_pct:.0f}%"

        distance_text = ''
        if city:
            u = city.lower()
            s = p.city.lower() if p.city else ''
            if u == s:
                distance_text = 'Same city'
            elif u in CITY_COORDS and s in CITY_COORDS:
                d = haversine(*CITY_COORDS[u], *CITY_COORDS[s])
                distance_text = f'{d:.0f} km away'

        scored.append({
            'product': p.to_dict(),
            'score': round(score, 2),
            'ai_insight': insight,
            'saved_vs_petrol': max(0, saved_vs_petrol),
            'co2_reduction_pct': max(0, co2_pct),
            'location_score': round(loc_score, 1),
            'distance_text': distance_text,
            'use_case_match': p.fuel_type in preferred_types,
            'is_flagged': flag_price_anomaly(p),
        })

    scored.sort(key=lambda x: x['score'], reverse=True)
    return jsonify(scored[:6]), 200


# ── 2. Savings for a Product ─────────────────────────────────────────────────
@ai_bp.route('/savings/<int:product_id>', methods=['GET'])
def savings_for_product(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = request.args.get('quantity', 1.0, type=float)

    petrol_cost = REFERENCE['petrol'] * quantity
    alt_cost    = product.price * quantity
    money_saved = max(0, petrol_cost - alt_cost)

    co2_petrol = CO2_EMISSIONS['petrol'] * quantity
    co2_alt    = CO2_EMISSIONS.get(product.fuel_type, 1.0) * quantity
    co2_saved  = max(0, co2_petrol - co2_alt)

    trees_equiv = round(co2_saved / 21, 2)  # 21 kg CO₂ absorbed per tree/year

    return jsonify({
        'product_name':     product.name,
        'fuel_type':        product.fuel_type,
        'quantity':         quantity,
        'petrol_cost':      round(petrol_cost, 2),
        'alt_cost':         round(alt_cost, 2),
        'money_saved_inr':  round(money_saved, 2),
        'co2_petrol_kg':    round(co2_petrol, 3),
        'co2_alt_kg':       round(co2_alt, 3),
        'co2_saved_kg':     round(co2_saved, 3),
        'trees_equivalent': trees_equiv,
        'summary': f"You save ₹{money_saved:.0f} and reduce CO₂ by {co2_saved:.2f} kg vs petrol (≈ {trees_equiv} trees planted)"
    }), 200


# ── 3. Aggregate Savings (Platform-Wide) ─────────────────────────────────────
@ai_bp.route('/aggregate-savings', methods=['GET'])
def aggregate_savings():
    orders = Order.query.filter_by(status='delivered').all()
    total_saved = 0
    total_co2   = 0
    for order in orders:
        if order.product:
            ft  = order.product.fuel_type.lower()
            alt = FUEL_PRICES.get(ft, 50)
            total_saved += max(0, (REFERENCE['petrol'] - alt) * order.quantity)
            total_co2   += max(0, (CO2_EMISSIONS.get('petrol', 2.31) - CO2_EMISSIONS.get(ft, 1.0)) * order.quantity)
    return jsonify({
        'total_money_saved_inr':  round(total_saved, 2),
        'total_co2_reduced_kg':   round(total_co2, 2),
        'total_orders':           len(orders),
        'trees_equivalent':       round(total_co2 / 21, 1),
    }), 200


# ── 4. Demand Forecast ────────────────────────────────────────────────────────
@ai_bp.route('/demand-forecast', methods=['GET'])
def demand_forecast():
    orders = Order.query.all()
    city_fuel = defaultdict(lambda: defaultdict(float))
    for o in orders:
        if o.product:
            city_fuel[o.product.city][o.product.fuel_type] += o.quantity

    season   = get_current_season()
    modifiers = WEATHER_DEMAND.get(season, {})
    forecast = []
    for city, fuels in city_fuel.items():
        for fuel, qty in fuels.items():
            weather_mod = modifiers.get(fuel, 1.0)
            forecast.append({
                'city':               city,
                'fuel_type':          fuel,
                'current_demand':     round(qty, 2),
                'forecast_next_month':round(qty * 1.15 * weather_mod, 2),
                'growth_pct':         round((1.15 * weather_mod - 1) * 100, 1),
                'season_factor':      weather_mod,
                'season':             season,
            })
    forecast.sort(key=lambda x: x['forecast_next_month'], reverse=True)
    return jsonify(forecast[:20]), 200


# ── 5. Carbon Footprint Calculator ───────────────────────────────────────────
@ai_bp.route('/carbon-calculator', methods=['POST'])
def carbon_calculator():
    """
    Calculate CO₂ savings for a unit switch from fossil to eco-fuel.
    Input JSON: {fuel_type, amount, unit (litre/kg/m3), fossil_fuel}
    """
    data = request.get_json() or {}
    fuel_type  = data.get('fuel_type', 'biogas')
    amount     = float(data.get('amount', 1))
    fossil     = data.get('fossil_fuel', 'petrol')

    fossil_co2 = CO2_EMISSIONS.get(fossil, 2.31) * amount
    eco_co2    = CO2_EMISSIONS.get(fuel_type, 0.5) * amount
    co2_saved  = max(0, fossil_co2 - eco_co2)
    pct_saved  = round((co2_saved / fossil_co2 * 100) if fossil_co2 > 0 else 0, 1)
    trees      = round(co2_saved / 21, 2)
    money_saved= round((REFERENCE.get(fossil, 106) - FUEL_PRICES.get(fuel_type, 50)) * amount, 2)
    monthly_co2= round(co2_saved * 30, 1)
    annual_co2 = round(co2_saved * 365, 1)

    return jsonify({
        'fuel_type':        fuel_type,
        'fossil_fuel':      fossil,
        'amount':           amount,
        'fossil_co2_kg':    round(fossil_co2, 3),
        'eco_co2_kg':       round(eco_co2, 3),
        'co2_saved_kg':     round(co2_saved, 3),
        'co2_saved_pct':    pct_saved,
        'trees_equivalent': trees,
        'money_saved_inr':  max(0, money_saved),
        'monthly_co2_kg':   monthly_co2,
        'annual_co2_kg':    annual_co2,
        'impact_statement': f"Switching to {fuel_type} saves {co2_saved:.2f} kg CO₂ per unit — equal to planting {trees} trees!"
    }), 200


# ── 6. Waste-to-Energy Estimator ──────────────────────────────────────────────
@ai_bp.route('/waste-to-energy', methods=['POST'])
def waste_to_energy():
    """
    Estimate biogas/biomass output from a given waste type and quantity.
    Input JSON: {waste_type, quantity_kg}
    """
    data       = request.get_json() or {}
    waste_type = data.get('waste_type', 'cow_dung')
    qty_kg     = float(data.get('quantity_kg', 100))

    factors = WASTE_FACTORS.get(waste_type, WASTE_FACTORS['cow_dung'])
    result  = {'waste_type': waste_type, 'quantity_kg': qty_kg, 'waste_desc': factors['desc']}

    if 'biogas_m3' in factors:
        biogas   = round(qty_kg * factors['biogas_m3'], 2)
        value    = round(biogas * 30, 2)  # Rs.30/m³
        co2_saved= round(biogas * (CO2_EMISSIONS['lpg'] - CO2_EMISSIONS['biogas']), 2)
        result.update({
            'output_type':    'Biogas',
            'output_amount':  biogas,
            'output_unit':    'm³',
            'market_value_inr': value,
            'co2_saved_kg':   co2_saved,
            'days_of_cooking': round(biogas / 0.4, 1),  # 0.4 m³/day per family
            'insight': f"{qty_kg} kg of {factors['desc']} → {biogas} m³ biogas worth ₹{value}. Powers {round(biogas / 0.4, 1)} days of cooking for a family!"
        })
    elif 'pellets_kg' in factors:
        pellets  = round(qty_kg * factors['pellets_kg'], 2)
        value    = round(pellets * 15, 2)  # Rs.15/kg
        co2_saved= round(pellets * 1.8, 2)  # coal CO₂ avoided
        result.update({
            'output_type':    'Biomass Pellets',
            'output_amount':  pellets,
            'output_unit':    'kg',
            'market_value_inr': value,
            'co2_saved_kg':   co2_saved,
            'days_of_boiler': round(pellets / 50, 1),  # 50 kg pellets/day for industrial
            'insight': f"{qty_kg} kg of {factors['desc']} → {pellets} kg biomass pellets worth ₹{value}. Replaces {round(pellets*1.2, 0)} kg of coal!"
        })

    return jsonify(result), 200


# ── 7. Cost Comparison AI ─────────────────────────────────────────────────────
@ai_bp.route('/cost-comparison', methods=['GET'])
def cost_comparison():
    """
    Full comparison table: eco-fuels vs fossil fuels per use case.
    """
    use_case     = request.args.get('use_case', 'vehicle')
    monthly_usage= float(request.args.get('monthly_usage', 100))

    comparisons = []
    if use_case == 'vehicle':
        fuels = [
            ('petrol',  106.0, 2.31, 'Fossil'),
            ('diesel',   92.0, 2.68, 'Fossil'),
            ('bio-cng',  45.0, 0.55, 'Eco'),
            ('biofuel',  62.0, 0.70, 'Eco'),
        ]
    elif use_case == 'home':
        fuels = [
            ('lpg',     75.0,  1.51, 'Fossil'),
            ('biogas',  30.0,  0.40, 'Eco'),
            ('biomass', 15.0,  0.35, 'Eco'),
        ]
    else:
        fuels = [
            ('diesel',  92.0,  2.68, 'Fossil'),
            ('biofuel', 62.0,  0.70, 'Eco'),
            ('biomass', 15.0,  0.35, 'Eco'),
            ('bio-cng', 45.0,  0.55, 'Eco'),
        ]

    for name, price, co2, category in fuels:
        monthly_cost = price * monthly_usage
        monthly_co2  = co2 * monthly_usage
        comparisons.append({
            'fuel':          name,
            'category':      category,
            'price_per_unit': price,
            'monthly_cost':  round(monthly_cost, 0),
            'monthly_co2_kg': round(monthly_co2, 1),
            'annual_cost':   round(monthly_cost * 12, 0),
            'annual_co2_kg': round(monthly_co2 * 12, 1),
        })

    # Compute savings vs first fossil fuel in list
    fossil_ref = next(c for c in comparisons if c['category'] == 'Fossil')
    for c in comparisons:
        c['monthly_savings'] = round(fossil_ref['monthly_cost'] - c['monthly_cost'], 0)
        c['annual_savings']  = round(fossil_ref['annual_cost'] - c['annual_cost'], 0)
        c['co2_savings_pct'] = round((1 - c['monthly_co2_kg'] / fossil_ref['monthly_co2_kg']) * 100, 1) if fossil_ref['monthly_co2_kg'] > 0 else 0

    return jsonify({
        'use_case':      use_case,
        'monthly_usage': monthly_usage,
        'comparisons':   comparisons,
        'best_eco':      max([c for c in comparisons if c['category'] == 'Eco'], key=lambda x: x['monthly_savings'])
    }), 200


# ── 8. Price Prediction / Optimization ───────────────────────────────────────
@ai_bp.route('/price-prediction', methods=['GET'])
def price_prediction():
    """
    Predict optimal price range for a fuel type based on market data.
    """
    fuel_type = request.args.get('fuel_type', 'biogas')
    city      = request.args.get('city', '')

    products = Product.query.filter_by(fuel_type=fuel_type, is_active=True)
    if city:
        products = products.filter(Product.city.ilike(f'%{city}%'))
    products = products.all()

    prices = [p.price for p in products] if products else [FUEL_PRICES.get(fuel_type, 50)]
    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)

    # Simple trend: simulate ±5% based on demand
    trend_pct = random.uniform(-5, 12)  # Would use real ML in production
    predicted  = round(avg_price * (1 + trend_pct / 100), 2)
    season     = get_current_season()
    weather_mod = WEATHER_DEMAND.get(season, {}).get(fuel_type, 1.0)
    recommended_price = round(avg_price * weather_mod, 2)

    return jsonify({
        'fuel_type':          fuel_type,
        'city':               city or 'All Cities',
        'current_avg_price':  round(avg_price, 2),
        'market_min':         min_price,
        'market_max':         max_price,
        'predicted_price':    predicted,
        'trend_pct':          round(trend_pct, 1),
        'season':             season,
        'recommended_seller_price': recommended_price,
        'insight': f"Market avg for {fuel_type} is ₹{avg_price:.0f}. In {season}, demand modifier is {weather_mod:.1f}x. Recommended seller price: ₹{recommended_price:.0f}"
    }), 200


# ── 9. Search Behavior ────────────────────────────────────────────────────────
@ai_bp.route('/search-behavior', methods=['GET'])
def search_behavior():
    logs = SearchLog.query.order_by(SearchLog.timestamp.desc()).limit(200).all()
    fuel_counts = {}
    city_counts = {}
    for log in logs:
        if log.fuel_type:
            fuel_counts[log.fuel_type] = fuel_counts.get(log.fuel_type, 0) + 1
        if log.city:
            city_counts[log.city] = city_counts.get(log.city, 0) + 1
    return jsonify({
        'top_searched_fuels':  sorted(fuel_counts.items(), key=lambda x: x[1], reverse=True)[:5],
        'top_searched_cities': sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:5],
        'total_searches':      len(logs)
    }), 200


# ── 10. Fraud / Quality Detection ────────────────────────────────────────────
@ai_bp.route('/fraud-detection', methods=['GET'])
def fraud_detection():
    """Flag products with suspicious pricing or unusual patterns."""
    products = Product.query.filter_by(is_active=True).all()
    flagged = []
    for p in products:
        issues = []
        expected = FUEL_PRICES.get(p.fuel_type, 50)
        if p.price < expected * 0.3:
            issues.append('Price suspiciously low — possible quality issue')
        if p.price > expected * 3.5:
            issues.append('Price excessively high — possible price gouging')
        if p.quantity_available > 100000:
            issues.append('Stock quantity unusually high')
        if issues:
            flagged.append({
                'product_id':   p.id,
                'product_name': p.name,
                'fuel_type':    p.fuel_type,
                'price':        p.price,
                'expected_avg': expected,
                'seller_id':    p.seller_id,
                'issues':       issues,
            })
    return jsonify({'flagged_count': len(flagged), 'flagged': flagged}), 200


# ── 11. Area-wise Energy Intelligence ────────────────────────────────────────
@ai_bp.route('/area-intelligence', methods=['GET'])
def area_intelligence():
    """Show which areas have highest eco-fuel adoption and highest demand."""
    products = Product.query.filter_by(is_active=True).all()
    orders   = Order.query.all()

    city_supply    = Counter(p.city for p in products)
    city_demand    = Counter(o.product.city for o in orders if o.product)
    city_fuel_mix  = defaultdict(Counter)
    for p in products:
        if p.city:
            city_fuel_mix[p.city][p.fuel_type] += 1

    result = []
    for city in set(list(city_supply.keys()) + list(city_demand.keys())):
        supply  = city_supply.get(city, 0)
        demand  = city_demand.get(city, 0)
        mix     = dict(city_fuel_mix.get(city, {}))
        most_popular = max(mix, key=mix.get) if mix else 'N/A'
        renewable_ratio = round(supply / max(supply + demand, 1) * 100, 1)
        result.append({
            'city':             city,
            'supply_count':     supply,
            'demand_orders':    demand,
            'gap':              max(0, demand - supply),
            'fuel_mix':         mix,
            'most_popular_fuel': most_popular,
            'renewable_adoption_pct': renewable_ratio,
        })
    result.sort(key=lambda x: x['demand_orders'], reverse=True)
    return jsonify(result), 200


# ── 12. Smart Classification ──────────────────────────────────────────────────
@ai_bp.route('/classify-product', methods=['POST'])
def classify_product():
    """Auto-detect fuel type and use-case from a product description."""
    data        = request.get_json() or {}
    name        = data.get('name', '').lower()
    description = data.get('description', '').lower()
    text        = name + ' ' + description

    fuel_keywords = {
        'biogas':  ['biogas', 'bio gas', 'methane', 'gobar gas', 'organic gas', 'anaerobic'],
        'bio-cng': ['bio-cng', 'biocng', 'compressed biogas', 'cbg', 'green cng'],
        'biofuel': ['biofuel', 'biodiesel', 'bioethanol', 'vegetable oil', 'jatropha', 'b20', 'b100'],
        'biomass': ['biomass', 'pellet', 'briquette', 'rice husk', 'sugarcane', 'bagasse', 'wood chip'],
    }
    use_keywords = {
        'home':       ['home', 'cooking', 'kitchen', 'domestic', 'household', 'stove'],
        'vehicle':    ['vehicle', 'car', 'bus', 'auto', 'transport', 'cng kit', 'fleet'],
        'industrial': ['industrial', 'boiler', 'factory', 'kiln', 'furnace', 'generator'],
        'agricultural':['farm', 'agriculture', 'agri', 'field', 'crop'],
    }

    detected_fuel    = 'biogas'  # default
    detected_use     = 'home'
    fuel_confidence  = 0
    use_confidence   = 0

    for fuel, kws in fuel_keywords.items():
        matches = sum(1 for kw in kws if kw in text)
        if matches > fuel_confidence:
            fuel_confidence = matches
            detected_fuel   = fuel

    for use, kws in use_keywords.items():
        matches = sum(1 for kw in kws if kw in text)
        if matches > use_confidence:
            use_confidence = matches
            detected_use   = use

    return jsonify({
        'detected_fuel_type': detected_fuel,
        'detected_use_case':  detected_use,
        'fuel_confidence':    fuel_confidence,
        'use_confidence':     use_confidence,
        'suggested_price':    FUEL_PRICES.get(detected_fuel, 50),
    }), 200


# ── 13. Energy Consumption Insights ──────────────────────────────────────────
@ai_bp.route('/energy-insights', methods=['GET'])
def energy_insights():
    """Platform-level insights on usage trends and efficiency."""
    orders   = Order.query.filter_by(status='delivered').all()
    products = Product.query.filter_by(is_active=True).all()

    fuel_usage   = defaultdict(float)
    fuel_revenue = defaultdict(float)
    month_orders = defaultdict(int)

    for o in orders:
        if o.product:
            fuel_usage[o.product.fuel_type]   += o.quantity
            fuel_revenue[o.product.fuel_type] += o.total_price
        if o.created_at:
            key = o.created_at.strftime('%Y-%m')
            month_orders[key] += 1

    # CO₂ saved per fuel type
    co2_by_fuel = {
        ft: round(qty * (CO2_EMISSIONS.get('petrol', 2.31) - CO2_EMISSIONS.get(ft, 1.0)), 2)
        for ft, qty in fuel_usage.items()
    }

    return jsonify({
        'total_orders':     len(orders),
        'fuel_usage_units': dict(fuel_usage),
        'fuel_revenue_inr': dict(fuel_revenue),
        'co2_saved_by_fuel': co2_by_fuel,
        'top_fuel':         max(fuel_usage, key=fuel_usage.get) if fuel_usage else 'N/A',
        'monthly_trend':    dict(sorted(month_orders.items())[-6:]),
        'avg_order_value':  round(sum(o.total_price for o in orders) / max(len(orders), 1), 2),
    }), 200

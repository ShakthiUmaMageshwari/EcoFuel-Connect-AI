from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from models import db, Product, Order, SearchLog, User
from collections import Counter
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


@analytics_bp.route('/demand', methods=['GET'])
def demand_by_area():
    orders = Order.query.all()
    data = {}
    for order in orders:
        city = order.product.city if order.product else 'Unknown'
        fuel = order.product.fuel_type if order.product else 'Unknown'
        key = city
        if key not in data:
            data[key] = {}
        data[key][fuel] = data[key].get(fuel, 0) + order.quantity

    result = [{'city': city, 'fuels': fuels} for city, fuels in data.items()]
    return jsonify(result), 200


@analytics_bp.route('/popular', methods=['GET'])
def popular_fuels():
    logs = SearchLog.query.all()
    fuel_counts = Counter(log.fuel_type for log in logs if log.fuel_type)
    city_counts = Counter(log.city for log in logs if log.city)

    products = Product.query.filter_by(is_active=True).all()
    fuel_listing_counts = Counter(p.fuel_type for p in products)

    return jsonify({
        'search_trends': dict(fuel_counts.most_common(10)),
        'city_demand': dict(city_counts.most_common(10)),
        'fuel_listings': dict(fuel_listing_counts)
    }), 200


@analytics_bp.route('/savings', methods=['GET'])
def aggregate_savings():
    PETROL_PRICE = 106.0  # INR per litre
    DIESEL_PRICE = 92.0
    CO2_FACTOR = 2.31    # kg CO2 per litre petrol equivalent

    orders = Order.query.filter_by(status='delivered').all()
    total_saved = 0
    total_co2 = 0

    fuel_prices = {
        'biogas': 30,
        'bio-cng': 45,
        'biofuel': 60,
        'biomass': 25,
    }

    for order in orders:
        if order.product:
            ft = order.product.fuel_type.lower()
            alt_price = fuel_prices.get(ft, 50)
            saved = (PETROL_PRICE - alt_price) * order.quantity
            co2 = CO2_FACTOR * order.quantity * 0.7  # 70% cleaner
            total_saved += max(0, saved)
            total_co2 += max(0, co2)

    return jsonify({
        'total_money_saved_inr': round(total_saved, 2),
        'total_co2_reduced_kg': round(total_co2, 2),
        'total_orders': len(orders)
    }), 200


@analytics_bp.route('/supply-gap', methods=['GET'])
def supply_gap():
    orders = Order.query.all()
    demand = Counter(order.product.city for order in orders if order.product)

    products = Product.query.filter_by(is_active=True).all()
    supply = Counter(p.city for p in products)

    cities = set(list(demand.keys()) + list(supply.keys()))
    gaps = []
    for city in cities:
        d = demand.get(city, 0)
        s = supply.get(city, 0)
        gaps.append({'city': city, 'demand': d, 'supply': s, 'gap': max(0, d - s)})

    gaps.sort(key=lambda x: x['gap'], reverse=True)
    return jsonify(gaps), 200


@analytics_bp.route('/dashboard', methods=['GET'])
def platform_stats():
    total_users = User.query.filter_by(role='buyer').count()
    total_sellers = User.query.filter_by(role='seller').count()
    total_products = Product.query.filter_by(is_active=True).count()
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    delivered_orders = Order.query.filter_by(status='delivered').count()

    return jsonify({
        'total_users': total_users,
        'total_sellers': total_sellers,
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders
    }), 200

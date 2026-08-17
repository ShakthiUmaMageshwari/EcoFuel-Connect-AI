from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Order, User
from datetime import datetime
import random

delivery_bp = Blueprint('delivery', __name__, url_prefix='/api/delivery')

# ── In-memory delivery agent store (demo) ──────────────────────────────────
# In production, persist this in the DB.
AGENTS = {
    "DA001": {
        "id": "DA001",
        "name": "Ravi Kumar",
        "phone": "+91 98765 43210",
        "vehicle": "Electric Scooter",
        "vehicle_number": "TN 09 AB 1234",
        "city": "Chennai",
        "zone": "Anna Nagar",
        "status": "online",  # online | offline | on_delivery
        "rating": 4.8,
        "total_deliveries": 312,
        "today_deliveries": 7,
        "today_earnings": 840,
        "joined": "2024-08-15",
        "is_eco_certified": True,
        "lat": 13.0827, "lng": 80.2707
    },
    "DA002": {
        "id": "DA002",
        "name": "Priya Sharma",
        "phone": "+91 87654 32109",
        "vehicle": "CNG Auto",
        "vehicle_number": "DL 4C CD 5678",
        "city": "Delhi",
        "zone": "Dwarka",
        "status": "on_delivery",
        "rating": 4.6,
        "total_deliveries": 189,
        "today_deliveries": 5,
        "today_earnings": 620,
        "joined": "2024-10-22",
        "is_eco_certified": True,
        "lat": 28.5921, "lng": 77.0460
    },
    "DA003": {
        "id": "DA003",
        "name": "Suresh Babu",
        "phone": "+91 76543 21098",
        "vehicle": "Bicycle",
        "vehicle_number": "N/A",
        "city": "Bangalore",
        "zone": "Koramangala",
        "status": "online",
        "rating": 4.9,
        "total_deliveries": 528,
        "today_deliveries": 11,
        "today_earnings": 1320,
        "joined": "2024-05-03",
        "is_eco_certified": True,
        "lat": 12.9352, "lng": 77.6244
    },
    "DA004": {
        "id": "DA004",
        "name": "Anita Patel",
        "phone": "+91 65432 10987",
        "vehicle": "Electric Bike",
        "vehicle_number": "MH 44 EF 9012",
        "city": "Mumbai",
        "zone": "Andheri",
        "status": "offline",
        "rating": 4.7,
        "total_deliveries": 241,
        "today_deliveries": 0,
        "today_earnings": 0,
        "joined": "2024-09-11",
        "is_eco_certified": False,
        "lat": 19.1136, "lng": 72.8697
    },
    "DA005": {
        "id": "DA005",
        "name": "Vikram Singh",
        "phone": "+91 54321 09876",
        "vehicle": "Electric Scooter",
        "vehicle_number": "PB 08 GH 3456",
        "city": "Hyderabad",
        "zone": "Gachibowli",
        "status": "on_delivery",
        "rating": 4.5,
        "total_deliveries": 103,
        "today_deliveries": 3,
        "today_earnings": 390,
        "joined": "2025-01-07",
        "is_eco_certified": True,
        "lat": 17.4401, "lng": 78.3489
    },
}

# Demo delivery assignments
ACTIVE_DELIVERIES = [
    {
        "delivery_id": "DEL-9281",
        "agent_id": "DA002",
        "order_id": 4,
        "pickup": {"name": "GreenBiogas Hub", "address": "Plot 12, Phase-II Industrial Area, Dwarka, Delhi", "lat": 28.5984, "lng": 77.0365},
        "dropoff": {"name": "Rajesh Mehta", "address": "B-204, Sector 9, Dwarka, Delhi – 110075", "lat": 28.5845, "lng": 77.0530},
        "fuel_type": "Biogas",
        "quantity": "5 m³",
        "distance_km": 3.2,
        "eta_min": 8,
        "status": "picked_up",
        "started_at": "2026-03-24T06:25:00Z",
    },
    {
        "delivery_id": "DEL-9282",
        "agent_id": "DA005",
        "order_id": 7,
        "pickup": {"name": "EcoFuel Station Gachi", "address": "Sy No 112, Nanakramguda, Gachibowli, Hyderabad", "lat": 17.4458, "lng": 78.3553},
        "dropoff": {"name": "Tech Park Canteen", "address": "DLF Cyber City, Gachibowli, Hyderabad – 500032", "lat": 17.4347, "lng": 78.3426},
        "fuel_type": "Bio-CNG",
        "quantity": "12 kg",
        "distance_km": 1.8,
        "eta_min": 4,
        "status": "en_route",
        "started_at": "2026-03-24T06:28:00Z",
    },
]


@delivery_bp.route('/agents', methods=['GET'])
def list_agents():
    city = request.args.get('city', '').strip()
    status = request.args.get('status', '').strip()
    agents = list(AGENTS.values())
    if city:
        agents = [a for a in agents if a['city'].lower() == city.lower()]
    if status:
        agents = [a for a in agents if a['status'] == status]
    return jsonify(agents), 200


@delivery_bp.route('/agents/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    agent = AGENTS.get(agent_id.upper())
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    return jsonify(agent), 200


@delivery_bp.route('/agents/<agent_id>/status', methods=['PUT'])
def update_agent_status(agent_id):
    agent = AGENTS.get(agent_id.upper())
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ('online', 'offline', 'on_delivery'):
        return jsonify({'error': 'Invalid status'}), 400
    agent['status'] = new_status
    return jsonify(agent), 200


@delivery_bp.route('/active', methods=['GET'])
def active_deliveries():
    return jsonify(ACTIVE_DELIVERIES), 200


@delivery_bp.route('/stats', methods=['GET'])
def delivery_stats():
    agents = list(AGENTS.values())
    online = sum(1 for a in agents if a['status'] == 'online')
    on_del = sum(1 for a in agents if a['status'] == 'on_delivery')
    offline = sum(1 for a in agents if a['status'] == 'offline')
    total_del = sum(a['today_deliveries'] for a in agents)
    total_earn = sum(a['today_earnings'] for a in agents)
    avg_rating = round(sum(a['rating'] for a in agents) / len(agents), 2)
    return jsonify({
        "total_agents": len(agents),
        "online": online,
        "on_delivery": on_del,
        "offline": offline,
        "today_deliveries": total_del,
        "today_earnings": total_earn,
        "avg_rating": avg_rating,
        "active_deliveries": len(ACTIVE_DELIVERIES),
    }), 200

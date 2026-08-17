from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Seller, Product, Order

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def require_admin():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return None, jsonify({'error': 'Admin access required'}), 403
    return user, None, None


@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
def stats():
    user, err, code = require_admin()
    if err:
        return err, code

    return jsonify({
        'total_users': User.query.filter_by(role='buyer').count(),
        'total_sellers': User.query.filter_by(role='seller').count(),
        'total_products': Product.query.count(),
        'active_products': Product.query.filter_by(is_active=True).count(),
        'total_orders': Order.query.count(),
        'pending_orders': Order.query.filter_by(status='pending').count(),
        'delivered_orders': Order.query.filter_by(status='delivered').count(),
    }), 200


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    user, err, code = require_admin()
    if err:
        return err, code

    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200


@admin_bp.route('/sellers', methods=['GET'])
@jwt_required()
def list_sellers():
    user, err, code = require_admin()
    if err:
        return err, code

    sellers = Seller.query.all()
    return jsonify([s.to_dict() for s in sellers]), 200


@admin_bp.route('/sellers/<int:seller_id>/verify', methods=['PUT'])
@jwt_required()
def verify_seller(seller_id):
    user, err, code = require_admin()
    if err:
        return err, code

    seller = Seller.query.get_or_404(seller_id)
    data = request.get_json()
    seller.verified = data.get('verified', True)
    db.session.commit()
    return jsonify({'message': 'Seller verification updated', 'seller': seller.to_dict()}), 200


@admin_bp.route('/products', methods=['GET'])
@jwt_required()
def list_products():
    user, err, code = require_admin()
    if err:
        return err, code

    products = Product.query.order_by(Product.created_at.desc()).all()
    return jsonify([p.to_dict() for p in products]), 200

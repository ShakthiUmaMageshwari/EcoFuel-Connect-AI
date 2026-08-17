from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Order, Product, User, Seller

orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')


@orders_bp.route('', methods=['POST'])
@jwt_required()
def place_order():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    product = Product.query.get_or_404(data['product_id'])

    if product.quantity_available < data['quantity']:
        return jsonify({'error': 'Insufficient stock'}), 400

    total_price = round(product.price * data['quantity'], 2)
    order = Order(
        buyer_id=user_id,
        product_id=product.id,
        quantity=data['quantity'],
        total_price=total_price,
        delivery_type=data.get('delivery_type', 'delivery'),
        delivery_address=data.get('delivery_address', user.city),
        notes=data.get('notes', '')
    )
    product.quantity_available -= data['quantity']
    if product.seller:
        product.seller.total_sales += 1
    db.session.add(order)
    db.session.commit()
    return jsonify(order.to_dict()), 201


@orders_bp.route('/buyer', methods=['GET'])
@jwt_required()
def buyer_orders():
    user_id = int(get_jwt_identity())
    orders = Order.query.filter_by(buyer_id=user_id).order_by(Order.created_at.desc()).all()
    return jsonify([o.to_dict() for o in orders]), 200


@orders_bp.route('/seller', methods=['GET'])
@jwt_required()
def seller_orders():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    if user.role != 'seller' or not user.seller_profile:
        return jsonify({'error': 'Unauthorized'}), 403

    product_ids = [p.id for p in user.seller_profile.products]
    orders = Order.query.filter(Order.product_id.in_(product_ids)).order_by(Order.created_at.desc()).all()
    return jsonify([o.to_dict() for o in orders]), 200


@orders_bp.route('/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_status(order_id):
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    order = Order.query.get_or_404(order_id)

    # Seller or buyer (for cancellation) can update
    if user.role == 'seller':
        if not user.seller_profile or order.product.seller_id != user.seller_profile.id:
            return jsonify({'error': 'Unauthorized'}), 403
    elif order.buyer_id != user_id and user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    order.status = data['status']
    db.session.commit()
    return jsonify(order.to_dict()), 200

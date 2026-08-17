from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from models import db, Product, Seller, User, SearchLog

products_bp = Blueprint('products', __name__, url_prefix='/api/products')


def optional_jwt():
    try:
        verify_jwt_in_request(optional=True)
        return get_jwt_identity()
    except Exception:
        return None


@products_bp.route('', methods=['GET'])
def list_products():
    query = Product.query.filter_by(is_active=True)

    fuel_type = request.args.get('fuel_type')
    city = request.args.get('city')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    use_case = request.args.get('use_case')
    sort = request.args.get('sort', 'created_at')
    search = request.args.get('search')

    if fuel_type:
        query = query.filter(Product.fuel_type == fuel_type)
    if city:
        query = query.filter(Product.city.ilike(f'%{city}%'))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if use_case:
        query = query.filter(Product.use_case == use_case)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%') | Product.description.ilike(f'%{search}%'))

    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'popular':
        query = query.order_by(Product.views.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    products = query.all()

    # Log search
    uid = optional_jwt()
    if city or fuel_type or search:
        log = SearchLog(
            user_id=int(uid) if uid else None,
            query=search or '',
            fuel_type=fuel_type or '',
            city=city or ''
        )
        db.session.add(log)
        db.session.commit()

    return jsonify([p.to_dict() for p in products]), 200


@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.views += 1
    db.session.commit()
    data = product.to_dict()
    data['reviews'] = [r.to_dict() for r in product.reviews]
    return jsonify(data), 200


@products_bp.route('', methods=['POST'])
@jwt_required()
def create_product():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    if user.role != 'seller':
        return jsonify({'error': 'Only sellers can list products'}), 403

    seller = user.seller_profile
    if not seller:
        return jsonify({'error': 'Seller profile not found'}), 404

    data = request.get_json()
    product = Product(
        seller_id=seller.id,
        name=data['name'],
        fuel_type=data['fuel_type'],
        price=data['price'],
        unit=data.get('unit', 'kg'),
        quantity_available=data['quantity_available'],
        city=data.get('city', user.city),
        pincode=data.get('pincode', user.pincode),
        description=data.get('description', ''),
        use_case=data.get('use_case', 'home'),
        image_url=data.get('image_url', '')
    )
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@products_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    product = Product.query.get_or_404(product_id)

    if user.role != 'seller' or product.seller_id != user.seller_profile.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    for field in ['name', 'fuel_type', 'price', 'unit', 'quantity_available', 'city', 'pincode', 'description', 'use_case', 'image_url', 'is_active']:
        if field in data:
            setattr(product, field, data[field])

    db.session.commit()
    return jsonify(product.to_dict()), 200


@products_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    product = Product.query.get_or_404(product_id)

    if user.role != 'seller' or (user.seller_profile and product.seller_id != user.seller_profile.id):
        return jsonify({'error': 'Unauthorized'}), 403

    product.is_active = False
    db.session.commit()
    return jsonify({'message': 'Product removed'}), 200

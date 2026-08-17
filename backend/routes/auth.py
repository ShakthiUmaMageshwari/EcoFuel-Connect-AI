from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, Seller

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    role = data.get('role', 'buyer')

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400

    user = User(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone', ''),
        city=data.get('city', ''),
        pincode=data.get('pincode', ''),
        role=role
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.flush()

    if role == 'seller':
        seller = Seller(
            user_id=user.id,
            business_name=data.get('business_name', user.name + "'s Business"),
            address=data.get('address', ''),
            description=data.get('description', ''),
        )
        db.session.add(seller)

    db.session.commit()
    token = create_access_token(identity=str(user.id))
    return jsonify({'token': token, 'user': user.to_dict()}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({'token': token, 'user': user.to_dict()}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    data = user.to_dict()
    if user.role == 'seller' and user.seller_profile:
        data['seller'] = user.seller_profile.to_dict()
    return jsonify(data), 200

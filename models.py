from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(15))
    city = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    role = db.Column(db.String(20), default='buyer')  # buyer, seller, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    seller_profile = db.relationship('Seller', backref='user', uselist=False)
    orders = db.relationship('Order', foreign_keys='Order.buyer_id', backref='buyer', lazy=True)
    reviews = db.relationship('Review', foreign_keys='Review.buyer_id', backref='reviewer', lazy=True)
    search_logs = db.relationship('SearchLog', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'city': self.city,
            'pincode': self.pincode,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }


class Seller(db.Model):
    __tablename__ = 'sellers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    business_name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.Text)
    description = db.Column(db.Text)
    verified = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=0.0)
    total_sales = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship('Product', backref='seller', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'business_name': self.business_name,
            'address': self.address,
            'description': self.description,
            'verified': self.verified,
            'rating': self.rating,
            'total_sales': self.total_sales,
            'seller_name': self.user.name if self.user else '',
            'seller_city': self.user.city if self.user else '',
        }


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    fuel_type = db.Column(db.String(50), nullable=False)  # biogas, bio-cng, biofuel, biomass
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), default='kg')  # kg, litre, cubic_meter, unit
    quantity_available = db.Column(db.Float, nullable=False)
    city = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    description = db.Column(db.Text)
    use_case = db.Column(db.String(50))  # home, vehicle, industrial, agricultural
    image_url = db.Column(db.String(300))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)

    orders = db.relationship('Order', backref='product', lazy=True)
    reviews = db.relationship('Review', backref='product', lazy=True)

    def to_dict(self):
        avg_rating = 0.0
        if self.reviews:
            avg_rating = round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)
        return {
            'id': self.id,
            'seller_id': self.seller_id,
            'name': self.name,
            'fuel_type': self.fuel_type,
            'price': self.price,
            'unit': self.unit,
            'quantity_available': self.quantity_available,
            'city': self.city,
            'pincode': self.pincode,
            'description': self.description,
            'use_case': self.use_case,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'views': self.views,
            'avg_rating': avg_rating,
            'review_count': len(self.reviews),
            'seller_name': self.seller.business_name if self.seller else '',
            'seller_verified': self.seller.verified if self.seller else False,
        }


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default='pending')  # pending, confirmed, delivered, cancelled
    delivery_type = db.Column(db.String(20), default='delivery')  # delivery, pickup
    delivery_address = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'buyer_id': self.buyer_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'total_price': self.total_price,
            'status': self.status,
            'delivery_type': self.delivery_type,
            'delivery_address': self.delivery_address,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'product_name': self.product.name if self.product else '',
            'fuel_type': self.product.fuel_type if self.product else '',
            'buyer_name': self.buyer.name if self.buyer else '',
        }


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'buyer_id': self.buyer_id,
            'product_id': self.product_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat(),
            'reviewer_name': self.reviewer.name if self.reviewer else 'Anonymous'
        }


class SearchLog(db.Model):
    __tablename__ = 'search_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    query = db.Column(db.String(200))
    fuel_type = db.Column(db.String(50))
    city = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

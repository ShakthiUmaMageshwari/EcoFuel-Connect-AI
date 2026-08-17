from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')


def create_app():
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
    app.config['SECRET_KEY'] = 'ecofuel-secret-2024-india'
    app.config['JWT_SECRET_KEY'] = 'ecofuel-jwt-secret-2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'ecofuel.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # No expiry for demo

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    JWTManager(app)

    from routes.auth import auth_bp
    from routes.products import products_bp
    from routes.orders import orders_bp
    from routes.analytics import analytics_bp
    from routes.admin import admin_bp
    from routes.ai import ai_bp
    from routes.chatbot import chatbot_bp
    from routes.delivery import delivery_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(delivery_bp)

    # Serve frontend
    @app.route('/')
    def index():
        return send_from_directory(FRONTEND_DIR, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        if os.path.exists(os.path.join(FRONTEND_DIR, path)):
            return send_from_directory(FRONTEND_DIR, path)
        return send_from_directory(FRONTEND_DIR, 'index.html')

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error'}), 500

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        # Auto-seed if DB is empty
        from models import User
        if User.query.count() == 0:
            from seed_data import seed
            seed()
            print("[OK] Database seeded with demo data")
    print("[*] EcoFuel Connect AI Backend running on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

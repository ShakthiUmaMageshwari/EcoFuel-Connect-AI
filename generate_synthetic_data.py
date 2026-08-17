import os
import random
from app import create_app
from models import db, User, Seller, Product

# List of 28 States and 8 Union Territories in India
INDIA_LOCATIONS = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", 
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", 
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", 
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", 
    "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", 
    "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", 
    "Lakshadweep", "Delhi", "Puducherry", "Ladakh", "Jammu and Kashmir"
]

FUEL_TYPES = {
    'biogas': {'unit': 'cubic_meter', 'price_range': (20, 35), 'avail_range': (500, 2000)},
    'bio-cng': {'unit': 'kg', 'price_range': (40, 55), 'avail_range': (400, 1500)},
    'biofuel': {'unit': 'litre', 'price_range': (60, 80), 'avail_range': (8000, 15000)}, # High availability
    'biomass': {'unit': 'kg', 'price_range': (12, 25), 'avail_range': (2000, 6000)},
    'bio-lpg': {'unit': 'kg', 'price_range': (45, 65), 'avail_range': (7000, 12000)}  # High availability
}

def generate_data():
    app = create_app()
    with app.app_context():
        print("[*] Starting synthetic data generation...")
        
        # 1. Create a Global Supplier if doesn't exist
        supplier_email = "global.supplier@ecofuel.in"
        user = User.query.filter_by(email=supplier_email).first()
        if not user:
            user = User(name='Bharat Eco Energy', email=supplier_email, phone='9199999999',
                        city='National', pincode='000000', role='seller')
            user.set_password('ecofuel123')
            db.session.add(user)
            db.session.commit()
            
            seller = Seller(user_id=user.id, business_name='Bharat Eco Energy Ltd.', 
                           address='All India Operations',
                           description='Leading distributor of sustainable fuels across India.', 
                           verified=True, rating=4.8)
            db.session.add(seller)
            db.session.commit()
        else:
            seller = Seller.query.filter_by(user_id=user.id).first()

        # 2. Generate Products for each location
        new_products_count = 0
        for location in INDIA_LOCATIONS:
            for f_type, config in FUEL_TYPES.items():
                # Randomize name and description
                name = f"{location} {f_type.replace('-', ' ').title()}"
                if f_type == 'bio-lpg':
                    name = f"Premium {location} Bio-LPG"
                elif f_type == 'biofuel':
                    name = f"Advanced {location} Bio-Fuel"
                
                desc = f"Sustainable {f_type} sourced from organic waste in {location}. High quality and eco-friendly."
                
                # Check if product already exists for this location/type combo to avoid duplicates
                existing = Product.query.filter_by(seller_id=seller.id, fuel_type=f_type, city=location).first()
                if existing:
                    continue

                prod = Product(
                    seller_id=seller.id,
                    name=name,
                    fuel_type=f_type,
                    price=round(random.uniform(*config['price_range']), 2),
                    unit=config['unit'],
                    quantity_available=round(random.uniform(*config['avail_range']), 1),
                    city=location,
                    pincode=str(random.randint(110001, 700001)),
                    use_case=random.choice(['home', 'vehicle', 'industrial', 'agricultural']),
                    description=desc,
                    views=random.randint(10, 500)
                )
                db.session.add(prod)
                new_products_count += 1
        
        db.session.commit()
        print(f"[OK] Successfully added {new_products_count} new synthetic products across India.")

if __name__ == "__main__":
    generate_data()

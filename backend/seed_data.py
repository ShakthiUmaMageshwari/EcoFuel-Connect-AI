from models import db, User, Seller, Product, Order, Review, SearchLog
from datetime import datetime, timedelta
import random


def seed():
    # ── Admin ──────────────────────────────────────────────
    admin = User(name='EcoFuel Admin', email='admin@ecofuel.in', phone='9000000000',
                 city='Delhi', pincode='110001', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)

    # ── Sellers ────────────────────────────────────────────
    sellers_data = [
        {'name': 'Rajesh Kumar', 'email': 'rajesh@biofarm.in', 'city': 'Delhi', 'pincode': '110044',
         'biz': 'GreenGas Biotech', 'desc': 'Biogas & Bio-CNG from cow dung and food waste'},
        {'name': 'Priya Sharma', 'email': 'priya@ecobio.in', 'city': 'Bangalore', 'pincode': '560001',
         'biz': 'BioGreen Solutions', 'desc': 'Biofuel produced from restaurant food waste'},
        {'name': 'Suresh Patel', 'email': 'suresh@biogas.in', 'city': 'Mumbai', 'pincode': '400001',
         'biz': 'PureFuel Energies', 'desc': 'Bulk biogas supply for industrial & home use'},
        {'name': 'Anitha Reddy', 'email': 'anitha@agrobio.in', 'city': 'Chennai', 'pincode': '600001',
         'biz': 'AgroBio Fuels', 'desc': 'Agricultural waste to biomass energy'},
        {'name': 'Vikram Singh', 'email': 'vikram@cleanfuel.in', 'city': 'Pune', 'pincode': '411001',
         'biz': 'CleanFuel Co-op', 'desc': 'Community-owned biofuel and Bio-CNG plant'},
    ]

    seller_users = []
    seller_profiles = []
    for s in sellers_data:
        u = User(name=s['name'], email=s['email'], phone='98' + str(random.randint(10000000, 99999999)),
                 city=s['city'], pincode=s['pincode'], role='seller')
        u.set_password('seller123')
        db.session.add(u)
        db.session.flush()
        sel = Seller(user_id=u.id, business_name=s['biz'], address=s['city'],
                     description=s['desc'], verified=True,
                     rating=round(random.uniform(3.8, 5.0), 1))
        db.session.add(sel)
        db.session.flush()
        seller_users.append(u)
        seller_profiles.append(sel)

    # ── Products ───────────────────────────────────────────
    products_data = [
        # Seller 0 - Delhi
        dict(seller_idx=0, name='Premium Biogas Cylinder', fuel_type='biogas', price=28, unit='cubic_meter',
             qty=500, city='Delhi', pincode='110044', use_case='home',
             desc='Pure biogas from cow dung. Clean-burning, odorless, and perfect for cooking and heating.'),
        dict(seller_idx=0, name='Bio-CNG for Vehicles', fuel_type='bio-cng', price=43, unit='kg',
             qty=200, city='Delhi', pincode='110044', use_case='vehicle',
             desc='Compressed Bio-CNG suitable for CNG vehicles. Reduce fuel bills by 40%.'),
        # Seller 1 - Bangalore
        dict(seller_idx=1, name='Biofuel Blend B20', fuel_type='biofuel', price=62, unit='litre',
             qty=1000, city='Bangalore', pincode='560001', use_case='vehicle',
             desc='B20 biofuel blend from restaurant waste oil. Compatible with most diesel engines.'),
        dict(seller_idx=1, name='Household Biogas Pack', fuel_type='biogas', price=25, unit='cubic_meter',
             qty=300, city='Bangalore', pincode='560001', use_case='home',
             desc='Monthly subscription biogas for home kitchen. No cylinder deposit needed.'),
        # Seller 2 - Mumbai
        dict(seller_idx=2, name='Industrial Biogas Supply', fuel_type='biogas', price=22, unit='cubic_meter',
             qty=2000, city='Mumbai', pincode='400001', use_case='industrial',
             desc='Bulk biogas for factories and commercial kitchens. Competitive bulk pricing.'),
        dict(seller_idx=2, name='Bio-CNG Station Supply', fuel_type='bio-cng', price=48, unit='kg',
             qty=500, city='Mumbai', pincode='400001', use_case='vehicle',
             desc='Station-grade Bio-CNG for auto-rickshaws and buses.'),
        # Seller 3 - Chennai
        dict(seller_idx=3, name='Agri Biomass Pellets', fuel_type='biomass', price=18, unit='kg',
             qty=5000, city='Chennai', pincode='600001', use_case='agricultural',
             desc='Rice husk and sugarcane bagasse pellets for rural energy needs.'),
        dict(seller_idx=3, name='Farm Biogas Kit', fuel_type='biogas', price=30, unit='cubic_meter',
             qty=150, city='Chennai', pincode='600001', use_case='agricultural',
             desc='Biogas from agricultural waste for farm machinery and irrigation pumps.'),
        # Seller 4 - Pune
        dict(seller_idx=4, name='Pure Biofuel B100', fuel_type='biofuel', price=68, unit='litre',
             qty=800, city='Pune', pincode='411001', use_case='vehicle',
             desc='100% biofuel from non-edible oil seeds. Zero net carbon emissions.'),
        dict(seller_idx=4, name='Community Bio-CNG', fuel_type='bio-cng', price=40, unit='kg',
             qty=600, city='Pune', pincode='411001', use_case='vehicle',
             desc='Cooperative Bio-CNG plant. Low cost, zero tailpipe pollution.'),
        dict(seller_idx=4, name='Biogas Home Connection', fuel_type='biogas', price=20, unit='cubic_meter',
             qty=400, city='Pune', pincode='411001', use_case='home',
             desc='Direct piped biogas for residential areas. No dependency on LPG.'),
        dict(seller_idx=0, name='Biomass Briquettes', fuel_type='biomass', price=15, unit='kg',
             qty=3000, city='Delhi', pincode='110044', use_case='industrial',
             desc='High-density biomass briquettes from crop residue. Replace coal in boilers.'),
    ]

    product_objs = []
    for p in products_data:
        prod = Product(
            seller_id=seller_profiles[p['seller_idx']].id,
            name=p['name'], fuel_type=p['fuel_type'], price=p['price'],
            unit=p['unit'], quantity_available=p['qty'], city=p['city'],
            pincode=p['pincode'], use_case=p['use_case'], description=p['desc'],
            views=random.randint(20, 300)
        )
        db.session.add(prod)
        product_objs.append(prod)
    db.session.flush()

    # ── Buyers ─────────────────────────────────────────────
    buyers_data = [
        {'name': 'Amit Verma', 'email': 'amit@gmail.com', 'city': 'Delhi', 'pincode': '110001'},
        {'name': 'Neha Gupta', 'email': 'neha@gmail.com', 'city': 'Mumbai', 'pincode': '400002'},
        {'name': 'Kiran Rao', 'email': 'kiran@gmail.com', 'city': 'Bangalore', 'pincode': '560002'},
        {'name': 'Deepak Nair', 'email': 'deepak@gmail.com', 'city': 'Chennai', 'pincode': '600002'},
        {'name': 'Meera Joshi', 'email': 'meera@gmail.com', 'city': 'Pune', 'pincode': '411002'},
    ]

    buyer_objs = []
    for b in buyers_data:
        u = User(name=b['name'], email=b['email'],
                 phone='91' + str(random.randint(10000000, 99999999)),
                 city=b['city'], pincode=b['pincode'], role='buyer')
        u.set_password('buyer123')
        db.session.add(u)
        buyer_objs.append(u)
    db.session.flush()

    # ── Orders ─────────────────────────────────────────────
    statuses = ['delivered', 'delivered', 'delivered', 'confirmed', 'pending']
    for i in range(25):
        buyer = random.choice(buyer_objs)
        product = random.choice(product_objs)
        qty = round(random.uniform(1, 10), 1)
        order = Order(
            buyer_id=buyer.id,
            product_id=product.id,
            quantity=qty,
            total_price=round(qty * product.price, 2),
            status=random.choice(statuses),
            delivery_type=random.choice(['delivery', 'pickup']),
            delivery_address=buyer.city
        )
        db.session.add(order)

    # ── Reviews ────────────────────────────────────────────
    review_comments = [
        "Excellent quality! Much cheaper than LPG.",
        "Great product, delivery on time.",
        "Good alternative to petrol. Saved a lot!",
        "Clean burning, no smoke. Highly recommended.",
        "Very good. Will order again.",
        "Affordable and eco-friendly.",
        "Better than expected quality.",
        "Reduced my fuel bills significantly.",
    ]
    for i in range(15):
        review = Review(
            buyer_id=random.choice(buyer_objs).id,
            product_id=random.choice(product_objs).id,
            rating=random.randint(3, 5),
            comment=random.choice(review_comments)
        )
        db.session.add(review)

    # ── Search Logs ────────────────────────────────────────
    cities = ['Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Pune', 'Hyderabad', 'Kolkata']
    fuel_types = ['biogas', 'bio-cng', 'biofuel', 'biomass']
    for i in range(60):
        log = SearchLog(
            user_id=random.choice(buyer_objs).id,
            query=random.choice(['cheap fuel', 'biogas near me', 'alternative fuel', '']),
            fuel_type=random.choice(fuel_types),
            city=random.choice(cities)
        )
        db.session.add(log)

    db.session.commit()
    print("[OK] Seed data inserted successfully!")

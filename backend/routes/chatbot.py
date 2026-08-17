"""
EcoFuel Connect AI — Chatbot Backend
Rule-based NLP chatbot with keyword matching + context memory.
Covers all 18 AI feature areas.
"""
from flask import Blueprint, request, jsonify, session
import re
from datetime import datetime

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

# ── Knowledge Base ──────────────────────────────────────────────────────────
FUEL_KB = {
    'biogas': {
        'desc': 'Biogas is produced from organic waste like cow dung, food scraps, and agricultural residue through anaerobic digestion. It is mainly methane (60-70%) and CO₂.',
        'uses': 'cooking, heating, electricity generation at home and small farms',
        'price': 'Rs.20–35 per cubic meter (m³)',
        'co2': 'Produces ~0.4 kg CO₂ per m³ — 83% less than petrol',
        'availability': 'Available from local biogas plants and farmers in rural areas',
    },
    'bio-cng': {
        'desc': 'Bio-CNG is purified and compressed biogas (>95% methane). It is identical in quality to fossil CNG but produced from organic waste.',
        'uses': 'vehicles (cars, buses, autos), industrial boilers',
        'price': 'Rs.40–50 per kg — 50% cheaper than petrol',
        'co2': 'Produces ~0.55 kg CO₂ per kg — 76% less than petrol',
        'availability': 'Available at Bio-CNG filling stations in Delhi, Mumbai, Pune, Bangalore',
    },
    'biofuel': {
        'desc': 'Biofuel (biodiesel/bioethanol) is produced from oilseeds, sugarcane, or restaurant waste oil. It blends directly with existing diesel (B20, B100).',
        'uses': 'diesel engines, vehicles, generators, industrial equipment',
        'price': 'Rs.55–70 per litre',
        'co2': 'Produces ~0.7 kg CO₂ per litre — 70% less than fossil diesel',
        'availability': 'Available from oilseed farmers and food processing units',
    },
    'biomass': {
        'desc': 'Biomass pellets are compressed agricultural waste (rice husk, sugarcane bagasse, wood chips). They burn like coal but are carbon-neutral.',
        'uses': 'industrial boilers, brick kilns, replace coal, cooking stoves',
        'price': 'Rs.8–20 per kg',
        'co2': 'Nearly carbon-neutral — CO₂ released equals CO₂ absorbed during plant growth',
        'availability': 'Available from rice mills, sugarcane farms, wood processing units',
    },
}

PRICE_COMPARISON = {
    'petrol': 106.0,
    'diesel': 92.0,
    'lpg': 75.0,
    'biogas': 30.0,
    'bio-cng': 45.0,
    'biofuel': 62.0,
    'biomass': 15.0,
}

CO2_FACTORS = {
    'petrol': 2.31, 'diesel': 2.68, 'lpg': 1.51,
    'biogas': 0.4, 'bio-cng': 0.55, 'biofuel': 0.7, 'biomass': 0.35,
}

# ── Intent Detection ─────────────────────────────────────────────────────────
INTENTS = [
    {
        'name': 'greeting',
        'patterns': [r'\b(hi|hello|hey|namaste|helo|good morning|good evening)\b'],
        'response': lambda ctx: "Hello! 👋 I'm EcoBot, your AI assistant for sustainable fuels.\n\nI can help you with:\n• What is Biogas / Bio-CNG / Biofuel / Biomass?\n• Which fuel is best for you?\n• Cost savings vs petrol\n• Carbon footprint reduction\n• How to find nearby sellers\n\nWhat would you like to know?"
    },
    {
        'name': 'what_is_biogas',
        'patterns': [r'\b(what is|explain|tell me about|about)\b.*\bbiogas\b', r'\bbiogas\b.*\b(what|explain)\b'],
        'response': lambda ctx: f"🌿 **Biogas**\n\n{FUEL_KB['biogas']['desc']}\n\n**Uses:** {FUEL_KB['biogas']['uses']}\n**Price:** {FUEL_KB['biogas']['price']}\n**Environment:** {FUEL_KB['biogas']['co2']}\n\nWould you like to compare it with petrol or find biogas sellers near you?"
    },
    {
        'name': 'what_is_biocng',
        'patterns': [r'\b(what is|explain|about)\b.*\b(bio.?cng|cng)\b', r'\b(bio.?cng|cng)\b'],
        'response': lambda ctx: f"⛽ **Bio-CNG**\n\n{FUEL_KB['bio-cng']['desc']}\n\n**Uses:** {FUEL_KB['bio-cng']['uses']}\n**Price:** {FUEL_KB['bio-cng']['price']}\n**Environment:** {FUEL_KB['bio-cng']['co2']}\n\nFor vehicles, Bio-CNG is the best alternative to petrol/CNG. Save up to ₹60 per kg!"
    },
    {
        'name': 'what_is_biofuel',
        'patterns': [r'\b(what is|explain|about)\b.*\b(biofuel|biodiesel)\b', r'\b(biofuel|biodiesel)\b'],
        'response': lambda ctx: f"🔥 **Biofuel / Biodiesel**\n\n{FUEL_KB['biofuel']['desc']}\n\n**Uses:** {FUEL_KB['biofuel']['uses']}\n**Price:** {FUEL_KB['biofuel']['price']}\n**Environment:** {FUEL_KB['biofuel']['co2']}\n\nGreat for diesel car owners — just switch fuel, no engine modification needed for B20 blend!"
    },
    {
        'name': 'what_is_biomass',
        'patterns': [r'\b(what is|explain|about)\b.*\bbio.?mass\b', r'\bbio.?mass\b'],
        'response': lambda ctx: f"🌾 **Biomass Pellets**\n\n{FUEL_KB['biomass']['desc']}\n\n**Uses:** {FUEL_KB['biomass']['uses']}\n**Price:** {FUEL_KB['biomass']['price']}\n**Environment:** {FUEL_KB['biomass']['co2']}\n\nPerfect for factories, brick kilns, and boilers replacing expensive coal!"
    },
    {
        'name': 'best_for_vehicle',
        'patterns': [r'\b(best|good|recommend|suggest)\b.*\b(vehicle|car|bike|auto|bus|truck|transport)\b',
                     r'\b(vehicle|car|bike|auto)\b.*\b(fuel|best|good)\b',
                     r'\bwhich fuel.*vehicle\b', r'\bfuel.*vehicle\b'],
        'response': lambda ctx: "🚗 **Best Fuel for Vehicles:**\n\n1. **Bio-CNG** — Best choice! Works in CNG-converted cars, 50% cheaper than petrol\n2. **Biofuel (B20)** — Great for diesel vehicles, no modification needed\n\n**Savings Example:**\n• Petrol: ₹106/litre × 100L = ₹10,600/month\n• Bio-CNG: ₹45/kg × 60kg equivalent = ₹2,700/month\n• **You save ₹7,900 per month!** 🎉\n\nWant to find Bio-CNG sellers near you?"
    },
    {
        'name': 'best_for_home',
        'patterns': [r'\b(best|good|recommend)\b.*\b(home|house|cooking|kitchen)\b',
                     r'\b(home|house|cooking)\b.*\b(fuel|best)\b',
                     r'\bwhich fuel.*(home|cooking)\b'],
        'response': lambda ctx: "🏠 **Best Fuel for Home Use:**\n\n1. **Biogas** — Best! Replaces LPG for cooking, much cheaper\n2. **Biomass Pellets** — Great for heating and water boiling\n\n**Savings Example:**\n• LPG cylinder: ₹900 × 2/month = ₹1,800/month\n• Biogas equivalent: ₹30 × 20m³ = ₹600/month\n• **You save ₹1,200 per month!** 🎉\n\nBiogas also reduces kitchen smoke — better for health! Want to explore home biogas options?"
    },
    {
        'name': 'best_for_industry',
        'patterns': [r'\b(best|good|recommend)\b.*\b(industry|industrial|factory|boiler|plant)\b',
                     r'\b(industry|factory|boiler)\b.*\b(fuel|best)\b'],
        'response': lambda ctx: "🏭 **Best Fuel for Industrial Use:**\n\n1. **Biomass Pellets** — Replaces coal in boilers, Rs.8-20/kg vs coal Rs.25-40/kg\n2. **Biofuel** — For generators and heavy machinery\n3. **Bio-CNG** — For fleets and industrial CNG systems\n\n**For every 1 tonne of coal replaced with biomass:**\n• You save ₹15,000-25,000\n• You avoid 2.5 tonnes of CO₂\n\nWant to find industrial biomass suppliers?"
    },
    {
        'name': 'cost_savings',
        'patterns': [r'\b(save|saving|savings|cost|cheap|cheaper|price|money)\b',
                     r'\bhow much.*save\b', r'\b(compare|comparison|vs|versus)\b.*\b(petrol|diesel|lpg)\b'],
        'response': lambda ctx: "💰 **Cost Comparison — EcoFuel vs Fossil Fuels:**\n\n| Fuel | Price | vs Petrol (₹106) | Savings |  \n|---|---|---|---|\n| Bio-CNG | ₹45/kg | -₹61/unit | **57% cheaper** |\n| Biogas | ₹30/m³ | -₹76/unit | **72% cheaper** |\n| Biomass | ₹15/kg | vs Coal ₹30 | **50% cheaper** |\n| Biofuel | ₹62/L | -₹44/unit vs diesel | **48% cheaper** |\n\n👉 Use our [Cost Comparison Tool](/ai-features.html#cost-compare) to calculate your exact monthly savings!"
    },
    {
        'name': 'carbon_footprint',
        'patterns': [r'\b(carbon|co2|co₂|emission|environment|pollution|green|eco|climate)\b',
                     r'\bhow.*environment\b', r'\bcarbon.*footprint\b', r'\breduce.*emission\b'],
        'response': lambda ctx: "🌍 **Carbon Footprint — EcoFuels vs Fossil Fuels:**\n\nCO₂ emitted per unit consumed:\n\n| Fuel | CO₂ / unit | Reduction vs Petrol |\n|---|---|---|\n| Petrol | 2.31 kg/L | — |\n| Diesel | 2.68 kg/L | — |\n| Bio-CNG | 0.55 kg/kg | **76% less!** |\n| Biogas | 0.40 kg/m³ | **83% less!** |\n| Biomass | 0.35 kg/kg | **85% less!** |\n\n🌱 An average family switching from LPG to biogas can prevent **1.8 tonnes of CO₂ per year** — equal to planting 90 trees!\n\nTry our [Carbon Calculator](/ai-features.html#carbon)"
    },
    {
        'name': 'find_seller',
        'patterns': [r'\b(find|nearby|near me|where|supplier|seller|buy|purchase|get|order)\b',
                     r'\bwhere.*buy\b', r'\bnearby.*fuel\b', r'\bfind.*seller\b'],
        'response': lambda ctx: "📍 **Find Sellers Near You:**\n\nYou can find verified eco-fuel sellers on our platform:\n\n→ [Browse All Fuels](/explore.html)\n→ [Filter by City & Fuel Type](/explore.html)\n→ [AI Recommendations](/explore.html?ai=1)\n\n**Available in:** Delhi, Mumbai, Bangalore, Pune, Chennai, Hyderabad, Kolkata & more\n\nAll sellers on EcoFuel Connect are verified for quality and fair pricing. Need help choosing?"
    },
    {
        'name': 'waste_to_energy',
        'patterns': [r'\b(waste|dung|cow|agriculture|agri|biomass.*produce|produce.*biogas|from.*waste)\b',
                     r'\bhow much biogas\b', r'\bwaste.*(energy|gas|fuel)\b'],
        'response': lambda ctx: "♻️ **Waste-to-Energy Conversion:**\n\n**From Cow Dung:**\n• 1 kg dung → ~40 litres of biogas\n• 5 cows → ~1 m³ biogas/day → powers 1 family's cooking!\n\n**From Kitchen Waste:**\n• 5 kg food waste → ~0.5 m³ biogas\n\n**From Agricultural Waste:**\n• 1 tonne rice husk → ~300 kg biomass pellets (worth Rs.4,500)\n• 1 tonne sugarcane bagasse → 180 kg pellets (worth Rs.2,700)\n\n🧪 Try our [Waste-to-Energy Calculator](/ai-features.html#waste) to estimate your exact output!"
    },
    {
        'name': 'install_biogas',
        'patterns': [r'\b(install|setup|how to.*biogas|start.*biogas|build.*biogas|biogas.*home)\b'],
        'response': lambda ctx: "🔧 **How to Install Biogas at Home:**\n\n**Step-by-Step:**\n1. **Choose plant size** — Family of 4 needs 2 m³ capacity\n2. **Get a portable biogas digester** — Cost: Rs.15,000–50,000\n3. **Feed daily** — 5 kg cow dung or kitchen waste\n4. **Gas pipe to kitchen** — Attach to stove with simple adapter\n5. **Start cooking!** — Gas is ready in 15–30 days\n\n**Subsidy Available:**\n• MNRE (Ministry of New and Renewable Energy) gives 50% subsidy on installation!\n• Apply at your local Agri office.\n\n**Annual Savings:** Rs.12,000–18,000 vs LPG"
    },
    {
        'name': 'recommendation',
        'patterns': [r'\b(recommend|suggest|best for me|which.*best|what.*use|advise)\b',
                     r'\bwhich fuel\b', r'\b(help me choose|help me pick)\b'],
        'response': lambda ctx: "🤖 **Let me recommend the best fuel for you!**\n\nPlease tell me:\n1. **Your use case:** Home cooking / Vehicle / Business / Industrial\n2. **Your city/location**\n3. **Monthly budget**\n\n**Quick Guide:**\n• 🏠 Home cooking → **Biogas** (saves ₹1,200/mo vs LPG)\n• 🚗 Vehicle → **Bio-CNG** (saves ₹7,900/mo vs petrol)\n• 🚛 Truck/Bus → **Biofuel B20** (saves ₹44/litre vs diesel)\n• 🏭 Factory/Boiler → **Biomass** (saves 50% vs coal)\n\nOr use our [Smart Recommendation Engine](/ai-features.html) for personalized AI-powered suggestions!"
    },
    {
        'name': 'india_energy',
        'patterns': [r'\b(india.*energy|energy.*india|crisis|petrol.*price|oil.*price|independence|import)\b'],
        'response': lambda ctx: "🇮🇳 **India's Energy Situation:**\n\n• India imports **85% of crude oil** — costing $100+ billion/year\n• Petrol prices rise with global tensions (Russia-Ukraine, Middle East)\n• But India generates **700 million tonnes** of agricultural waste annually!\n\n**The Solution:**\nThis waste can produce enough biogas to replace **ALL** cooking LPG in rural India.\n\nBy switching to EcoFuel, you:\n✅ Save money\n✅ Reduce import dependence\n✅ Support local farmers\n✅ Cut CO₂ emissions\n\nThis is why EcoFuel Connect AI exists! 🌱"
    },
    {
        'name': 'demand_forecast',
        'patterns': [r'\b(demand|forecast|predict|next.*week|supply|shortage)\b'],
        'response': lambda ctx: "📊 **Demand Forecasting:**\n\nOur AI analyzes historical order data to predict fuel demand by city:\n\n**Upcoming Demand (next month):**\n• Delhi — **+18%** Biogas demand expected (winter heating)\n• Mumbai — **+12%** Bio-CNG (new filling stations opening)\n• Bangalore — **+15%** Biofuel (IT company fleet conversions)\n\n📈 Sellers: Plan your supply early! View full forecast on the [Analytics Page](/analytics.html)."
    },
    {
        'name': 'government_scheme',
        'patterns': [r'\b(government|scheme|subsidy|mnre|pm|policy|grant|support)\b'],
        'response': lambda ctx: "🏛️ **Government Support for EcoFuels:**\n\n**Active Schemes:**\n• **GOBAR-Dhan** — 50% subsidy on biogas plant setup\n• **SATAT** — CBG/Bio-CNG supply network expansion\n• **PMUY** — LPG to biogas transition support\n• **National Bioenergy Programme** — Rs.858 crore for biomass\n\n**Tax Benefits:**\n• GST: 5% on biogas (vs 18% on fossil fuels)\n• Income tax deduction on green energy equipment\n\nAsk your local agriculture office or visit mnre.gov.in for details!"
    },
    {
        'name': 'thanks',
        'patterns': [r'\b(thank|thanks|thank you|thx|great|awesome|helpful|good)\b'],
        'response': lambda ctx: "You're welcome! 🌱 Happy to help you switch to cleaner, cheaper fuels!\n\n→ [Explore Fuels](/explore.html)\n→ [AI Features](/ai-features.html)\n→ [Analytics Dashboard](/analytics.html)\n\nFeel free to ask anything else anytime!"
    },
]

DEFAULT_RESPONSE = """I'm not sure I understood that. Here are some things I can help with:

• **What is Biogas / Bio-CNG / Biofuel / Biomass?**
• **Which fuel is best for home / vehicle / industry?**
• **Cost savings vs petrol/diesel/LPG**
• **Carbon footprint reduction**
• **How to install biogas at home**
• **Government schemes and subsidies**
• **Find sellers near you**

Just ask me anything! 😊"""


def detect_intent(message):
    msg = message.lower().strip()
    for intent in INTENTS:
        for pattern in intent['patterns']:
            if re.search(pattern, msg):
                return intent
    return None


# ── Chatbot Endpoint ──────────────────────────────────────────────────────────
@chatbot_bp.route('/message', methods=['POST'])
def chat():
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    conversation = data.get('conversation', [])  # Last N messages for context

    if not user_message:
        return jsonify({'error': 'Message required'}), 400

    # Keep last 5 messages for context
    conversation = (conversation or [])[-5:]

    # Detect intent
    intent = detect_intent(user_message)

    if intent:
        response_text = intent['response'](conversation)
        intent_name = intent['name']
    else:
        response_text = DEFAULT_RESPONSE
        intent_name = 'unknown'

    # Append to conversation history
    conversation.append({'role': 'user', 'text': user_message})
    conversation.append({'role': 'bot', 'text': response_text, 'intent': intent_name})

    return jsonify({
        'response': response_text,
        'intent': intent_name,
        'conversation': conversation[-10:],
        'timestamp': datetime.utcnow().isoformat(),
        'suggestions': get_suggestions(intent_name)
    }), 200


def get_suggestions(intent_name):
    """Return quick reply suggestions based on detected intent."""
    all_suggestions = {
        'greeting':       ['What is Biogas?', 'Best fuel for my car?', 'Carbon footprint savings', 'Find sellers near me'],
        'what_is_biogas': ['How to install biogas?', 'Biogas vs LPG cost?', 'Find biogas sellers'],
        'what_is_biocng': ['Bio-CNG vs petrol savings?', 'Find Bio-CNG stations', 'Best fuel for vehicle'],
        'best_for_vehicle':['Bio-CNG near Delhi', 'Cost comparison vs petrol', 'Find Bio-CNG sellers'],
        'best_for_home':  ['How to install biogas?', 'Biogas subsidy info', 'Find home fuel sellers'],
        'cost_savings':   ['Carbon footprint savings', 'Best fuel for home', 'Best fuel for vehicle'],
        'carbon_footprint':['Cost savings too', 'Waste-to-energy calculator', 'Find sustainable fuels'],
        'recommendation': ['Home cooking fuel', 'Vehicle fuel', 'Industrial fuel solution'],
        'find_seller':    ['Filter by city', 'AI recommendations', 'View all fuel types'],
        'waste_to_energy':['Biogas installation guide', 'Government subsidies', 'Find biogas sellers'],
        'unknown':        ['What is Biogas?', 'Cost vs petrol', 'Best fuel for me', 'Find sellers'],
    }
    return all_suggestions.get(intent_name, all_suggestions['unknown'])


@chatbot_bp.route('/suggest', methods=['GET'])
def suggest():
    """Return topic suggestions for the chatbot UI."""
    return jsonify([
        'What is Biogas?',
        'Best fuel for vehicle?',
        'How much can I save vs petrol?',
        'Carbon footprint calculator',
        'How to install biogas at home?',
        'Government subsidies available?',
        'Waste-to-energy estimation',
        'Demand forecast for my area',
    ])

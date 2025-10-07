from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import logging

logger = logging.getLogger(__name__)

def clean_mongo_doc(doc):
    """Remove MongoDB ObjectId fields from document"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [clean_mongo_doc(item) for item in doc]
    if isinstance(doc, dict):
        cleaned = {}
        for key, value in doc.items():
            if key == '_id':
                continue  # Skip MongoDB ObjectId field
            cleaned[key] = clean_mongo_doc(value)
        return cleaned
    return doc

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'moneymojo_db')

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]
async def get_database():
    """Get database instance"""
    return db

async def init_database():
    """Initialize database with indexes and constraints"""
    try:
        # Create indexes for better performance
        
        # Users collection indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("id", unique=True)
        await db.users.create_index("created_at")
        await db.users.create_index("email_verified")
        await db.users.create_index("is_active")
        await db.users.create_index("last_login")
        
        # Transactions collection indexes
        await db.transactions.create_index("user_id")
        await db.transactions.create_index("date")
        await db.transactions.create_index([("user_id", 1), ("date", -1)])
        await db.transactions.create_index("type")
        await db.transactions.create_index("is_hustle_related")
        
        # User hustles collection indexes
        await db.user_hustles.create_index("created_by")
        await db.user_hustles.create_index("status")
        await db.user_hustles.create_index("category")
        await db.user_hustles.create_index("created_at")
        await db.user_hustles.create_index("is_admin_posted")
        await db.user_hustles.create_index("application_deadline")
        
        # Hustle applications collection indexes
        await db.hustle_applications.create_index("hustle_id")
        await db.hustle_applications.create_index("applicant_id")
        await db.hustle_applications.create_index([("hustle_id", 1), ("applicant_id", 1)], unique=True)
        await db.hustle_applications.create_index("applied_at")
        await db.hustle_applications.create_index("status")
        
        # Budgets collection indexes
        await db.budgets.create_index("user_id")
        await db.budgets.create_index("month")
        await db.budgets.create_index([("user_id", 1), ("month", 1), ("category", 1)], unique=True)
        
        # Email verification collection indexes
        await db.email_verifications.create_index("email")
        await db.email_verifications.create_index("expires_at", expireAfterSeconds=0)
        
        # Password reset collection indexes
        await db.password_resets.create_index("email")
        await db.password_resets.create_index("expires_at", expireAfterSeconds=0)
        
        # Financial goals collection indexes
        await db.financial_goals.create_index("user_id")
        await db.financial_goals.create_index("category")
        await db.financial_goals.create_index("is_active")
        await db.financial_goals.create_index([("user_id", 1), ("category", 1)])
        
        # Category suggestions collection indexes
        await db.category_suggestions.create_index("category")
        await db.category_suggestions.create_index("is_active")
        await db.category_suggestions.create_index([("category", 1), ("priority", -1)])
        
        # Emergency types collection indexes
        await db.emergency_types.create_index("name", unique=True)
        await db.emergency_types.create_index("urgency_level")
        
        # Hospitals collection indexes
        await db.hospitals.create_index("city")
        await db.hospitals.create_index("state")
        await db.hospitals.create_index([("latitude", 1), ("longitude", 1)])
        await db.hospitals.create_index("rating")
        await db.hospitals.create_index("is_emergency")
        
        # Click analytics collection indexes
        await db.click_analytics.create_index("user_id")
        await db.click_analytics.create_index("category")
        await db.click_analytics.create_index("clicked_at")
        await db.click_analytics.create_index([("category", 1), ("clicked_at", -1)])
        
        # Auto import sources collection indexes
        await db.auto_import_sources.create_index("user_id")
        await db.auto_import_sources.create_index("source_type")
        await db.auto_import_sources.create_index("provider")
        await db.auto_import_sources.create_index("is_active")
        await db.auto_import_sources.create_index("created_at")
        
        # Parsed transactions collection indexes
        await db.parsed_transactions.create_index("user_id")
        await db.parsed_transactions.create_index("source_id")
        await db.parsed_transactions.create_index("created_at")
        await db.parsed_transactions.create_index("confidence_score")
        
        # Transaction suggestions collection indexes
        await db.transaction_suggestions.create_index("user_id")
        await db.transaction_suggestions.create_index("parsed_transaction_id")
        await db.transaction_suggestions.create_index("status")
        await db.transaction_suggestions.create_index("created_at")
        await db.transaction_suggestions.create_index([("user_id", 1), ("status", 1)])
        await db.transaction_suggestions.create_index("confidence_score")
        
        # Learning feedback collection indexes
        await db.learning_feedback.create_index("user_id")
        await db.learning_feedback.create_index("suggestion_id")
        await db.learning_feedback.create_index("feedback_type")
        await db.learning_feedback.create_index("created_at")
        await db.learning_feedback.create_index([("user_id", 1), ("feedback_type", 1)])
        
        # Universities collection indexes
        await db.universities.create_index("name", unique=True)
        await db.universities.create_index("city")
        await db.universities.create_index("state")
        await db.universities.create_index("type")
        await db.universities.create_index("ranking")
        await db.universities.create_index("is_verified")
        await db.universities.create_index([("city", 1), ("state", 1)])
        await db.universities.create_index([("state", 1), ("ranking", 1)])
        await db.universities.create_index("student_levels")
        
        logger.info("Database indexes created successfully")
        
        # Initialize seed data
        await init_seed_data()
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")

async def init_seed_data():
    """Initialize seed data for category suggestions and emergency data"""
    try:
        # Initialize Category Suggestions
        existing_suggestions = await db.category_suggestions.count_documents({})
        if existing_suggestions == 0:
            category_suggestions = [
                # Movies Category
                {"category": "Movies", "name": "BookMyShow", "url": "https://bookmyshow.com", "type": "both", "priority": 10, "description": "Book movie tickets online", "is_active": True},
                {"category": "Movies", "name": "PVR Cinemas", "url": "https://pvrcinemas.com", "type": "both", "priority": 9, "description": "Premium movie experience", "is_active": True},
                {"category": "Movies", "name": "INOX Movies", "url": "https://inoxmovies.com", "type": "both", "priority": 8, "description": "Luxury cinema experience", "is_active": True},
                
                # Transportation Category
                {"category": "Transportation", "name": "Uber", "url": "https://uber.com", "type": "app", "priority": 10, "description": "Ride sharing service", "is_active": True},
                {"category": "Transportation", "name": "Ola Cabs", "url": "https://olacabs.com", "type": "app", "priority": 9, "description": "Local taxi service", "is_active": True},
                {"category": "Transportation", "name": "Rapido", "url": "https://rapido.bike", "type": "app", "priority": 8, "description": "Bike taxi service", "is_active": True},
                {"category": "Transportation", "name": "RedBus", "url": "https://redbus.in", "type": "both", "priority": 9, "description": "Bus booking service", "is_active": True},
                {"category": "Transportation", "name": "Namma Yatri", "url": "https://nammayatri.in", "type": "app", "priority": 7, "description": "Open mobility platform", "is_active": True},
                
                # Shopping Category  
                {"category": "Shopping", "name": "Amazon", "url": "https://amazon.in", "type": "both", "priority": 10, "description": "Online marketplace", "is_active": True},
                {"category": "Shopping", "name": "Flipkart", "url": "https://flipkart.com", "type": "both", "priority": 9, "description": "E-commerce platform", "is_active": True},
                {"category": "Shopping", "name": "Meesho", "url": "https://meesho.com", "type": "both", "priority": 8, "description": "Social commerce platform", "is_active": True},
                {"category": "Shopping", "name": "Myntra", "url": "https://myntra.com", "type": "both", "priority": 8, "description": "Fashion and lifestyle", "is_active": True},
                {"category": "Shopping", "name": "Ajio", "url": "https://ajio.com", "type": "both", "priority": 7, "description": "Fashion retailer", "is_active": True},
                
                # Food Category
                {"category": "Food", "name": "Zomato", "url": "https://zomato.com", "type": "both", "priority": 10, "description": "Food delivery service", "is_active": True},
                {"category": "Food", "name": "Swiggy", "url": "https://swiggy.com", "type": "both", "priority": 10, "description": "Food delivery platform", "is_active": True},
                {"category": "Food", "name": "Domino's Pizza", "url": "https://dominos.co.in", "type": "both", "priority": 8, "description": "Pizza delivery", "is_active": True},
                {"category": "Food", "name": "McDonald's", "url": "https://mcdelivery.co.in", "type": "both", "priority": 7, "description": "Fast food delivery", "is_active": True},
                
                # Groceries Category
                {"category": "Groceries", "name": "Swiggy Instamart", "url": "https://swiggy.com/instamart", "type": "app", "priority": 10, "description": "Quick grocery delivery", "is_active": True},
                {"category": "Groceries", "name": "Blinkit", "url": "https://blinkit.com", "type": "both", "priority": 10, "description": "10-minute grocery delivery", "is_active": True},
                {"category": "Groceries", "name": "BigBasket", "url": "https://bigbasket.com", "type": "both", "priority": 9, "description": "Online grocery store", "is_active": True},
                {"category": "Groceries", "name": "Zepto", "url": "https://zepto.co.in", "type": "app", "priority": 9, "description": "Ultra-fast grocery delivery", "is_active": True},
                {"category": "Groceries", "name": "JioMart", "url": "https://jiomart.com", "type": "both", "priority": 8, "description": "Digital commerce platform", "is_active": True},
                
                # Entertainment Category
                {"category": "Entertainment", "name": "Netflix", "url": "https://netflix.com", "type": "both", "priority": 10, "description": "Streaming service", "offers": "Various subscription plans", "is_active": True},
                {"category": "Entertainment", "name": "Amazon Prime Video", "url": "https://primevideo.com", "type": "both", "priority": 9, "description": "Prime video streaming", "is_active": True},
                {"category": "Entertainment", "name": "Disney+ Hotstar", "url": "https://hotstar.com", "type": "both", "priority": 9, "description": "Disney and sports content", "is_active": True},
                {"category": "Entertainment", "name": "YouTube Premium", "url": "https://youtube.com/premium", "type": "both", "priority": 8, "description": "Ad-free YouTube experience", "is_active": True},
                {"category": "Entertainment", "name": "SonyLIV", "url": "https://sonyliv.com", "type": "both", "priority": 7, "description": "Sony content streaming", "is_active": True},
                
                # Books Category
                {"category": "Books", "name": "Amazon Kindle", "url": "https://amazon.in/kindle", "type": "both", "priority": 10, "description": "Digital books platform", "is_active": True},
                {"category": "Books", "name": "Audible", "url": "https://audible.in", "type": "both", "priority": 9, "description": "Audiobooks service", "is_active": True},
                {"category": "Books", "name": "Flipkart Books", "url": "https://flipkart.com/books", "type": "website", "priority": 8, "description": "Online bookstore", "is_active": True},
                {"category": "Books", "name": "Crossword", "url": "https://crossword.in", "type": "both", "priority": 7, "description": "Book retailer", "is_active": True},
                {"category": "Books", "name": "Storytel", "url": "https://storytel.com", "type": "app", "priority": 6, "description": "Audiobook streaming", "is_active": True},
            ]
            
            await db.category_suggestions.insert_many(category_suggestions)
            logger.info(f"Inserted {len(category_suggestions)} category suggestions")
        
        # Initialize Emergency Types
        existing_emergency_types = await db.emergency_types.count_documents({})
        if existing_emergency_types == 0:
            emergency_types = [
                {"name": "Medical Emergency", "icon": "🚑", "description": "Heart attack, stroke, severe injury, breathing problems", "urgency_level": "high"},
                {"name": "Accident", "icon": "🚗", "description": "Vehicle accidents, workplace accidents, home accidents", "urgency_level": "high"},
                {"name": "Fire Emergency", "icon": "🔥", "description": "House fire, building fire, forest fire", "urgency_level": "high"},
                {"name": "Natural Disaster", "icon": "🌪️", "description": "Earthquake, flood, cyclone, landslide", "urgency_level": "high"},
                {"name": "Crime/Security", "icon": "👮", "description": "Theft, assault, suspicious activity, security threat", "urgency_level": "medium"},
                {"name": "Mental Health Crisis", "icon": "🧠", "description": "Suicide risk, severe anxiety, panic attack", "urgency_level": "high"},
            ]
            
            await db.emergency_types.insert_many(emergency_types)
            logger.info(f"Inserted {len(emergency_types)} emergency types")
        
        # Initialize Sample Hospital Data (Major cities)
        existing_hospitals = await db.hospitals.count_documents({})
        if existing_hospitals == 0:
            sample_hospitals = [
                # Mumbai
                {"name": "Kokilaben Dhirubhai Ambani Hospital", "city": "Mumbai", "state": "Maharashtra", "phone": "022-42696969", "emergency_phone": "022-42696911", "latitude": 19.1334, "longitude": 72.8267, "rating": 4.5, "type": "private", "is_emergency": True, "is_24x7": True, "specialties": ["Cardiology", "Neurology", "Oncology"], "address": "Rao Saheb Achutrao Patwardhan Marg, Four Bungalows, Andheri West"},
                {"name": "Lilavati Hospital", "city": "Mumbai", "state": "Maharashtra", "phone": "022-26567777", "emergency_phone": "022-26567911", "latitude": 19.0545, "longitude": 72.8302, "rating": 4.3, "type": "private", "is_emergency": True, "is_24x7": True, "specialties": ["Emergency Medicine", "Trauma Care"], "address": "A-791, Bandra Reclamation, Bandra West"},
                
                # Delhi
                {"name": "All India Institute of Medical Sciences (AIIMS)", "city": "New Delhi", "state": "Delhi", "phone": "011-26588500", "emergency_phone": "011-26588663", "latitude": 28.5672, "longitude": 77.2100, "rating": 4.8, "type": "government", "is_emergency": True, "is_24x7": True, "specialties": ["All Specialties"], "address": "Sri Aurobindo Marg, Ansari Nagar"},
                {"name": "Fortis Hospital Shalimar Bagh", "city": "New Delhi", "state": "Delhi", "phone": "011-47135000", "emergency_phone": "011-47135911", "latitude": 28.7196, "longitude": 77.1569, "rating": 4.2, "type": "private", "is_emergency": True, "is_24x7": True, "specialties": ["Cardiology", "Orthopedics"], "address": "AA-299, Shahpur Jat, Shalimar Bagh"},
                
                # Bangalore
                {"name": "Manipal Hospital Whitefield", "city": "Bangalore", "state": "Karnataka", "phone": "080-66712000", "emergency_phone": "080-66712911", "latitude": 12.9699, "longitude": 77.7499, "rating": 4.4, "type": "private", "is_emergency": True, "is_24x7": True, "specialties": ["Emergency Care", "Critical Care"], "address": "#143, 212-2015, HRBR Layout, Kalyan Nagar, Whitefield"},
                {"name": "Apollo Hospital Bannerghatta", "city": "Bangalore", "state": "Karnataka", "phone": "080-26304050", "emergency_phone": "080-26304911", "latitude": 12.8008, "longitude": 77.6495, "rating": 4.3, "type": "private", "is_emergency": True, "is_24x7": True, "specialties": ["Multi-specialty"], "address": "154/11, Opposite IIM-B, Bannerghatta Road"},
                
                # Chennai
                {"name": "Apollo Hospital Greams Road", "city": "Chennai", "state": "Tamil Nadu", "phone": "044-28293333", "emergency_phone": "044-28293911", "latitude": 13.0661, "longitude": 80.2589, "rating": 4.5, "type": "private", "is_emergency": True, "is_24x7": True, "specialties": ["Cardiology", "Transplant"], "address": "21, Greams Lane, Off Greams Road"},
                {"name": "Fortis Malar Hospital", "city": "Chennai", "state": "Tamil Nadu", "phone": "044-42892222", "emergency_phone": "044-42892911", "latitude": 13.0339, "longitude": 80.2403, "rating": 4.2, "type": "private", "is_emergency": True, "is_24x7": True, "specialties": ["Emergency Medicine"], "address": "52, 1st Main Road, Gandhi Nagar, Adyar"},
            ]
            
            await db.hospitals.insert_many(sample_hospitals)
            logger.info(f"Inserted {len(sample_hospitals)} sample hospitals")
        
        # Initialize Universities Database
        existing_universities = await db.universities.count_documents({})
        if existing_universities == 0:
            comprehensive_universities = [
                # === MAHARASHTRA ===
                {
                    "name": "Indian Institute of Technology Bombay",
                    "short_name": "IIT Bombay",
                    "location": "Mumbai, Maharashtra",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "type": "engineering_institute",
                    "student_levels": ["undergraduate", "graduate"],
                    "categories": ["engineering", "technology", "research"],
                    "ranking": 1,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "University of Mumbai",
                    "short_name": "Mumbai University",
                    "location": "Mumbai, Maharashtra",
                    "city": "Mumbai", 
                    "state": "Maharashtra",
                    "type": "state_university",
                    "student_levels": ["high_school", "undergraduate", "graduate"],
                    "categories": ["general", "commerce", "science", "arts"],
                    "ranking": 15,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "Indian Institute of Technology Pune",
                    "short_name": "IISER Pune",
                    "location": "Pune, Maharashtra",
                    "city": "Pune",
                    "state": "Maharashtra", 
                    "type": "science_institute",
                    "student_levels": ["undergraduate", "graduate"],
                    "categories": ["science", "research"],
                    "ranking": 8,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "Pune University",
                    "short_name": "Pune University",
                    "location": "Pune, Maharashtra",
                    "city": "Pune",
                    "state": "Maharashtra",
                    "type": "state_university", 
                    "student_levels": ["high_school", "undergraduate", "graduate"],
                    "categories": ["general", "engineering", "management"],
                    "ranking": 18,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                
                # === DELHI ===
                {
                    "name": "Indian Institute of Technology Delhi",
                    "short_name": "IIT Delhi",
                    "location": "New Delhi",
                    "city": "Delhi",
                    "state": "Delhi",
                    "type": "engineering_institute",
                    "student_levels": ["undergraduate", "graduate"],
                    "categories": ["engineering", "technology", "research"],
                    "ranking": 2,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "Delhi University",
                    "short_name": "DU",
                    "location": "New Delhi",
                    "city": "Delhi", 
                    "state": "Delhi",
                    "type": "central_university",
                    "student_levels": ["high_school", "undergraduate", "graduate"],
                    "categories": ["general", "commerce", "science", "arts", "law"],
                    "ranking": 12,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "Jawaharlal Nehru University",
                    "short_name": "JNU",
                    "location": "New Delhi",
                    "city": "Delhi",
                    "state": "Delhi",
                    "type": "central_university",
                    "student_levels": ["undergraduate", "graduate"],
                    "categories": ["liberal_arts", "social_sciences", "languages"],
                    "ranking": 10,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "Indian Institute of Management Delhi",
                    "short_name": "IIM Delhi",
                    "location": "New Delhi",
                    "city": "Delhi",
                    "state": "Delhi", 
                    "type": "management_institute",
                    "student_levels": ["graduate"],
                    "categories": ["management", "business"],
                    "ranking": 4,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                
                # === KARNATAKA ===
                {
                    "name": "Indian Institute of Science",
                    "short_name": "IISc Bangalore",
                    "location": "Bangalore, Karnataka",
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "type": "science_institute",
                    "student_levels": ["undergraduate", "graduate"],
                    "categories": ["science", "engineering", "research"],
                    "ranking": 1,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "Indian Institute of Management Bangalore",
                    "short_name": "IIM Bangalore",
                    "location": "Bangalore, Karnataka",
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "type": "management_institute",
                    "student_levels": ["graduate"],
                    "categories": ["management", "business"],
                    "ranking": 2,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "Bangalore University",
                    "short_name": "Bangalore University",
                    "location": "Bangalore, Karnataka",
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "type": "state_university",
                    "student_levels": ["high_school", "undergraduate", "graduate"],
                    "categories": ["general", "science", "commerce", "arts"],
                    "ranking": 20,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "National Institute of Technology Karnataka",
                    "short_name": "NIT Surathkal",
                    "location": "Surathkal, Karnataka",
                    "city": "Mangalore",
                    "state": "Karnataka",
                    "type": "engineering_institute", 
                    "student_levels": ["undergraduate", "graduate"],
                    "categories": ["engineering", "technology"],
                    "ranking": 13,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                
                # === TAMIL NADU ===
                {
                    "name": "Indian Institute of Technology Madras",
                    "short_name": "IIT Madras",
                    "location": "Chennai, Tamil Nadu",
                    "city": "Chennai",
                    "state": "Tamil Nadu",
                    "type": "engineering_institute",
                    "student_levels": ["undergraduate", "graduate"],
                    "categories": ["engineering", "technology", "research"],
                    "ranking": 3,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "Anna University",
                    "short_name": "Anna University",
                    "location": "Chennai, Tamil Nadu",
                    "city": "Chennai",
                    "state": "Tamil Nadu",
                    "type": "technical_university",
                    "student_levels": ["high_school", "undergraduate", "graduate"],
                    "categories": ["engineering", "technology", "applied_sciences"],
                    "ranking": 14,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "University of Madras",
                    "short_name": "Madras University",
                    "location": "Chennai, Tamil Nadu",
                    "city": "Chennai",
                    "state": "Tamil Nadu",
                    "type": "state_university",
                    "student_levels": ["high_school", "undergraduate", "graduate"],
                    "categories": ["general", "science", "arts", "commerce"],
                    "ranking": 22,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                
                # === WEST BENGAL ===
                {
                    "name": "Indian Institute of Technology Kharagpur",
                    "short_name": "IIT Kharagpur",
                    "location": "Kharagpur, West Bengal", 
                    "city": "Kharagpur",
                    "state": "West Bengal",
                    "type": "engineering_institute",
                    "student_levels": ["undergraduate", "graduate"],
                    "categories": ["engineering", "technology", "research"],
                    "ranking": 5,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "University of Calcutta", 
                    "short_name": "Calcutta University",
                    "location": "Kolkata, West Bengal",
                    "city": "Kolkata",
                    "state": "West Bengal",
                    "type": "state_university",
                    "student_levels": ["high_school", "undergraduate", "graduate"],
                    "categories": ["general", "science", "arts", "commerce", "law"],
                    "ranking": 16,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "Jadavpur University",
                    "short_name": "Jadavpur University",
                    "location": "Kolkata, West Bengal",
                    "city": "Kolkata",
                    "state": "West Bengal",
                    "type": "state_university",
                    "student_levels": ["undergraduate", "graduate"],
                    "categories": ["engineering", "science", "arts"],
                    "ranking": 11,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                
                # === RAJASTHAN ===
                {
                    "name": "Indian Institute of Technology Jodhpur",
                    "short_name": "IIT Jodhpur", 
                    "location": "Jodhpur, Rajasthan",
                    "city": "Jodhpur",
                    "state": "Rajasthan",
                    "type": "engineering_institute",
                    "student_levels": ["undergraduate", "graduate"],
                    "categories": ["engineering", "technology"],
                    "ranking": 17,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "University of Rajasthan",
                    "short_name": "Rajasthan University",
                    "location": "Jaipur, Rajasthan",
                    "city": "Jaipur",
                    "state": "Rajasthan",
                    "type": "state_university",
                    "student_levels": ["high_school", "undergraduate", "graduate"],
                    "categories": ["general", "science", "arts", "commerce"],
                    "ranking": 25,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                
                # === UTTAR PRADESH ===
                {
                    "name": "Indian Institute of Technology Kanpur",
                    "short_name": "IIT Kanpur",
                    "location": "Kanpur, Uttar Pradesh",
                    "city": "Kanpur", 
                    "state": "Uttar Pradesh",
                    "type": "engineering_institute",
                    "student_levels": ["undergraduate", "graduate"],
                    "categories": ["engineering", "technology", "research"],
                    "ranking": 6,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "Banaras Hindu University",
                    "short_name": "BHU",
                    "location": "Varanasi, Uttar Pradesh",
                    "city": "Varanasi",
                    "state": "Uttar Pradesh", 
                    "type": "central_university",
                    "student_levels": ["high_school", "undergraduate", "graduate"],
                    "categories": ["general", "engineering", "medicine", "arts"],
                    "ranking": 19,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "Lucknow University",
                    "short_name": "Lucknow University",
                    "location": "Lucknow, Uttar Pradesh",
                    "city": "Lucknow",
                    "state": "Uttar Pradesh",
                    "type": "state_university",
                    "student_levels": ["high_school", "undergraduate", "graduate"],
                    "categories": ["general", "science", "arts", "commerce", "law"],
                    "ranking": 24,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                
                # === ANDHRA PRADESH & TELANGANA ===
                {
                    "name": "Indian Institute of Technology Hyderabad",
                    "short_name": "IIT Hyderabad",
                    "location": "Hyderabad, Telangana",
                    "city": "Hyderabad",
                    "state": "Telangana",
                    "type": "engineering_institute",
                    "student_levels": ["undergraduate", "graduate"], 
                    "categories": ["engineering", "technology"],
                    "ranking": 16,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "Osmania University",
                    "short_name": "Osmania University",
                    "location": "Hyderabad, Telangana",
                    "city": "Hyderabad",
                    "state": "Telangana",
                    "type": "state_university",
                    "student_levels": ["high_school", "undergraduate", "graduate"],
                    "categories": ["general", "science", "engineering", "medicine"],
                    "ranking": 21,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                
                # === GUJARAT ===
                {
                    "name": "Indian Institute of Technology Gandhinagar",
                    "short_name": "IIT Gandhinagar",
                    "location": "Gandhinagar, Gujarat",
                    "city": "Gandhinagar",
                    "state": "Gujarat",
                    "type": "engineering_institute",
                    "student_levels": ["undergraduate", "graduate"],
                    "categories": ["engineering", "technology"],
                    "ranking": 18,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "Gujarat University",
                    "short_name": "Gujarat University", 
                    "location": "Ahmedabad, Gujarat",
                    "city": "Ahmedabad",
                    "state": "Gujarat",
                    "type": "state_university",
                    "student_levels": ["high_school", "undergraduate", "graduate"],
                    "categories": ["general", "science", "commerce", "arts"],
                    "ranking": 23,
                    "is_verified": True,
                    "student_count": 0,
                    "created_at": datetime.now(timezone.utc)
                }
            ]
            
            await db.universities.insert_many(comprehensive_universities)
            logger.info(f"Initialized {len(comprehensive_universities)} universities in database")
        else:
            logger.info(f"Universities already exist ({existing_universities} found), skipping initialization")
        
        logger.info("Seed data initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize seed data: {str(e)}")

async def cleanup_test_data():
    """Remove test/dummy data from production database"""
    try:
        # Remove test users (emails with 'test', 'dummy', 'example' etc.)
        test_patterns = [
            {"email": {"$regex": "test", "$options": "i"}},
            {"email": {"$regex": "dummy", "$options": "i"}},
            {"email": {"$regex": "example", "$options": "i"}},
            {"email": {"$regex": "demo", "$options": "i"}},
            {"full_name": {"$regex": "test", "$options": "i"}},
            {"full_name": {"$regex": "dummy", "$options": "i"}},
            {"full_name": {"$regex": "demo", "$options": "i"}}
        ]
        
        # Get test user IDs before deletion
        test_users = await db.users.find({"$or": test_patterns}).to_list(None)
        test_user_ids = [user["id"] for user in test_users]
        
        if test_user_ids:
            # Delete test users
            result = await db.users.delete_many({"$or": test_patterns})
            logger.info(f"Removed {result.deleted_count} test users")
            
            # Delete related data for test users
            await db.transactions.delete_many({"user_id": {"$in": test_user_ids}})
            await db.user_hustles.delete_many({"created_by": {"$in": test_user_ids}})
            await db.hustle_applications.delete_many({"applicant_id": {"$in": test_user_ids}})
            await db.budgets.delete_many({"user_id": {"$in": test_user_ids}})
            
            logger.info("Cleaned up related test data")
        
        # Remove transactions with unrealistic amounts (likely test data)
        await db.transactions.delete_many({"amount": {"$gt": 10000000}})  # > 1 crore
        await db.transactions.delete_many({"amount": {"$lt": 1}})  # < 1 rupee
        
        # Remove hustles with unrealistic pay rates
        await db.user_hustles.delete_many({"pay_rate": {"$gt": 100000}})  # > 1 lakh per hour
        await db.user_hustles.delete_many({"pay_rate": {"$lt": 10}})  # < 10 rupees per hour
        
        logger.info("Database cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to cleanup test data: {str(e)}")

async def get_user_by_email(email: str):
    """Get user by email"""
    return await db.users.find_one({"email": email})

async def get_user_by_id(user_id: str):
    """Get user by ID"""
    return await db.users.find_one({"id": user_id})

async def create_user(user_data: dict):
    """Create new user"""
    user_data["created_at"] = datetime.now(timezone.utc)
    return await db.users.insert_one(user_data)

async def update_user(user_id: str, update_data: dict):
    """Update user data"""
    return await db.users.update_one({"id": user_id}, {"$set": update_data})

async def create_transaction(transaction_data: dict):
    """Create new transaction"""
    transaction_data["date"] = datetime.now(timezone.utc)
    return await db.transactions.insert_one(transaction_data)

async def get_user_transactions(user_id: str, limit: int = 50, skip: int = 0):
    """Get user transactions"""
    cursor = db.transactions.find({"user_id": user_id}).sort("date", -1).skip(skip).limit(limit)
    return await cursor.to_list(limit)

async def get_transaction_summary(user_id: str, start_date: datetime = None):
    """Get transaction summary for user"""
    match_filter = {"user_id": user_id}
    if start_date:
        match_filter["date"] = {"$gte": start_date}
    
    pipeline = [
        {"$match": match_filter},
        {"$group": {
            "_id": "$type",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }}
    ]
    
    return await db.transactions.aggregate(pipeline).to_list(None)

async def create_hustle(hustle_data: dict):
    """Create new hustle"""
    hustle_data["created_at"] = datetime.now(timezone.utc)
    return await db.user_hustles.insert_one(hustle_data)

async def get_active_hustles(limit: int = 100):
    """Get active hustles"""
    cursor = db.user_hustles.find({"status": "active"}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(limit)

async def create_hustle_application(application_data: dict):
    """Create hustle application"""
    application_data["applied_at"] = datetime.now(timezone.utc)
    return await db.hustle_applications.insert_one(application_data)

async def get_user_applications(user_id: str):
    """Get user's hustle applications"""
    cursor = db.hustle_applications.find({"applicant_id": user_id}).sort("applied_at", -1)
    return await cursor.to_list(None)

async def create_budget(budget_data: dict):
    """Create budget"""
    budget_data["created_at"] = datetime.now(timezone.utc)
    return await db.budgets.insert_one(budget_data)

async def get_user_budgets(user_id: str):
    """Get user budgets"""
    cursor = db.budgets.find({"user_id": user_id})
    return await cursor.to_list(None)

async def store_verification_code(email: str, code: str, expires_at: datetime):
    """Store email verification code"""
    await db.email_verifications.update_one(
        {"email": email},
        {
            "$set": {
                "email": email,
                "code": code,
                "expires_at": expires_at,
                "created_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )

async def get_verification_code(email: str):
    """Get verification code for email"""
    return await db.email_verifications.find_one({"email": email})

async def delete_verification_code(email: str):
    """Delete verification code"""
    await db.email_verifications.delete_one({"email": email})

async def store_password_reset_code(email: str, code: str, expires_at: datetime):
    """Store password reset code"""
    await db.password_resets.update_one(
        {"email": email},
        {
            "$set": {
                "email": email,
                "code": code,
                "expires_at": expires_at,
                "created_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )

async def get_password_reset_code(email: str):
    """Get password reset code for email"""
    return await db.password_resets.find_one({"email": email})

async def delete_password_reset_code(email: str):
    """Delete password reset code"""
    await db.password_resets.delete_one({"email": email})

# Financial Goals Database Functions
async def create_financial_goal(goal_data: dict):
    """Create financial goal"""
    goal_data["created_at"] = datetime.now(timezone.utc)
    goal_data["is_active"] = True  # Ensure goals are marked as active
    return await db.financial_goals.insert_one(goal_data)

async def get_user_financial_goals(user_id: str):
    """Get user's financial goals"""
    cursor = db.financial_goals.find({"user_id": user_id, "is_active": True}).sort("created_at", -1)
    return await cursor.to_list(None)

async def update_financial_goal(goal_id: str, user_id: str, update_data: dict):
    """Update financial goal"""
    return await db.financial_goals.update_one(
        {"id": goal_id, "user_id": user_id},
        {"$set": update_data}
    )

async def delete_financial_goal(goal_id: str, user_id: str):
    """Delete financial goal"""
    return await db.financial_goals.update_one(
        {"id": goal_id, "user_id": user_id},
        {"$set": {"is_active": False}}
    )

# Category Suggestions Database Functions
async def get_category_suggestions(category: str):
    """Get suggestions for a category"""
    cursor = db.category_suggestions.find(
        {"category": category, "is_active": True}
    ).sort("priority", -1)
    return await cursor.to_list(None)

async def create_category_suggestion(suggestion_data: dict):
    """Create category suggestion"""
    suggestion_data["created_at"] = datetime.now(timezone.utc)
    return await db.category_suggestions.insert_one(suggestion_data)

async def get_emergency_types():
    """Get all emergency types"""
    cursor = db.emergency_types.find({}).sort("urgency_level", -1)
    return await cursor.to_list(None)

async def get_hospitals_by_location(city: str, state: str = None, limit: int = 10):
    """Get hospitals by location"""
    match_filter = {"city": {"$regex": city, "$options": "i"}}
    if state:
        match_filter["state"] = {"$regex": state, "$options": "i"}
    
    cursor = db.hospitals.find(match_filter).sort("rating", -1).limit(limit)
    return await cursor.to_list(limit)

async def get_nearby_hospitals(latitude: float, longitude: float, radius_km: float = 10, limit: int = 10):
    """Get hospitals near coordinates using $geoNear"""
    # Note: This requires a 2dsphere index on location field
    # For now, we'll use a simple distance calculation
    cursor = db.hospitals.find({
        "latitude": {"$gte": latitude - 0.1, "$lte": latitude + 0.1},
        "longitude": {"$gte": longitude - 0.1, "$lte": longitude + 0.1}
    }).sort("rating", -1).limit(limit)
    return await cursor.to_list(limit)

async def create_click_analytics(analytics_data: dict):
    """Record click analytics"""
    analytics_data["clicked_at"] = datetime.now(timezone.utc)
    return await db.click_analytics.insert_one(analytics_data)

async def get_popular_suggestions(category: str, days: int = 30):
    """Get popular suggestions based on click analytics"""
    from datetime import timedelta
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    pipeline = [
        {
            "$match": {
                "category": category,
                "clicked_at": {"$gte": start_date}
            }
        },
        {
            "$group": {
                "_id": "$suggestion_name",
                "click_count": {"$sum": 1},
                "suggestion_url": {"$first": "$suggestion_url"}
            }
        },
        {
            "$sort": {"click_count": -1}
        },
        {
            "$limit": 10
        }
    ]
    
    return await db.click_analytics.aggregate(pipeline).to_list(10)

# Advanced Income Tracking System Database Functions

async def create_auto_import_source(source_data: dict):
    """Create new auto-import source"""
    source_data["created_at"] = datetime.now(timezone.utc)
    return await db.auto_import_sources.insert_one(source_data)

async def get_user_auto_import_sources(user_id: str):
    """Get user's auto-import sources"""
    cursor = db.auto_import_sources.find({"user_id": user_id}).sort("created_at", -1)
    sources = await cursor.to_list(100)
    return clean_mongo_doc(sources)

async def update_auto_import_source(source_id: str, update_data: dict):
    """Update auto-import source"""
    return await db.auto_import_sources.update_one({"id": source_id}, {"$set": update_data})

async def create_parsed_transaction(parsed_data: dict):
    """Create new parsed transaction"""
    parsed_data["created_at"] = datetime.now(timezone.utc)
    return await db.parsed_transactions.insert_one(parsed_data)

async def get_parsed_transaction(parsed_id: str):
    """Get parsed transaction by ID"""
    doc = await db.parsed_transactions.find_one({"id": parsed_id})
    return clean_mongo_doc(doc)

async def create_transaction_suggestion(suggestion_data: dict):
    """Create new transaction suggestion"""
    suggestion_data["created_at"] = datetime.now(timezone.utc)
    return await db.transaction_suggestions.insert_one(suggestion_data)

async def get_user_pending_suggestions(user_id: str, limit: int = 20):
    """Get user's pending transaction suggestions"""
    cursor = db.transaction_suggestions.find({
        "user_id": user_id, 
        "status": "pending"
    }).sort("created_at", -1).limit(limit)
    suggestions = await cursor.to_list(limit)
    return clean_mongo_doc(suggestions)

async def update_suggestion_status(suggestion_id: str, status: str, approved_at: datetime = None):
    """Update suggestion status"""
    update_data = {"status": status}
    if approved_at:
        update_data["approved_at"] = approved_at
    return await db.transaction_suggestions.update_one({"id": suggestion_id}, {"$set": update_data})

async def get_suggestion_by_id(suggestion_id: str):
    """Get suggestion by ID"""
    doc = await db.transaction_suggestions.find_one({"id": suggestion_id})
    return clean_mongo_doc(doc)

async def create_learning_feedback(feedback_data: dict):
    """Create learning feedback entry"""
    feedback_data["created_at"] = datetime.now(timezone.utc)
    return await db.learning_feedback.insert_one(feedback_data)

async def get_user_learning_feedback(user_id: str, limit: int = 100):
    """Get user's learning feedback for improving AI suggestions"""
    cursor = db.learning_feedback.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
    feedback = await cursor.to_list(limit)
    return clean_mongo_doc(feedback)

async def check_duplicate_transaction(user_id: str, amount: float, date_range_hours: int = 24):
    """Check for potential duplicate transactions within specified time range"""
    # Check for transactions with same amount within the time range
    start_time = datetime.now(timezone.utc) - timedelta(hours=date_range_hours)
    
    existing_transactions = await db.transactions.find({
        "user_id": user_id,
        "amount": amount,
        "date": {"$gte": start_time}
    }).to_list(10)
    
    return existing_transactions

async def get_user_transaction_patterns(user_id: str, days: int = 30):
    """Get user's transaction patterns for better categorization"""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    pipeline = [
        {"$match": {"user_id": user_id, "date": {"$gte": start_date}}},
        {"$group": {
            "_id": {
                "category": "$category",
                "type": "$type",
                "source": "$source"
            },
            "count": {"$sum": 1},
            "avg_amount": {"$avg": "$amount"},
            "total_amount": {"$sum": "$amount"}
        }},
        {"$sort": {"count": -1}}
    ]
    
    return await db.transactions.aggregate(pipeline).to_list(50)

"""
Fallback Hospital Database - Comprehensive hospital data for major Indian cities
This serves as a reliable backup when OpenStreetMap API is rate-limited or unavailable.
Contains real hospital data with specializations, contact info, and emergency capabilities.
"""

import logging
from typing import List, Dict, Optional
import math

logger = logging.getLogger(__name__)

class FallbackHospitalDatabase:
    def __init__(self):
        """Initialize comprehensive hospital database for major Indian cities"""
        self.hospitals = self._load_hospital_data()
        self.specialty_mappings = self._load_specialty_mappings()
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        R = 6371  # Radius of Earth in km
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = (math.sin(dLat/2) * math.sin(dLat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dLon/2) * math.sin(dLon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    def _load_specialty_mappings(self) -> Dict:
        """Load emergency type to specialty mappings"""
        return {
            # Accident Types
            "road accident": {
                "primary": ["Trauma Surgery", "Emergency Medicine", "Orthopedics"],
                "secondary": ["Neurosurgery", "Plastic Surgery", "ICU"],
                "description": "Trauma and accident care"
            },
            "workplace accident": {
                "primary": ["Occupational Medicine", "Trauma Surgery", "Emergency Medicine"],
                "secondary": ["Orthopedics", "Rehabilitation"],
                "description": "Workplace injury specialists"
            },
            "sports injury": {
                "primary": ["Sports Medicine", "Orthopedics", "Emergency Medicine"],
                "secondary": ["Physiotherapy", "Rehabilitation"],
                "description": "Sports injury specialists"
            },
            "fall injury": {
                "primary": ["Orthopedics", "Trauma Surgery", "Emergency Medicine"],
                "secondary": ["Neurology", "Geriatrics"],
                "description": "Fall injury care"
            },
            
            # Medical Emergencies
            "cardiac": {
                "primary": ["Cardiology", "Emergency Medicine", "Cardiac Surgery"],
                "secondary": ["ICU", "Interventional Cardiology"],
                "description": "Heart emergency care"
            },
            "pediatric": {
                "primary": ["Pediatrics", "Emergency Medicine", "NICU"],
                "secondary": ["Pediatric Surgery", "Child Psychology"],
                "description": "Children's emergency care"
            },
            "orthopedic": {
                "primary": ["Orthopedics", "Emergency Medicine", "Orthopedic Surgery"],
                "secondary": ["Sports Medicine", "Physiotherapy"],
                "description": "Bone and joint care"
            },
            "neurological": {
                "primary": ["Neurology", "Emergency Medicine", "Neurosurgery"],
                "secondary": ["Stroke Care", "ICU"],
                "description": "Brain and nerve care"
            },
            "respiratory": {
                "primary": ["Pulmonology", "Emergency Medicine", "Critical Care"],
                "secondary": ["ICU", "Anesthesiology"],
                "description": "Lung and breathing care"
            },
            "gastroenterology": {
                "primary": ["Gastroenterology", "Emergency Medicine", "GI Surgery"],
                "secondary": ["Hepatology", "Endoscopy"],
                "description": "Digestive system care"
            },
            "psychiatric": {
                "primary": ["Psychiatry", "Emergency Medicine", "Mental Health"],
                "secondary": ["Psychology", "Crisis Intervention"],
                "description": "Mental health crisis care"
            },
            "obstetric": {
                "primary": ["Obstetrics", "Emergency Medicine", "Gynecology"],
                "secondary": ["NICU", "Anesthesiology"],
                "description": "Pregnancy emergency care"
            },
            "general": {
                "primary": ["Emergency Medicine", "General Medicine", "Internal Medicine"],
                "secondary": ["ICU", "General Surgery"],
                "description": "General emergency care"
            },
            "trauma": {
                "primary": ["Trauma Surgery", "Emergency Medicine", "Critical Care"],
                "secondary": ["Orthopedics", "Neurosurgery"],
                "description": "Trauma care"
            }
        }
    
    def _load_hospital_data(self) -> List[Dict]:
        """Load comprehensive hospital database for major Indian cities"""
        return [
            # Mumbai Hospitals
            {
                "name": "Kokilaben Dhirubhai Ambani Hospital",
                "city": "Mumbai", "state": "Maharashtra",
                "latitude": 19.1334, "longitude": 72.8267,
                "phone": "+91-22-42696969", "emergency_phone": "108",
                "rating": 4.5, "is_24x7": True, "is_emergency": True,
                "address": "Rao Saheb Achutrao Patwardhan Marg, Four Bungalows, Andheri West, Mumbai, Maharashtra 400053",
                "specialties": ["Cardiology", "Neurology", "Oncology", "Emergency Medicine", "ICU", "Trauma Surgery", "Orthopedics"],
                "features": ["24/7 Emergency", "ICU", "Trauma Center", "Ambulance Service", "Pharmacy", "Blood Bank"],
                "hospital_type": "Multi-specialty"
            },
            {
                "name": "Lilavati Hospital and Research Centre",
                "city": "Mumbai", "state": "Maharashtra", 
                "latitude": 19.0545, "longitude": 72.8302,
                "phone": "+91-22-26567777", "emergency_phone": "108",
                "rating": 4.3, "is_24x7": True, "is_emergency": True,
                "address": "A-791, Bandra Reclamation, Bandra West, Mumbai, Maharashtra 400050",
                "specialties": ["Emergency Medicine", "Trauma Surgery", "Cardiology", "Neurosurgery", "Orthopedics", "ICU"],
                "features": ["24/7 Emergency", "Trauma Center", "ICU", "Ambulance Service", "Blood Bank", "Pharmacy"],
                "hospital_type": "Multi-specialty"
            },
            {
                "name": "Tata Memorial Hospital",
                "city": "Mumbai", "state": "Maharashtra",
                "latitude": 19.0107, "longitude": 72.8595,
                "phone": "+91-22-24177000", "emergency_phone": "108",
                "rating": 4.2, "is_24x7": True, "is_emergency": True,
                "address": "Dr. E Borges Road, Parel, Mumbai, Maharashtra 400012",
                "specialties": ["Oncology", "Emergency Medicine", "Surgery", "Radiation Therapy", "ICU"],
                "features": ["24/7 Emergency", "Cancer Center", "ICU", "Blood Bank", "Pharmacy"],
                "hospital_type": "Specialty"
            },
            
            # Delhi Hospitals  
            {
                "name": "All India Institute of Medical Sciences (AIIMS)",
                "city": "New Delhi", "state": "Delhi",
                "latitude": 28.5672, "longitude": 77.2100,
                "phone": "+91-11-26588500", "emergency_phone": "108", 
                "rating": 4.6, "is_24x7": True, "is_emergency": True,
                "address": "Sri Aurobindo Marg, Ansari Nagar, New Delhi, Delhi 110029",
                "specialties": ["Emergency Medicine", "Cardiology", "Neurology", "Trauma Surgery", "Orthopedics", "ICU", "All Specialties"],
                "features": ["24/7 Emergency", "Trauma Center", "ICU", "Ambulance Service", "Blood Bank", "All Facilities"],
                "hospital_type": "Government Multi-specialty"
            },
            {
                "name": "Fortis Hospital Shalimar Bagh",
                "city": "New Delhi", "state": "Delhi",
                "latitude": 28.7196, "longitude": 77.1569,
                "phone": "+91-11-47135000", "emergency_phone": "108",
                "rating": 4.2, "is_24x7": True, "is_emergency": True,
                "address": "A-Block, Shalimar Bagh, New Delhi, Delhi 110088",
                "specialties": ["Cardiology", "Orthopedics", "Emergency Medicine", "Neurology", "ICU"],
                "features": ["24/7 Emergency", "ICU", "Cardiac Center", "Ambulance Service", "Pharmacy"],
                "hospital_type": "Multi-specialty"
            },
            {
                "name": "Max Super Speciality Hospital Saket",
                "city": "New Delhi", "state": "Delhi",
                "latitude": 28.5238, "longitude": 77.2154,
                "phone": "+91-11-26515050", "emergency_phone": "108",
                "rating": 4.4, "is_24x7": True, "is_emergency": True,
                "address": "1 Press Enclave Road, Saket, New Delhi, Delhi 110017",
                "specialties": ["Cardiology", "Neurology", "Emergency Medicine", "Orthopedics", "Oncology", "ICU"],
                "features": ["24/7 Emergency", "Heart Center", "ICU", "Trauma Center", "Blood Bank"],
                "hospital_type": "Multi-specialty"
            },
            
            # Bangalore Hospitals
            {
                "name": "Manipal Hospital Whitefield",
                "city": "Bangalore", "state": "Karnataka", 
                "latitude": 12.9699, "longitude": 77.7499,
                "phone": "+91-80-66712000", "emergency_phone": "108",
                "rating": 4.4, "is_24x7": True, "is_emergency": True,
                "address": "#143, 212-2015, HRBR Layout, Kalyan Nagar, Whitefield, Bangalore, Karnataka 560066",
                "specialties": ["Emergency Medicine", "Critical Care", "Cardiology", "Neurology", "Orthopedics", "ICU"],
                "features": ["24/7 Emergency", "ICU", "Critical Care", "Ambulance Service", "Pharmacy", "Blood Bank"],
                "hospital_type": "Multi-specialty"
            },
            {
                "name": "Apollo Hospital Bannerghatta",
                "city": "Bangalore", "state": "Karnataka",
                "latitude": 12.8008, "longitude": 77.6495,
                "phone": "+91-80-26304050", "emergency_phone": "108",
                "rating": 4.3, "is_24x7": True, "is_emergency": True,
                "address": "154/11, Opposite IIM-B, Bannerghatta Road, Bangalore, Karnataka 560076",
                "specialties": ["Emergency Medicine", "Cardiology", "Neurology", "Orthopedics", "Oncology", "ICU", "Multi-specialty"],
                "features": ["24/7 Emergency", "Heart Center", "Cancer Center", "ICU", "Blood Bank", "Pharmacy"],
                "hospital_type": "Multi-specialty"
            },
            {
                "name": "Fortis Hospital Bannerghatta Road",
                "city": "Bangalore", "state": "Karnataka",
                "latitude": 12.8542, "longitude": 77.6127,
                "phone": "+91-80-66214444", "emergency_phone": "108", 
                "rating": 4.2, "is_24x7": True, "is_emergency": True,
                "address": "154/9, Bannerghatta Road, Opposite IIM-B, Bangalore, Karnataka 560076",
                "specialties": ["Emergency Medicine", "Cardiology", "Orthopedics", "Neurology", "ICU"],
                "features": ["24/7 Emergency", "Cardiac Care", "ICU", "Ambulance Service", "Pharmacy"],
                "hospital_type": "Multi-specialty"
            },
            
            # Chennai Hospitals
            {
                "name": "Apollo Hospital Greams Road",
                "city": "Chennai", "state": "Tamil Nadu",
                "latitude": 13.0661, "longitude": 80.2589,
                "phone": "+91-44-28293333", "emergency_phone": "108",
                "rating": 4.5, "is_24x7": True, "is_emergency": True,
                "address": "21, Greams Lane, Off Greams Road, Chennai, Tamil Nadu 600006",
                "specialties": ["Cardiology", "Transplant Surgery", "Emergency Medicine", "Neurology", "Orthopedics", "ICU"],
                "features": ["24/7 Emergency", "Transplant Center", "Heart Center", "ICU", "Blood Bank"],
                "hospital_type": "Multi-specialty"
            },
            {
                "name": "Fortis Malar Hospital",
                "city": "Chennai", "state": "Tamil Nadu",
                "latitude": 13.0339, "longitude": 80.2403,
                "phone": "+91-44-42892222", "emergency_phone": "108",
                "rating": 4.2, "is_24x7": True, "is_emergency": True,
                "address": "52, 1st Main Road, Gandhi Nagar, Adyar, Chennai, Tamil Nadu 600020",
                "specialties": ["Emergency Medicine", "Cardiology", "Neurology", "Orthopedics", "ICU"],
                "features": ["24/7 Emergency", "ICU", "Heart Center", "Ambulance Service"],
                "hospital_type": "Multi-specialty"
            },
            
            # Kolkata Hospitals
            {
                "name": "AMRI Hospital Salt Lake",
                "city": "Kolkata", "state": "West Bengal",
                "latitude": 22.5726, "longitude": 88.4139,
                "phone": "+91-33-66063800", "emergency_phone": "108",
                "rating": 4.2, "is_24x7": True, "is_emergency": True,
                "address": "JC - 16 & 17, Sector III, Salt Lake City, Kolkata, West Bengal 700098",
                "specialties": ["Emergency Medicine", "Cardiology", "Neurology", "Orthopedics", "ICU"],
                "features": ["24/7 Emergency", "Heart Center", "ICU", "Ambulance Service", "Blood Bank"],
                "hospital_type": "Multi-specialty"
            },
            {
                "name": "Apollo Gleneagles Hospital",
                "city": "Kolkata", "state": "West Bengal", 
                "latitude": 22.5204, "longitude": 88.3431,
                "phone": "+91-33-23203040", "emergency_phone": "108",
                "rating": 4.3, "is_24x7": True, "is_emergency": True,
                "address": "58, Canal Circular Road, Kadapara, Phool Bagan, Kolkata, West Bengal 700054",
                "specialties": ["Emergency Medicine", "Cardiology", "Neurology", "Oncology", "Orthopedics", "ICU"],
                "features": ["24/7 Emergency", "Cancer Center", "Heart Center", "ICU", "Blood Bank"],
                "hospital_type": "Multi-specialty"
            },
            
            # Hyderabad Hospitals
            {
                "name": "Apollo Hospital Jubilee Hills",
                "city": "Hyderabad", "state": "Telangana",
                "latitude": 17.4274, "longitude": 78.4067,
                "phone": "+91-40-23607777", "emergency_phone": "108",
                "rating": 4.4, "is_24x7": True, "is_emergency": True,
                "address": "Road No. 72, Opp. Bharatiya Vidya Bhavan, Film Nagar, Jubilee Hills, Hyderabad, Telangana 500033",
                "specialties": ["Emergency Medicine", "Cardiology", "Neurology", "Orthopedics", "Oncology", "ICU"],
                "features": ["24/7 Emergency", "Heart Center", "Cancer Center", "ICU", "Ambulance Service"],
                "hospital_type": "Multi-specialty"
            },
            {
                "name": "Yashoda Hospital Secunderabad",
                "city": "Hyderabad", "state": "Telangana",
                "latitude": 17.4513, "longitude": 78.5014,
                "phone": "+91-40-44776677", "emergency_phone": "108",
                "rating": 4.2, "is_24x7": True, "is_emergency": True,
                "address": "Minister Road, Secunderabad, Hyderabad, Telangana 500003",
                "specialties": ["Emergency Medicine", "Cardiology", "Neurology", "Orthopedics", "ICU"],
                "features": ["24/7 Emergency", "ICU", "Heart Center", "Blood Bank", "Pharmacy"],
                "hospital_type": "Multi-specialty"
            },
            
            # Pune Hospitals
            {
                "name": "Ruby Hall Clinic",
                "city": "Pune", "state": "Maharashtra",
                "latitude": 18.5204, "longitude": 73.8567,
                "phone": "+91-20-26122888", "emergency_phone": "108",
                "rating": 4.3, "is_24x7": True, "is_emergency": True,
                "address": "40, Sassoon Road, Near Pune Railway Station, Pune, Maharashtra 411001",
                "specialties": ["Emergency Medicine", "Cardiology", "Neurology", "Orthopedics", "ICU"],
                "features": ["24/7 Emergency", "Heart Center", "ICU", "Ambulance Service", "Blood Bank"],
                "hospital_type": "Multi-specialty"
            },
            {
                "name": "Sahyadri Hospital",
                "city": "Pune", "state": "Maharashtra",
                "latitude": 18.5074, "longitude": 73.8077,
                "phone": "+91-20-67206720", "emergency_phone": "108",
                "rating": 4.2, "is_24x7": True, "is_emergency": True,
                "address": "30-C, Erandawane, Karve Road, Pune, Maharashtra 411004",
                "specialties": ["Emergency Medicine", "Cardiology", "Neurology", "Orthopedics", "ICU"],
                "features": ["24/7 Emergency", "ICU", "Heart Center", "Trauma Center", "Blood Bank"],
                "hospital_type": "Multi-specialty"
            },
            
            # Ahmedabad Hospitals
            {
                "name": "Apollo Hospital Ahmedabad",
                "city": "Ahmedabad", "state": "Gujarat",
                "latitude": 23.0225, "longitude": 72.5714,
                "phone": "+91-79-66701800", "emergency_phone": "108",
                "rating": 4.3, "is_24x7": True, "is_emergency": True,
                "address": "Plot No 1A, GIDC Estate, Bhat, Gandhinagar, Gujarat 382428",
                "specialties": ["Emergency Medicine", "Cardiology", "Neurology", "Orthopedics", "Oncology", "ICU"],
                "features": ["24/7 Emergency", "Heart Center", "Cancer Center", "ICU", "Blood Bank"],
                "hospital_type": "Multi-specialty"
            },
            
            # Jaipur Hospitals
            {
                "name": "Fortis Escorts Hospital",
                "city": "Jaipur", "state": "Rajasthan",
                "latitude": 26.9124, "longitude": 75.7873,
                "phone": "+91-141-2710700", "emergency_phone": "108",
                "rating": 4.2, "is_24x7": True, "is_emergency": True,
                "address": "Jawahar Lal Nehru Marg, Malviya Nagar, Jaipur, Rajasthan 302017",
                "specialties": ["Emergency Medicine", "Cardiology", "Neurology", "Orthopedics", "ICU"],
                "features": ["24/7 Emergency", "Heart Center", "ICU", "Ambulance Service", "Blood Bank"],
                "hospital_type": "Multi-specialty"
            }
        ]
    
    def get_nearby_hospitals(self, latitude: float, longitude: float, 
                           emergency_type: str, radius_km: float = 25) -> List[Dict]:
        """Get nearby hospitals from fallback database"""
        try:
            # Get specialty info for the emergency type
            specialty_info = self.specialty_mappings.get(emergency_type, 
                                                       self.specialty_mappings["general"])
            
            nearby_hospitals = []
            
            for hospital in self.hospitals:
                # Calculate distance
                distance = self._calculate_distance(
                    latitude, longitude, 
                    hospital["latitude"], hospital["longitude"]
                )
                
                # Filter by radius
                if distance <= radius_km:
                    # Calculate specialty match score
                    match_score = 0
                    hospital_specialties = set(hospital["specialties"])
                    
                    # Primary specialties (higher weight)
                    for spec in specialty_info["primary"]:
                        if spec in hospital_specialties:
                            match_score += 3
                    
                    # Secondary specialties (lower weight)
                    for spec in specialty_info["secondary"]:
                        if spec in hospital_specialties:
                            match_score += 1
                    
                    # Always include emergency hospitals
                    if match_score > 0 or hospital["is_emergency"]:
                        hospital_data = {
                            "name": hospital["name"],
                            "address": hospital["address"],
                            "phone": hospital["phone"],
                            "emergency_phone": hospital["emergency_phone"],
                            "distance": f"{distance:.1f} km",
                            "rating": hospital["rating"],
                            "specialties": hospital["specialties"],
                            "features": hospital["features"],
                            "estimated_time": f"{int(distance * 3)}-{int(distance * 4)} minutes",
                            "hospital_type": hospital["hospital_type"],
                            "specialty_match_score": match_score,
                            "speciality": specialty_info["description"],
                            "matched_specialties": [
                                s for s in specialty_info["primary"] + specialty_info["secondary"]
                                if s in hospital_specialties
                            ]
                        }
                        nearby_hospitals.append(hospital_data)
            
            # Sort by specialty match score first, then by distance
            nearby_hospitals.sort(key=lambda x: (-x["specialty_match_score"], float(x["distance"].split()[0])))
            
            logger.info(f"Fallback database: Found {len(nearby_hospitals)} hospitals within {radius_km}km")
            return nearby_hospitals
            
        except Exception as e:
            logger.error(f"Fallback database error: {str(e)}")
            return []
    
    def get_hospitals_by_city(self, city: str, emergency_type: str = "general") -> List[Dict]:
        """Get all hospitals in a specific city"""
        try:
            city_hospitals = []
            specialty_info = self.specialty_mappings.get(emergency_type, 
                                                       self.specialty_mappings["general"])
            
            for hospital in self.hospitals:
                if hospital["city"].lower() == city.lower():
                    # Calculate specialty match score
                    match_score = 0
                    hospital_specialties = set(hospital["specialties"])
                    
                    for spec in specialty_info["primary"]:
                        if spec in hospital_specialties:
                            match_score += 3
                    
                    for spec in specialty_info["secondary"]:
                        if spec in hospital_specialties:
                            match_score += 1
                    
                    hospital_data = {
                        "name": hospital["name"],
                        "address": hospital["address"],
                        "phone": hospital["phone"],
                        "emergency_phone": hospital["emergency_phone"],
                        "distance": "City hospital",
                        "rating": hospital["rating"],
                        "specialties": hospital["specialties"],
                        "features": hospital["features"],
                        "estimated_time": "15-30 minutes",
                        "hospital_type": hospital["hospital_type"],
                        "specialty_match_score": match_score,
                        "speciality": specialty_info["description"],
                        "matched_specialties": [
                            s for s in specialty_info["primary"] + specialty_info["secondary"]
                            if s in hospital_specialties
                        ]
                    }
                    city_hospitals.append(hospital_data)
            
            # Sort by specialty match score
            city_hospitals.sort(key=lambda x: -x["specialty_match_score"])
            
            logger.info(f"Found {len(city_hospitals)} hospitals in {city}")
            return city_hospitals
            
        except Exception as e:
            logger.error(f"City hospitals lookup error: {str(e)}")
            return []
    
    def get_all_cities(self) -> List[str]:
        """Get list of all cities in the database"""
        cities = list(set(hospital["city"] for hospital in self.hospitals))
        return sorted(cities)
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        cities = self.get_all_cities()
        specialties = set()
        for hospital in self.hospitals:
            specialties.update(hospital["specialties"])
        
        return {
            "total_hospitals": len(self.hospitals),
            "cities_covered": len(cities),
            "cities": cities,
            "total_specialties": len(specialties),
            "emergency_hospitals": len([h for h in self.hospitals if h["is_emergency"]]),
            "24x7_hospitals": len([h for h in self.hospitals if h["is_24x7"]])
        }

# Global instance
fallback_db = FallbackHospitalDatabase()

# Export for use in other modules
__all__ = ['FallbackHospitalDatabase', 'fallback_db']

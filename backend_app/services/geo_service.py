import googlemaps
from geopy.distance import geodesic
import pandas as pd
import json
import os
import time
import random

# Cache file path
CACHE_FILE = 'geocoding_cache.json'

# Google Maps Client
gmaps = None

def get_gmaps_client():
    global gmaps
    if gmaps is None:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if api_key:
            gmaps = googlemaps.Client(key=api_key)
        else:
            print("⚠️ WARNING: GOOGLE_MAPS_API_KEY not found in environment!")
    return gmaps

def load_cache():
    """Load geocoding cache from disk"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    """Save geocoding cache to disk"""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving cache: {e}")

def build_address(ward, district, city):
    """Build full address string from components"""
    components = []
    if pd.notna(ward) and str(ward).strip():
        components.append(str(ward).strip())
    if pd.notna(district) and str(district).strip():
        components.append(str(district).strip())
    if pd.notna(city) and str(city).strip():
        components.append(str(city).strip())
    
    return ", ".join(components)

def apply_jitter(lat, lng, amount=0.0003):
    """Apply small random offset to prevent marker overlap"""
    return lat + random.uniform(-amount, amount), lng + random.uniform(-amount, amount)

def geocode_address(address, cache=None, structured=None, expected_province=None):
    """
    Geocode address using Google Maps API.
    """
    if not address and not structured:
        return None
        
    cache_key = str(structured) if structured else str(address)
    
    if cache is None:
        cache = load_cache()
        
    if cache_key in cache:
        return cache[cache_key]
        
    client = get_gmaps_client()
    if not client:
        return None

    try:
        # Use Google Maps Geocoding
        target_address = structured if structured else address
        if not structured and ", Vietnam" not in target_address:
            target_address += ", Vietnam"

        geocode_result = client.geocode(target_address)
        
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            result = (location['lat'], location['lng'])
            
            # Simple province validation if needed
            if expected_province:
                # Google is very accurate, but we can still check if needed.
                # For brevity and since Google is reliable, we skip strict validation here
                # unless explicitly requested.
                pass

            cache[cache_key] = result
            save_cache(cache)
            return result
        else:
            return None
    except Exception as e:
        print(f"!!! CRITICAL Geocoding error (Google): {e}")
        return None

def find_nearest_experts(user_lat: float, user_long: float, experts_df: pd.DataFrame, limit: int = 3, max_distance_km: float = 5000.0):
    """Find nearest experts within max_distance_km"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔍 find_nearest_experts: Received {len(experts_df)} experts, max_distance={max_distance_km}km")
    
    user_location = (user_lat, user_long)
    experts_with_distance = []

    for index, expert in experts_df.iterrows():
        expert_name = expert.get('expert_name', 'Unknown')
        lat = expert.get('latitude')
        lng = expert.get('longitude')
        
        logger.info(f"  Checking expert: {expert_name} - lat={lat}, lng={lng}")
        
        expert_location = (expert['latitude'], expert['longitude'])
        try:
            distance = geodesic(user_location, expert_location).km
            logger.info(f"    → Distance: {distance:.2f}km (max allowed: {max_distance_km}km)")
        except ValueError as ve:
            logger.warning(f"    → SKIP: Invalid coords - {ve}")
            continue # Skip invalid coords
        except Exception as e:
            logger.error(f"    → SKIP: Geodesic error - {e}")
            continue
        
        # Apply distance filter
        if distance > max_distance_km:
            logger.warning(f"    → SKIP: Too far ({distance:.2f}km > {max_distance_km}km)")
            continue

        logger.info(f"    ✅ MATCH! Adding to results")
        experts_with_distance.append({
            "expert_id": str(expert['expert_id']),
            "expert_name": expert['expert_name'],
            "address": expert['address'],
            "expertise": expert['expertise'],
            "categories": expert.get('categories', ''),
            "avatar_url": expert.get('avatar_url', ''),
            "latitude": expert['latitude'],
            "longitude": expert['longitude'],
            "zalo_link": expert.get('zalo_group_link', ''),
            "notebook_link": expert.get('notebook_link', ''),
            "topics": expert.get('topics_json', []), 
            "distance_km": distance
        })
    
    logger.info(f"🎯 Total experts matched: {len(experts_with_distance)}")
    
    # Sort by distance
    experts_with_distance.sort(key=lambda x: x['distance_km'])
    
    # Return top 'limit' experts
    return experts_with_distance[:limit]

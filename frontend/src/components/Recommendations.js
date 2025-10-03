import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  LinkIcon, 
  StarIcon, 
  ShoppingBagIcon,
  FilmIcon,
  TruckIcon,
  BookOpenIcon,
  PlayIcon,
  ShoppingCartIcon,
  ExclamationTriangleIcon,
  MapPinIcon,
  PhoneIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Recommendations = () => {
  const [allSuggestions, setAllSuggestions] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('Food');
  const [emergencyTypes, setEmergencyTypes] = useState([]);
  const [selectedEmergency, setSelectedEmergency] = useState('');
  const [hospitals, setHospitals] = useState([]);
  const [loadingHospitals, setLoadingHospitals] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [locationError, setLocationError] = useState('');
  const [manualLocation, setManualLocation] = useState('');
  const [showManualLocation, setShowManualLocation] = useState(false);
  const [nearbyPlaces, setNearbyPlaces] = useState([]);
  
  // Enhanced Emergency Fund states
  const [accidentType, setAccidentType] = useState('');
  const [selectedMedicalEmergency, setSelectedMedicalEmergency] = useState('');
  const [customMedicalEmergency, setCustomMedicalEmergency] = useState('');

  // Add error handler for unhandled promise rejections
  useEffect(() => {
    const handleUnhandledRejection = (event) => {
      console.error('❌ Unhandled promise rejection in Recommendations:', event.reason);
      
      // If it's a geolocation error, handle it gracefully
      if (event.reason && (event.reason.code === 1 || event.reason.code === 2 || event.reason.code === 3)) {
        setLocationError('Location access failed. Please enter location manually.');
        setShowManualLocation(true);
        event.preventDefault(); // Prevent the error from being logged to console
      }
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    
    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  const categoryIcons = {
    'Food': ShoppingCartIcon,
    'Transportation': TruckIcon,
    'Books': BookOpenIcon,
    'Entertainment': PlayIcon,
    'Rent': ShoppingBagIcon,
    'Utilities': ExclamationTriangleIcon,
    'Movies': FilmIcon,
    'Shopping': ShoppingBagIcon,
    'Groceries': ShoppingCartIcon,
    'Subscriptions': StarIcon,
    'Emergency Fund': ExclamationTriangleIcon
  };

  const categories = ['Food', 'Transportation', 'Books', 'Entertainment', 'Rent', 'Utilities', 'Movies', 'Shopping', 'Groceries', 'Subscriptions', 'Emergency Fund'];

  // Emergency categories with enhanced accident and medical types
  const emergencyCategories = [
    {
      id: 'fire_emergency',
      name: 'Fire Emergency',
      icon: '🔥',
      description: 'Fire stations, emergency shelters',
      placeTypes: ['fire_station', 'emergency_shelter']
    },
    {
      id: 'crime_security',
      name: 'Crime/Security',
      icon: '🚔',
      description: 'Police stations, security posts',
      placeTypes: ['police', 'security']
    },
    {
      id: 'accident',
      name: 'Accident',
      icon: '🚗',
      description: 'Hospitals, trauma centers',
      placeTypes: ['hospital', 'clinic', 'emergency']
    },
    {
      id: 'mental_health',
      name: 'Mental Health Crisis',
      icon: '🧠',
      description: 'Counseling centers, helplines',
      placeTypes: ['therapist', 'counseling', 'mental_health']
    },
    {
      id: 'natural_disaster',
      name: 'Natural Disaster',
      icon: '🌪️',
      description: 'Relief centers, shelters',
      placeTypes: ['emergency_shelter', 'relief_center', 'evacuation']
    },
    {
      id: 'medical_emergency',
      name: 'Medical Emergency',
      icon: '🏥',
      description: 'Hospitals, pharmacies, clinics',
      placeTypes: ['hospital', 'pharmacy', 'clinic', 'emergency']
    }
  ];

  // Medical emergency types for dropdown
  const medicalEmergencyTypes = [
    { value: 'cardiac', label: 'Cardiac Emergency' },
    { value: 'pediatric', label: 'Pediatric Emergency' },
    { value: 'orthopedic', label: 'Orthopedic Emergency' },
    { value: 'neurological', label: 'Neurological Emergency' },
    { value: 'respiratory', label: 'Respiratory Emergency' },
    { value: 'gastroenterology', label: 'Gastroenterology Emergency' },
    { value: 'psychiatric', label: 'Psychiatric Emergency' },
    { value: 'obstetric', label: 'Obstetric Emergency' },
    { value: 'general', label: 'General Emergency' },
    { value: 'trauma', label: 'Trauma Emergency' }
  ];

  useEffect(() => {
    try {
      fetchAllSuggestions();
      // Initialize emergency categories
      setEmergencyTypes(emergencyCategories);
    } catch (error) {
      console.error('❌ Error initializing Recommendations component:', error);
      setLoading(false);
    }
  }, []);

  // Emergency services functions removed

  // Get user's current location with enhanced error handling
  const getUserLocation = async () => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        const error = new Error('Geolocation is not supported by this browser');
        setLocationError('Geolocation is not supported by this browser. Please enter location manually.');
        setShowManualLocation(true);
        reject(error);
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          try {
            const location = {
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
              accuracy: position.coords.accuracy
            };
            setUserLocation(location);
            setLocationError('');
            console.log('✅ Location obtained successfully:', location);
            resolve(location);
          } catch (err) {
            console.error('❌ Error processing location position:', err);
            setLocationError('Error processing location data. Please try manual input.');
            setShowManualLocation(true);
            reject(err);
          }
        },
        (error) => {
          try {
            let errorMessage = '';
            console.error('❌ Geolocation error:', error);
            
            switch (error.code) {
              case 1: // PERMISSION_DENIED
                errorMessage = 'Location access denied. Please enable location or enter manually.';
                break;
              case 2: // POSITION_UNAVAILABLE
                errorMessage = 'Location information unavailable. Please enter manually.';
                break;
              case 3: // TIMEOUT
                errorMessage = 'Location request timed out. Please enter manually.';
                break;
              default:
                errorMessage = 'Unable to get location. Please enter manually.';
                break;
            }
            
            setLocationError(errorMessage);
            setShowManualLocation(true);
            
            // Create a standard error object instead of rejecting with the GeolocationPositionError
            const standardError = new Error(errorMessage);
            standardError.code = error.code;
            standardError.originalError = error;
            reject(standardError);
          } catch (err) {
            console.error('❌ Error in geolocation error handler:', err);
            setLocationError('Location error occurred. Please enter manually.');
            setShowManualLocation(true);
            reject(new Error('Location error occurred. Please enter manually.'));
          }
        },
        { 
          enableHighAccuracy: true, 
          timeout: 10000, 
          maximumAge: 300000 
        }
      );
    });
  };

  // Enhanced geocoding with better Indian address parsing and error handling
  const geocodeManualLocation = async (locationString) => {
    const cleanedLocation = locationString.trim();
    
    if (!cleanedLocation) {
      throw new Error('Please enter a valid location');
    }
    
    console.log(`🔍 Geocoding manual location: "${cleanedLocation}"`);
    
    // Enhanced location parsing for Indian addresses - more comprehensive
    const parseIndianAddress = (locationString) => {
      const parts = locationString.split(',').map(part => part.trim());
      const formats = [];
      
      // Parse different address formats systematically
      if (parts.length >= 3) {
        // Full address: area, city, state
        const area = parts[0];
        const city = parts[1]; 
        const state = parts[2];
        
        formats.push(locationString); // Original format
        formats.push(`${area}, ${city}, ${state}, India`); // Add country
        formats.push(`${city}, ${state}, India`); // City, state format
        formats.push(`${area} ${city} ${state}`); // Space-separated
        formats.push(`${city}, ${state}`); // Just city and state
        formats.push(`${city} ${state}`); // City state without comma
        
        console.log(`📍 Parsed address parts: Area="${area}", City="${city}", State="${state}"`);
      } else if (parts.length === 2) {
        // city, state format
        const city = parts[0];
        const state = parts[1];
        
        formats.push(locationString); // Original
        formats.push(`${city}, ${state}, India`); // Add country
        formats.push(`${city} ${state} India`); // Space format
        formats.push(`${city}, ${state}`); // Keep original
        formats.push(`${city} ${state}`); // No comma
        
        console.log(`📍 Parsed address parts: City="${city}", State="${state}"`);
      } else {
        // Single location - could be city, area, or landmark
        const location = parts[0];
        
        formats.push(location); // Original
        formats.push(`${location}, India`); // Add country
        formats.push(`${location}, Karnataka, India`); // Common state fallback
        formats.push(`${location}, Karnataka`); // State only
        formats.push(`${location} Karnataka`); // Space format
        
        console.log(`📍 Single location: "${location}"`);
      }
      
      // Remove duplicates while preserving order
      return [...new Set(formats)];
    };
    
    // Geocoding services with improved parsing
    const geocodingServices = [
      {
        name: 'OpenStreetMap Nominatim',
        url: (query) => `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=5&countrycodes=in&addressdetails=1&bounded=1`,
        parseResult: (data, originalQuery) => {
          if (data && data.length > 0) {
            console.log(`📋 Nominatim returned ${data.length} results for "${originalQuery}"`);
            
            // Sort results by relevance and importance
            const sortedResults = data.sort((a, b) => {
              // Prefer results that match the query better
              const aNameMatch = a.display_name.toLowerCase().includes(originalQuery.toLowerCase()) ? 1 : 0;
              const bNameMatch = b.display_name.toLowerCase().includes(originalQuery.toLowerCase()) ? 1 : 0;
              
              if (aNameMatch !== bNameMatch) return bNameMatch - aNameMatch;
              
              // Then by importance
              return (b.importance || 0) - (a.importance || 0);
            });
            
            const bestMatch = sortedResults[0];
            
            return {
              latitude: parseFloat(bestMatch.lat),
              longitude: parseFloat(bestMatch.lon),
              address: bestMatch.display_name,
              source: 'OpenStreetMap Nominatim',
              confidence: bestMatch.importance || 0.5
            };
          }
          return null;
        }
      },
      {
        name: 'OpenStreetMap Photon',
        url: (query) => `https://photon.komoot.io/api/?q=${encodeURIComponent(query)}&limit=5&osm_tag=place:city,place:town,place:village&lang=en`,
        parseResult: (data, originalQuery) => {
          if (data && data.features && data.features.length > 0) {
            console.log(`📋 Photon returned ${data.features.length} results for "${originalQuery}"`);
            
            const bestMatch = data.features[0];
            const coords = bestMatch.geometry?.coordinates;
            if (coords && coords.length >= 2) {
              const address = bestMatch.properties?.name || bestMatch.properties?.label || bestMatch.properties?.display_name || 'Location found';
              
              return {
                latitude: coords[1],
                longitude: coords[0],
                address: address,
                source: 'OpenStreetMap Photon',
                confidence: 0.7
              };
            }
          }
          return null;
        }
      }
    ];
    
    const addressFormats = parseIndianAddress(cleanedLocation);
    console.log(`🎯 Generated ${addressFormats.length} address format variations:`, addressFormats);
    
    let bestResult = null;
    let highestConfidence = 0;
    
    // Try each geocoding service with each address format
    for (const service of geocodingServices) {
      for (let i = 0; i < addressFormats.length; i++) {
        const addressFormat = addressFormats[i];
        
        try {
          console.log(`🔄 Trying ${service.name} with format ${i+1}/${addressFormats.length}: "${addressFormat}"`);
          
          const url = service.url(addressFormat);
          const response = await fetch(url, {
            headers: {
              'User-Agent': 'EarnAura-Emergency-Finder/1.0',
              'Accept': 'application/json'
            }
          });
          
          if (!response.ok) {
            console.warn(`⚠️ ${service.name} returned ${response.status} for "${addressFormat}"`);
            continue;
          }
          
          const data = await response.json();
          const result = service.parseResult(data, addressFormat);
          
          if (result && result.latitude && result.longitude) {
            console.log(`✅ ${service.name} found location: ${result.address} (confidence: ${result.confidence})`);
            
            // Keep the best result based on confidence and format priority
            const formatPriority = 1 - (i / addressFormats.length); // Earlier formats get higher priority
            const totalScore = result.confidence + formatPriority;
            
            if (totalScore > highestConfidence) {
              bestResult = result;
              highestConfidence = totalScore;
            }
            
            // If we found a high-confidence result early, use it
            if (result.confidence > 0.8) {
              break;
            }
          } else {
            console.log(`❌ ${service.name} found no results for "${addressFormat}"`);
          }
        } catch (error) {
          console.warn(`❌ ${service.name} failed for "${addressFormat}":`, error.message);
          continue;
        }
      }
      
      // If we found a good result, don't try other services
      if (bestResult && bestResult.confidence > 0.7) {
        break;
      }
    }
    
    if (bestResult) {
      console.log(`🎉 Best geocoding result:`, bestResult);
      
      const location = {
        latitude: bestResult.latitude,
        longitude: bestResult.longitude,
        address: bestResult.address,
        source: bestResult.source,
        manual: true // Flag to indicate this was manually entered
      };
      
      setUserLocation(location);
      setLocationError('');
      setShowManualLocation(false);
      return location;
    }
    
    // Try coordinate parsing as final fallback
    const coordMatch = cleanedLocation.match(/(-?\d+\.?\d*),?\s*(-?\d+\.?\d*)/);
    if (coordMatch) {
      const latitude = parseFloat(coordMatch[1]);
      const longitude = parseFloat(coordMatch[2]);
      
      if (latitude >= 6 && latitude <= 37 && longitude >= 68 && longitude <= 98) { // India bounds
        console.log(`🎯 Using coordinates: ${latitude}, ${longitude}`);
        
        const location = {
          latitude,
          longitude,
          address: `${latitude}, ${longitude}`,
          source: 'Manual Coordinates',
          manual: true
        };
        
        setUserLocation(location);
        setLocationError('');
        setShowManualLocation(false);
        return location;
      }
    }
    
    // Enhanced error messages with specific guidance
    const parts = cleanedLocation.split(',').length;
    let errorMessage = '❌ Location not found. ';
    
    if (cleanedLocation.length < 3) {
      errorMessage += 'Please enter a more specific location (at least 3 characters).';
    } else if (parts === 1) {
      errorMessage += 'Try adding more details: "area, city" or "city, state" (e.g., "MG Road, Tumkur" or "Tumkur, Karnataka")';
    } else if (parts >= 2) {
      errorMessage += 'Please check the spelling. Format: "area, city, state" or "city, state" (e.g., "MG Road, Tumkur, Karnataka")';
    }
    
    setLocationError(errorMessage);
    throw new Error(errorMessage);
  };

  // Enhanced fetch nearby places with specific type support
  const fetchNearbyPlaces = async (category, location = null, specificType = null) => {
    const currentLocation = location || userLocation;
    if (!currentLocation) {
      setLocationError('Location required to find nearby places');
      return;
    }

    setLoadingHospitals(true);
    setNearbyPlaces([]);

    try {
      const categoryConfig = emergencyCategories.find(cat => cat.id === category);
      if (!categoryConfig) return;

      // Enhanced search radius and location coverage
      const radius = 15000; // Increased to 15km for broader search
      
      let overpassQuery = '[out:json][timeout:25];(';
      
      // Enhanced place types based on category and specific type
      const placeTypes = categoryConfig.placeTypes;
      
      placeTypes.forEach(placeType => {
        let amenityTag = '';
        let additionalFilters = '';
        
        switch (placeType) {
          case 'fire_station':
            amenityTag = 'amenity=fire_station';
            break;
          case 'emergency_shelter':
            amenityTag = 'amenity=shelter';
            break;
          case 'police':
            amenityTag = 'amenity=police';
            break;
          case 'hospital':
            amenityTag = 'amenity=hospital';
            // Add specific filters for accident and medical emergencies
            if (category === 'accident' && specificType) {
              if (specificType.toLowerCase().includes('road') || specificType.toLowerCase().includes('traffic')) {
                additionalFilters = '[emergency=yes][healthcare:speciality~"trauma|emergency"]';
              } else if (specificType.toLowerCase().includes('workplace')) {
                additionalFilters = '[healthcare:speciality~"occupational|trauma"]';
              }
            } else if (category === 'medical_emergency' && specificType) {
              const specialtyMap = {
                'cardiac': 'cardiology',
                'pediatric': 'paediatrics',
                'orthopedic': 'orthopaedics',
                'neurological': 'neurology',
                'respiratory': 'pulmonology',
                'gastroenterology': 'gastroenterology',
                'psychiatric': 'psychiatry',
                'obstetric': 'obstetrics',
                'trauma': 'trauma'
              };
              const specialty = specialtyMap[specificType] || specificType;
              additionalFilters = `[healthcare:speciality~"${specialty}|emergency|general"]`;
            }
            break;
          case 'clinic':
            amenityTag = 'amenity=clinic';
            // Add specific filters for medical emergencies
            if (category === 'medical_emergency' && specificType) {
              const specialtyMap = {
                'cardiac': 'cardiology',
                'pediatric': 'paediatrics',
                'orthopedic': 'orthopaedics',
                'neurological': 'neurology',
                'respiratory': 'pulmonology',
                'gastroenterology': 'gastroenterology',
                'psychiatric': 'psychiatry',
                'obstetric': 'obstetrics'
              };
              const specialty = specialtyMap[specificType] || specificType;
              additionalFilters = `[healthcare:speciality~"${specialty}"]`;
            }
            break;
          case 'pharmacy':
            amenityTag = 'amenity=pharmacy';
            break;
          case 'emergency':
            amenityTag = 'emergency=yes';
            break;
          default:
            amenityTag = `amenity=${placeType}`;
        }
        
        // Enhanced query to search broader areas
        overpassQuery += `node[${amenityTag}${additionalFilters}](around:${radius},${currentLocation.latitude},${currentLocation.longitude});`;
        overpassQuery += `way[${amenityTag}${additionalFilters}](around:${radius},${currentLocation.latitude},${currentLocation.longitude});`;
        
        // Add relation search for comprehensive coverage
        overpassQuery += `relation[${amenityTag}${additionalFilters}](around:${radius},${currentLocation.latitude},${currentLocation.longitude});`;
      });
      
      overpassQuery += ');out center meta;';

      const response = await fetch('https://overpass-api.de/api/interpreter', {
        method: 'POST',
        body: overpassQuery,
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch places from OpenStreetMap');
      }

      const data = await response.json();
      
      // Enhanced result processing
      const places = data.elements.map(element => {
        const lat = element.lat || (element.center && element.center.lat);
        const lon = element.lon || (element.center && element.center.lon);
        
        if (!lat || !lon) return null;

        // Calculate distance (but won't display the symbols)
        const distance = calculateDistance(
          currentLocation.latitude,
          currentLocation.longitude,
          lat,
          lon
        );

        return {
          id: element.id,
          name: element.tags?.name || `${categoryConfig.name} Service`,
          address: formatAddress(element.tags),
          phone: element.tags?.phone || element.tags?.['contact:phone'],
          emergency_phone: element.tags?.['emergency:phone'] || '108',
          latitude: lat,
          longitude: lon,
          distance: distance,
          distanceText: distance < 1 ? `${Math.round(distance * 1000)}m` : `${distance.toFixed(1)}km`,
          type: determineServiceType(element.tags, placeTypes),
          amenity: element.tags?.amenity,
          opening_hours: element.tags?.opening_hours,
          website: element.tags?.website || element.tags?.['contact:website'],
          rating: null, // OSM doesn't have ratings
          tags: element.tags
        };
      }).filter(place => place !== null);

      // Sort by distance and limit to 10 results
      const sortedPlaces = places.sort((a, b) => a.distance - b.distance).slice(0, 10);
      setNearbyPlaces(sortedPlaces);
      
    } catch (error) {
      console.error('Error fetching nearby places:', error);
      setLocationError('Failed to find nearby places. Please try again.');
      setNearbyPlaces([]);
    } finally {
      setLoadingHospitals(false);
    }
  };

  // Helper function to calculate distance between two coordinates
  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371; // Radius of Earth in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };

  // Helper function to format address from OSM tags
  const formatAddress = (tags) => {
    if (!tags) return 'Address not available';
    
    const parts = [];
    if (tags['addr:housenumber'] && tags['addr:street']) {
      parts.push(`${tags['addr:housenumber']} ${tags['addr:street']}`);
    } else if (tags['addr:street']) {
      parts.push(tags['addr:street']);
    }
    
    if (tags['addr:city']) parts.push(tags['addr:city']);
    if (tags['addr:state']) parts.push(tags['addr:state']);
    if (tags['addr:postcode']) parts.push(tags['addr:postcode']);
    
    return parts.length > 0 ? parts.join(', ') : 'Address not available';
  };

  // Helper function to determine service type from tags
  const determineServiceType = (tags, placeTypes) => {
    if (!tags) return 'Emergency Service';
    
    if (tags.amenity === 'fire_station') return 'Fire Station';
    if (tags.amenity === 'police') return 'Police Station';
    if (tags.amenity === 'hospital') return 'Hospital';
    if (tags.amenity === 'clinic') return 'Clinic';
    if (tags.amenity === 'pharmacy') return 'Pharmacy';
    if (tags.amenity === 'shelter') return 'Emergency Shelter';
    if (tags.emergency === 'yes') return 'Emergency Service';
    
    return 'Emergency Service';
  };

  // Navigate to place using Google Maps or OpenStreetMap
  const navigateToPlace = (place) => {
    const { latitude, longitude, name } = place;
    
    // Try Google Maps first (universal URL scheme)
    const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}&destination_place_id=${encodeURIComponent(name)}`;
    
    // OpenStreetMap fallback
    const osmUrl = `https://www.openstreetmap.org/directions?to=${latitude},${longitude}#map=16/${latitude}/${longitude}`;
    
    // Check if it's a mobile device for app deep linking
    const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
      // Try to open in Google Maps app first
      const appUrl = `google.navigation:q=${latitude},${longitude}`;
      
      // Create a temporary link to test if app is available
      const link = document.createElement('a');
      link.href = appUrl;
      
      setTimeout(() => {
        // Fallback to web if app didn't open
        window.open(googleMapsUrl, '_blank');
      }, 500);
      
      // Try to trigger app
      try {
        link.click();
      } catch (e) {
        window.open(googleMapsUrl, '_blank');
      }
    } else {
      // Desktop: open Google Maps in new tab
      window.open(googleMapsUrl, '_blank');
    }
  };

  const fetchAllSuggestions = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      
      const categoryPromises = categories.filter(cat => cat !== 'Emergency Fund').map(async (category) => {
        try {
          const response = await axios.get(`${API}/app-suggestions/${category.toLowerCase()}`, { headers });
          return { category, apps: response.data.apps || [] };
        } catch (error) {
          console.error(`Error fetching suggestions for ${category}:`, error);
          return { category, apps: [] };
        }
      });

      const results = await Promise.all(categoryPromises);
      const suggestions = {};
      
      results.forEach(({ category, apps }) => {
        suggestions[category] = apps;
      });

      setAllSuggestions(suggestions);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEmergencySelect = async (emergencyCategory) => {
    setSelectedEmergency(emergencyCategory.id);
    setNearbyPlaces([]);
    
    // Reset specific emergency type selections
    setAccidentType('');
    setSelectedMedicalEmergency('');
    setCustomMedicalEmergency('');
    
    try {
      // Try to get location first
      let location = userLocation;
      if (!location) {
        location = await getUserLocation();
      }
      
      // For accident and medical emergencies, don't immediately fetch - wait for type selection
      if (emergencyCategory.id === 'accident' || emergencyCategory.id === 'medical_emergency') {
        // Just set the category, user needs to specify type first
        return;
      }
      
      // For other emergencies, fetch immediately
      await fetchNearbyPlaces(emergencyCategory.id, location);
      
    } catch (error) {
      console.error('Error getting location:', error);
      // Show manual location input if geolocation fails
      setShowManualLocation(true);
    }
  };

  // Handle accident type search with enhanced backend integration
  const handleAccidentSearch = async () => {
    if (!accidentType.trim()) return;
    
    setLoadingHospitals(true);
    setNearbyPlaces([]);
    
    try {
      let location = userLocation;
      if (!location) {
        location = await getUserLocation();
      }
      
      // Call enhanced backend API for accident-specific hospital recommendations
      const token = localStorage.getItem('token');
      const headers = token ? { 
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      } : { 'Content-Type': 'application/json' };
      
      const response = await axios.post(`${API}/emergency-hospitals`, {
        latitude: location.latitude,
        longitude: location.longitude
      }, {
        headers,
        params: { emergency_type: accidentType.trim() }
      });
      
      if (response.data && response.data.hospitals) {
        const hospitals = response.data.hospitals.map(hospital => ({
          id: hospital.name,
          name: hospital.name,
          address: hospital.address,
          phone: hospital.phone,
          emergency_phone: hospital.emergency_phone || '108',
          latitude: location.latitude + (Math.random() - 0.5) * 0.01, // Approximate location
          longitude: location.longitude + (Math.random() - 0.5) * 0.01,
          distance: hospital.distance,
          distanceText: hospital.distance,
          type: hospital.hospital_type || 'Hospital',
          rating: hospital.rating,
          opening_hours: '24/7 Emergency',
          speciality: hospital.speciality,
          matched_specialties: hospital.matched_specialties || [],
          features: hospital.features || [],
          estimated_time: hospital.estimated_time
        }));
        
        setNearbyPlaces(hospitals);
      }
      
    } catch (error) {
      console.error('Error getting specialized hospitals for accident:', error);
      setLocationError('Failed to find specialized trauma centers. Please try again.');
      
      // Fallback to OpenStreetMap search
      await fetchNearbyPlaces('accident', location, accidentType);
    } finally {
      setLoadingHospitals(false);
    }
  };

  // Handle medical emergency type search with enhanced backend integration
  const handleMedicalEmergencySearch = async () => {
    const emergencyType = customMedicalEmergency.trim() || selectedMedicalEmergency;
    if (!emergencyType) return;
    
    setLoadingHospitals(true);
    setNearbyPlaces([]);
    
    try {
      let location = userLocation;
      if (!location) {
        location = await getUserLocation();
      }
      
      // Call enhanced backend API for medical specialty-specific hospital recommendations
      const token = localStorage.getItem('token');
      const headers = token ? { 
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      } : { 'Content-Type': 'application/json' };
      
      const response = await axios.post(`${API}/emergency-hospitals`, {
        latitude: location.latitude,
        longitude: location.longitude
      }, {
        headers,
        params: { emergency_type: emergencyType }
      });
      
      if (response.data && response.data.hospitals) {
        const hospitals = response.data.hospitals.map(hospital => ({
          id: hospital.name,
          name: hospital.name,
          address: hospital.address,
          phone: hospital.phone,
          emergency_phone: hospital.emergency_phone || '108',
          latitude: location.latitude + (Math.random() - 0.5) * 0.01, // Approximate location
          longitude: location.longitude + (Math.random() - 0.5) * 0.01,
          distance: hospital.distance,
          distanceText: hospital.distance,
          type: hospital.hospital_type || 'Hospital',
          rating: hospital.rating,
          opening_hours: '24/7 Emergency',
          speciality: hospital.speciality,
          matched_specialties: hospital.matched_specialties || [],
          features: hospital.features || [],
          estimated_time: hospital.estimated_time
        }));
        
        setNearbyPlaces(hospitals);
      }
      
    } catch (error) {
      console.error('Error getting specialized hospitals for medical emergency:', error);
      setLocationError('Failed to find specialized medical centers. Please try again.');
      
      // Fallback to OpenStreetMap search
      await fetchNearbyPlaces('medical_emergency', location, emergencyType);
    } finally {
      setLoadingHospitals(false);
    }
  };

  const handleSuggestionClick = async (suggestion, category) => {
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      
      // Track click
      await axios.post(`${API}/track-suggestion-click`, {
        category: category,
        suggestion_name: suggestion.name,
        suggestion_url: suggestion.url,
        user_location: userLocation
      }, { headers });
      
      // Open in new tab
      window.open(suggestion.url, '_blank', 'noopener,noreferrer');
    } catch (error) {
      console.error('Error tracking suggestion click:', error);
      // Still open the link even if tracking fails
      window.open(suggestion.url, '_blank', 'noopener,noreferrer');
    }
  };

  // Enhanced manual location submission with better backend integration
  const handleManualLocationSubmit = async () => {
    if (!manualLocation.trim()) {
      setLocationError('Please enter a location');
      return;
    }
    
    try {
      setLoadingHospitals(true);
      setLocationError('');
      
      console.log(`🎯 Processing manual location: "${manualLocation}"`);
      
      // Step 1: Geocode the manual location
      const location = await geocodeManualLocation(manualLocation);
      
      console.log(`✅ Location geocoded successfully:`, location);
      
      // Step 2: If we have a selected emergency, immediately search for hospitals
      if (selectedEmergency) {
        console.log(`🏥 Searching for ${selectedEmergency} hospitals at geocoded location`);
        
        // Determine specific emergency type
        let specificType = null;
        if (selectedEmergency === 'accident' && accidentType.trim()) {
          specificType = accidentType.trim();
          console.log(`🚗 Accident type: ${specificType}`);
        } else if (selectedEmergency === 'medical_emergency') {
          specificType = customMedicalEmergency.trim() || selectedMedicalEmergency;
          console.log(`🏥 Medical emergency type: ${specificType}`);
        }
        
        // For accident and medical emergencies, use backend API
        if ((selectedEmergency === 'accident' || selectedEmergency === 'medical_emergency') && specificType) {
          console.log(`🔍 Using backend API for specialized hospital search`);
          
          const token = localStorage.getItem('token');
          const headers = token ? { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          } : { 'Content-Type': 'application/json' };
          
          try {
            const response = await axios.post(`${API}/emergency-hospitals`, {
              latitude: location.latitude,
              longitude: location.longitude
            }, {
              headers,
              params: { emergency_type: specificType }
            });
            
            if (response.data && response.data.hospitals) {
              console.log(`✅ Backend returned ${response.data.hospitals.length} hospitals`);
              
              const hospitals = response.data.hospitals.map(hospital => ({
                id: hospital.name || `hospital-${Math.random()}`,
                name: hospital.name,
                address: hospital.address,
                phone: hospital.phone,
                emergency_phone: hospital.emergency_phone || '108',
                latitude: location.latitude + (Math.random() - 0.5) * 0.01, // Approximate location
                longitude: location.longitude + (Math.random() - 0.5) * 0.01,
                distance: hospital.distance,
                distanceText: hospital.distance,
                type: hospital.hospital_type || 'Hospital',
                rating: hospital.rating,
                opening_hours: '24/7 Emergency',
                speciality: hospital.speciality,
                matched_specialties: hospital.matched_specialties || [],
                features: hospital.features || [],
                estimated_time: hospital.estimated_time
              }));
              
              setNearbyPlaces(hospitals);
              console.log(`🎉 Successfully set ${hospitals.length} hospitals for display`);
            } else {
              console.warn('⚠️ Backend API returned no hospitals, falling back to OSM search');
              await fetchNearbyPlaces(selectedEmergency, location, specificType);
            }
          } catch (apiError) {
            console.error('❌ Backend API failed, falling back to OSM search:', apiError);
            await fetchNearbyPlaces(selectedEmergency, location, specificType);
          }
        } else {
          // For other emergency types, use OpenStreetMap search
          console.log(`🗺️ Using OpenStreetMap search for ${selectedEmergency}`);
          await fetchNearbyPlaces(selectedEmergency, location, specificType);
        }
      } else {
        console.log(`📍 Location set successfully, waiting for emergency type selection`);
      }
      
    } catch (error) {
      console.error('❌ Manual location processing failed:', error);
      setLocationError(error.message || 'Failed to process location. Please try again.');
    } finally {
      setLoadingHospitals(false);
    }
  };

  const handlePlaceCall = (phone) => {
    if (phone) {
      window.location.href = `tel:${phone}`;
    }
  };

  const handleGoogleSearch = (category) => {
    const searchQueries = {
      'Food': 'best food delivery apps restaurants near me',
      'Transportation': 'best transportation apps ride sharing public transport',
      'Books': 'best book reading apps online bookstores',
      'Entertainment': 'best entertainment apps streaming services',
      'Rent': 'best rental apps apartment finder real estate',
      'Utilities': 'best utility apps bill payment services',
      'Movies': 'best movie streaming apps cinema booking',
      'Shopping': 'best shopping apps online stores deals',
      'Groceries': 'best grocery delivery apps supermarket online',
      'Subscriptions': 'best subscription management apps services',
      'Emergency Fund': 'emergency fund savings apps financial planning'
    };
    
    const query = searchQueries[category] || `best ${category.toLowerCase()} apps`;
    const googleUrl = `https://www.google.com/search?q=${encodeURIComponent(query)}`;
    window.open(googleUrl, '_blank', 'noopener,noreferrer');
  };

  const filteredCategories = [selectedCategory].filter(cat => 
    cat === 'Emergency Fund' || allSuggestions[cat]
  );

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Smart Recommendations</h1>
        <p className="text-gray-600">Discover the best apps and websites for your expense categories</p>
      </div>

      {/* Emergency Services Section Removed */}

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2 justify-center">
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
              selectedCategory === category
                ? 'bg-emerald-600 text-white shadow-lg'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {category}
          </button>
        ))}
      </div>

      {/* Regular Category Suggestions */}
      <div className="space-y-8">
        {filteredCategories.map((category) => {
          if (category === 'Emergency Fund') {
            return null; // Emergency Fund is handled separately below
          }
          
          const Icon = categoryIcons[category];
          const suggestions = allSuggestions[category] || [];
          
          return (
            <div key={category} className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center gap-3 mb-6">
                {Icon && <Icon className="w-6 h-6 text-emerald-600" />}
                <h2 className="text-xl font-semibold text-gray-900">{category}</h2>
                <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                  {suggestions.length} options
                </span>
              </div>
              
              {suggestions.length > 0 ? (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {suggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => handleSuggestionClick(suggestion, category)}
                        className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-emerald-300 hover:shadow-md transition-all duration-200 text-left group"
                      >
                        <div className="flex-shrink-0 relative">
                          <div className="w-12 h-12 rounded-lg bg-white p-1 flex items-center justify-center">
                            {suggestion.logo ? (
                              <img 
                                src={suggestion.logo} 
                                alt={`${suggestion.name} logo`}
                                className="max-w-full max-h-full object-contain"
                                onError={(e) => {
                                  // Hide the image and show fallback
                                  e.target.style.display = 'none';
                                  const fallback = document.createElement('div');
                                  fallback.className = 'w-10 h-10 bg-gradient-to-br from-emerald-500 to-blue-500 rounded-lg flex items-center justify-center text-white font-bold text-sm';
                                  fallback.textContent = suggestion.name.charAt(0);
                                  e.target.parentElement.appendChild(fallback);
                                }}
                                style={{maxWidth: '100%', maxHeight: '100%'}}
                              />
                            ) : (
                              <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-blue-500 rounded-lg flex items-center justify-center text-white font-bold text-sm">
                                {suggestion.name.charAt(0)}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold text-gray-900 truncate">
                              {suggestion.name}
                            </h3>
                            {suggestion.price_comparison && (
                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                Compare Prices
                              </span>
                            )}
                          </div>
                          {suggestion.description && (
                            <p className="text-sm text-gray-600 line-clamp-2">
                              {suggestion.description}
                            </p>
                          )}
                          <div className="flex items-center gap-2 mt-2">
                            <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded">
                              {suggestion.type}
                            </span>
                          </div>
                        </div>
                        <LinkIcon className="w-5 h-5 text-gray-400 group-hover:text-emerald-600 transition-colors" />
                      </button>
                    ))}
                  </div>
                  
                  {/* Search on Google Button */}
                  <div className="mt-6 text-center">
                    <button
                      onClick={() => handleGoogleSearch(category)}
                      className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
                    >
                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                      </svg>
                      Search on Google
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <p className="text-gray-500 text-center py-8">No suggestions available for this category.</p>
                  
                  {/* Search on Google Button for empty categories */}
                  <div className="text-center">
                    <button
                      onClick={() => handleGoogleSearch(category)}
                      className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
                    >
                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                      </svg>
                      Search on Google
                    </button>
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>

      {/* Emergency Fund Special Section */}
      {selectedCategory === 'Emergency Fund' && (
        <div className="bg-gradient-to-r from-red-50 to-orange-50 rounded-xl shadow-lg p-6 border border-red-200">
          <div className="flex items-center gap-3 mb-6">
            <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
            <h2 className="text-xl font-semibold text-gray-900">Emergency Services Finder</h2>
          </div>
          
          <div className="space-y-6">
            {/* Location Status */}
            {!userLocation && !showManualLocation && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <MapPinIcon className="w-5 h-5 text-blue-600" />
                  <h3 className="font-medium text-blue-800">Location Access Required</h3>
                </div>
                <p className="text-sm text-blue-700 mb-3">
                  We need your location to find nearby emergency services. Your location data stays on your device.
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={async () => {
                      try {
                        await getUserLocation();
                      } catch (error) {
                        console.error('❌ Location access failed:', error);
                        // Error is already handled in getUserLocation, just ensure we don't crash
                      }
                    }}
                    className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    📍 Use My Location
                  </button>
                  <button
                    onClick={() => setShowManualLocation(true)}
                    className="px-4 py-2 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    📝 Enter Manually
                  </button>
                </div>
              </div>
            )}

            {/* Manual Location Input - Enhanced UI */}
            {showManualLocation && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <h3 className="font-medium text-yellow-800 mb-3">📍 Enter Your Location Manually</h3>
                <p className="text-sm text-yellow-700 mb-3">
                  Enter your address to find nearby hospitals within 25km radius. We support various formats.
                </p>
                
                {/* Examples section */}
                <div className="mb-3 p-2 bg-white border border-yellow-200 rounded text-xs">
                  <p className="font-medium text-yellow-800 mb-1">💡 Supported formats:</p>
                  <div className="space-y-1 text-yellow-700">
                    <div>• <span className="font-mono bg-gray-100 px-1 rounded">MG Road, Tumkur, Karnataka</span> (area, city, state)</div>
                    <div>• <span className="font-mono bg-gray-100 px-1 rounded">Tumkur, Karnataka</span> (city, state)</div>
                    <div>• <span className="font-mono bg-gray-100 px-1 rounded">Mumbai</span> (city only)</div>
                    <div>• <span className="font-mono bg-gray-100 px-1 rounded">12.9716, 77.5946</span> (coordinates)</div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <input
                    type="text"
                    value={manualLocation}
                    onChange={(e) => {
                      setManualLocation(e.target.value);
                      // Clear error when user starts typing
                      if (locationError) setLocationError('');
                    }}
                    placeholder="e.g., MG Road, Tumkur, Karnataka"
                    className="w-full px-3 py-2 border border-yellow-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleManualLocationSubmit();
                      }
                    }}
                  />
                  
                  <div className="flex gap-2">
                    <button
                      onClick={handleManualLocationSubmit}
                      disabled={!manualLocation.trim() || loadingHospitals}
                      className="flex-1 px-4 py-2 bg-yellow-600 text-white text-sm rounded-lg hover:bg-yellow-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                    >
                      {loadingHospitals ? (
                        <span className="flex items-center justify-center gap-2">
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          Finding Location...
                        </span>
                      ) : (
                        '🔍 Find Location'
                      )}
                    </button>
                    
                    <button
                      onClick={() => {
                        setShowManualLocation(false);
                        setManualLocation('');
                        setLocationError('');
                      }}
                      className="px-4 py-2 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                  
                  <button
                    onClick={() => {
                      setShowManualLocation(false);
                      setLocationError('');
                    }}
                    className="text-sm text-yellow-600 hover:text-yellow-800 w-full text-center"
                  >
                    ← Try automatic location detection instead
                  </button>
                </div>
              </div>
            )}

            {/* Location Error */}
            {locationError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700">{locationError}</p>
              </div>
            )}

            {/* Current Location Display */}
            {userLocation && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-2">
                  <MapPinIcon className="w-4 h-4 text-green-600" />
                  <span className="text-sm text-green-700 font-medium">
                    Location: {userLocation.address ? userLocation.address.split(',').slice(0, 2).join(', ') : 
                    `${userLocation.latitude.toFixed(4)}, ${userLocation.longitude.toFixed(4)}`}
                  </span>
                </div>
              </div>
            )}

            {/* Emergency Type Selection */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                What type of emergency?
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {emergencyTypes.map((type, index) => (
                  <button
                    key={type.id}
                    onClick={() => handleEmergencySelect(type)}
                    disabled={!userLocation && !showManualLocation}
                    className={`p-4 rounded-lg border text-left transition-all duration-200 ${
                      selectedEmergency === type.id
                        ? 'border-red-300 bg-red-50 text-red-800'
                        : userLocation || showManualLocation
                          ? 'border-gray-200 bg-white hover:border-red-200 hover:bg-red-50'
                          : 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{type.icon}</span>
                      <div className="flex-1">
                        <h3 className="font-medium text-sm">{type.name}</h3>
                        <p className="text-xs text-gray-600 mt-1">{type.description}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Accident Type Search */}
            {selectedEmergency === 'accident' && (
              <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                <h3 className="font-medium text-orange-800 mb-3">🚗 Specify Accident Type</h3>
                <p className="text-sm text-orange-700 mb-3">
                  Enter the specific type of accident to find the most relevant trauma centers and hospitals.
                </p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={accidentType}
                    onChange={(e) => setAccidentType(e.target.value)}
                    placeholder="e.g., road accident, workplace accident, sports injury"
                    className="flex-1 px-3 py-2 border border-orange-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                    onKeyPress={(e) => e.key === 'Enter' && handleAccidentSearch()}
                  />
                  <button
                    onClick={handleAccidentSearch}
                    disabled={!accidentType.trim()}
                    className="px-4 py-2 bg-orange-600 text-white text-sm rounded-lg hover:bg-orange-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    🔍 Find Centers
                  </button>
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {['road accident', 'workplace accident', 'sports injury', 'fall injury'].map(suggestion => (
                    <button
                      key={suggestion}
                      onClick={() => {
                        setAccidentType(suggestion);
                        setTimeout(() => handleAccidentSearch(), 100);
                      }}
                      className="px-2 py-1 text-xs bg-white border border-orange-200 rounded text-orange-600 hover:bg-orange-50"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Medical Emergency Type Selection */}
            {selectedEmergency === 'medical_emergency' && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="font-medium text-blue-800 mb-3">🏥 Select Medical Emergency Type</h3>
                <p className="text-sm text-blue-700 mb-3">
                  Choose the type of medical emergency to find specialized hospitals and clinics.
                </p>
                
                {/* Medical Emergency Dropdown */}
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-blue-800 mb-1">
                      Common Emergency Types:
                    </label>
                    <select
                      value={selectedMedicalEmergency}
                      onChange={(e) => setSelectedMedicalEmergency(e.target.value)}
                      className="w-full px-3 py-2 border border-blue-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select emergency type...</option>
                      {medicalEmergencyTypes.map(type => (
                        <option key={type.value} value={type.value}>{type.label}</option>
                      ))}
                    </select>
                  </div>

                  <div className="text-center text-gray-500 text-sm font-medium">OR</div>

                  {/* Custom Medical Emergency Input */}
                  <div>
                    <label className="block text-sm font-medium text-blue-800 mb-1">
                      Custom Emergency Type:
                    </label>
                    <input
                      type="text"
                      value={customMedicalEmergency}
                      onChange={(e) => setCustomMedicalEmergency(e.target.value)}
                      placeholder="e.g., diabetic emergency, allergic reaction, seizure"
                      className="w-full px-3 py-2 border border-blue-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      onKeyPress={(e) => e.key === 'Enter' && handleMedicalEmergencySearch()}
                    />
                  </div>

                  <button
                    onClick={handleMedicalEmergencySearch}
                    disabled={!selectedMedicalEmergency && !customMedicalEmergency.trim()}
                    className="w-full px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    🔍 Find Specialized Care
                  </button>
                </div>
              </div>
            )}

            {/* Nearby Places Results */}
            {selectedEmergency && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Nearby {emergencyTypes.find(t => t.id === selectedEmergency)?.name} Services
                  </h3>
                  <button
                    onClick={() => {
                      setSelectedEmergency('');
                      setNearbyPlaces([]);
                    }}
                    className="text-sm text-gray-600 hover:text-gray-800"
                  >
                    ← Back
                  </button>
                </div>
                
                {loadingHospitals ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
                    <span className="ml-2 text-gray-600">Finding nearby services...</span>
                  </div>
                ) : nearbyPlaces.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {nearbyPlaces.map((place, index) => (
                      <div key={place.id || index} className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <h4 className="font-semibold text-gray-900 text-sm leading-tight">
                              {place.name}
                            </h4>
                            <div className="flex items-center gap-2 mt-1">
                              <p className="text-xs text-blue-600">{place.type}</p>
                              {place.rating && (
                                <div className="flex items-center gap-1">
                                  <StarIcon className="w-3 h-3 text-yellow-400 fill-current" />
                                  <span className="text-xs text-gray-600">{place.rating}</span>
                                </div>
                              )}
                            </div>
                          </div>
                          {place.distanceText && (
                            <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                              {place.distanceText}
                            </div>
                          )}
                        </div>
                        
                        {/* Specialty Information */}
                        {place.speciality && (
                          <div className="mb-2 p-2 bg-blue-50 rounded-lg">
                            <p className="text-xs font-medium text-blue-800">🏥 {place.speciality}</p>
                            {place.matched_specialties && place.matched_specialties.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-1">
                                {place.matched_specialties.slice(0, 3).map((specialty, idx) => (
                                  <span key={idx} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                                    {specialty}
                                  </span>
                                ))}
                                {place.matched_specialties.length > 3 && (
                                  <span className="text-xs text-blue-600">+{place.matched_specialties.length - 3} more</span>
                                )}
                              </div>
                            )}
                          </div>
                        )}

                        {/* Features */}
                        {place.features && place.features.length > 0 && (
                          <div className="mb-2">
                            <div className="flex flex-wrap gap-1">
                              {place.features.slice(0, 3).map((feature, idx) => (
                                <span key={idx} className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                                  ✓ {feature}
                                </span>
                              ))}
                              {place.features.length > 3 && (
                                <span className="text-xs text-green-600">+{place.features.length - 3} more</span>
                              )}
                            </div>
                          </div>
                        )}
                        
                        <div className="space-y-2 text-sm text-gray-600">
                          <div className="flex items-start gap-2">
                            <MapPinIcon className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                            <span className="text-xs">{place.address}</span>
                          </div>
                          
                          {place.estimated_time && (
                            <div className="text-xs text-orange-600 bg-orange-50 px-2 py-1 rounded">
                              ⏱️ Estimated arrival: {place.estimated_time}
                            </div>
                          )}
                          
                          {place.opening_hours && (
                            <div className="text-xs text-gray-500">
                              🕐 {place.opening_hours}
                            </div>
                          )}

                          <div className="flex items-center gap-2 pt-2">
                            {place.phone && (
                              <button
                                onClick={() => handlePlaceCall(place.phone)}
                                className="flex items-center gap-1 px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors"
                              >
                                <PhoneIcon className="w-3 h-3" />
                                Call
                              </button>
                            )}
                            
                            <button
                              onClick={() => handlePlaceCall('108')}
                              className="flex items-center gap-1 px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 transition-colors"
                            >
                              <PhoneIcon className="w-3 h-3" />
                              Emergency (108)
                            </button>

                            <button
                              onClick={() => navigateToPlace(place)}
                              className="flex items-center gap-1 px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition-colors"
                            >
                              🧭 Navigate
                            </button>
                          </div>

                          {place.website && (
                            <div className="pt-1">
                              <a
                                href={place.website}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs text-blue-600 hover:text-blue-800 underline"
                              >
                                Visit Website
                              </a>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <ExclamationTriangleIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-600 mb-4">
                      No {emergencyTypes.find(t => t.id === selectedEmergency)?.name.toLowerCase()} services found nearby.
                    </p>
                    <div className="flex gap-2 justify-center">
                      <button
                        onClick={() => handlePlaceCall('108')}
                        className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition-colors"
                      >
                        🚨 Call Emergency (108)
                      </button>
                      <button
                        onClick={() => handlePlaceCall('112')}
                        className="px-4 py-2 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 transition-colors"
                      >
                        🆘 Call National Emergency (112)
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          
            {/* Search on Google Button for Emergency Fund */}
            <div className="mt-6 text-center">
              <button
                onClick={() => handleGoogleSearch('Emergency Fund')}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Search More Emergency Services
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Recommendations;

import math
import requests
import sys

try:
    if sys.stdout and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Doctor
from .serializers import DoctorSerializer


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two GPS coords."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def search_doctors_google_places(lat, lng, radius, specialization=''):
    """Fetch doctors from Google Maps Places API + Local Database"""
    print(f"\n{'='*60}")
    print(f"🔍 SEARCHING FOR DOCTORS")
    print(f"  📍 Location: {lat:.4f}, {lng:.4f}")
    print(f"  📏 Radius: {radius} m ({radius/1000} km)")
    print(f"  🩺 Specialization: {specialization or 'Any'}")
    print(f"{'='*60}\n")
    
    doctors = []
    
    # Step 1: Try Google Maps Places API
    print("1️⃣  Querying Google Maps Places API...")
    try:
        google_doctors = search_google_places(lat, lng, radius, specialization)
        if google_doctors:
            print(f"   ✅ Found {len(google_doctors)} doctors from Google Maps")
            doctors.extend(google_doctors)
    except Exception as e:
        print(f"   ⚠️  Google Maps error: {str(e)}")
    
    # Step 2: Add doctors from local database
    print("2️⃣  Checking local database...")
    db_doctors = get_database_doctors_nearby(lat, lng, radius/1000, specialization)
    if db_doctors:
        print(f"   ✅ Found {len(db_doctors)} doctors from database")
        doctors.extend(db_doctors)
    
    # Remove duplicates by name and location
    seen = set()
    unique_doctors = []
    for doc in doctors:
        key = (doc['name'], round(doc['latitude'], 3), round(doc['longitude'], 3))
        if key not in seen:
            seen.add(key)
            unique_doctors.append(doc)
    
    unique_doctors.sort(key=lambda x: x['distance'])
    
    print(f"\n✅ Total unique doctors: {len(unique_doctors)}\n")
    return unique_doctors


def search_google_places(lat, lng, radius, specialization=''):
    """Search for doctors using Google Maps Places API"""
    try:
        from django.conf import settings
        
        api_key = settings.GOOGLE_MAPS_API_KEY
        if not api_key:
            print("   ⚠️  No Google Maps API key configured")
            return []
        
        google_doctors = []
        
        # Map specializations to Google Places search queries
        queries = get_google_places_queries(specialization)
        
        for query_name, query_type in queries:
            print(f"   🔍 Searching for: {query_name}")
            
            # Use Nearby Search API
            url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
            params = {
                'location': f'{lat},{lng}',
                'radius': int(radius),  # Google uses meters
                'type': query_type,
                'keyword': query_name,
                'key': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'OK':
                results = data.get('results', [])
                print(f"      ✓ Found {len(results)} places")
                
                for place in results:
                    try:
                        # Get place details to get phone number
                        place_id = place['place_id']
                        detail_url = 'https://maps.googleapis.com/maps/api/place/details/json'
                        detail_params = {
                            'place_id': place_id,
                            'fields': 'formatted_phone_number,website,rating,reviews,open_now',
                            'key': api_key
                        }
                        detail_response = requests.get(detail_url, params=detail_params, timeout=10)
                        detail_data = detail_response.json().get('result', {})
                        
                        lat_doc = place['geometry']['location']['lat']
                        lng_doc = place['geometry']['location']['lng']
                        dist = haversine(lat, lng, lat_doc, lng_doc)
                        
                        doctor_info = {
                            'id': place_id,
                            'name': place.get('name', 'Healthcare Provider'),
                            'specialization': specialization or 'General Physician',
                            'latitude': lat_doc,
                            'longitude': lng_doc,
                            'address': place.get('vicinity', 'Address not available'),
                            'rating': place.get('rating', 0),
                            'phone': detail_data.get('formatted_phone_number', 'Not available'),
                            'is_available': detail_data.get('open_now', True),
                            'distance': round(dist, 2),
                            'consultation_fee': 'Varies',
                            'hospital_name': place.get('name', ''),
                            'years_experience': 0,
                            'source': 'Google Maps',
                        }
                        google_doctors.append(doctor_info)
                    except Exception as e:
                        print(f"      ⚠️  Error processing place: {str(e)}")
                        continue
            elif data.get('status') == 'ZERO_RESULTS':
                print(f"      ℹ️  No results for {query_name}")
            else:
                print(f"      ⚠️  API Status: {data.get('status')} - {data.get('error_message', '')}")
        
        return google_doctors
    except Exception as e:
        print(f"   ❌ Google Places API error: {str(e)}")
        return []


def get_google_places_queries(specialization):
    """Get Google Places search queries for a specialization"""
    queries_map = {
        'Cardiologist': [
            ('cardiologist', 'doctor'),
            ('heart specialist', 'doctor'),
            ('cardiac hospital', 'hospital'),
        ],
        'Pulmonologist': [
            ('pulmonologist', 'doctor'),
            ('lung specialist', 'doctor'),
            ('respiratory clinic', 'hospital'),
        ],
        'Neurologist': [
            ('neurologist', 'doctor'),
            ('brain specialist', 'doctor'),
            ('neuro hospital', 'hospital'),
        ],
        'Orthopedist': [
            ('orthopedist', 'doctor'),
            ('bone specialist', 'doctor'),
            ('orthopedic hospital', 'hospital'),
        ],
        'Dermatologist': [
            ('dermatologist', 'doctor'),
            ('skin specialist', 'doctor'),
            ('skin clinic', 'doctor'),
        ],
        'Gastroenterologist': [
            ('gastroenterologist', 'doctor'),
            ('gastro specialist', 'doctor'),
            ('gastro clinic', 'doctor'),
        ],
        'Endocrinologist': [
            ('endocrinologist', 'doctor'),
            ('diabetes specialist', 'doctor'),
            ('hormone clinic', 'doctor'),
        ],
        'Nephrologist': [
            ('nephrologist', 'doctor'),
            ('kidney specialist', 'doctor'),
            ('kidney hospital', 'hospital'),
        ],
        'Psychiatrist': [
            ('psychiatrist', 'doctor'),
            ('mental health clinic', 'doctor'),
        ],
        'General Physician': [
            ('general practitioner', 'doctor'),
            ('doctor', 'doctor'),
            ('clinic', 'doctor'),
        ],
    }
    
    if specialization in queries_map:
        return queries_map[specialization]
    else:
        return [('doctor', 'doctor'), ('hospital', 'hospital'), ('clinic', 'doctor')]


def get_database_doctors_nearby(lat, lng, radius, specialization=''):
    """Fallback: Get doctors from local database"""
    try:
        print(f"   📊 Checking database (radius: {radius}km)...")
        doctors_qs = Doctor.objects.filter(is_available=True)
        if specialization:
            doctors_qs = doctors_qs.filter(specialization=specialization)
        
        doctors = []
        for doc in doctors_qs:
            if doc.latitude and doc.longitude:
                dist = haversine(lat, lng, doc.latitude, doc.longitude)
                if dist <= radius:
                    doctors.append({
                        'id': doc.id,
                        'name': doc.name,
                        'specialization': doc.specialization,
                        'latitude': doc.latitude,
                        'longitude': doc.longitude,
                        'address': doc.address or f"{doc.city}" or 'Address not available',
                        'rating': doc.rating,
                        'phone': doc.phone or 'Not available',
                        'is_available': doc.is_available,
                        'distance': round(dist, 2),
                        'consultation_fee': f"Rs {doc.consultation_fee}" if doc.consultation_fee else 'Not available',
                        'hospital_name': doc.hospital_name,
                        'years_experience': doc.years_experience,
                        'source': 'Database',
                    })
        
        doctors.sort(key=lambda x: x['distance'])
        print(f"      ✓ Found {len(doctors)} doctors from database")
        return doctors
    except Exception as e:
        print(f"      ❌ Error fetching from database: {str(e)}")
        return []


# ─── Web Views ───────────────────────────────────────────────────────────────

@login_required
def doctor_list(request):
    specialization = request.GET.get('specialization', '')
    doctors = Doctor.objects.filter(is_available=True)
    if specialization:
        doctors = doctors.filter(specialization=specialization)
    specializations = Doctor.SPECIALIZATION_CHOICES
    return render(request, 'doctors/list.html', {
        'doctors': doctors,
        'specializations': specializations,
        'selected': specialization,
    })


@login_required
def doctor_map(request):
    doctors = Doctor.objects.filter(is_available=True)
    # Get specialist based on latest prediction
    specialist = None
    try:
        from health.models import HealthRecord
        latest = HealthRecord.objects.filter(user=request.user).select_related('prediction').first()
        if latest and hasattr(latest, 'prediction'):
            specialist = latest.prediction.specialist_needed
    except Exception:
        pass
    
    # Get specialization from URL parameter if provided
    specialization = request.GET.get('specialization', specialist or 'General Physician')
    
    return render(request, 'doctors/map.html', {
        'doctors': doctors,
        'specialist': specialist,
        'specialization': specialization,
        'user': request.user,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })


@login_required
def doctor_detail(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    return render(request, 'doctors/detail.html', {'doctor': doctor})


# ─── API Views ───────────────────────────────────────────────────────────────

class DoctorListAPIView(generics.ListAPIView):
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['specialization', 'is_available', 'city']

    def get_queryset(self):
        return Doctor.objects.filter(is_available=True)


class DoctorDetailAPIView(generics.RetrieveAPIView):
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]
    queryset = Doctor.objects.all()


class NearbyDoctorsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            lat = float(request.query_params.get('lat', 0))
            lng = float(request.query_params.get('lng', 0))
            radius_km = float(request.query_params.get('radius', 50))
            specialization = request.query_params.get('specialization', '').strip()
        except (ValueError, TypeError):
            return Response({'error': 'Invalid parameters', 'doctors': []}, status=status.HTTP_400_BAD_REQUEST)

        if lat == 0 and lng == 0:
            return Response({'error': 'Valid latitude and longitude are required', 'doctors': []}, status=status.HTTP_400_BAD_REQUEST)

        # Convert radius from km to meters for Google Maps API
        radius_meters = int(radius_km * 1000)
        
        print(f"\n{'='*70}")
        print(f"🏥 NEARBY DOCTORS API ENDPOINT CALLED")
        print(f"  📍 Location: {lat}, {lng}")
        print(f"  📏 Radius: {radius_km} km ({radius_meters} meters)")
        print(f"  🩺 Specialization: {specialization or 'Any'}")
        print(f"{'='*70}\n")
        
        # Fetch doctors from Google Places API and database
        doctors = search_doctors_google_places(lat, lng, radius_meters, specialization)
        
        print(f"📊 Total doctors found: {len(doctors)}\n")
        
        return Response({'doctors': doctors})


class SaveUserLocationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            lat = float(request.data.get('latitude'))
            lng = float(request.data.get('longitude'))
        except (ValueError, TypeError):
            return Response({'error': 'Invalid latitude or longitude'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.latitude = lat
        request.user.longitude = lng
        request.user.save()
        return Response({'success': True, 'message': 'Location saved successfully'})

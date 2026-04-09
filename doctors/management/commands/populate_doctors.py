from django.core.management.base import BaseCommand
from doctors.models import Doctor


DOCTORS_DATA = [
    # ────── MUMBAI CARDIOLOGISTS ──────
    {"name": "Dr. Rajesh Verma", "specialization": "Cardiologist", "hospital_name": "Apollo Hospitals Mumbai", "license_number": "MH-CARD-001", "years_experience": 18, "phone": "9876543210", "email": "rajesh.verma@apollo.com", "address": "Navi Peth, Pune Road, Mumbai", "latitude": 19.0176, "longitude": 72.8271, "city": "Mumbai", "rating": 4.8, "consultation_fee": 1200},
    {"name": "Dr. Anita Sharma", "specialization": "Cardiologist", "hospital_name": "Fortis Hospital Mulund", "license_number": "MH-CARD-002", "years_experience": 15, "phone": "9876543211", "email": "anita.sharma@fortis.com", "address": "Mulund East, Mumbai", "latitude": 19.1731, "longitude": 72.9370, "city": "Mumbai", "rating": 4.7, "consultation_fee": 1100},
    {"name": "Dr. Vikram Saxena", "specialization": "Cardiologist", "hospital_name": "Lilavati Hospital", "license_number": "MH-CARD-003", "years_experience": 20, "phone": "9876543212", "email": "vikram.saxena@lilavati.com", "address": "Bandra, Mumbai", "latitude": 19.0596, "longitude": 72.8295, "city": "Mumbai", "rating": 4.9, "consultation_fee": 1000},
    {"name": "Dr. Priya Gupta", "specialization": "Cardiologist", "hospital_name": "Hinduja Hospital", "license_number": "MH-CARD-004", "years_experience": 12, "phone": "9876543213", "email": "priya.gupta@hinduja.com", "address": "Mahim, Mumbai", "latitude": 19.0427, "longitude": 72.8262, "city": "Mumbai", "rating": 4.6, "consultation_fee": 1150},

    # ────── MUMBAI PULMONOLOGISTS ──────
    {"name": "Dr. Sunita Reddy", "specialization": "Pulmonologist", "hospital_name": "Max Healthcare Mumbai", "license_number": "MH-PULM-001", "years_experience": 14, "phone": "9876543214", "email": "sunita.reddy@maxhealth.com", "address": "Vile Parle East, Mumbai", "latitude": 19.1136, "longitude": 72.8697, "city": "Mumbai", "rating": 4.7, "consultation_fee": 900},
    {"name": "Dr. Rohan Sharma", "specialization": "Pulmonologist", "hospital_name": "Breach Candy Hospital", "license_number": "MH-PULM-002", "years_experience": 16, "phone": "9876543215", "email": "rohan.sharma@breachcandy.com", "address": "Breach Candy, Mumbai", "latitude": 19.0320, "longitude": 72.8266, "city": "Mumbai", "rating": 4.8, "consultation_fee": 950},
    {"name": "Dr. Kavya Patel", "specialization": "Pulmonologist", "hospital_name": "Jupiter Hospital", "license_number": "MH-PULM-003", "years_experience": 11, "phone": "9876543216", "email": "kavya.patel@jupiter.com", "address": "Thane West, Mumbai", "latitude": 19.2183, "longitude": 72.9781, "city": "Mumbai", "rating": 4.5, "consultation_fee": 850},

    # ────── MUMBAI ENDOCRINOLOGISTS ──────
    {"name": "Dr. Deepa Nair", "specialization": "Endocrinologist", "hospital_name": "Kokilaben Hospital", "license_number": "MH-ENDO-001", "years_experience": 13, "phone": "9876543217", "email": "deepa.nair@kokilaben.com", "address": "Mahim, Mumbai", "latitude": 19.0427, "longitude": 72.8262, "city": "Mumbai", "rating": 4.8, "consultation_fee": 1000},
    {"name": "Dr. Mohit Verma", "specialization": "Endocrinologist", "hospital_name": "Global Hospital", "license_number": "MH-ENDO-002", "years_experience": 10, "phone": "9876543218", "email": "mohit.verma@globalhospital.com", "address": "Parel, Mumbai", "latitude": 19.0088, "longitude": 72.8260, "city": "Mumbai", "rating": 4.6, "consultation_fee": 950},
    {"name": "Dr. Anjali Singh", "specialization": "Endocrinologist", "hospital_name": "Nanavati Hospital", "license_number": "MH-ENDO-003", "years_experience": 12, "phone": "9876543219", "email": "anjali.singh@nanavati.com", "address": "Bandra, Mumbai", "latitude": 19.0596, "longitude": 72.8295, "city": "Mumbai", "rating": 4.7, "consultation_fee": 1050},

    # ────── MUMBAI GENERAL PHYSICIANS ──────
    {"name": "Dr. Suresh Kumar", "specialization": "General Physician", "hospital_name": "Holy Family Hospital", "license_number": "MH-GP-001", "years_experience": 15, "phone": "9876543220", "email": "suresh.kumar@holyfamily.com", "address": "Byculla, Mumbai", "latitude": 18.9675, "longitude": 72.8194, "city": "Mumbai", "rating": 4.5, "consultation_fee": 600},
    {"name": "Dr. Neha Gupta", "specialization": "General Physician", "hospital_name": "Prince Aly Khan Hospital", "license_number": "MH-GP-002", "years_experience": 9, "phone": "9876543221", "email": "neha.gupta@princealykhan.com", "address": "Mazagaon, Mumbai", "latitude": 18.9709, "longitude": 72.8347, "city": "Mumbai", "rating": 4.4, "consultation_fee": 550},
    {"name": "Dr. Amit Soni", "specialization": "General Physician", "hospital_name": "SL Raheja Hospital", "license_number": "MH-GP-003", "years_experience": 11, "phone": "9876543222", "email": "amit.soni@raheja.com", "address": "Mahim, Mumbai", "latitude": 19.0427, "longitude": 72.8262, "city": "Mumbai", "rating": 4.6, "consultation_fee": 650},
    {"name": "Dr. Priya Menon", "specialization": "General Physician", "hospital_name": "Mount Elizabeth Hospital", "license_number": "MH-GP-004", "years_experience": 13, "phone": "9876543223", "email": "priya.menon@mountelizabeth.com", "address": "Dadar, Mumbai", "latitude": 19.0176, "longitude": 72.8271, "city": "Mumbai", "rating": 4.7, "consultation_fee": 700},

    # ────── MUMBAI NEUROLOGISTS ──────
    {"name": "Dr. Anil Gupta", "specialization": "Neurologist", "hospital_name": "Wockhardt Hospital", "license_number": "MH-NEURO-001", "years_experience": 17, "phone": "9876543224", "email": "anil.gupta@wockhardt.com", "address": "Mira Road, Mumbai", "latitude": 19.3847, "longitude": 72.7919, "city": "Mumbai", "rating": 4.8, "consultation_fee": 1200},
    {"name": "Dr. Meera Iyer", "specialization": "Neurologist", "hospital_name": "Dr Balabhai Nanavati and HN Reliance Hospital", "license_number": "MH-NEURO-002", "years_experience": 14, "phone": "9876543225", "email": "meera.iyer@nanavati.com", "address": "Bandra, Mumbai", "latitude": 19.0596, "longitude": 72.8295, "city": "Mumbai", "rating": 4.9, "consultation_fee": 1300},

    # ────── MUMBAI ORTHOPEDISTS ──────
    {"name": "Dr. Ravi Verma", "specialization": "Orthopedist", "hospital_name": "Shock Trauma Center", "license_number": "MH-ORTHO-001", "years_experience": 16, "phone": "9876543226", "email": "ravi.verma@shocktrauma.com", "address": "Fort, Mumbai", "latitude": 18.9676, "longitude": 72.8245, "city": "Mumbai", "rating": 4.7, "consultation_fee": 900},
    {"name": "Dr. Rajesh Nair", "specialization": "Orthopedist", "hospital_name": "SSO Hospital", "license_number": "MH-ORTHO-002", "years_experience": 13, "phone": "9876543227", "email": "rajesh.nair@ssohospital.com", "address": "Colaba, Mumbai", "latitude": 18.9550, "longitude": 72.8235, "city": "Mumbai", "rating": 4.6, "consultation_fee": 850},

    # ────── MUMBAI DERMATOLOGISTS ──────
    {"name": "Dr. Rahul Saxena", "specialization": "Dermatologist", "hospital_name": "Skin and You Clinic", "license_number": "MH-DERM-001", "years_experience": 10, "phone": "9876543228", "email": "rahul.saxena@skinandyou.com", "address": "Bandra West, Mumbai", "latitude": 19.0596, "longitude": 72.8295, "city": "Mumbai", "rating": 4.7, "consultation_fee": 800},
    {"name": "Dr. Anjali Malhotra", "specialization": "Dermatologist", "hospital_name": "Laser Centre", "license_number": "MH-DERM-002", "years_experience": 9, "phone": "9876543229", "email": "anjali.malhotra@lasercentre.com", "address": "Lokhandwala, Mumbai", "latitude": 19.1413, "longitude": 72.8378, "city": "Mumbai", "rating": 4.5, "consultation_fee": 750},

    # ────── MUMBAI GASTROENTEROLOGISTS ──────
    {"name": "Dr. Pooja Verma", "specialization": "Gastroenterologist", "hospital_name": "Gastro Care Centre", "license_number": "MH-GASTRO-001", "years_experience": 12, "phone": "9876543230", "email": "pooja.verma@gastrocare.com", "address": "Kala Ghoda, Mumbai", "latitude": 18.9645, "longitude": 72.8319, "city": "Mumbai", "rating": 4.8, "consultation_fee": 1000},
    {"name": "Dr. Sanjay Desai", "specialization": "Gastroenterologist", "hospital_name": "Digestive Disorders Clinic", "license_number": "MH-GASTRO-002", "years_experience": 11, "phone": "9876543231", "email": "sanjay.desai@digestivecare.com", "address": "Grant Road, Mumbai", "latitude": 18.9549, "longitude": 72.8262, "city": "Mumbai", "rating": 4.6, "consultation_fee": 950},

    # ────── MUMBAI NEPHROLOGISTS ──────
    {"name": "Dr. Nikhil Patel", "specialization": "Nephrologist", "hospital_name": "Kidney Care Institute", "license_number": "MH-NEPHR-001", "years_experience": 14, "phone": "9876543232", "email": "nikhil.patel@kidneycare.com", "address": "Dadar East, Mumbai", "latitude": 19.0176, "longitude": 72.8271, "city": "Mumbai", "rating": 4.7, "consultation_fee": 1050},
    {"name": "Dr. Isha Kumar", "specialization": "Nephrologist", "hospital_name": "Renal Health Centre", "license_number": "MH-NEPHR-002", "years_experience": 10, "phone": "9876543233", "email": "isha.kumar@renalhealth.com", "address": "Thane, Mumbai", "latitude": 19.2183, "longitude": 72.9781, "city": "Mumbai", "rating": 4.5, "consultation_fee": 950},

    # ────── MUMBAI PSYCHIATRISTS ──────
    {"name": "Dr. Arjun Singh", "specialization": "Psychiatrist", "hospital_name": "Minds Matter Clinic", "license_number": "MH-PSYCH-001", "years_experience": 13, "phone": "9876543234", "email": "arjun.singh@mindsmatter.com", "address": "Powai, Mumbai", "latitude": 19.1136, "longitude": 72.9045, "city": "Mumbai", "rating": 4.6, "consultation_fee": 850},
    {"name": "Dr. Divya Sharma", "specialization": "Psychiatrist", "hospital_name": "Mental Health Associates", "license_number": "MH-PSYCH-002", "years_experience": 11, "phone": "9876543235", "email": "divya.sharma@mha.com", "address": "Kala Ghoda, Mumbai", "latitude": 18.9645, "longitude": 72.8319, "city": "Mumbai", "rating": 4.8, "consultation_fee": 900},
]


class Command(BaseCommand):
    help = 'Populate database with sample doctors data'

    def handle(self, *args, **kwargs):
        created = 0
        for data in DOCTORS_DATA:
            doc, made = Doctor.objects.get_or_create(
                license_number=data['license_number'],
                defaults=data
            )
            if made:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully created {created} doctors ({len(DOCTORS_DATA) - created} already existed)'))

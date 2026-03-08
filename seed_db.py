#!/usr/bin/env python3
"""
IN-GRES Database Initialization and Seeding Script
Creates SQLite database with all Indian states, districts, and groundwater data
"""

import sqlite3
import random
import os

DB_PATH = 'ingres.db'

# Comprehensive list of Indian States and Union Territories with their districts
STATES_DATA = {
    # Andhra Pradesh
    "Andhra Pradesh": ["Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", 
                       "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam",
                       "Vizianagaram", "West Godavari", "YSR Kadapa"],
    
    # Arunachal Pradesh
    "Arunachal Pradesh": ["Tawang", "West Kameng", "East Kameng", "Papum Pare", "Kurung Kumey",
                          "Kra Daadi", "Lower Subansiri", "Upper Subansiri", "West Siang",
                          "East Siang", "Siang", "Upper Siang", "Lower Siang", "Lower Dibang Valley",
                          "Dibang Valley", "Anjaw", "Lohit", "Namsai", "Changlang", "Tirap", "Longding"],
    
    # Assam
    "Assam": ["Baksa", "Barpeta", "Biswanath", "Bongaigaon", "Cachar", "Charaideo",
              "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao",
              "Goalpara", "Golaghat", "Hailakandi", "Hojai", "Jorhat", "Kamrup",
              "Kamrup Metropolitan", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur",
              "Majuli", "Morigaon", "Nagaon", "Nalbari", "Sivasagar", "Sonitpur", "South Salmara",
              "Tinsukia", "Udalguri", "West Karbi Anglong"],
    
    # Bihar
    "Bihar": ["Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur",
              "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj",
              "Jamui", "Jehanabad", "Kaimur", "Katihar", "Khagaria", "Kishanganj",
              "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda",
              "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran",
              "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran"],
    
    # Chhattisgarh
    "Chhattisgarh": ["Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur",
                     "Bilaspur", "Dantewada", "Dhamtari", "Durg", "Gariaband", "Janjgir-Champa",
                     "Jashpur", "Kanker", "Kabirdham", "Kondagaon", "Korba", "Koriya",
                     "Mahasamund", "Mungeli", "Narayanpur", "Raigarh", "Raipur", "Rajnandgaon",
                     "Sukma", "Surajpur", "Surguja"],
    
    # Goa
    "Goa": ["North Goa", "South Goa"],
    
    # Gujarat
    "Gujarat": ["Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch",
                "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhumi Dwarka",
                "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch",
                "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal",
                "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar",
                "Tapi", "Vadodara", "Valsad"],
    
    # Haryana
    "Haryana": ["Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram",
                "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra",
                "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari",
                "Rohtak", "Sirsa", "Sonipat", "Yamunanagar"],
    
    # Himachal Pradesh
    "Himachal Pradesh": ["Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu",
                         "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur", "Solan", "Una"],
    
    # Jharkhand
    "Jharkhand": ["Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum",
                  "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribag", "Jamtara",
                  "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu",
                  "Ramgarh", "Ranchi", "Sahebganj", "Seraikela Kharsawan", "Simdega", "West Singhbhum"],
    
    # Karnataka
    "Karnataka": ["Bagalkot", "Bangalore Rural", "Bangalore Urban", "Belagavi", "Ballari",
                  "Bidar", "Vijayapura", "Chamarajanagar", "Chikballapur", "Chikkamagaluru",
                  "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag",
                  "Gulbarga", "Hassan", "Haveri", "Kodagu", "Kolar", "Koppal",
                  "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga", "Tumakuru",
                  "Udupi", "Uttara Kannada", "Yadgir"],
    
    # Kerala
    "Kerala": ["Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam",
               "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta",
               "Thiruvananthapuram", "Thrissur", "Wayanad"],
    
    # Madhya Pradesh
    "Madhya Pradesh": ["Agar Malwa", "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat",
                       "Barwani", "Betul", "Bhind", "Bhopal", "Burhanpur", "Chhatarpur",
                       "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori",
                       "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur",
                       "Jhabua", "Katni", "Khandwa", "Khargone", "Mandla", "Mandsaur",
                       "Morena", "Narsinghpur", "Neemuch", "Panna", "Raisen", "Rajgarh",
                       "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni", "Shahdol",
                       "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh",
                       "Ujjain", "Umaria", "Vidisha"],
    
    # Maharashtra
    "Maharashtra": ["Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara",
                    "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli",
                    "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban",
                    "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad", "Palghar",
                    "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara",
                    "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal"],
    
    # Manipur
    "Manipur": ["Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West",
                "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl",
                "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul"],
    
    # Meghalaya
    "Meghalaya": ["East Garo Hills", "East Jaintia Hills", "East Khasi Hills",
                  "North Garo Hills", "Ri Bhoi", "South Garo Hills", "South West Garo Hills",
                  "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills"],
    
    # Mizoram
    "Mizoram": ["Aizawl", "Champhai", "Kolasib", "Lawngtlai", "Lunglei", "Mamit",
                "Saiha", "Serchhip"],
    
    # Nagaland
    "Nagaland": ["Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon",
                 "Peren", "Phek", "Tuensang", "Wokha", "Zunheboto"],
    
    # Odisha
    "Odisha": ["Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh",
               "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur",
               "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar",
               "Khordha", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh",
               "Nuapada", "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh"],
    
    # Punjab
    "Punjab": ["Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka",
               "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana",
               "Mansa", "Moga", "Mohali", "Muktsar", "Nawanshahr", "Pathankot", "Patiala",
               "Rupnagar", "Sangrur", "Tarn Taran"],
    
    # Rajasthan
    "Rajasthan": ["Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur",
                  "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa",
                  "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore",
                  "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota", "Nagaur",
                  "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar", "Sirohi",
                  "Sri Ganganagar", "Tonk", "Udaipur"],
    
    # Sikkim
    "Sikkim": ["East Sikkim", "North Sikkim", "South Sikkim", "West Sikkim"],
    
    # Tamil Nadu
    "Tamil Nadu": ["Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
                   "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kanchipuram",
                   "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai",
                   "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai",
                   "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi", "Thanjavur",
                   "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tirupathur",
                   "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore",
                   "Viluppuram", "Virudhunagar"],
    
    # Telangana
    "Telangana": ["Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangoan",
                  "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar",
                  "Khammam", "Komaram Bheem", "Mahabubabad", "Mahbubnagar", "Mancherial",
                  "Medak", "Medchal–Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda",
                  "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla",
                  "Rangareddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy",
                  "Warangal Rural", "Warangal Urban", "Yadadri Bhuvanagiri"],
    
    # Tripura
    "Tripura": ["Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura",
                "Unakoti", "West Tripura"],
    
    # Uttar Pradesh
    "Uttar Pradesh": ["Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya",
                      "Ayodhya", "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur",
                      "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor",
                      "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah",
                      "Etawah", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar",
                      "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur",
                      "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj",
                      "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kushinagar",
                      "Lakhimpur Kheri", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba",
                      "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad",
                      "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Rae Bareli",
                      "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur",
                      "Shamli", "Shrawasti", "Siddharthnagar", "Sitapur", "Sonbhadra",
                      "Sultanpur", "Unnao", "Varanasi"],
    
    # Uttarakhand
    "Uttarakhand": ["Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar",
                    "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal",
                    "Udham Singh Nagar", "Uttarkashi"],
    
    # West Bengal
    "West Bengal": ["Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur",
                    "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong",
                    "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas",
                    "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur",
                    "Purulia", "South 24 Parganas", "Uttar Dinajpur"],
    
    # Union Territories
    "Andaman and Nicobar Islands": ["Nicobar", "North and Middle Andaman", "South Andaman"],
    "Chandigarh": ["Chandigarh"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Dadra and Nagar Haveli", "Daman", "Diu"],
    "Delhi": ["Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi",
              "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi",
              "West Delhi"],
    "Jammu and Kashmir": ["Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal",
                          "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch",
                          "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian",
                          "Srinagar", "Udhampur"],
    "Ladakh": ["Kargil", "Leh"],
    "Lakshadweep": ["Lakshadweep"],
    "Puducherry": ["Karaikal", "Mahe", "Puducherry", "Yanam"]
}

# Aquifer types and geological formations
AQUIFER_TYPES = [
    "Alluvial", "Hard Rock - Granite", "Hard Rock - Basalt", 
    "Hard Rock - Sandstone", "Hard Rock - Limestone", "Hard Rock - Gneiss",
    "Sedimentary", "Coastal Alluvial", "Deltaic Alluvial"
]

# Rock types based on region
ROCK_TYPES_BY_STATE = {
    "Andhra Pradesh": ["Granite", "Gneiss", "Sandstone", "Limestone"],
    "Arunachal Pradesh": ["Gneiss", "Schist", "Granite", "Sandstone"],
    "Assam": ["Alluvium", "Sandstone", "Shale", "Granite"],
    "Bihar": ["Alluvium", "Granite", "Gneiss", "Sandstone"],
    "Chhattisgarh": ["Granite", "Limestone", "Sandstone", "Gneiss"],
    "Goa": ["Basalt", "Granite", "Gneiss"],
    "Gujarat": ["Alluvium", "Basalt", "Limestone", "Sandstone"],
    "Haryana": ["Alluvium", "Granite", "Sandstone"],
    "Himachal Pradesh": ["Granite", "Gneiss", "Limestone", "Sandstone"],
    "Jharkhand": ["Granite", "Gneiss", "Sandstone", "Basalt"],
    "Karnataka": ["Granite", "Gneiss", "Basalt", "Sandstone"],
    "Kerala": ["Gneiss", "Granite", "Laterite", "Alluvium"],
    "Madhya Pradesh": ["Basalt", "Granite", "Sandstone", "Limestone"],
    "Maharashtra": ["Basalt", "Granite", "Gneiss", "Alluvium"],
    "Manipur": ["Sandstone", "Shale", "Limestone", "Gneiss"],
    "Meghalaya": ["Granite", "Gneiss", "Limestone", "Sandstone"],
    "Mizoram": ["Sandstone", "Shale", "Limestone"],
    "Nagaland": ["Sandstone", "Shale", "Granite", "Gneiss"],
    "Odisha": ["Granite", "Gneiss", "Limestone", "Alluvium"],
    "Punjab": ["Alluvium", "Granite", "Sandstone"],
    "Rajasthan": ["Alluvium", "Granite", "Sandstone", "Limestone", "Gneiss"],
    "Sikkim": ["Gneiss", "Granite", "Schist"],
    "Tamil Nadu": ["Granite", "Gneiss", "Sandstone", "Limestone"],
    "Telangana": ["Granite", "Gneiss", "Basalt", "Sandstone"],
    "Tripura": ["Alluvium", "Sandstone", "Shale"],
    "Uttar Pradesh": ["Alluvium", "Granite", "Sandstone"],
    "Uttarakhand": ["Granite", "Gneiss", "Limestone", "Sandstone"],
    "West Bengal": ["Alluvium", "Granite", "Gneiss", "Basalt"],
    "Andaman and Nicobar Islands": ["Limestone", "Sandstone", "Shale"],
    "Chandigarh": ["Alluvium", "Granite"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Basalt", "Alluvium"],
    "Delhi": ["Alluvium", "Granite", "Quartzite"],
    "Jammu and Kashmir": ["Granite", "Gneiss", "Limestone", "Sandstone"],
    "Ladakh": ["Granite", "Gneiss", "Limestone"],
    "Lakshadweep": ["Limestone", "Coral"],
    "Puducherry": ["Alluvium", "Gneiss", "Sandstone"]
}

def get_category(soe):
    """Determine groundwater category based on Stage of Extraction"""
    if soe < 70:
        return "Safe"
    elif soe < 90:
        return "Semi-Critical"
    elif soe <= 100:
        return "Critical"
    else:
        return "Over-exploited"

def generate_realistic_data(state_name, district_name, year):
    """Generate realistic groundwater data based on region characteristics"""
    
    # Regional factors affecting groundwater
    semi_arid_states = ["Rajasthan", "Gujarat", "Haryana", "Punjab", "Delhi", 
                        "Telangana", "Karnataka", "Maharashtra", "Madhya Pradesh"]
    coastal_states = ["Kerala", "Tamil Nadu", "Andhra Pradesh", "Odisha", 
                      "West Bengal", "Goa", "Gujarat", "Maharashtra"]
    himalayan_states = ["Himachal Pradesh", "Uttarakhand", "Jammu and Kashmir", 
                        "Ladakh", "Sikkim", "Arunachal Pradesh", "Meghalaya", 
                        "Nagaland", "Manipur", "Mizoram", "Tripura"]
    
    # Base recharge and extraction based on region
    if state_name in semi_arid_states:
        base_recharge = random.uniform(8000, 25000)  # MCM
        base_extraction = random.uniform(10000, 35000)  # MCM
    elif state_name in coastal_states:
        base_recharge = random.uniform(15000, 40000)  # MCM
        base_extraction = random.uniform(12000, 35000)  # MCM
    elif state_name in himalayan_states:
        base_recharge = random.uniform(5000, 20000)  # MCM
        base_extraction = random.uniform(2000, 12000)  # MCM
    else:
        base_recharge = random.uniform(10000, 30000)  # MCM
        base_extraction = random.uniform(8000, 25000)  # MCM
    
    # Adjust for district size (smaller districts have less resource)
    size_factor = random.uniform(0.3, 1.5)
    
    # Year variation
    year_factor = 1.0 + (year - 2020) * random.uniform(-0.05, 0.05)
    
    # Calculate values
    total_annual_recharge = round(base_recharge * size_factor * year_factor, 2)
    total_extraction = round(base_extraction * size_factor * year_factor * random.uniform(0.6, 1.3), 2)
    
    # Ensure extraction doesn't exceed 150% of recharge for semi-arid, 120% for others
    max_extraction_ratio = 1.5 if state_name in semi_arid_states else 1.2
    if total_extraction > total_annual_recharge * max_extraction_ratio:
        total_extraction = round(total_annual_recharge * random.uniform(0.4, max_extraction_ratio), 2)
    
    # Extractable resource (typically 60-70% of recharge)
    extractable_resource = round(total_annual_recharge * random.uniform(0.60, 0.70), 2)
    
    # Stage of Extraction calculation
    if extractable_resource > 0:
        soe = round((total_extraction / extractable_resource) * 100, 2)
    else:
        soe = 0
    
    # Additional parameters
    monsoon_recharge = round(total_annual_recharge * random.uniform(0.55, 0.70), 2)
    non_monsoon_recharge = round(total_annual_recharge - monsoon_recharge, 2)
    
    irrigation_extraction = round(total_extraction * random.uniform(0.75, 0.90), 2)
    domestic_extraction = round(total_extraction * random.uniform(0.05, 0.15), 2)
    industrial_extraction = round(total_extraction - irrigation_extraction - domestic_extraction, 2)
    
    # Resource availability
    net_availability = round(extractable_resource - total_extraction, 2)
    
    # Water level data
    pre_monsoon_level = round(random.uniform(2.0, 25.0), 2)
    post_monsoon_level = round(pre_monsoon_level - random.uniform(1.0, 6.0), 2)
    if post_monsoon_level < 0.5:
        post_monsoon_level = round(random.uniform(0.5, 3.0), 2)
    
    # Wells data
    dug_wells = random.randint(500, 15000)
    shallow_tubewells = random.randint(200, 8000)
    deep_tubewells = random.randint(50, 3000)
    
    # Aquifer and rock type
    aquifer_type = random.choice(AQUIFER_TYPES)
    rock_types = ROCK_TYPES_BY_STATE.get(state_name, ["Alluvium", "Granite"])
    rock_type = random.choice(rock_types)
    
    # Area data
    geographical_area = round(random.uniform(500, 8000), 2)  # sq km
    cultivable_area = round(geographical_area * random.uniform(0.4, 0.7), 2)
    irrigated_area = round(cultivable_area * random.uniform(0.3, 0.8), 2)
    
    return {
        'assessment_year': year,
        'total_annual_recharge': total_annual_recharge,
        'monsoon_recharge': monsoon_recharge,
        'non_monsoon_recharge': non_monsoon_recharge,
        'total_extraction': total_extraction,
        'irrigation_extraction': irrigation_extraction,
        'domestic_extraction': domestic_extraction,
        'industrial_extraction': industrial_extraction,
        'extractable_resource': extractable_resource,
        'net_availability': net_availability,
        'stage_of_extraction': soe,
        'category': get_category(soe),
        'pre_monsoon_level': pre_monsoon_level,
        'post_monsoon_level': post_monsoon_level,
        'dug_wells': dug_wells,
        'shallow_tubewells': shallow_tubewells,
        'deep_tubewells': deep_tubewells,
        'aquifer_type': aquifer_type,
        'rock_type': rock_type,
        'geographical_area': geographical_area,
        'cultivable_area': cultivable_area,
        'irrigated_area': irrigated_area
    }

def create_database():
    """Create and seed the database with comprehensive data"""
    
    # Remove existing database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE districts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (state_id) REFERENCES states (id),
            UNIQUE(state_id, name)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE assessment_units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            district_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            area_sqkm REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (district_id) REFERENCES districts (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE groundwater_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            district_id INTEGER NOT NULL,
            assessment_year INTEGER NOT NULL,
            total_annual_recharge REAL,
            monsoon_recharge REAL,
            non_monsoon_recharge REAL,
            total_extraction REAL,
            irrigation_extraction REAL,
            domestic_extraction REAL,
            industrial_extraction REAL,
            extractable_resource REAL,
            net_availability REAL,
            stage_of_extraction REAL,
            category TEXT,
            pre_monsoon_level REAL,
            post_monsoon_level REAL,
            dug_wells INTEGER,
            shallow_tubewells INTEGER,
            deep_tubewells INTEGER,
            aquifer_type TEXT,
            rock_type TEXT,
            geographical_area REAL,
            cultivable_area REAL,
            irrigated_area REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (district_id) REFERENCES districts (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE visitor_count (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            count INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Initialize visitor count
    cursor.execute('INSERT INTO visitor_count (count) VALUES (0)')
    
    # Insert states
    state_code_map = {}
    used_codes = set()
    for state_name in STATES_DATA.keys():
        # Generate state code
        words = state_name.split()
        if len(words) == 1:
            base_code = state_name[:3].upper()
        else:
            base_code = ''.join([w[0] for w in words[:3]]).upper()
        
        # Ensure unique code
        code = base_code
        counter = 1
        while code in used_codes:
            code = f"{base_code[:2]}{counter}"
            counter += 1
        used_codes.add(code)
        
        cursor.execute('INSERT INTO states (name, code) VALUES (?, ?)', (state_name, code))
        state_id = cursor.lastrowid
        state_code_map[state_name] = state_id
    
    print(f"Inserted {len(state_code_map)} states")
    
    # Insert districts and generate groundwater data
    total_districts = 0
    total_records = 0
    years = [2020, 2022]
    
    for state_name, districts in STATES_DATA.items():
        state_id = state_code_map[state_name]
        
        for district_name in districts:
            # Insert district
            cursor.execute('''
                INSERT INTO districts (state_id, name, code) 
                VALUES (?, ?, ?)
            ''', (state_id, district_name, f"D{total_districts + 1}"))
            district_id = cursor.lastrowid
            total_districts += 1
            
            # Generate assessment units (2-5 per district)
            num_units = random.randint(2, 5)
            for i in range(num_units):
                unit_name = f"{district_name} Block {i + 1}"
                unit_area = round(random.uniform(100, 500), 2)
                cursor.execute('''
                    INSERT INTO assessment_units (district_id, name, area_sqkm)
                    VALUES (?, ?, ?)
                ''', (district_id, unit_name, unit_area))
            
            # Generate groundwater data for each year
            for year in years:
                data = generate_realistic_data(state_name, district_name, year)
                cursor.execute('''
                    INSERT INTO groundwater_data (
                        district_id, assessment_year, total_annual_recharge,
                        monsoon_recharge, non_monsoon_recharge, total_extraction,
                        irrigation_extraction, domestic_extraction, industrial_extraction,
                        extractable_resource, net_availability, stage_of_extraction,
                        category, pre_monsoon_level, post_monsoon_level,
                        dug_wells, shallow_tubewells, deep_tubewells,
                        aquifer_type, rock_type, geographical_area,
                        cultivable_area, irrigated_area
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    district_id, data['assessment_year'], data['total_annual_recharge'],
                    data['monsoon_recharge'], data['non_monsoon_recharge'], data['total_extraction'],
                    data['irrigation_extraction'], data['domestic_extraction'], data['industrial_extraction'],
                    data['extractable_resource'], data['net_availability'], data['stage_of_extraction'],
                    data['category'], data['pre_monsoon_level'], data['post_monsoon_level'],
                    data['dug_wells'], data['shallow_tubewells'], data['deep_tubewells'],
                    data['aquifer_type'], data['rock_type'], data['geographical_area'],
                    data['cultivable_area'], data['irrigated_area']
                ))
                total_records += 1
    
    print(f"Inserted {total_districts} districts")
    print(f"Inserted {total_records} groundwater records")
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX idx_district_state ON districts(state_id)')
    cursor.execute('CREATE INDEX idx_gw_district ON groundwater_data(district_id)')
    cursor.execute('CREATE INDEX idx_gw_year ON groundwater_data(assessment_year)')
    cursor.execute('CREATE INDEX idx_gw_category ON groundwater_data(category)')
    
    conn.commit()
    conn.close()
    
    print(f"\nDatabase created successfully: {DB_PATH}")
    print(f"Total States/UTs: {len(state_code_map)}")
    print(f"Total Districts: {total_districts}")
    print(f"Total Groundwater Records: {total_records}")

if __name__ == "__main__":
    create_database()

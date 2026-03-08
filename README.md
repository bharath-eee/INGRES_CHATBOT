# IN-GRES: India Groundwater Resource Estimation System

## 📊 Project Overview

IN-GRES (INDIA Groundwater Resource Estimation System) is an AI-powered web application for groundwater resource assessment, built using Python Flask with HTML, CSS, and JavaScript frontend. It implements the GEC-2015 (Ground Water Resource Estimation Committee) methodology for categorizing groundwater assessment units across India.

## 🏗️ Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python Flask |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Database | SQLite |
| API | RESTful JSON API |

## 📁 Project Structure

```
ingres-python/
├── app.py                 # Flask backend with all API endpoints
├── seed_db.py             # Database initialization & seeding
├── manage_data.py         # Data management utility
├── requirements.txt       # Python dependencies
├── README.md              # Documentation
├── templates/
│   └── index.html         # Main single-page application
├── static/
│   ├── css/style.css      # Water-themed responsive styling
│   └── js/app.js          # Frontend logic & API calls
└── ingres.db              # SQLite database (created after seeding)
```

## ✨ Key Features

### 1. 📊 Dashboard Tab
- Overview cards: Total States, Districts, Recharge, Extraction, Avg SoE
- Category distribution: Safe, Semi-Critical, Critical, Over-exploited
- State-wise summary table (clickable for detailed reports)
- GEC-2015 methodology information

### 2. 📁 Data Explorer Tab
- Filter by State, District, Year, Category
- Search functionality for districts and states
- Paginated data table
- Click rows for detailed district reports

### 3. 🤖 AI Assistant Tab
- Natural language queries
- India national overview
- GEC-2015 methodology explanation
- Category distribution analysis
- State-specific reports

### 4. ➕ Add Data Tab
- Add new states and districts
- Add groundwater data records
- Bulk import via API

## 📈 Database Contents

| Entity | Count |
|--------|-------|
| States/UTs | 36 (All Indian States & Union Territories) |
| Districts | ~780 (All districts across India) |
| Assessment Units | ~3,000 |
| Groundwater Records | ~1,500+ (2020 & 2022) |

### States/UTs Included:
- Andhra Pradesh, Arunachal Pradesh, Assam, Bihar, Chhattisgarh, Goa, Gujarat, Haryana, Himachal Pradesh, Jharkhand, Karnataka, Kerala, Madhya Pradesh, Maharashtra, Manipur, Meghalaya, Mizoram, Nagaland, Odisha, Punjab, Rajasthan, Sikkim, Tamil Nadu, Telangana, Tripura, Uttar Pradesh, Uttarakhand, West Bengal
- Union Territories: Andaman and Nicobar Islands, Chandigarh, Dadra and Nagar Haveli and Daman and Diu, Delhi, Jammu and Kashmir, Ladakh, Lakshadweep, Puducherry

## 🔌 API Endpoints

### Page Routes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main application page |

### Data APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/states` | List all states |
| GET | `/api/districts?stateId=` | Districts by state |
| GET | `/api/summary?year=` | Aggregated statistics |
| GET | `/api/groundwater` | Filtered groundwater data |
| GET | `/api/state/<id>` | State GEC report |
| GET | `/api/district/<id>` | District GEC report |
| GET | `/api/india` | National summary |
| GET | `/api/visitor` | Visitor counter |
| GET | `/api/search?q=` | Search districts/states |
| POST | `/api/chat` | AI chatbot endpoint |

### Data Management APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/data/states` | Add new state |
| POST | `/api/data/districts` | Add new district |
| POST | `/api/data/groundwater` | Add groundwater data |
| PUT | `/api/data/groundwater/<id>` | Update groundwater data |
| DELETE | `/api/data/groundwater/<id>` | Delete groundwater data |
| POST | `/api/data/import` | Bulk import data |

## 💧 GEC-2015 Methodology

The system implements the Ground Water Resource Estimation Committee 2015 methodology:

| Category | Stage of Extraction (SoE) |
|----------|---------------------------|
| ✅ Safe | SoE < 70% |
| ⚠️ Semi-Critical | 70% ≤ SoE < 90% |
| 🔴 Critical | 90% ≤ SoE ≤ 100% |
| ❌ Over-exploited | SoE > 100% |

**SoE Formula:** `SoE = (Total Extraction / Total Extractable Resources) × 100`

## 🚀 How to Run

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Installation & Running

```bash
# 1. Navigate to the project directory
cd ingres-python

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create and seed the database (first time only)
python seed_db.py

# 4. Start the Flask server
python app.py
```

The application will be available at: `http://localhost:5000`

### Data Management Utility

```bash
# Show database statistics
python manage_data.py stats

# Export data
python manage_data.py export-states
python manage_data.py export-districts
python manage_data.py export-groundwater --year 2022

# Import data
python manage_data.py import-json data.json

# Add new records
python manage_data.py add-state "New State" "NS"
python manage_data.py add-district 1 "New District"

# Backup & Restore
python manage_data.py backup
python manage_data.py list-backups
python manage_data.py restore ingres_backup_20240101_120000.db
```

## 📝 Sample JSON for Data Import

```json
{
    "states": [
        {"name": "New State", "code": "NS"}
    ],
    "districts": [
        {"name": "New District", "state_id": 1, "code": "ND"}
    ],
    "groundwater": [
        {
            "district_id": 1,
            "assessment_year": 2022,
            "total_annual_recharge": 15000.50,
            "monsoon_recharge": 10000.00,
            "non_monsoon_recharge": 5000.50,
            "total_extraction": 12000.00,
            "irrigation_extraction": 10000.00,
            "domestic_extraction": 1500.00,
            "industrial_extraction": 500.00,
            "extractable_resource": 10500.00,
            "stage_of_extraction": 114.29,
            "pre_monsoon_level": 15.5,
            "post_monsoon_level": 10.2,
            "aquifer_type": "Alluvial",
            "rock_type": "Alluvium"
        }
    ]
}
```

## 🎨 UI Features

- Water-themed blue/teal color scheme
- Government branding (Ministry of Jal Shakti)
- Responsive design (mobile-friendly)
- Interactive category visualization
- Formatted GEC reports with ASCII tables
- Modal dialogs for detailed reports
- Toast notifications for user feedback

## 📊 Data Fields

### Groundwater Data Fields
| Field | Unit | Description |
|-------|------|-------------|
| total_annual_recharge | MCM | Total annual groundwater recharge |
| monsoon_recharge | MCM | Recharge during monsoon season |
| non_monsoon_recharge | MCM | Recharge during non-monsoon season |
| total_extraction | MCM | Total groundwater extraction |
| irrigation_extraction | MCM | Extraction for irrigation |
| domestic_extraction | MCM | Extraction for domestic use |
| industrial_extraction | MCM | Extraction for industrial use |
| extractable_resource | MCM | Extractable groundwater resource |
| net_availability | MCM | Net groundwater availability |
| stage_of_extraction | % | Stage of Extraction percentage |
| pre_monsoon_level | m bgl | Pre-monsoon water level |
| post_monsoon_level | m bgl | Post-monsoon water level |
| dug_wells | count | Number of dug wells |
| shallow_tubewells | count | Number of shallow tubewells |
| deep_tubewells | count | Number of deep tubewells |
| geographical_area | sq km | Total geographical area |
| cultivable_area | sq km | Cultivable land area |
| irrigated_area | sq km | Irrigated land area |

## 🔒 Notes

- The database is created locally as `ingres.db`
- Visitor counter is stored in the database
- Data is generated with realistic values based on regional characteristics
- Categories are automatically calculated based on SoE values

## 📄 License

© 2024 Ministry of Jal Shakti, Government of India. All Rights Reserved.

---

**IN-GRES** - Empowering groundwater resource management through data-driven insights.

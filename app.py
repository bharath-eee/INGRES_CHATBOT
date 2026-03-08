#!/usr/bin/env python3
"""
IN-GRES: INDIA Groundwater Resource Estimation System
Flask Backend Application with RESTful API
"""

from flask import Flask, jsonify, request, render_template, g
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

DATABASE = 'ingres.db'


def get_db():
    """Get database connection for current request"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    """Close database connection at end of request"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def dict_from_row(row):
    """Convert sqlite3.Row to dictionary"""
    return dict(zip(row.keys(), row))


def dict_list_from_rows(rows):
    """Convert list of sqlite3.Row to list of dictionaries"""
    return [dict_from_row(row) for row in rows]


# ============== PAGE ROUTES ==============

@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')


# ============== API ROUTES ==============

@app.route('/api/states', methods=['GET'])
def get_states():
    """Get all states with basic statistics"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT s.id, s.name, s.code,
               COUNT(DISTINCT d.id) as district_count,
               COUNT(DISTINCT au.id) as unit_count
        FROM states s
        LEFT JOIN districts d ON s.id = d.state_id
        LEFT JOIN assessment_units au ON d.id = au.district_id
        GROUP BY s.id
        ORDER BY s.name
    ''')
    
    states = dict_list_from_rows(cursor.fetchall())
    return jsonify(states)


@app.route('/api/districts', methods=['GET'])
def get_districts():
    """Get districts, optionally filtered by state"""
    db = get_db()
    cursor = db.cursor()
    state_id = request.args.get('stateId', type=int)
    
    if state_id:
        cursor.execute('''
            SELECT d.id, d.name, d.code, d.state_id, s.name as state_name
            FROM districts d
            JOIN states s ON d.state_id = s.id
            WHERE d.state_id = ?
            ORDER BY d.name
        ''', (state_id,))
    else:
        cursor.execute('''
            SELECT d.id, d.name, d.code, d.state_id, s.name as state_name
            FROM districts d
            JOIN states s ON d.state_id = s.id
            ORDER BY s.name, d.name
        ''')
    
    districts = dict_list_from_rows(cursor.fetchall())
    return jsonify(districts)


@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Get aggregated statistics for dashboard"""
    db = get_db()
    cursor = db.cursor()
    year = request.args.get('year', default=2022, type=int)
    
    # Overall summary
    cursor.execute('''
        SELECT 
            COUNT(DISTINCT s.id) as total_states,
            COUNT(DISTINCT d.id) as total_districts,
            COUNT(DISTINCT au.id) as total_units,
            SUM(gw.total_annual_recharge) as total_recharge,
            SUM(gw.total_extraction) as total_extraction,
            AVG(gw.stage_of_extraction) as avg_soe,
            SUM(gw.net_availability) as total_net_availability
        FROM groundwater_data gw
        JOIN districts d ON gw.district_id = d.id
        JOIN states s ON d.state_id = s.id
        LEFT JOIN assessment_units au ON d.id = au.district_id
        WHERE gw.assessment_year = ?
    ''', (year,))
    
    summary = dict_from_row(cursor.fetchone())
    
    # Category distribution
    cursor.execute('''
        SELECT 
            category,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM groundwater_data WHERE assessment_year = ?), 2) as percentage
        FROM groundwater_data
        WHERE assessment_year = ?
        GROUP BY category
        ORDER BY 
            CASE category
                WHEN 'Safe' THEN 1
                WHEN 'Semi-Critical' THEN 2
                WHEN 'Critical' THEN 3
                WHEN 'Over-exploited' THEN 4
            END
    ''', (year, year))
    
    categories = dict_list_from_rows(cursor.fetchall())
    
    # State-wise summary
    cursor.execute('''
        SELECT 
            s.id, s.name, s.code,
            COUNT(DISTINCT d.id) as district_count,
            SUM(gw.total_annual_recharge) as total_recharge,
            SUM(gw.total_extraction) as total_extraction,
            ROUND(AVG(gw.stage_of_extraction), 2) as avg_soe,
            SUM(gw.net_availability) as net_availability,
            SUM(CASE WHEN gw.category = 'Safe' THEN 1 ELSE 0 END) as safe_count,
            SUM(CASE WHEN gw.category = 'Semi-Critical' THEN 1 ELSE 0 END) as semi_critical_count,
            SUM(CASE WHEN gw.category = 'Critical' THEN 1 ELSE 0 END) as critical_count,
            SUM(CASE WHEN gw.category = 'Over-exploited' THEN 1 ELSE 0 END) as over_exploited_count
        FROM states s
        JOIN districts d ON s.id = d.state_id
        JOIN groundwater_data gw ON d.id = gw.district_id
        WHERE gw.assessment_year = ?
        GROUP BY s.id
        ORDER BY s.name
    ''', (year,))
    
    state_summary = dict_list_from_rows(cursor.fetchall())
    
    return jsonify({
        'summary': summary,
        'categories': categories,
        'state_summary': state_summary,
        'year': year
    })


@app.route('/api/groundwater', methods=['GET'])
def get_groundwater_data():
    """Get filtered groundwater data with pagination"""
    db = get_db()
    cursor = db.cursor()
    
    # Filters
    state_id = request.args.get('stateId', type=int)
    district_id = request.args.get('districtId', type=int)
    year = request.args.get('year', type=int)
    category = request.args.get('category')
    search = request.args.get('search', '').strip()
    
    # Pagination
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('perPage', default=20, type=int)
    offset = (page - 1) * per_page
    
    # Build query
    base_query = '''
        SELECT 
            gw.id, gw.assessment_year, gw.category,
            gw.total_annual_recharge, gw.total_extraction,
            gw.stage_of_extraction, gw.net_availability,
            gw.pre_monsoon_level, gw.post_monsoon_level,
            gw.aquifer_type, gw.rock_type,
            d.id as district_id, d.name as district_name,
            s.id as state_id, s.name as state_name, s.code as state_code
        FROM groundwater_data gw
        JOIN districts d ON gw.district_id = d.id
        JOIN states s ON d.state_id = s.id
        WHERE 1=1
    '''
    
    params = []
    
    if state_id:
        base_query += ' AND s.id = ?'
        params.append(state_id)
    
    if district_id:
        base_query += ' AND d.id = ?'
        params.append(district_id)
    
    if year:
        base_query += ' AND gw.assessment_year = ?'
        params.append(year)
    
    if category:
        base_query += ' AND gw.category = ?'
        params.append(category)
    
    if search:
        base_query += ' AND (d.name LIKE ? OR s.name LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    
    # Get total count
    count_query = f'SELECT COUNT(*) as total FROM ({base_query})'
    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']
    
    # Get paginated data
    data_query = base_query + ' ORDER BY s.name, d.name, gw.assessment_year LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    cursor.execute(data_query, params)
    
    data = dict_list_from_rows(cursor.fetchall())
    
    return jsonify({
        'data': data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': (total + per_page - 1) // per_page
        }
    })


@app.route('/api/state/<int:state_id>', methods=['GET'])
def get_state_report(state_id):
    """Get detailed GEC report for a state"""
    db = get_db()
    cursor = db.cursor()
    year = request.args.get('year', default=2022, type=int)
    
    # State info
    cursor.execute('SELECT * FROM states WHERE id = ?', (state_id,))
    state = cursor.fetchone()
    if not state:
        return jsonify({'error': 'State not found'}), 404
    
    state = dict_from_row(state)
    
    # District-wise data
    cursor.execute('''
        SELECT 
            d.id, d.name,
            gw.total_annual_recharge, gw.monsoon_recharge, gw.non_monsoon_recharge,
            gw.total_extraction, gw.irrigation_extraction, gw.domestic_extraction, gw.industrial_extraction,
            gw.extractable_resource, gw.net_availability, gw.stage_of_extraction, gw.category,
            gw.pre_monsoon_level, gw.post_monsoon_level,
            gw.dug_wells, gw.shallow_tubewells, gw.deep_tubewells,
            gw.aquifer_type, gw.rock_type
        FROM districts d
        JOIN groundwater_data gw ON d.id = gw.district_id
        WHERE d.state_id = ? AND gw.assessment_year = ?
        ORDER BY d.name
    ''', (state_id, year))
    
    districts = dict_list_from_rows(cursor.fetchall())
    
    # State totals
    cursor.execute('''
        SELECT 
            SUM(total_annual_recharge) as total_recharge,
            SUM(total_extraction) as total_extraction,
            AVG(stage_of_extraction) as avg_soe,
            SUM(net_availability) as net_availability,
            SUM(CASE WHEN category = 'Safe' THEN 1 ELSE 0 END) as safe_count,
            SUM(CASE WHEN category = 'Semi-Critical' THEN 1 ELSE 0 END) as semi_critical_count,
            SUM(CASE WHEN category = 'Critical' THEN 1 ELSE 0 END) as critical_count,
            SUM(CASE WHEN category = 'Over-exploited' THEN 1 ELSE 0 END) as over_exploited_count
        FROM groundwater_data gw
        JOIN districts d ON gw.district_id = d.id
        WHERE d.state_id = ? AND gw.assessment_year = ?
    ''', (state_id, year))
    
    totals = dict_from_row(cursor.fetchone())
    
    return jsonify({
        'state': state,
        'districts': districts,
        'totals': totals,
        'year': year
    })


@app.route('/api/district/<int:district_id>', methods=['GET'])
def get_district_report(district_id):
    """Get detailed GEC report for a district"""
    db = get_db()
    cursor = db.cursor()
    year = request.args.get('year', default=2022, type=int)
    
    # District info
    cursor.execute('''
        SELECT d.*, s.name as state_name, s.code as state_code
        FROM districts d
        JOIN states s ON d.state_id = s.id
        WHERE d.id = ?
    ''', (district_id,))
    
    district = cursor.fetchone()
    if not district:
        return jsonify({'error': 'District not found'}), 404
    
    district = dict_from_row(district)
    
    # Groundwater data
    cursor.execute('''
        SELECT * FROM groundwater_data
        WHERE district_id = ? AND assessment_year = ?
    ''', (district_id, year))
    
    gw_data = cursor.fetchone()
    if not gw_data:
        return jsonify({'error': 'No data found for this district'}), 404
    
    gw_data = dict_from_row(gw_data)
    
    # Assessment units
    cursor.execute('''
        SELECT * FROM assessment_units
        WHERE district_id = ?
    ''', (district_id,))
    
    units = dict_list_from_rows(cursor.fetchall())
    
    return jsonify({
        'district': district,
        'groundwater': gw_data,
        'assessment_units': units,
        'year': year
    })


@app.route('/api/india', methods=['GET'])
def get_india_summary():
    """Get national summary statistics"""
    db = get_db()
    cursor = db.cursor()
    year = request.args.get('year', default=2022, type=int)
    
    # National totals
    cursor.execute('''
        SELECT 
            COUNT(DISTINCT s.id) as total_states,
            COUNT(DISTINCT d.id) as total_districts,
            COUNT(DISTINCT au.id) as total_units,
            SUM(total_annual_recharge) as total_recharge,
            SUM(total_extraction) as total_extraction,
            AVG(stage_of_extraction) as avg_soe,
            SUM(net_availability) as net_availability,
            SUM(CASE WHEN category = 'Safe' THEN 1 ELSE 0 END) as safe_count,
            SUM(CASE WHEN category = 'Semi-Critical' THEN 1 ELSE 0 END) as semi_critical_count,
            SUM(CASE WHEN category = 'Critical' THEN 1 ELSE 0 END) as critical_count,
            SUM(CASE WHEN category = 'Over-exploited' THEN 1 ELSE 0 END) as over_exploited_count
        FROM groundwater_data gw
        JOIN districts d ON gw.district_id = d.id
        JOIN states s ON d.state_id = s.id
        LEFT JOIN assessment_units au ON d.id = au.district_id
        WHERE gw.assessment_year = ?
    ''', (year,))
    
    summary = dict_from_row(cursor.fetchone())
    
    # Year comparison
    cursor.execute('''
        SELECT 
            assessment_year,
            SUM(total_annual_recharge) as total_recharge,
            SUM(total_extraction) as total_extraction,
            AVG(stage_of_extraction) as avg_soe
        FROM groundwater_data
        GROUP BY assessment_year
        ORDER BY assessment_year
    ''')
    
    yearly_trend = dict_list_from_rows(cursor.fetchall())
    
    return jsonify({
        'summary': summary,
        'yearly_trend': yearly_trend,
        'year': year
    })


@app.route('/api/visitor', methods=['GET'])
def get_visitor_count():
    """Get and increment visitor count"""
    db = get_db()
    cursor = db.cursor()
    
    # Increment count
    cursor.execute('UPDATE visitor_count SET count = count + 1, last_updated = ? WHERE id = 1',
                   (datetime.now(),))
    db.commit()
    
    # Get count
    cursor.execute('SELECT count, last_updated FROM visitor_count WHERE id = 1')
    result = dict_from_row(cursor.fetchone())
    
    return jsonify(result)


@app.route('/api/search', methods=['GET'])
def search_entities():
    """Search districts and states"""
    db = get_db()
    cursor = db.cursor()
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'districts': [], 'states': []})
    
    # Search districts
    cursor.execute('''
        SELECT d.id, d.name, s.name as state_name
        FROM districts d
        JOIN states s ON d.state_id = s.id
        WHERE d.name LIKE ?
        ORDER BY d.name
        LIMIT 20
    ''', (f'%{query}%',))
    
    districts = dict_list_from_rows(cursor.fetchall())
    
    # Search states
    cursor.execute('''
        SELECT id, name, code
        FROM states
        WHERE name LIKE ?
        ORDER BY name
        LIMIT 10
    ''', (f'%{query}%',))
    
    states = dict_list_from_rows(cursor.fetchall())
    
    return jsonify({
        'districts': districts,
        'states': states,
        'query': query
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """AI Chatbot endpoint for natural language queries"""
    data = request.get_json()
    user_message = data.get('message', '').lower().strip()
    
    db = get_db()
    cursor = db.cursor()
    
    # Get context data
    cursor.execute('''
        SELECT 
            COUNT(DISTINCT s.id) as total_states,
            COUNT(DISTINCT d.id) as total_districts,
            SUM(gw.total_annual_recharge) as total_recharge,
            SUM(gw.total_extraction) as total_extraction,
            AVG(gw.stage_of_extraction) as avg_soe,
            SUM(CASE WHEN gw.category = 'Safe' THEN 1 ELSE 0 END) as safe,
            SUM(CASE WHEN gw.category = 'Semi-Critical' THEN 1 ELSE 0 END) as semi_critical,
            SUM(CASE WHEN gw.category = 'Critical' THEN 1 ELSE 0 END) as critical,
            SUM(CASE WHEN gw.category = 'Over-exploited' THEN 1 ELSE 0 END) as over_exploited
        FROM groundwater_data gw
        JOIN districts d ON gw.district_id = d.id
        JOIN states s ON d.state_id = s.id
        WHERE gw.assessment_year = 2022
    ''')
    
    india_stats = dict_from_row(cursor.fetchone())
    
    response = ""
    
    # Simple NLP for common queries
    if any(word in user_message for word in ['hello', 'hi', 'hey', 'namaste']):
        response = f"""🙏 Namaste! Welcome to IN-GRES - India Groundwater Resource Estimation System.

I can help you with:
• Groundwater statistics for India, states, and districts
• GEC-2015 methodology explanation
• Category-wise distribution of assessment units
• State and district reports

**India Overview (2022):**
- Total States/UTs: {india_stats['total_states']}
- Total Districts: {india_stats['total_districts']}
- Total Annual Recharge: {india_stats['total_recharge']:,.2f} MCM
- Total Extraction: {india_stats['total_extraction']:,.2f} MCM
- Average Stage of Extraction: {india_stats['avg_soe']:.2f}%

How can I assist you today?"""
    
    elif any(word in user_message for word in ['india', 'national', 'country', 'overview']):
        response = f"""🇮🇳 **India Groundwater Overview (2022)**

**Basic Statistics:**
• States/UTs: {india_stats['total_states']}
• Districts: {india_stats['total_districts']}
• Total Annual Recharge: {india_stats['total_recharge']:,.2f} Million Cubic Metres (MCM)
• Total Extraction: {india_stats['total_extraction']:,.2f} MCM
• Net Groundwater Availability: {india_stats['total_recharge'] - india_stats['total_extraction']:,.2f} MCM

**Category Distribution:**
✅ Safe: {india_stats['safe']} units
⚠️ Semi-Critical: {india_stats['semi_critical']} units
🔴 Critical: {india_stats['critical']} units
❌ Over-exploited: {india_stats['over_exploited']} units

**Average Stage of Extraction:** {india_stats['avg_soe']:.2f}%"""
    
    elif any(word in user_message for word in ['gec', 'methodology', 'formula', 'stage']):
        response = """📊 **GEC-2015 Methodology**

The Ground Water Resource Estimation Committee (GEC-2015) methodology is used for assessing groundwater resources in India.

**Stage of Extraction (SoE) Formula:**
```
SoE = (Total Extraction / Extractable Resources) × 100
```

**Category Classification:**
| Category | Stage of Extraction |
|----------|---------------------|
| ✅ Safe | SoE < 70% |
| ⚠️ Semi-Critical | 70% ≤ SoE < 90% |
| 🔴 Critical | 90% ≤ SoE ≤ 100% |
| ❌ Over-exploited | SoE > 100% |

**Key Components:**
1. **Recharge Estimation**: Monsoon and Non-monsoon recharge
2. **Extraction Assessment**: Irrigation, Domestic, Industrial use
3. **Resource Availability**: Net groundwater available for future use

**Data Sources:**
- Central Ground Water Board (CGWB)
- State Ground Water Departments
- Census data for domestic water use"""
    
    elif any(word in user_message for word in ['safe', 'critical', 'category', 'categories']):
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM groundwater_data
            WHERE assessment_year = 2022
            GROUP BY category
        ''')
        categories = dict_list_from_rows(cursor.fetchall())
        
        response = "📊 **Category-wise Distribution (2022)**\n\n"
        for cat in categories:
            emoji = {'Safe': '✅', 'Semi-Critical': '⚠️', 'Critical': '🔴', 'Over-exploited': '❌'}.get(cat['category'], '📍')
            response += f"{emoji} **{cat['category']}**: {cat['count']} assessment units\n"
        
        response += "\n**GEC-2015 Classification:**\n"
        response += "• Safe: SoE < 70% - Groundwater development can continue\n"
        response += "• Semi-Critical: 70-90% - Careful monitoring required\n"
        response += "• Critical: 90-100% - Strict regulation needed\n"
        response += "• Over-exploited: >100% - Immediate intervention required"
    
    elif 'report' in user_message:
        # Try to find state or district
        words = user_message.replace('report', '').strip()
        if words:
            cursor.execute('''
                SELECT id, name FROM states WHERE LOWER(name) LIKE ?
            ''', (f'%{words}%',))
            state = cursor.fetchone()
            
            if state:
                state = dict_from_row(state)
                cursor.execute('''
                    SELECT COUNT(*) as count, 
                           SUM(CASE WHEN category = 'Safe' THEN 1 ELSE 0 END) as safe,
                           SUM(CASE WHEN category = 'Critical' THEN 1 ELSE 0 END) as critical,
                           SUM(CASE WHEN category = 'Over-exploited' THEN 1 ELSE 0 END) as over
                    FROM groundwater_data gw
                    JOIN districts d ON gw.district_id = d.id
                    WHERE d.state_id = ? AND gw.assessment_year = 2022
                ''', (state['id'],))
                stats = dict_from_row(cursor.fetchone())
                
                response = f"📋 **{state['name']} Groundwater Report (2022)**\n\n"
                response += f"• Total Assessment Units: {stats['count']}\n"
                response += f"✅ Safe: {stats['safe']}\n"
                response += f"🔴 Critical: {stats['critical']}\n"
                response += f"❌ Over-exploited: {stats['over']}\n\n"
                response += "Click on the state in the dashboard for detailed report."
            else:
                response = f"No state found matching '{words}'. Please try a different name."
        else:
            response = "Please specify a state name for the report. Example: 'Rajasthan report'"
    
    elif any(word in user_message for word in ['help', 'what can', 'how to']):
        response = """🤖 **IN-GRES AI Assistant Help**

I can help you with the following:

**1. India Overview:**
• "Tell me about India groundwater"
• "National statistics"

**2. GEC Methodology:**
• "Explain GEC-2015"
• "What is Stage of Extraction?"

**3. Category Information:**
• "Show category distribution"
• "How many critical areas?"

**4. State Reports:**
• "Rajasthan report"
• "Punjab groundwater status"

**5. District Reports:**
• "Jaipur district report"
• "Gurgaon groundwater data"

**Tips:**
• Use natural language to ask questions
• Click on states/districts in the dashboard for detailed reports
• Use the Data Explorer tab for filtered queries"""
    
    else:
        # Default response with suggestions
        response = f"""I understand you're asking about: "{user_message}"

Here are some things I can help with:
• "India overview" - National groundwater statistics
• "GEC methodology" - Explanation of assessment methodology
• "Category distribution" - Safe/Critical/Over-exploited areas
• "[State name] report" - State-specific groundwater report
• "Help" - Show available commands

Would you like to know more about any of these?"""
    
    return jsonify({'response': response})


# ============== DATA MANAGEMENT ROUTES ==============

@app.route('/api/data/states', methods=['POST'])
def add_state():
    """Add a new state"""
    db = get_db()
    cursor = db.cursor()
    data = request.get_json()
    
    name = data.get('name', '').strip()
    code = data.get('code', '').strip().upper()
    
    if not name or not code:
        return jsonify({'error': 'Name and code are required'}), 400
    
    try:
        cursor.execute('INSERT INTO states (name, code) VALUES (?, ?)', (name, code))
        db.commit()
        return jsonify({'id': cursor.lastrowid, 'name': name, 'code': code}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'State already exists'}), 409


@app.route('/api/data/districts', methods=['POST'])
def add_district():
    """Add a new district"""
    db = get_db()
    cursor = db.cursor()
    data = request.get_json()
    
    name = data.get('name', '').strip()
    state_id = data.get('state_id')
    code = data.get('code', '').strip()
    
    if not name or not state_id:
        return jsonify({'error': 'Name and state_id are required'}), 400
    
    try:
        cursor.execute('INSERT INTO districts (name, state_id, code) VALUES (?, ?, ?)',
                       (name, state_id, code))
        db.commit()
        return jsonify({'id': cursor.lastrowid, 'name': name, 'state_id': state_id}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'District already exists in this state'}), 409


@app.route('/api/data/groundwater', methods=['POST'])
def add_groundwater_data():
    """Add groundwater data for a district"""
    db = get_db()
    cursor = db.cursor()
    data = request.get_json()
    
    required_fields = ['district_id', 'assessment_year', 'total_annual_recharge', 
                       'total_extraction', 'stage_of_extraction']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Calculate category if not provided
    if 'category' not in data:
        soe = data['stage_of_extraction']
        if soe < 70:
            data['category'] = 'Safe'
        elif soe < 90:
            data['category'] = 'Semi-Critical'
        elif soe <= 100:
            data['category'] = 'Critical'
        else:
            data['category'] = 'Over-exploited'
    
    try:
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
            data.get('district_id'), data.get('assessment_year'), data.get('total_annual_recharge'),
            data.get('monsoon_recharge'), data.get('non_monsoon_recharge'), data.get('total_extraction'),
            data.get('irrigation_extraction'), data.get('domestic_extraction'), data.get('industrial_extraction'),
            data.get('extractable_resource'), data.get('net_availability'), data.get('stage_of_extraction'),
            data.get('category'), data.get('pre_monsoon_level'), data.get('post_monsoon_level'),
            data.get('dug_wells'), data.get('shallow_tubewells'), data.get('deep_tubewells'),
            data.get('aquifer_type'), data.get('rock_type'), data.get('geographical_area'),
            data.get('cultivable_area'), data.get('irrigated_area')
        ))
        db.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Data added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/groundwater/<int:data_id>', methods=['PUT'])
def update_groundwater_data(data_id):
    """Update groundwater data"""
    db = get_db()
    cursor = db.cursor()
    data = request.get_json()
    
    # Build update query dynamically
    update_fields = []
    values = []
    
    allowed_fields = ['total_annual_recharge', 'monsoon_recharge', 'non_monsoon_recharge',
                      'total_extraction', 'irrigation_extraction', 'domestic_extraction',
                      'industrial_extraction', 'extractable_resource', 'net_availability',
                      'stage_of_extraction', 'category', 'pre_monsoon_level', 'post_monsoon_level',
                      'dug_wells', 'shallow_tubewells', 'deep_tubewells', 'aquifer_type',
                      'rock_type', 'geographical_area', 'cultivable_area', 'irrigated_area']
    
    for field in allowed_fields:
        if field in data:
            update_fields.append(f'{field} = ?')
            values.append(data[field])
    
    if not update_fields:
        return jsonify({'error': 'No fields to update'}), 400
    
    values.append(data_id)
    
    cursor.execute(f'''
        UPDATE groundwater_data 
        SET {', '.join(update_fields)}
        WHERE id = ?
    ''', values)
    
    db.commit()
    
    if cursor.rowcount > 0:
        return jsonify({'message': 'Data updated successfully'})
    else:
        return jsonify({'error': 'Record not found'}), 404


@app.route('/api/data/groundwater/<int:data_id>', methods=['DELETE'])
def delete_groundwater_data(data_id):
    """Delete groundwater data"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('DELETE FROM groundwater_data WHERE id = ?', (data_id,))
    db.commit()
    
    if cursor.rowcount > 0:
        return jsonify({'message': 'Data deleted successfully'})
    else:
        return jsonify({'error': 'Record not found'}), 404


@app.route('/api/data/import', methods=['POST'])
def import_data():
    """Import bulk data"""
    db = get_db()
    cursor = db.cursor()
    data = request.get_json()
    
    results = {'states': 0, 'districts': 0, 'groundwater': 0, 'errors': []}
    
    # Import states
    if 'states' in data:
        for state in data['states']:
            try:
                cursor.execute('INSERT OR IGNORE INTO states (name, code) VALUES (?, ?)',
                               (state['name'], state['code']))
                if cursor.rowcount > 0:
                    results['states'] += 1
            except Exception as e:
                results['errors'].append(f"State import error: {str(e)}")
    
    # Import districts
    if 'districts' in data:
        for district in data['districts']:
            try:
                cursor.execute('INSERT OR IGNORE INTO districts (name, state_id, code) VALUES (?, ?, ?)',
                               (district['name'], district['state_id'], district.get('code')))
                if cursor.rowcount > 0:
                    results['districts'] += 1
            except Exception as e:
                results['errors'].append(f"District import error: {str(e)}")
    
    # Import groundwater data
    if 'groundwater' in data:
        for gw in data['groundwater']:
            try:
                cursor.execute('''
                    INSERT INTO groundwater_data (
                        district_id, assessment_year, total_annual_recharge,
                        monsoon_recharge, non_monsoon_recharge, total_extraction,
                        irrigation_extraction, domestic_extraction, industrial_extraction,
                        extractable_resource, net_availability, stage_of_extraction,
                        category, pre_monsoon_level, post_monsoon_level,
                        dug_wells, shallow_tubewells, deep_tubewells,
                        aquifer_type, rock_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    gw['district_id'], gw['assessment_year'], gw['total_annual_recharge'],
                    gw.get('monsoon_recharge'), gw.get('non_monsoon_recharge'), gw['total_extraction'],
                    gw.get('irrigation_extraction'), gw.get('domestic_extraction'), gw.get('industrial_extraction'),
                    gw.get('extractable_resource'), gw.get('net_availability'), gw['stage_of_extraction'],
                    gw.get('category'), gw.get('pre_monsoon_level'), gw.get('post_monsoon_level'),
                    gw.get('dug_wells'), gw.get('shallow_tubewells'), gw.get('deep_tubewells'),
                    gw.get('aquifer_type'), gw.get('rock_type')
                ))
                results['groundwater'] += 1
            except Exception as e:
                results['errors'].append(f"Groundwater import error: {str(e)}")
    
    db.commit()
    return jsonify(results)


if __name__ == '__main__':
    # Check if database exists
    if not os.path.exists(DATABASE):
        print("Database not found. Please run seed_db.py first.")
        print("Run: python seed_db.py")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

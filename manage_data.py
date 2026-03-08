#!/usr/bin/env python3
"""
IN-GRES Data Management Utility
Tools for managing, importing, and exporting groundwater data

Usage:
    python manage_data.py --help
    python manage_data.py stats                    # Show database statistics
    python manage_data.py export-states            # Export states to JSON
    python manage_data.py export-districts         # Export districts to JSON
    python manage_data.py export-groundwater       # Export groundwater data to JSON
    python manage_data.py import-json file.json    # Import data from JSON
    python manage_data.py add-state "State Name" "CODE"
    python manage_data.py add-district state_id "District Name"
    python manage_data.py update-categories        # Recalculate all categories
    python manage_data.py backup                   # Create database backup
"""

import sqlite3
import json
import os
import sys
import argparse
import shutil
from datetime import datetime

DB_PATH = 'ingres.db'
BACKUP_DIR = 'backups'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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

def show_stats():
    """Display database statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("       IN-GRES Database Statistics")
    print("="*60)
    
    # States count
    cursor.execute('SELECT COUNT(*) as count FROM states')
    states_count = cursor.fetchone()['count']
    print(f"\n🏛️  States/UTs: {states_count}")
    
    # Districts count
    cursor.execute('SELECT COUNT(*) as count FROM districts')
    districts_count = cursor.fetchone()['count']
    print(f"🏘️  Districts: {districts_count}")
    
    # Assessment units count
    cursor.execute('SELECT COUNT(*) as count FROM assessment_units')
    units_count = cursor.fetchone()['count']
    print(f"📊 Assessment Units: {units_count}")
    
    # Groundwater records
    cursor.execute('SELECT COUNT(*) as count FROM groundwater_data')
    records_count = cursor.fetchone()['count']
    print(f"💧 Groundwater Records: {records_count}")
    
    # Records by year
    print("\n📅 Records by Year:")
    cursor.execute('''
        SELECT assessment_year, COUNT(*) as count
        FROM groundwater_data
        GROUP BY assessment_year
        ORDER BY assessment_year
    ''')
    for row in cursor.fetchall():
        print(f"   {row['assessment_year']}: {row['count']} records")
    
    # Category distribution
    print("\n📊 Category Distribution (2022):")
    cursor.execute('''
        SELECT category, COUNT(*) as count
        FROM groundwater_data
        WHERE assessment_year = 2022
        GROUP BY category
        ORDER BY 
            CASE category
                WHEN 'Safe' THEN 1
                WHEN 'Semi-Critical' THEN 2
                WHEN 'Critical' THEN 3
                WHEN 'Over-exploited' THEN 4
            END
    ''')
    for row in cursor.fetchall():
        emoji = {'Safe': '✅', 'Semi-Critical': '⚠️', 'Critical': '🔴', 'Over-exploited': '❌'}.get(row['category'], '📍')
        print(f"   {emoji} {row['category']}: {row['count']}")
    
    # Top 5 states by extraction
    print("\n🚰 Top 5 States by Total Extraction (2022):")
    cursor.execute('''
        SELECT s.name, SUM(gw.total_extraction) as total
        FROM groundwater_data gw
        JOIN districts d ON gw.district_id = d.id
        JOIN states s ON d.state_id = s.id
        WHERE gw.assessment_year = 2022
        GROUP BY s.id
        ORDER BY total DESC
        LIMIT 5
    ''')
    for i, row in enumerate(cursor.fetchall(), 1):
        print(f"   {i}. {row['name']}: {row['total']:,.2f} MCM")
    
    # Over-exploited districts
    print("\n❌ Over-exploited Districts (2022):")
    cursor.execute('''
        SELECT s.name as state, d.name as district, gw.stage_of_extraction
        FROM groundwater_data gw
        JOIN districts d ON gw.district_id = d.id
        JOIN states s ON d.state_id = s.id
        WHERE gw.assessment_year = 2022 AND gw.category = 'Over-exploited'
        ORDER BY gw.stage_of_extraction DESC
        LIMIT 10
    ''')
    for row in cursor.fetchall():
        print(f"   • {row['district']}, {row['state']}: {row['stage_of_extraction']:.1f}%")
    
    # Database file size
    if os.path.exists(DB_PATH):
        size = os.path.getsize(DB_PATH)
        print(f"\n💾 Database Size: {size / 1024:.2f} KB")
    
    conn.close()
    print("\n" + "="*60)

def export_states(output_file='states_export.json'):
    """Export states to JSON file"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM states ORDER BY name')
    states = [dict(zip(row.keys(), row)) for row in cursor.fetchall()]
    
    with open(output_file, 'w') as f:
        json.dump(states, f, indent=2)
    
    conn.close()
    print(f"✅ Exported {len(states)} states to {output_file}")

def export_districts(output_file='districts_export.json'):
    """Export districts to JSON file"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT d.*, s.name as state_name, s.code as state_code
        FROM districts d
        JOIN states s ON d.state_id = s.id
        ORDER BY s.name, d.name
    ''')
    districts = [dict(zip(row.keys(), row)) for row in cursor.fetchall()]
    
    with open(output_file, 'w') as f:
        json.dump(districts, f, indent=2)
    
    conn.close()
    print(f"✅ Exported {len(districts)} districts to {output_file}")

def export_groundwater(output_file='groundwater_export.json', year=None):
    """Export groundwater data to JSON file"""
    conn = get_db()
    cursor = conn.cursor()
    
    if year:
        cursor.execute('''
            SELECT gw.*, d.name as district_name, s.name as state_name
            FROM groundwater_data gw
            JOIN districts d ON gw.district_id = d.id
            JOIN states s ON d.state_id = s.id
            WHERE gw.assessment_year = ?
            ORDER BY s.name, d.name
        ''', (year,))
    else:
        cursor.execute('''
            SELECT gw.*, d.name as district_name, s.name as state_name
            FROM groundwater_data gw
            JOIN districts d ON gw.district_id = d.id
            JOIN states s ON d.state_id = s.id
            ORDER BY s.name, d.name, gw.assessment_year
        ''')
    
    data = [dict(zip(row.keys(), row)) for row in cursor.fetchall()]
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    conn.close()
    print(f"✅ Exported {len(data)} groundwater records to {output_file}")

def import_json(input_file):
    """Import data from JSON file"""
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    conn = get_db()
    cursor = conn.cursor()
    
    results = {'states': 0, 'districts': 0, 'groundwater': 0, 'errors': []}
    
    # Import states
    if 'states' in data:
        for state in data['states']:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO states (name, code)
                    VALUES (?, ?)
                ''', (state['name'], state['code']))
                if cursor.rowcount > 0:
                    results['states'] += 1
            except Exception as e:
                results['errors'].append(f"State {state.get('name', 'unknown')}: {str(e)}")
    
    # Import districts
    if 'districts' in data:
        for district in data['districts']:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO districts (name, state_id, code)
                    VALUES (?, ?, ?)
                ''', (district['name'], district['state_id'], district.get('code')))
                if cursor.rowcount > 0:
                    results['districts'] += 1
            except Exception as e:
                results['errors'].append(f"District {district.get('name', 'unknown')}: {str(e)}")
    
    # Import groundwater data
    if 'groundwater' in data:
        for gw in data['groundwater']:
            try:
                # Calculate category if not provided
                if 'category' not in gw and 'stage_of_extraction' in gw:
                    gw['category'] = get_category(gw['stage_of_extraction'])
                
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
                    gw['district_id'], gw['assessment_year'], gw.get('total_annual_recharge'),
                    gw.get('monsoon_recharge'), gw.get('non_monsoon_recharge'), gw.get('total_extraction'),
                    gw.get('irrigation_extraction'), gw.get('domestic_extraction'), gw.get('industrial_extraction'),
                    gw.get('extractable_resource'), gw.get('net_availability'), gw.get('stage_of_extraction'),
                    gw.get('category'), gw.get('pre_monsoon_level'), gw.get('post_monsoon_level'),
                    gw.get('dug_wells'), gw.get('shallow_tubewells'), gw.get('deep_tubewells'),
                    gw.get('aquifer_type'), gw.get('rock_type'), gw.get('geographical_area'),
                    gw.get('cultivable_area'), gw.get('irrigated_area')
                ))
                results['groundwater'] += 1
            except Exception as e:
                results['errors'].append(f"Groundwater record: {str(e)}")
    
    conn.commit()
    conn.close()
    
    print("\n📥 Import Results:")
    print(f"   States added: {results['states']}")
    print(f"   Districts added: {results['districts']}")
    print(f"   Groundwater records added: {results['groundwater']}")
    if results['errors']:
        print(f"\n⚠️ Errors ({len(results['errors'])}):")
        for err in results['errors'][:10]:
            print(f"   - {err}")

def add_state(name, code):
    """Add a new state"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO states (name, code) VALUES (?, ?)', (name, code.upper()))
        conn.commit()
        state_id = cursor.lastrowid
        print(f"✅ Added state: {name} (ID: {state_id}, Code: {code.upper()})")
    except sqlite3.IntegrityError:
        print(f"❌ State already exists: {name}")
    finally:
        conn.close()

def add_district(state_id, name):
    """Add a new district"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO districts (name, state_id) VALUES (?, ?)', (name, state_id))
        conn.commit()
        district_id = cursor.lastrowid
        print(f"✅ Added district: {name} (ID: {district_id}, State ID: {state_id})")
    except sqlite3.IntegrityError:
        print(f"❌ District already exists in this state: {name}")
    finally:
        conn.close()

def update_categories():
    """Recalculate all categories based on SoE"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE groundwater_data
        SET category = CASE
            WHEN stage_of_extraction < 70 THEN 'Safe'
            WHEN stage_of_extraction < 90 THEN 'Semi-Critical'
            WHEN stage_of_extraction <= 100 THEN 'Critical'
            ELSE 'Over-exploited'
        END
    ''')
    
    updated = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"✅ Updated categories for {updated} records")

def create_backup():
    """Create a backup of the database"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'ingres_backup_{timestamp}.db')
    
    shutil.copy2(DB_PATH, backup_file)
    print(f"✅ Backup created: {backup_file}")

def list_backups():
    """List all available backups"""
    if not os.path.exists(BACKUP_DIR):
        print("No backups found.")
        return
    
    backups = [f for f in os.listdir(BACKUP_DIR) if f.startswith('ingres_backup_')]
    
    if not backups:
        print("No backups found.")
        return
    
    print("\n📋 Available Backups:")
    for backup in sorted(backups, reverse=True):
        path = os.path.join(BACKUP_DIR, backup)
        size = os.path.getsize(path) / 1024
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        print(f"   {backup} ({size:.1f} KB, {mtime})")

def restore_backup(backup_file):
    """Restore database from backup"""
    backup_path = os.path.join(BACKUP_DIR, backup_file)
    
    if not os.path.exists(backup_path):
        print(f"❌ Backup not found: {backup_file}")
        return
    
    # Create backup of current database
    if os.path.exists(DB_PATH):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        current_backup = f'ingres_pre_restore_{timestamp}.db'
        shutil.copy2(DB_PATH, current_backup)
        print(f"💾 Current database saved as: {current_backup}")
    
    shutil.copy2(backup_path, DB_PATH)
    print(f"✅ Restored database from: {backup_file}")

def main():
    parser = argparse.ArgumentParser(
        description='IN-GRES Data Management Utility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python manage_data.py stats
    python manage_data.py export-groundwater --year 2022
    python manage_data.py import-json data.json
    python manage_data.py add-state "New State" "NS"
    python manage_data.py backup
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')
    
    # Export commands
    export_states_parser = subparsers.add_parser('export-states', help='Export states to JSON')
    export_states_parser.add_argument('-o', '--output', default='states_export.json', help='Output file')
    
    export_districts_parser = subparsers.add_parser('export-districts', help='Export districts to JSON')
    export_districts_parser.add_argument('-o', '--output', default='districts_export.json', help='Output file')
    
    export_gw_parser = subparsers.add_parser('export-groundwater', help='Export groundwater data to JSON')
    export_gw_parser.add_argument('-o', '--output', default='groundwater_export.json', help='Output file')
    export_gw_parser.add_argument('--year', type=int, help='Filter by year')
    
    # Import command
    import_parser = subparsers.add_parser('import-json', help='Import data from JSON file')
    import_parser.add_argument('file', help='JSON file to import')
    
    # Add commands
    add_state_parser = subparsers.add_parser('add-state', help='Add a new state')
    add_state_parser.add_argument('name', help='State name')
    add_state_parser.add_argument('code', help='State code (2-3 letters)')
    
    add_district_parser = subparsers.add_parser('add-district', help='Add a new district')
    add_district_parser.add_argument('state_id', type=int, help='State ID')
    add_district_parser.add_argument('name', help='District name')
    
    # Update command
    subparsers.add_parser('update-categories', help='Recalculate all categories')
    
    # Backup commands
    subparsers.add_parser('backup', help='Create database backup')
    subparsers.add_parser('list-backups', help='List available backups')
    
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('backup_file', help='Backup file name')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == 'stats':
        show_stats()
    elif args.command == 'export-states':
        export_states(args.output)
    elif args.command == 'export-districts':
        export_districts(args.output)
    elif args.command == 'export-groundwater':
        export_groundwater(args.output, args.year)
    elif args.command == 'import-json':
        import_json(args.file)
    elif args.command == 'add-state':
        add_state(args.name, args.code)
    elif args.command == 'add-district':
        add_district(args.state_id, args.name)
    elif args.command == 'update-categories':
        update_categories()
    elif args.command == 'backup':
        create_backup()
    elif args.command == 'list-backups':
        list_backups()
    elif args.command == 'restore':
        restore_backup(args.backup_file)

if __name__ == '__main__':
    main()

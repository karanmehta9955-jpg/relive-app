from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import csv
import os
import datetime
import json
import shutil
import time # Added for generating unique timestamp

# Initialize Flask App at the top level
app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
DATA_FILE = 'user_data.csv'
FIELD_NAMES = ['role', 'username', 'password', 'email', 'firstname', 'lastname', 'contact', 'created_date']

# --- CORE LISTINGS CONFIGURATION ---
LISTING_DATA_FILE = 'builder_listings.csv'
LISTING_FIELD_NAMES = ['builder_username', 'property_name', 'location', 'unit_type', 'listing_price', 'status', 'created_timestamp', 'expiry_date']

# --- LIVE PROFILE DETAILS CONFIGURATION ---
LIVE_LISTING_DETAILS_FILE = 'live_listing_details.csv'
LIVE_DETAILS_FIELD_NAMES = [
    'listing_timestamp', 'sq_ft', 'num_bedrooms', 'num_bathrooms', 'num_balcony', 
    'possession_on', 'apartment_name', 'parking', 'power_backup', 
    'age_of_building', 'ownership_type', 'maintenance_charges', 
    'flooring', 'built_up_area', 'carpet_area', 
    'furnishing_status', 'facing', 'floor', 
    'gated_security', 'description', 
    'unique_views', 'shortlists', 'contacted', 'visited',
    'amenities_json' 
]

# --- GLOBAL AMENITIES CONFIGURATION (NEW) ---
GLOBAL_AMENITIES_FILE = 'global_amenities.csv'
GLOBAL_AMENITIES_FIELD_NAMES = ['name', 'icon'] # New fields for the global list

# --- LOGGING CONFIGURATION ---
LOG_FILE = 'action_log.csv'
LOG_FIELD_NAMES = ['log_timestamp', 'action_type', 'user_id', 'details']
PROFILE_LOG_FILE = 'listing_profile_log.csv'
PROFILE_LOG_FIELD_NAMES = ['log_timestamp', 'listing_timestamp', 'section', 'field_name', 'old_value', 'new_value', 'editor_username']

# --- DEFAULT DATA (Hardcoded defaults for *new* listings) ---
INITIAL_MOCK_AMENITIES = [
    {'name': "Lift", 'icon': "↑↓"}, {'name': "Internet Provider", 'icon': "🌐"}, {'name': "Club House", 'icon': "🍹"}, 
    {'name': "Children's Play Area", 'icon': "🎠"}, {'name': "Fire Safety", 'icon': "🔥"}, {'name': "Security", 'icon': "🔒"}, 
    {'name': "Gas Pipeline", 'icon': "⛽"}, {'name': "Park", 'icon': "🌳"}, {'name': "Visitor Parking", 'icon': "🅿️"}, 
    {'name': "EV Chargers", 'icon': "⚡"}, {'name': "Swimming Pool", 'icon': "🏊"},
    # Include other defaults that are always available
    {'name': "Gymnasium", 'icon': "💪"}, {'name': "Rain Water Harvesting", 'icon': "💧"}, {'name': "Intercom Facility", 'icon': "📞"},
    {'name': "Vaastu Compliant", 'icon': "🕉️"}, {'name': "Jogging Track", 'icon': "🏃"}, {'name': "Sewage Treatment Plant", 'icon': "🧪"}
]

INITIAL_MOCK_DATA = {
    'sq_ft': "1450", 'num_bedrooms': "3", 'num_bathrooms': "3", 'num_balcony': "2", 'possession_on': "2026-03-01", 
    'apartment_name': "The Lakeview Grand", 'parking': "Bike and Car", 'power_backup': "Full", 
    'age_of_building': "New Construction", 'ownership_type': "Freehold", 'maintenance_charges': "3500", 
    'flooring': "Vitrified Tiles", 'built_up_area': "1600 sq.ft.", 'carpet_area': "1350 sq.ft.", 
    'furnishing_status': "Semi-Furnished", 'facing': "North-East", 'floor': "12th of 25", 
    'gated_security': "Yes", 
    'description': "A meticulously planned residential project offering breathtaking lake views, premium amenities, and strategic location close to the IT hub. Experience luxury living with spacious layouts and modern infrastructure.", 
    'unique_views': 450, 'shortlists': 12, 'contacted': 8, 'visited': 3,
    'amenities': INITIAL_MOCK_AMENITIES[:11] # Use a subset of the default list for the initial listing
}

def initialize_data_file():
    # ... (Initialization logic remains the same)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(FIELD_NAMES)
    
    if not os.path.exists(LISTING_DATA_FILE):
        with open(LISTING_DATA_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(LISTING_FIELD_NAMES)

    if not os.path.exists(LIVE_LISTING_DETAILS_FILE):
        with open(LIVE_LISTING_DETAILS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(LIVE_DETAILS_FIELD_NAMES)

    # **MODIFIED:** Initialize Global Amenities file
    if not os.path.exists(GLOBAL_AMENITIES_FILE):
        with open(GLOBAL_AMENITIES_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=GLOBAL_AMENITIES_FIELD_NAMES)
            writer.writeheader()
            # **IMPORTANT:** Pre-populate with all default amenities
            writer.writerows(INITIAL_MOCK_AMENITIES)

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(LOG_FIELD_NAMES)

    if not os.path.exists(PROFILE_LOG_FILE):
        with open(PROFILE_LOG_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(PROFILE_LOG_FIELD_NAMES)

initialize_data_file()

# --- Logging Functions (Unchanged) ---
def log_action(action_type, user_id, details):
    # ... (Logging logic remains the same)
    log_entry = {
        'log_timestamp': datetime.datetime.now().isoformat(),
        'action_type': action_type,
        'user_id': user_id,
        'details': details
    }
    try:
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=LOG_FIELD_NAMES)
            writer.writerow(log_entry)
        return True
    except Exception as e:
        print(f"CRITICAL LOGGING ERROR (Application WILL proceed): {e}")
        return False

def log_profile_change(listing_timestamp, section, field_name, old_value, new_value, editor_username):
    # ... (Profile logging logic remains the same)
    log_entry = {
        'log_timestamp': datetime.datetime.now().isoformat(),
        'listing_timestamp': listing_timestamp,
        'section': section,
        'field_name': field_name,
        'old_value': old_value,
        'new_value': new_value,
        'editor_username': editor_username
    }
    try:
        with open(PROFILE_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=PROFILE_LOG_FIELD_NAMES)
            writer.writerow(log_entry)
        return True
    except Exception as e:
        print(f"CRITICAL PROFILE LOGGING ERROR: {e}")
        return False

# --- Core Listing and Live Details Management (Minor Changes) ---
def load_users():
    # ... (Unchanged)
    users = []
    try:
        with open(DATA_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, fieldnames=FIELD_NAMES)
            next(reader)
            for row in reader:
                if row.get('username'):
                    users.append(row)
    except FileNotFoundError:
        pass
    return users

def save_user(data):
    # ... (Unchanged)
    try:
        with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELD_NAMES)
            writer.writerow(data)
        return True
    except Exception as e:
        print(f"Error saving user: {e}")
        return False

def load_listings():
    # ... (Unchanged)
    listings = []
    try:
        with open(LISTING_DATA_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, fieldnames=LISTING_FIELD_NAMES)
            # Skip header row if it exists
            try:
                next(reader)
            except StopIteration:
                pass # Empty file
                
            for row in reader:
                # Basic check to ensure row is not just an empty row from a broken file
                if row.get('property_name') or row.get('created_timestamp'):
                    listings.append(row)
    except FileNotFoundError:
        pass
    return listings

def save_listing(data):
    # Appends a single core listing entry
    try:
        with open(LISTING_DATA_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=LISTING_FIELD_NAMES)
            writer.writerow(data)
        return True
    except Exception as e:
        print(f"Error saving listing: {e}")
        return False

def update_all_listings(listings):
    # Rewrites the entire core listings file
    try:
        with open(LISTING_DATA_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=LISTING_FIELD_NAMES)
            writer.writeheader()
            writer.writerows(listings)
        return True
    except Exception as e:
        print(f"Error saving all listings: {e}")
        return False

def load_live_details():
    # ... (Unchanged, correctly handles JSON loading)
    details = {}
    try:
        with open(LIVE_LISTING_DETAILS_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, fieldnames=LIVE_DETAILS_FIELD_NAMES)
            try:
                next(reader)
            except StopIteration:
                pass
                
            for row in reader:
                if row.get('listing_timestamp'):
                    if row.get('amenities_json'):
                        try:
                            row['amenities'] = json.loads(row['amenities_json'])
                        except (json.JSONDecodeError, TypeError):
                            row['amenities'] = []
                    else:
                        row['amenities'] = []
                        
                    del row['amenities_json']
                    details[row['listing_timestamp']] = row
    except FileNotFoundError:
        pass
    return details

def save_live_detail(data):
    # Appends a single live detail entry (used only for new listings)
    try:
        csv_data = data.copy()
        
        # Ensure amenities is handled as JSON
        if 'amenities' in csv_data and isinstance(csv_data['amenities'], list):
            csv_data['amenities_json'] = json.dumps(csv_data['amenities'])
            del csv_data['amenities']
        else:
            # For new listings, if no amenities are passed, use the initial mock data amenities
            csv_data['amenities_json'] = json.dumps(INITIAL_MOCK_DATA.get('amenities', []))
            if 'amenities' in csv_data:
                 del csv_data['amenities']
            
        row_to_write = {field: csv_data.get(field, '') for field in LIVE_DETAILS_FIELD_NAMES}
        
        with open(LIVE_LISTING_DETAILS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=LIVE_DETAILS_FIELD_NAMES)
            writer.writerow(row_to_write)
        return True
    except Exception as e:
        print(f"Error saving live detail: {e}")
        return False

def update_all_live_details(details_dict):
    # Rewrites the entire live details file
    try:
        rows_to_write = []
        for timestamp, data in details_dict.items():
            csv_data = data.copy()
            
            if 'amenities' in csv_data and isinstance(csv_data['amenities'], list):
                csv_data['amenities_json'] = json.dumps(csv_data['amenities'])
                del csv_data['amenities']
            else:
                 csv_data['amenities_json'] = ''
                 if 'amenities' in csv_data:
                     del csv_data['amenities']

            row = {field: csv_data.get(field, '') for field in LIVE_DETAILS_FIELD_NAMES}
            rows_to_write.append(row)

        with open(LIVE_LISTING_DETAILS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=LIVE_DETAILS_FIELD_NAMES)
            writer.writeheader()
            writer.writerows(rows_to_write)
        return True
    except Exception as e:
        print(f"Error saving all live details: {e}")
        return False


# ----------------------------------------------------------------------
## Global Amenities Management (Unchanged)
# ----------------------------------------------------------------------

def load_global_amenities():
    """Loads the master list of all known amenities from the global CSV."""
    global_amenities = []
    try:
        # Use DictReader to read data with field names
        with open(GLOBAL_AMENITIES_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f) # DictReader automatically gets fieldnames from the first row
            for row in reader:
                if row.get('name'):
                    global_amenities.append(row)
    except FileNotFoundError:
        # Fallback: if file is somehow missing after init, use hardcoded defaults
        return INITIAL_MOCK_AMENITIES
    except Exception as e:
        print(f"Error loading global amenities: {e}")
        return INITIAL_MOCK_AMENITIES

    return global_amenities

def save_global_amenity(amenity_data):
    """Appends a new unique amenity to the global list."""
    if not amenity_data.get('name') or not amenity_data.get('icon'):
        return False

    # Check for duplicates before saving (rudimentary check, case insensitive)
    current_list = load_global_amenities()
    if any(a['name'].strip().lower() == amenity_data['name'].strip().lower() for a in current_list):
        return True # Already exists, consider it a success

    try:
        with open(GLOBAL_AMENITIES_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=GLOBAL_AMENITIES_FIELD_NAMES)
            writer.writerow(amenity_data)
        return True
    except Exception as e:
        print(f"Error saving new global amenity: {e}")
        return False

# ----------------------------------------------------------------------
## API Routes (MODIFIED/NEW)
# ----------------------------------------------------------------------

# --- NEW: Core Listing Creation ---
@app.route('/add_listing', methods=['POST'])
def add_listing():
    data = request.json
    required_keys = ['builder_username', 'property_name', 'location', 'unit_type', 'listing_price', 'status']
    
    if not all(key in data for key in required_keys):
        return jsonify({"success": False, "message": "Missing required core listing fields."}), 400

    # 1. Create unique timestamp for both core listing and details
    current_timestamp = datetime.datetime.now().isoformat()
    
    # 2. Prepare data for core listing file (builder_listings.csv)
    core_listing_data = {
        'builder_username': data['builder_username'],
        'property_name': data['property_name'],
        'location': data['location'],
        'unit_type': data['unit_type'],
        'listing_price': data['listing_price'],
        'status': data['status'],
        'created_timestamp': current_timestamp,
        # Default to empty string if not provided in the form
        'expiry_date': data.get('expiry_date', '') 
    }
    
    # 3. Save core listing
    if not save_listing(core_listing_data):
        return jsonify({"success": False, "message": "Server error saving core listing data."}), 500

    # 4. Save initial mock details (live_listing_details.csv)
    # This ensures a profile exists before the builder tries to edit it.
    initial_details = INITIAL_MOCK_DATA.copy()
    initial_details['listing_timestamp'] = current_timestamp
    initial_details['unique_views'] = 0 # Start metrics at 0
    initial_details['shortlists'] = 0
    initial_details['contacted'] = 0
    initial_details['visited'] = 0
    
    if not save_live_detail(initial_details):
        # Log failure, but core listing is saved. Application can still proceed.
        print(f"Warning: Failed to save initial live details for {current_timestamp}")

    log_action('LISTING_CREATED', data['builder_username'], f"New core listing created: {data['property_name']}")
    return jsonify({"success": True, "message": "New listing created successfully and profile initialized.", "timestamp": current_timestamp})

# --- NEW: Core Listing Update ---
@app.route('/update_listing', methods=['POST'])
def update_listing():
    data = request.json
    original_timestamp = data.get('original_timestamp')
    updated_data = data.get('updated_data')
    builder_username = updated_data.get('builder_username') # Get username from updated data

    if not original_timestamp or not updated_data or not builder_username:
        return jsonify({"success": False, "message": "Missing required data for update."}), 400

    all_listings = load_listings()
    found = False
    log_messages = []
    
    for listing in all_listings:
        if listing.get('created_timestamp') == original_timestamp and listing.get('builder_username') == builder_username:
            found = True
            
            # Update fields and log changes
            for field, new_value in updated_data.items():
                # Skip the builder_username from being logged as a change
                if field == 'builder_username':
                    continue
                
                old_value = listing.get(field)
                
                # Check for change and update
                if str(old_value) != str(new_value):
                    listing[field] = new_value
                    log_messages.append(f"Core: {field} changed from '{old_value}' to '{new_value}'")
                    log_profile_change(original_timestamp, 'Core', field, old_value, new_value, builder_username)
            break

    if not found:
        return jsonify({"success": False, "message": "Listing not found or user unauthorized."}), 404

    # Save all updated listings
    if update_all_listings(all_listings):
        log_action('LISTING_EDITED', builder_username, f"Updated core listing (TS: {original_timestamp}). Changes: {len(log_messages)}")
        return jsonify({"success": True, "message": "Listing updated successfully.", "changes": log_messages})
    else:
        return jsonify({"success": False, "message": "Server error while saving updated data."}), 500


@app.route('/add_global_amenity', methods=['POST'])
def add_global_amenity():
    """API endpoint to receive new amenity data and save it to the global CSV."""
    data = request.get_json()
    new_amenity_name = data.get('name')
    new_amenity_icon = data.get('icon', '⭐') # Default to star icon

    if not new_amenity_name:
        return jsonify({'success': False, 'message': 'Amenity name is required.'}), 400
    
    amenity_to_save = {'name': new_amenity_name, 'icon': new_amenity_icon}
    
    if save_global_amenity(amenity_to_save):
        return jsonify({'success': True, 'message': f'Amenity "{new_amenity_name}" added to global list.'})
    else:
        # This occurs only on file/IO error, not duplicate
        return jsonify({'success': False, 'message': 'Internal server error while saving amenity.'}), 500


@app.route('/get_listing_by_timestamp/<timestamp>', methods=['GET'])
def get_listing_by_timestamp(timestamp):
    # ... (Unchanged logic, relies on load_live_details)
    all_listings = load_listings()
    core_listing = next((l for l in all_listings if l.get('created_timestamp') == timestamp), None)
    
    if not core_listing:
        return jsonify({"success": False, "message": "Core listing not found."}), 404
        
    all_live_details = load_live_details()
    live_details = all_live_details.get(timestamp, {})
    
    merged_data = {**core_listing, **live_details}

    if 'listing_timestamp' in merged_data and merged_data['listing_timestamp'] == merged_data['created_timestamp']:
        del merged_data['listing_timestamp'] 
        
    return jsonify({"success": True, "listing": merged_data})


@app.route('/update_profile_data', methods=['POST'])
def update_profile_data():
    data = request.json
    listing_timestamp = data.get('listing_timestamp')
    editor_username = data.get('editor_username')
    section = data.get('section')
    updates = data.get('updates')
    
    if not listing_timestamp or not editor_username or not updates:
        return jsonify({"success": False, "message": "Missing required data."}), 400

    all_listings = load_listings()
    all_live_details = load_live_details()
    
    core_listing = next((l for l in all_listings if l.get('created_timestamp') == listing_timestamp), None)
    live_details = all_live_details.get(listing_timestamp)

    if not core_listing:
        return jsonify({"success": False, "message": "Original listing not found."}), 404

    # If live_details are missing (e.g., if a new listing failed to save initial details), initialize it
    if not live_details:
        live_details = INITIAL_MOCK_DATA.copy()
        live_details['listing_timestamp'] = listing_timestamp
        
    log_messages = []
    
    for field_name, new_value in updates.items():
        
        # **MODIFIED LOGIC:** Handle amenities, save new custom ones globally when the profile is saved
        if field_name == 'amenities':
            
            old_amenities_names = ', '.join([a['name'] for a in live_details.get('amenities', [])])
            new_amenities_names = ', '.join([a['name'] for a in new_value])
            
            # --- CRITICAL CHANGE: SAVE NEW CUSTOM AMENITIES GLOBALLY ---
            for amenity in new_value:
                # We can save any amenity in the final list, `save_global_amenity` handles the deduplication.
                save_global_amenity(amenity)
            # --- END CRITICAL CHANGE ---

            live_details['amenities'] = new_value 
            
            log_messages.append(f"Updated amenities list. (Names: '{old_amenities_names}' -> '{new_amenities_names}')")
            log_profile_change(listing_timestamp, section, field_name, old_amenities_names, new_amenities_names, editor_username)
            continue
            
        # Standard field update logic (Unchanged)
        # Determine if the field belongs to core_listing or live_details
        if field_name in LISTING_FIELD_NAMES:
            current_data_source = core_listing
        elif field_name in LIVE_DETAILS_FIELD_NAMES:
            current_data_source = live_details
        else:
            continue
            
        old_value = current_data_source.get(field_name, 'N/A')
        
        if str(old_value) != str(new_value):
            current_data_source[field_name] = new_value
            log_messages.append(f"Updated {field_name}: '{old_value}' -> '{new_value}'")
            log_profile_change(listing_timestamp, section, field_name, old_value, new_value, editor_username)

    # 3. Save ALL updated data
    success_core = update_all_listings(all_listings)
    all_live_details[listing_timestamp] = live_details
    success_live = update_all_live_details(all_live_details)

    if success_core and success_live:
        log_action('PROFILE_EDITED', editor_username, f"Edited profile for {core_listing['property_name']} (TS: {listing_timestamp}). Changes: {len(log_messages)}")
        return jsonify({"success": True, "message": "Profile data updated and changes logged.", "changes": log_messages})
    else:
        # Check which one failed for better logging
        error_message = f"Server error while saving updated data. Core save: {success_core}, Live save: {success_live}"
        return jsonify({"success": False, "message": error_message}), 500


# --- Other API Routes (Unchanged) ---
@app.route('/signup', methods=['POST'])
def signup():
    # ... (Unchanged)
    data = request.json
    required_keys = ['username', 'password', 'email', 'firstname', 'lastname', 'contact', 'role']
    if not all(key in data for key in required_keys):
        return jsonify({"success": False, "message": "Missing required signup fields."}), 400
    # ... (rest of function)
    users = load_users()
    for user in users:
        if user['role'] == data['role'] and (user['username'] == data['username'] or user['email'] == data['email']):
            return jsonify({"success": False, "message": "Username or Email already in use."})
    
    # Add created_date
    user_data = {key: data.get(key) for key in FIELD_NAMES if key != 'created_date'}
    user_data['created_date'] = datetime.datetime.now().strftime('%Y-%m-%d')
    
    if save_user(user_data):
        return jsonify({"success": True, "message": "Account created successfully! You can now login."})
    else:
        return jsonify({"success": False, "message": "Server error while saving data."}), 500

@app.route('/login', methods=['POST'])
def login():
    # ... (Unchanged)
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    if not username or not password or not role:
        return jsonify({"success": False, "message": "Missing username, password, or role."}), 400
    users = load_users()
    for user in users:
        if user['role'] == role and user['username'] == username and user['password'] == password:
            return jsonify({
                "success": True,
                "message": f"Login successful! Welcome, {user['firstname']}.",
                "firstname": user['firstname'],
                "lastname": user['lastname'],
                "username": user['username'],
                "email": user['email'],
                "contact": user['contact']
            })
    return jsonify({"success": False, "message": "Invalid credentials or role."})

@app.route('/unified-login', methods=['POST'])
def unified_login():
    """
    Unified login endpoint that detects user role automatically based on credentials.
    Accepts username or email for login.
    """
    data = request.json
    username_or_email = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username_or_email or not password:
        return jsonify({"success": False, "message": "Missing username/email or password."}), 400
    
    users = load_users()
    
    # Search for user by username or email
    for user in users:
        # Check if the input matches either username or email
        if (user['username'].lower() == username_or_email.lower() or 
            user['email'].lower() == username_or_email.lower()):
            # Verify password
            if user['password'] == password:
                return jsonify({
                    "success": True,
                    "message": f"Login successful! Welcome, {user['firstname']}.",
                    "firstname": user['firstname'],
                    "lastname": user['lastname'],
                    "username": user['username'],
                    "email": user['email'],
                    "contact": user['contact'],
                    "role": user['role']
                })
    
    return jsonify({"success": False, "message": "Invalid credentials. Please check your username/email and password."})

@app.route('/get_listings/<username>', methods=['GET'])
def get_listings(username):
    # ... (Unchanged)
    all_listings = load_listings()
    builder_listings = [
        listing for listing in all_listings
        if listing.get('builder_username') == username
    ]
    return jsonify({"success": True, "listings": builder_listings})

@app.route('/delete_listing', methods=['POST'])
def delete_listing():
    # ... (Unchanged)
    data = request.get_json()
    original_timestamp = data.get('original_timestamp')
    builder_username = data.get('builder_username')
    if not original_timestamp or not builder_username:
        return jsonify({"success": False, "message": "Missing required data (timestamp or username)."}), 400
    listings = load_listings()
    found = False
    property_name = 'N/A'
    for listing in listings:
        if listing.get('created_timestamp') == original_timestamp and listing.get('builder_username') == builder_username:
            property_name = listing.get('property_name', 'N/A')
            listing['status'] = 'Deleted'
            found = True
            break
    if found:
        if update_all_listings(listings):
            log_action('LISTING_DELETED', builder_username, f"Soft-deleted listing: {property_name} (TS: {original_timestamp})")
            return jsonify({"success": True, "message": "Listing status updated to 'Deleted'."})
        else:
            return jsonify({"success": False, "message": "Server error while saving status update."}), 500
    else:
        return jsonify({"success": False, "message": "Listing not found or user unauthorized."}), 404

@app.route('/get_profile_log/<listing_timestamp>', methods=['GET'])
def get_profile_log(listing_timestamp):
    # ... (Unchanged)
    logs = []
    try:
        with open(PROFILE_LOG_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, fieldnames=PROFILE_LOG_FIELD_NAMES)
            try:
                next(reader)
            except StopIteration:
                pass
                
            for row in reader:
                if row.get('listing_timestamp') == listing_timestamp:
                    logs.append(row)
        logs.reverse() 
        return jsonify({"success": True, "logs": logs})
    except FileNotFoundError:
        return jsonify({"success": False, "message": "Log file not found."}), 404
    except Exception as e:
        print(f"Error reading profile log: {e}")
        return jsonify({"success": False, "message": "Server error reading log."}), 500

@app.route('/listing_profile.html')
def serve_listing_profile():
    return send_from_directory('.', 'listing_profile.html')

@app.route('/consultant_listings.html')
def serve_consultant_listings():
    return send_from_directory('.', 'consultant_listings.html')

@app.route('/consultant_property_details.html')
def serve_consultant_property_details():
    return send_from_directory('.', 'consultant_property_details.html')

# --- NEW: Media Upload Endpoint ---
@app.route('/upload_media', methods=['POST'])
def upload_media():
    """Handle photo and video uploads for a listing."""
    listing_timestamp = request.form.get('listing_timestamp')
    editor_username = request.form.get('editor_username')
    
    if not listing_timestamp or not editor_username:
        return jsonify({"success": False, "message": "Missing listing_timestamp or editor_username."}), 400
    
    if 'files' not in request.files or len(request.files.getlist('files')) == 0:
        return jsonify({"success": False, "message": "No files selected for upload."}), 400
    
    # **FIX:** Replace colons with hyphens for Windows compatibility
    safe_timestamp = listing_timestamp.replace(':', '-')
    
    # Create media directory for this listing if it doesn't exist
    media_dir = os.path.join('media', safe_timestamp)
    os.makedirs(media_dir, exist_ok=True)
    
    uploaded_files = []
    files = request.files.getlist('files')
    
    try:
        for file in files:
            if file and file.filename:
                filename = os.path.basename(file.filename)
                timestamp_prefix = int(time.time() * 1000)
                unique_filename = f"{timestamp_prefix}_{filename}"
                filepath = os.path.join(media_dir, unique_filename)
                
                file.save(filepath)
                uploaded_files.append({
                    'filename': unique_filename,
                    'filepath': filepath,
                    'url': f"/media/{safe_timestamp}/{unique_filename}"
                })
        
        if uploaded_files:
            log_action('MEDIA_UPLOADED', editor_username, 
                      f"Uploaded {len(uploaded_files)} file(s) to listing {listing_timestamp}")
            log_profile_change(listing_timestamp, 'Media', 'files_uploaded', 
                             f"{len(uploaded_files)} file(s)", 
                             ', '.join([f['filename'] for f in uploaded_files]), 
                             editor_username)
            
            return jsonify({
                "success": True, 
                "message": f"Successfully uploaded {len(uploaded_files)} file(s).",
                "uploaded_files": uploaded_files
            })
        else:
            return jsonify({"success": False, "message": "No valid files were uploaded."}), 400
            
    except Exception as e:
        print(f"Error during media upload: {e}")
        return jsonify({"success": False, "message": f"Server error during upload: {str(e)}"}), 500


# --- NEW: Serve media files ---
@app.route('/media/<path:filepath>', methods=['GET'])
def serve_media(filepath):
    """Serve uploaded media files."""
    try:
        return send_from_directory('media', filepath)
    except Exception as e:
        print(f"Error serving media: {e}")
        return jsonify({"success": False, "message": "File not found."}), 404


# --- NEW: Update User Profile ---
@app.route('/update_user', methods=['POST'])
def update_user():
    """Update user profile information."""
    try:
        data = request.get_json()
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        phone = data.get('phone')

        if not username:
            return jsonify({"success": False, "message": "Username is required."}), 400

        # Read all users
        users = []
        updated = False
        
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['username'] == username:
                        # Update the user's information
                        if first_name:
                            row['firstname'] = first_name
                        if last_name:
                            row['lastname'] = last_name
                        if email:
                            row['email'] = email
                        if phone:
                            row['contact'] = phone
                        updated = True
                    users.append(row)

        if not updated:
            return jsonify({"success": False, "message": "User not found."}), 404

        # Write back to CSV
        with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['role', 'username', 'password', 'email', 'firstname', 'lastname', 'contact', 'created_date']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(users)

        log_action('UPDATE_PROFILE', username, f'Updated profile information')
        
        return jsonify({"success": True, "message": "Profile updated successfully."})

    except Exception as e:
        print(f"Error updating user: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# --- NEW: Change Password ---
@app.route('/change_password', methods=['POST'])
def change_password():
    """Change user password."""
    try:
        data = request.get_json()
        username = data.get('username')
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not username or not current_password or not new_password:
            return jsonify({"success": False, "message": "All fields are required."}), 400

        # Read all users
        users = []
        updated = False
        password_correct = False
        
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['username'] == username:
                        # Verify current password
                        if row['password'] == current_password:
                            row['password'] = new_password
                            password_correct = True
                            updated = True
                        else:
                            password_correct = False
                    users.append(row)

        if not updated and not password_correct:
            return jsonify({"success": False, "message": "Current password is incorrect."}), 401

        if not updated:
            return jsonify({"success": False, "message": "User not found."}), 404

        # Write back to CSV
        with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['role', 'username', 'password', 'email', 'firstname', 'lastname', 'contact', 'created_date']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(users)

        log_action('CHANGE_PASSWORD', username, 'Password changed successfully')
        
        return jsonify({"success": True, "message": "Password changed successfully."})

    except Exception as e:
        print(f"Error changing password: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# --- Serve Static Files (HTML, CSS, JS, Images) ---
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return send_from_directory('.', 'index.html')


# --- Server Start ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)
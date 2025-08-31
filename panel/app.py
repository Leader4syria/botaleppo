import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash
from panel.config import FLASK_SECRET_KEY
from panel.utils import db
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
PER_PAGE = 50
CACHE_FILE = 'products.json'

# --- AUTH ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['user'] = 'admin'
            return redirect(url_for('dashboard'))
        else:
            flash('بيانات اعتماد غير صالحة.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# --- CORE PAGES ---
@app.route('/')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/categories', methods=['GET'])
def categories_route():
    if 'user' not in session:
        return redirect(url_for('login'))
    categories = db.get_categories()
    return render_template('categories.html', categories=categories)

@app.route('/categories/add', methods=['POST'])
def add_category_route():
    if 'user' not in session:
        return redirect(url_for('login'))
    name = request.form.get('name')
    parent_id = request.form.get('parent_id')
    if name:
        db.add_category(name, parent_id if parent_id else None)
        flash('تمت إضافة الفئة بنجاح!', 'success')
    return redirect(url_for('categories_route'))

@app.route('/categories/delete/<int:id>')
def delete_category_route(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    db.delete_category(id)
    flash('تم حذف الفئة بنجاح!', 'warning')
    return redirect(url_for('categories_route'))

@app.route('/services')
def services_route():
    if 'user' not in session:
        return redirect(url_for('login'))
    services = db.get_services()
    return render_template('services.html', services=services)

@app.route('/services/delete/<int:id>')
def delete_service_route(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    db.delete_service(id)
    flash('تم حذف الخدمة بنجاح.', 'success')
    return redirect(url_for('services_route'))

# --- API TOOLS & CACHING ---
@app.route('/api_tools')
def api_tools_route():
    if 'user' not in session:
        return redirect(url_for('login'))

    page = request.args.get('page', 1, type=int)
    action = request.args.get('action')
    raw_response = None

    if action == 'update_cache':
        try:
            url = "https://api.oranosmarket.com/client/api/products"
            headers = {"api-token": "4b7b7a650e3d0004b45bf260d5202d9fad1dd53fab9a6fbd"}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            raw_response = response.json()
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(raw_response, f, ensure_ascii=False, indent=2)
            flash('تم تحديث كاش الخدمات بنجاح!', 'success')
        except Exception as e:
            flash(f'فشل تحديث الكاش: {e}', 'danger')
            raw_response = {'error': str(e)}

    # Display services from cache file
    services = []
    total_pages = 0
    last_updated = 'Never'
    try:
        if os.path.exists(CACHE_FILE):
            last_updated = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE)).strftime('%Y-%m-%d %H:%M:%S')
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                all_services_raw = json.load(f)

            all_services = []
            if isinstance(all_services_raw, list):
                for service in all_services_raw:
                    if isinstance(service, dict) and 'id' in service and 'name' in service:
                        all_services.append({
                            'id': service.get('id'),
                            'name': service.get('name'),
                            'price': service.get('price')
                        })

            start = (page - 1) * PER_PAGE
            end = start + PER_PAGE
            services = all_services[start:end]
            total_pages = (len(all_services) + PER_PAGE - 1) // PER_PAGE
    except Exception as e:
        flash(f'خطأ في قراءة ملف الكاش: {e}', 'danger')

    local_categories = db.get_categories()
    return render_template('api_tools.html',
                           services=services,
                           local_categories=local_categories,
                           current_page=page,
                           total_pages=total_pages,
                           last_updated=last_updated,
                           raw_response=raw_response,
                           action=action)

@app.route('/import_from_cache', methods=['POST'])
def import_from_cache_route():
    if 'user' not in session:
        return redirect(url_for('login'))

    service_id = request.form.get('service_id')
    category_id = request.form.get('category_id')
    price = request.form.get('price')

    if not service_id or not category_id or not price:
        flash('معلومات الخدمة أو الفئة غير كاملة.', 'danger')
        return redirect(url_for('api_tools_route'))

    service_to_add = None
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                all_services_raw = json.load(f)
            if isinstance(all_services_raw, list):
                for service in all_services_raw:
                    if isinstance(service, dict) and str(service.get('id')) == service_id:
                        service_to_add = service
                        break

        if service_to_add:
            db.add_service(
                name=service_to_add.get('name'),
                category_id=int(category_id),
                description='',
                api_service_id=service_to_add.get('id'),
                api_config_id=None,
                price=float(price),
                params=json.dumps(service_to_add.get('params', [])),
                qty_values=service_to_add.get('qty_values')
            )
            flash(f"تم استيراد الخدمة '{service_to_add.get('name')}' بنجاح!", 'success')
        else:
            flash(f"لم يتم العثور على الخدمة بالمعرف {service_id} في ملف الكاش.", 'danger')
    except Exception as e:
        flash(f"فشل استيراد الخدمة: {e}", 'danger')

    return redirect(url_for('services_route'))

if __name__ == '__main__':
    app.run(debug=True)

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash
from panel.config import FLASK_SECRET_KEY
from panel.utils import db

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
PER_PAGE = 50

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            session['user'] = 'admin'
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="بيانات اعتماد غير صالحة.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# --- Category Routes ---
@app.route('/categories')
def categories_route():
    if 'user' not in session:
        return redirect(url_for('login'))
    categories = db.get_categories()
    return render_template('categories.html', categories=categories)

@app.route('/categories/add', methods=['POST'])
def add_category_route():
    # ... (omitted for brevity, no changes)
    if 'user' not in session: return redirect(url_for('login'))
    name = request.form['name']
    parent_id = request.form.get('parent_id')
    if parent_id == '': parent_id = None
    else: parent_id = int(parent_id)
    db.add_category(name, parent_id)
    return redirect(url_for('categories_route'))


@app.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
def edit_category_route(id):
    # ... (omitted for brevity, no changes)
    if 'user' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        parent_id = request.form.get('parent_id')
        if parent_id == '': parent_id = None
        else: parent_id = int(parent_id)
        db.update_category(id, name, parent_id)
        return redirect(url_for('categories_route'))
    category = db.get_category(id)
    all_categories = db.get_categories()
    return render_template('edit_category.html', category=category, all_categories=all_categories)

@app.route('/categories/delete/<int:id>')
def delete_category_route(id):
    # ... (omitted for brevity, no changes)
    if 'user' not in session: return redirect(url_for('login'))
    db.delete_category(id)
    return redirect(url_for('categories_route'))

# --- Service Routes ---
@app.route('/services')
def services_route():
    if 'user' not in session:
        return redirect(url_for('login'))
    services = db.get_services()
    return render_template('services.html', services=services)

@app.route('/services/edit/<int:id>', methods=['GET', 'POST'])
def edit_service_route(id):
    # ... (omitted for brevity, no changes)
    if 'user' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        category_id = int(request.form['category_id'])
        description = request.form.get('description', '')
        api_service_id = request.form.get('api_service_id')
        if api_service_id == '' or not api_service_id.isdigit(): api_service_id = None
        else: api_service_id = int(api_service_id)
        db.update_service(id, name, category_id, description, api_service_id)
        return redirect(url_for('services_route'))
    service = db.get_service(id)
    all_categories = db.get_categories()
    return render_template('edit_service.html', service=service, all_categories=all_categories)


@app.route('/services/delete/<int:id>')
def delete_service_route(id):
    # ... (omitted for brevity, no changes)
    if 'user' not in session: return redirect(url_for('login'))
    db.delete_service(id)
    return redirect(url_for('services_route'))

# --- API Config Routes ---
@app.route('/apis')
def api_configs_route():
    if 'user' not in session:
        return redirect(url_for('login'))
    configs = db.get_api_configs()
    return render_template('apis.html', api_configs=configs)

@app.route('/apis/add', methods=['POST'])
def add_api_config_route():
    if 'user' not in session: return redirect(url_for('login'))
    db.add_api_config(api_name=request.form['api_name'], base_url=request.form['base_url'])
    flash('تمت إضافة تكوين API بنجاح!', 'success')
    return redirect(url_for('api_configs_route'))

@app.route('/apis/edit/<int:id>', methods=['GET', 'POST'])
def edit_api_config_route(id):
    if 'user' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        db.update_api_config(id=id, api_name=request.form['api_name'], base_url=request.form['base_url'])
        flash('تم تحديث تكوين API بنجاح!', 'success')
        return redirect(url_for('api_configs_route'))
    config = db.get_api_config(id)
    return render_template('edit_api.html', config=config)

@app.route('/apis/delete/<int:id>')
def delete_api_config_route(id):
    # ... (omitted for brevity, no changes)
    if 'user' not in session: return redirect(url_for('login'))
    db.delete_api_config(id)
    flash('تم حذف تكوين API بنجاح!', 'warning')
    return redirect(url_for('api_configs_route'))

# --- Live API Browser & Importer ---
@app.route('/browse_api')
def browse_api_route():
    if 'user' not in session:
        return redirect(url_for('login'))

    api_id = request.args.get('api_id', type=int)
    page = request.args.get('page', 1, type=int)
    extra_headers_str = request.args.get('extra_headers', '')

    all_services = []
    paginated_services = []
    total_pages = 0

    if api_id:
        api_config = db.get_api_config(api_id)
        if api_config:
            try:
                # Start with the hardcoded global token
                headers = {'api-token': '4b7b7a650e3d0004b45bf260d5202d9fad1dd53fab9a6fbd'}

                # Parse and merge extra headers
                if extra_headers_str:
                    for line in extra_headers_str.strip().split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            headers[key.strip()] = value.strip()

                api_url = api_config['base_url']
                response = requests.get(api_url, headers=headers, timeout=10)
                response.raise_for_status()
                content = response.json()

                if isinstance(content, list):
                    for item in content:
                        if 'services' in item and isinstance(item['services'], list):
                            for service in item['services']:
                                if 'service' in service and 'name' in service:
                                    all_services.append({
                                        'id': service.get('service'),
                                        'name': service.get('name'),
                                        'price': service.get('price'),
                                        'description': ''
                                    })

                # Paginate the results
                start = (page - 1) * PER_PAGE
                end = start + PER_PAGE
                paginated_services = all_services[start:end]
                total_pages = (len(all_services) + PER_PAGE - 1) // PER_PAGE

            except Exception as e:
                flash(f"Failed to fetch from API: {e}", 'danger')
        else:
            flash("Invalid API Configuration selected.", 'danger')

    api_configs = db.get_api_configs()
    local_categories = db.get_categories()
    return render_template('browse_api.html',
                           api_configs=api_configs,
                           services=paginated_services,
                           local_categories=local_categories,
                           selected_api_id=api_id,
                           current_page=page,
                           total_pages=total_pages)

@app.route('/import_single_service', methods=['POST'])
def import_single_service_route():
    if 'user' not in session:
        return redirect(url_for('login'))

    service_id = request.form.get('service_id')
    category_id = request.form.get('category_id')
    api_id = request.form.get('api_id', type=int)

    if not all([service_id, category_id, api_id]):
        flash('معلومات الخدمة أو الفئة أو API غير كاملة.', 'danger')
        return redirect(url_for('browse_api_route'))

    api_config = db.get_api_config(api_id)
    if not api_config:
        flash('Invalid API Configuration selected.', 'danger')
        return redirect(url_for('browse_api_route'))

    # Re-fetch to find the service to import
    try:
        headers = {'api-token': '4b7b7a650e3d0004b45bf260d5202d9fad1dd53fab9a6fbd'}
        api_url = api_config['base_url']
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        content = response.json()

        service_to_add = None
        if isinstance(content, list):
            for item in content:
                if 'services' in item and isinstance(item['services'], list):
                    for service in item['services']:
                        if str(service.get('service')) == service_id:
                            service_to_add = service
                            break
                if service_to_add:
                    break

        if service_to_add:
            db.add_service(
                name=service_to_add.get('name'),
                category_id=int(category_id),
                description='',
                api_service_id=service_to_add.get('service'),
                api_config_id=api_id
            )
            flash(f"تم استيراد الخدمة '{service_to_add.get('name')}' بنجاح!", 'success')
        else:
            flash(f"لم يتم العثور على الخدمة بالمعرف {service_id} في استجابة الـ API.", 'danger')
    except Exception as e:
        flash(f"Failed to import service: {e}", 'danger')

    return redirect(url_for('services_route'))


if __name__ == '__main__':
    app.run(debug=True)

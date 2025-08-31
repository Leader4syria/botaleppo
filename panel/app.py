import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, session, flash
from panel.config import FLASK_SECRET_KEY
from panel.utils import db
from bot.utils.api import APIClient

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY

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

@app.route('/categories')
def categories_route():
    if 'user' not in session:
        return redirect(url_for('login'))
    categories = db.get_categories()
    return render_template('categories.html', categories=categories)

@app.route('/categories/add', methods=['POST'])
def add_category_route():
    if 'user' not in session:
        return redirect(url_for('login'))
    name = request.form['name']
    parent_id = request.form.get('parent_id')
    if parent_id == '':
        parent_id = None
    else:
        parent_id = int(parent_id)
    db.add_category(name, parent_id)
    return redirect(url_for('categories_route'))

@app.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
def edit_category_route(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        parent_id = request.form.get('parent_id')
        if parent_id == '':
            parent_id = None
        else:
            parent_id = int(parent_id)
        db.update_category(id, name, parent_id)
        return redirect(url_for('categories_route'))

    category = db.get_category(id)
    all_categories = db.get_categories()
    return render_template('edit_category.html', category=category, all_categories=all_categories)

@app.route('/categories/delete/<int:id>')
def delete_category_route(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    db.delete_category(id)
    return redirect(url_for('categories_route'))

@app.route('/services')
def services_route():
    if 'user' not in session:
        return redirect(url_for('login'))
    services = db.get_services()
    categories = db.get_categories()
    return render_template('services.html', services=services, categories=categories)

@app.route('/services/add', methods=['POST'])
def add_service_route():
    if 'user' not in session:
        return redirect(url_for('login'))
    name = request.form['name']
    category_id = int(request.form['category_id'])
    # These fields are not in the simple add form, so we pass defaults
    db.add_service(name=name, category_id=category_id, description='', api_service_id=None)
    return redirect(url_for('services_route'))

@app.route('/services/edit/<int:id>', methods=['GET', 'POST'])
def edit_service_route(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        category_id = int(request.form['category_id'])
        description = request.form.get('description', '')
        api_service_id = request.form.get('api_service_id')
        if api_service_id == '' or not api_service_id.isdigit():
            api_service_id = None
        else:
            api_service_id = int(api_service_id)
        db.update_service(id, name, category_id, description, api_service_id)
        return redirect(url_for('services_route'))

    service = db.get_service(id)
    all_categories = db.get_categories()
    return render_template('edit_service.html', service=service, all_categories=all_categories)

@app.route('/services/delete/<int:id>')
def delete_service_route(id):
    if 'user' not in session:
        return redirect(url_for('login'))
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
    if 'user' not in session:
        return redirect(url_for('login'))

    db.add_api_config(
        api_name=request.form['api_name'],
        base_url=request.form['base_url'],
        auth_header_name=request.form.get('auth_header_name'),
        auth_token=request.form.get('auth_token')
    )
    flash('تمت إضافة تكوين API بنجاح!', 'success')
    return redirect(url_for('api_configs_route'))

@app.route('/apis/edit/<int:id>', methods=['GET', 'POST'])
def edit_api_config_route(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        db.update_api_config(
            id=id,
            api_name=request.form['api_name'],
            base_url=request.form['base_url'],
            auth_header_name=request.form.get('auth_header_name'),
            auth_token=request.form.get('auth_token')
        )
        flash('تم تحديث تكوين API بنجاح!', 'success')
        return redirect(url_for('api_configs_route'))

    config = db.get_api_config(id)
    return render_template('edit_api.html', config=config)

@app.route('/apis/delete/<int:id>')
def delete_api_config_route(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    db.delete_api_config(id)
    flash('تم حذف تكوين API بنجاح!', 'warning')
    return redirect(url_for('api_configs_route'))


import requests
import json

@app.route('/api_explorer', methods=['GET', 'POST'])
def api_explorer_route():
    if 'user' not in session:
        return redirect(url_for('login'))

    response_data = session.pop('response_data', None)
    parsed_services = session.pop('parsed_services', None)

    if request.method == 'POST':
        try:
            url = request.form['url']
            method = request.form['method']
            headers_str = request.form.get('headers', '')
            body_str = request.form.get('body', '')

            headers = {}
            if headers_str:
                for line in headers_str.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        headers[key.strip()] = value.strip()

            kwargs = {'headers': headers, 'timeout': 10}
            if method == 'POST' and body_str:
                kwargs['json'] = json.loads(body_str)

            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            response_data = response.json()
            session['response_data'] = response_data

            # Try to parse services from the response
            if isinstance(response_data, list):
                parsed_services = []
                for item in response_data:
                    if isinstance(item, dict) and 'services' in item:
                        for service in item.get('services', []):
                             if isinstance(service, dict) and 'service' in service and 'name' in service:
                                parsed_services.append({
                                    'id': service.get('service'),
                                    'name': service.get('name'),
                                    'price': service.get('price'),
                                    # Description is left empty as requested
                                    'description': ''
                                })
                session['parsed_services'] = parsed_services

        except requests.exceptions.RequestException as e:
            response_data = {'error': 'Request failed', 'details': str(e)}
        except json.JSONDecodeError:
            response_data = {'error': 'Invalid JSON in body'}
        except Exception as e:
            response_data = {'error': 'An unexpected error occurred', 'details': str(e)}

        return redirect(url_for('api_explorer_route'))

    api_configs = db.get_api_configs()
    local_categories = db.get_categories()
    return render_template('api_explorer.html', api_configs=api_configs, response_data=response_data, parsed_services=parsed_services, local_categories=local_categories)

@app.route('/import_services', methods=['POST'])
def import_services_route():
    if 'user' not in session:
        return redirect(url_for('login'))

    selected_ids = request.form.getlist('selected_services')
    category_id = request.form.get('category_id')

    if not selected_ids or not category_id:
        flash('الرجاء تحديد خدمة واحدة على الأقل وفئة.', 'warning')
        return redirect(url_for('api_explorer_route'))

    # Get the full service details from the session
    all_services = session.get('parsed_services', [])

    services_to_import = [s for s in all_services if str(s.get('id')) in selected_ids]

    count = 0
    for service in services_to_import:
        db.add_service(
            name=service.get('name'),
            category_id=int(category_id),
            description=service.get('description', ''),
            api_service_id=service.get('id')
        )
        count += 1

    flash(f"تم استيراد {count} خدمة بنجاح!", 'success')
    return redirect(url_for('services_route'))


if __name__ == '__main__':
    app.run(debug=True)

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

import json

@app.route('/file_import', methods=['GET', 'POST'])
def file_import_route():
    if 'user' not in session:
        return redirect(url_for('login'))

    parsed_services = None
    if request.method == 'POST':
        if 'json_file' not in request.files:
            flash('No file part', 'warning')
            return redirect(request.url)
        file = request.files['json_file']
        if file.filename == '':
            flash('No selected file', 'warning')
            return redirect(request.url)
        if file and file.filename.endswith('.json'):
            try:
                content = json.load(file.stream)

                # Logic to parse services from the uploaded file content
                if isinstance(content, list):
                    parsed_services = []
                    for item in content:
                        if isinstance(item, dict) and 'services' in item:
                            for service in item.get('services', []):
                                if isinstance(service, dict) and 'service' in service and 'name' in service:
                                    parsed_services.append({
                                        'id': service.get('service'),
                                        'name': service.get('name'),
                                        'price': service.get('price'),
                                        'description': ''
                                    })
                if parsed_services:
                    flash(f"تم تحليل الملف بنجاح وعرض {len(parsed_services)} خدمة.", 'success')
                else:
                    flash('لم يتم العثور على خدمات بالتنسيق المتوقع في الملف.', 'info')

            except Exception as e:
                flash(f"Error processing file: {e}", 'danger')
        else:
            flash('ملف غير صالح. الرجاء تحميل ملف .json فقط.', 'danger')

    local_categories = db.get_categories()
    return render_template('file_import.html', parsed_services=parsed_services, local_categories=local_categories)

@app.route('/import_single_service', methods=['POST'])
def import_single_service_route():
    if 'user' not in session:
        return redirect(url_for('login'))

    service_id_to_import = request.form.get('service_id')
    category_id = request.form.get('category_id')

    if not service_id_to_import or not category_id:
        flash('معلومات الخدمة أو الفئة غير كاملة.', 'danger')
        return redirect(url_for('file_import_route'))

    # To remain stateless, we must re-fetch the API content to find the service details
    api_client = APIClient()
    content = api_client.get_api_content()
    service_to_add = None

    if content and isinstance(content, list):
        for category in content:
            if 'services' in category and isinstance(category['services'], list):
                for service in category['services']:
                    if str(service.get('service')) == service_id_to_import:
                        service_to_add = service
                        break
            if service_to_add:
                break

    if service_to_add:
        db.add_service(
            name=service_to_add.get('name'),
            category_id=int(category_id),
            description='', # Empty as requested
            api_service_id=service_to_add.get('service')
        )
        flash(f"تم استيراد الخدمة '{service_to_add.get('name')}' بنجاح!", 'success')
    else:
        flash(f"لم يتم العثور على الخدمة بالمعرف {service_id_to_import} في استجابة الـ API.", 'danger')

    return redirect(url_for('services_route'))


if __name__ == '__main__':
    app.run(debug=True)

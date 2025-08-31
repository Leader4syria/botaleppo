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

@app.route('/import', methods=['GET', 'POST'])
def import_route():
    if 'user' not in session:
        return redirect(url_for('login'))

    api_client = APIClient()

    if request.method == 'POST':
        selected_ids = request.form.getlist('selected_services')
        category_id = request.form.get('category_id')

        if not selected_ids or not category_id:
            flash('الرجاء تحديد خدمة واحدة على الأقل وفئة.', 'warning')
            return redirect(url_for('import_route'))

        api_services = session.get('api_services', [])

        services_to_import = [s for s in api_services if str(s.get('id')) in selected_ids]

        count = 0
        for service in services_to_import:
            # Assuming the API response has 'id', 'name', and 'description'
            db.add_service(
                name=service.get('name'),
                category_id=int(category_id),
                description=service.get('description', ''),
                api_service_id=service.get('id')
            )
            count += 1

        session.pop('api_services', None) # Clear session cache
        flash(f"تم استيراد {count} خدمة بنجاح!", 'success')
        return redirect(url_for('services_route'))

    api_services_data = None
    if 'fetch' in request.args:
        content = api_client.get_api_content()
        all_services = []
        if content and isinstance(content, list):
            for category in content:
                if 'services' in category and isinstance(category['services'], list):
                    for service in category['services']:
                        # The API response has 'service' as id, 'name', 'rate', 'min', 'max', 'desc', 'category'
                        # I need to map these to my column names.
                        all_services.append({
                            'id': service.get('service'),
                            'name': service.get('name'),
                            'description': service.get('desc')
                        })

        session['api_services'] = all_services
        api_services_data = all_services

    local_categories = db.get_categories()
    return render_template('import.html', api_services=api_services_data, local_categories=local_categories)


if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, session
from panel.config import FLASK_SECRET_KEY
from panel.utils import db
from panel.utils.supabase_client import supabase

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user_session = supabase.auth.sign_in_with_password({"email": email, "password": password})
            session['user'] = user_session.session.user.id
            return redirect(url_for('dashboard'))
        except Exception as e:
            return render_template('login.html', error="فشل تسجيل الدخول.")
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
    db.add_service(name, category_id)
    return redirect(url_for('services_route'))

@app.route('/services/edit/<int:id>', methods=['GET', 'POST'])
def edit_service_route(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        category_id = int(request.form['category_id'])
        db.update_service(id, name, category_id)
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

if __name__ == '__main__':
    app.run(debug=True)

# === REPLACE ONLY THE ROUTES SECTION IN wsgi.py WITH THIS ===

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    sites = Website.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', sites=sites)

@app.route('/add', methods=['POST'])
@login_required
def add_site():
    url = request.form['url'].strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    site = Website(url=url, name=request.form.get('name', ''), user_id=current_user.id)
    db.session.add(site)
    db.session.commit()
    audit_website.delay(site.id)
    flash('Website added! Full 37-metric audit started...', 'success')
    return redirect(url_for('dashboard'))

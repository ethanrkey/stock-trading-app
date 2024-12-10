from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from stock_trading.models.user_model import Users

auth = Blueprint('auth', __name__)

@auth.route('/')  # Add this new route
def index():
    if current_user.is_authenticated:
        return redirect(url_for('portfolio.view_portfolio'))
    return redirect(url_for('auth.login'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('portfolio.view_portfolio'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            if Users.check_password(username, password):
                user = Users.query.filter_by(username=username).first()
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('portfolio.view_portfolio'))
            else:
                flash('Invalid username or password')
        except ValueError:
            flash('Invalid username or password')
    
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('portfolio.view_portfolio'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password:
            flash('Username and password are required.')
            return render_template('auth/register.html')
            
        if password != confirm_password:
            flash('Passwords do not match.')
            return render_template('auth/register.html')
        
        try:
            Users.create_user(username, password)
            flash('Registration successful! Please login.')
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e))
    
    return render_template('auth/register.html')
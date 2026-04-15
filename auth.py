from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = db.users.find_one({"username": username})
        if user and check_password_hash(user['password_hash'], password):
            session['user'] = username
            session['user_id'] = str(user['_id'])
            return redirect(url_for('dashboard'))
            
        flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Fields cannot be empty.', 'error')
            return redirect(url_for('auth.signup'))
            
        if db.users.find_one({"username": username}):
            flash('Username already exists.', 'error')
            return redirect(url_for('auth.signup'))
        
        hashed_password = generate_password_hash(password)
        db.users.insert_one({"username": username, "password_hash": hashed_password, "score": 0, "matches_played": 0, "elo": 1200})
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('signup.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

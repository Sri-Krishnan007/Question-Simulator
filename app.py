import os
from flask import Flask, render_template, session, redirect, url_for
from flask_socketio import SocketIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from db import db
from auth import auth_bp
from room import room_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "fallback_dev_secret")

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(room_bp, url_prefix='/room')

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Register Events
from events import register_events
register_events(socketio)

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
        
    user_data = db.users.find_one({"username": session['user']})
    if not user_data:
        session.clear()
        return redirect(url_for('index'))
        
    # Query the 5 most recent matches this user played in
    history_cursor = db.history.find({"players": session['user']}).sort("_id", -1).limit(5)
    history = list(history_cursor)
        
    return render_template('dashboard.html', user=user_data, history=history)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    # debug mode should strictly be driven by environment variable in real production
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    socketio.run(app, host='0.0.0.0', port=port, debug=debug_mode)

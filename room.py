import string
import random
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import db

room_bp = Blueprint('room', __name__)

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

@room_bp.route('/create', methods=['POST'])
def create_room():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
        
    topic = request.form.get('topic', 'Game Theory')
    if topic == 'Other':
        topic = request.form.get('custom_topic', 'Game Theory')
        
    try:
        rounds = int(request.form.get('rounds', 1))
    except ValueError:
        rounds = 1
        
    room_code = generate_room_code()
    
    db.rooms.insert_one({
        "room_code": room_code,
        "host": session['user'],
        "topic": topic,
        "total_rounds": rounds,
        "difficulty": "Medium",
        "players": [session['user']],
        "status": "waiting",
        "current_round": 0,
        "past_scenarios": [],
        "is_ai_mode": False
    })
    
    return redirect(url_for('room.view_room', room_code=room_code))

@room_bp.route('/create_ai', methods=['POST'])
def create_ai_room():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
        
    topic = request.form.get('topic', 'Game Theory')
    if topic == 'Other':
        topic = request.form.get('custom_topic', 'Game Theory')
        
    persona = request.form.get('persona', 'Tit-for-Tat')
    
    try:
        rounds = int(request.form.get('rounds', 1))
    except ValueError:
        rounds = 1
        
    room_code = generate_room_code()
    
    db.rooms.insert_one({
        "room_code": room_code,
        "host": session['user'],
        "topic": topic,
        "total_rounds": rounds, 
        "persona": persona,
        "players": [session['user'], "AI Opponent"],
        "status": "playing",
        "current_round": 1,
        "current_answers": {},
        "past_scenarios": [],
        "user_history": [],
        "is_ai_mode": True
    })
    
    return redirect(url_for('room.view_room', room_code=room_code))

@room_bp.route('/join', methods=['POST'])
def join_room():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
        
    room_code = request.form.get('room_code', '').upper()
    room = db.rooms.find_one({"room_code": room_code})
    
    if not room:
        flash("Room not found.", "error")
        return redirect(url_for('dashboard'))
        
    if room['status'] != "waiting":
        flash("Game already in progress or finished.", "error")
        return redirect(url_for('dashboard'))
        
    if session['user'] not in room['players']:
        if len(room['players']) >= 2:
            flash("Room is full.", "error")
            return redirect(url_for('dashboard'))
        db.rooms.update_one({"room_code": room_code}, {"$push": {"players": session['user']}})
        
    return redirect(url_for('room.view_room', room_code=room_code))

@room_bp.route('/<room_code>')
def view_room(room_code):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
        
    room = db.rooms.find_one({"room_code": room_code})
    if not room:
        flash("Room not found.", "error")
        return redirect(url_for('dashboard'))
        
    return render_template('room.html', room=room, user=session['user'])

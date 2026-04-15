from flask_socketio import join_room, leave_room, emit
from flask import request
from db import db
from ai import generate_question

# Map socket IDs to room and user for disconnect handling
active_connections = {}

def register_events(socketio):
    @socketio.on('join_game')
    def handle_join_game(data):
        room_code = data.get('room_code')
        user = data.get('user')
        join_room(room_code)
        
        active_connections[request.sid] = {"room_code": room_code, "user": user}
        
        room_data = db.rooms.find_one({"room_code": room_code})
        if not room_data: return
        
        emit('player_joined', {'players': room_data['players']}, to=room_code)
        
        if room_data.get('is_ai_mode'):
            if not room_data.get('current_question'):
                emit('game_started', {"message": f"Round 1 VS AI is starting... Difficulty: {room_data.get('difficulty')}"}, to=room_code)
                emit('question_loading', {"message": "Groq Engine is crafting a unique strategic scenario..."}, to=room_code)
                
                past_scens = room_data.get('past_scenarios', [])
                question_data = generate_question(topic=room_data['topic'], difficulty=room_data.get('persona', 'Medium'), past_scenarios=past_scens)
                
                scenario_text = question_data.get('scenario', '')[:150] + "..."
                db.rooms.update_one({"room_code": room_code}, {
                    "$set": {"current_question": question_data},
                    "$push": {"past_scenarios": scenario_text}
                })
                emit('new_question', question_data, to=room_code)
            else:
                emit('game_started', {"message": "Game resumed."}, to=room_code)
                emit('new_question', room_data.get('current_question'), to=room_code)
            return

        if len(room_data['players']) >= 2:
            emit('game_ready', {"host": room_data['host']}, to=room_code)

    @socketio.on('start_game_request')
    def handle_start_game(data):
        room_code = data.get('room_code')
        user = data.get('user')
        
        room_data = db.rooms.find_one({"room_code": room_code})
        if room_data and room_data['host'] == user:
            db.rooms.update_one({"room_code": room_code}, {"$set": {"status": "playing", "current_round": 1, "current_answers": {}}})
            emit('game_started', {"message": "Game is starting..."}, to=room_code)
            
            emit('question_loading', {"message": "AI is generating the scenario..."}, to=room_code)
            
            past_scens = room_data.get('past_scenarios', [])
            question_data = generate_question(topic=room_data['topic'], difficulty="Medium", past_scenarios=past_scens)
            
            scenario_text = question_data.get('scenario', '')[:150] + "..."
            db.rooms.update_one({"room_code": room_code}, {
                "$set": {"current_question": question_data},
                "$push": {"past_scenarios": scenario_text}
            })
            emit('new_question', question_data, to=room_code)

    @socketio.on('start_next_round')
    def handle_start_next_round(data):
        room_code = data.get('room_code')
        user = data.get('user')
        
        room_data = db.rooms.find_one({"room_code": room_code})
        if room_data and room_data['host'] == user:
            db.rooms.update_one({"room_code": room_code}, {"$set": {"status": "playing"}})
            emit('game_started', {"message": f"Round {room_data.get('current_round')} is starting..."}, to=room_code)
            
            emit('question_loading', {"message": f"AI is generating scenario for Round {room_data.get('current_round')}..."}, to=room_code)
            
            past_scens = room_data.get('past_scenarios', [])
            question_data = generate_question(topic=room_data['topic'], difficulty=room_data.get('persona', room_data.get('difficulty', 'Medium')), past_scenarios=past_scens)
            
            scenario_text = question_data.get('scenario', '')[:150] + "..."
            db.rooms.update_one({"room_code": room_code}, {
                "$set": {"current_question": question_data},
                "$push": {"past_scenarios": scenario_text}
            })
            emit('new_question', question_data, to=room_code)
            
    @socketio.on('submit_answer')
    def handle_submit_answer(data):
        room_code = data.get('room_code')
        user = data.get('user')
        answer = data.get('answer')
        
        room_data = db.rooms.find_one({"room_code": room_code})
        if not room_data: return
        
        # Atomic update to avoid race conditions
        db.rooms.update_one(
            {"room_code": room_code},
            {"$set": {f"current_answers.{user}": answer}}
        )
        
        emit('player_answered', {"user": user}, to=room_code)
        
        # Refetch room to check answers length
        room_data = db.rooms.find_one({"room_code": room_code})
        answers = room_data.get('current_answers', {})
        
        if room_data.get('is_ai_mode'):
            # Record user history for AI memory
            db.rooms.update_one({"room_code": room_code}, {"$push": {"user_history": answer}})
            evaluate_round(room_code, answers, room_data)
        elif len(answers) >= len(room_data['players']):
            evaluate_round(room_code, answers, room_data)
            
    @socketio.on('disconnect')
    def handle_disconnect():
        conn = active_connections.get(request.sid)
        if conn:
            room_code = conn['room_code']
            user = conn['user']
            del active_connections[request.sid]
            
            room = db.rooms.find_one({"room_code": room_code})
            if room and room.get('status') in ['playing', 'waiting_next_round']:
                db.rooms.update_one({"room_code": room_code}, {"$set": {"status": "finished"}})
                emit('opponent_disconnected', {"message": f"{user} disconnected. Match terminated."}, to=room_code)

    def evaluate_round(room_code, answers, room_data):
        question = room_data.get('current_question')
        points_map = question.get('points', {})
        explanation = question.get('explanation', '')
        best_opt = question.get('best_option', '')
        
        results = {}
        for player, ans in answers.items():
            pts = int(points_map.get(ans, 0)) if str(ans) != "Timeout" else 0
            results[player] = { "answer": ans, "points": pts }
            db.users.update_one({"username": player}, {"$inc": {"score": pts, "matches_played": 1}})
            
        if room_data.get('is_ai_mode'):
            persona = room_data.get('persona', 'Perfect Rational')
            user_hist = room_data.get('user_history', [])
            
            ai_ans = best_opt
            if persona == 'Tit-for-Tat' and len(user_hist) > 1:
                # Copy player's previous answer
                ai_ans = user_hist[-2]
            elif persona == 'Altruist':
                # Pick an option that has reasonable points but maybe not the best to favor mutual
                good_opts = [k for k, v in points_map.items() if v > 0]
                if good_opts:
                    ai_ans = good_opts[-1] # Simplistic heuristic
            elif persona == 'Grudger':
                # If player ever scored 0, pick the worst option for them (simulate by picking worst option overall)
                if any(int(points_map.get(h, 0)) == 0 for h in user_hist[:-1]):
                    ai_ans = min(points_map, key=points_map.get)
                    
            if ai_ans not in points_map: ai_ans = best_opt
                
            ai_pts = int(points_map.get(ai_ans, 0))
            results["AI Opponent"] = { "answer": ai_ans, "points": ai_pts }
            
        match_record = {
            "room_code": room_code,
            "topic": room_data['topic'],
            "players": room_data['players'],
            "results": results,
            "explanation": explanation,
            "best_option": best_opt
        }
        db.history.insert_one(match_record)
        
        is_final = True
        if room_data.get('total_rounds', 1) > room_data.get('current_round', 1):
            is_final = False
            
        # ELO Calculation
        elo_changes = {}
        if is_final and len(room_data['players']) == 2 and not room_data.get('is_ai_mode'):
            p1, p2 = room_data['players'][0], room_data['players'][1]
            u1 = db.users.find_one({"username": p1})
            u2 = db.users.find_one({"username": p2})
            if u1 and u2:
                r1, r2 = u1.get('elo', 1200), u2.get('elo', 1200)
                e1 = 1 / (1 + 10 ** ((r2 - r1) / 400))
                e2 = 1 / (1 + 10 ** ((r1 - r2) / 400))
                
                s1 = results.get(p1, {}).get('points', 0)
                s2 = results.get(p2, {}).get('points', 0)
                
                if s1 > s2:
                    score1, score2 = 1, 0
                elif s2 > s1:
                    score1, score2 = 0, 1
                else:
                    score1, score2 = 0.5, 0.5
                    
                K = 32
                new_r1 = r1 + K * (score1 - e1)
                new_r2 = r2 + K * (score2 - e2)
                
                elo_changes[p1] = new_r1 - r1
                elo_changes[p2] = new_r2 - r2
                
                db.users.update_one({"username": p1}, {"$set": {"elo": new_r1}})
                db.users.update_one({"username": p2}, {"$set": {"elo": new_r2}})
        
        if is_final:
            db.rooms.update_one({"room_code": room_code}, {"$set": {"status": "finished"}})
        else:
            db.rooms.update_one({"room_code": room_code}, {"$set": {"status": "waiting_next_round", "current_answers": {}}, "$inc": {"current_round": 1}})
            
        match_record.pop('_id', None)
        match_record['elo_change'] = elo_changes
        match_record['is_final'] = is_final
        emit('round_results', match_record, to=room_code)

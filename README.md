# Interactive Game Theory Simulator & Decision Analysis

An interactive, real-time multiplayer simulation platform focused on exploring classical Game Theory problems—most notably the **Prisoner’s Dilemma**—through AI-driven procedurally generated scenarios. 

This project transitions static mathematical payoff matrices into dynamic, scenario-based decisions bridging Human vs. Human and Human vs. AI competitive logic. 

## 🌟 Why This Project is Unique
Most Game Theory simulators rely on hardcoded "Cooperate" or "Defect" buttons with rigid, zero-context points. We completely reinvented this by integrating a **Large Language Model (Groq AI)** to procedurally generate highly readable, engaging, and *unique* real-world scenarios on the fly. 
- You aren't just choosing "A" or "B"—you're deciding whether to merge in traffic, undercut a business competitor, or betray a heist partner.
- The platform shifts cognitive load to algorithmic strategies, testing not only isolated choices but multi-round behavior tracking.

## 🎯 Game Theory Conditions & Concepts Included
The engine strictly parses gameplay through the lens of mathematical optimization, enforcing these core principles:
1. **Nash Equilibrium:** Scenarios are designed with a strictly identifiable equilibrium state where no player can unilaterally deviate and improve their payoff.
2. **Strict Dominance Analysis:** Mathematical options are generated with distinct Point allocations (10, 5, 0) reflecting dominated vs. dominating strategies in finite games.
3. **Repeated/Multi-Round Dilemmas:** Investigating the evolution of cooperation in repeated interactions (Iterated Prisoner's Dilemma) rather than one-shot constraints.
4. **Zero-Sum & Non-Zero-Sum:** Variable topic prompts enforce different types of matrix outcomes, including *Stag Hunt*, *Hawk-Dove*, and *Tragedy of the Commons*.

## 🤖 Dynamic AI Personas
To truly test player psychology in the **Play VS AI** mode, we eschewed simple "Easy/Medium" difficulties for explicitly modeled classical Game Theory algorithms:
- **Perfect Rational:** Plays entirely mathematically, always executing the exact Nash Equilibrium to guarantee minimizing maximum loss.
- **Tit-for-Tat:** The famously robust zero-sum strategy; cooperates the first round, and then directly mimics the player's previous action in every subsequent round.
- **Altruist:** Evaluates the sub-game to always select the option that maximizes mutual overall utility, leaving it vulnerable to exploitation.
- **Grudger:** Cooperates indefinitely—until the player defects. Once the player defects, it aggressively minimizes the player's score forever in retaliation.

## 🔥 Features
- **Real-time Matchmaking:** WebSockets (`Flask-SocketIO`) heavily manage concurrent multiplayer state handling.
- **Elo Rating System:** Incorporates a rigorous competitive K-32 Elo formula. Defeating perfect rational players or highly skilled peers realistically distributes rank instead of just endlessly accruing points.
- **Atomic Concurrency Handling:** Multiplayer races (where players answer at the exact same millisecond) are handled smoothly via MongoDB atomic array pointers.
- **Disconnection Resiliency:** Sockets track active pings to gracefully forfeit and summarize matches if an opponent unexpectedly rage-quits.
- **Customizable Dilemmas:** Create custom topics (e.g. "Space Race", "Traffic Logic", "AI Security Dilemma") which fundamentally shifts the contextual matrix.

## 🚀 Technologies Used
- **Backend Framework:** Python / Flask
- **Real-Time Engine:** Flask-SocketIO
- **Database:** MongoDB (PyMongo) with Atomic State Management
- **Generative AI:** Groq API (`llama-3.3-70b-versatile`)
- **Frontend / Styling:** Raw HTML/CSS with Glassmorphism aesthetic and asynchronous Socket listeners.

## ⚙️ Setup & Installation
1. Clone the repository.
2. Install necessary requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your `.env` configuration file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key
   MONGO_URI=your_mongodb_cluster_url
   SECRET_KEY=your_flask_secret
   ```
4. Run the startup script:
   ```bash
   python app.py
   ```
5. Navigate to `http://localhost:5000` to begin experimenting with human decisions!

---
*Developed for Game Theory & Decision Analysis Techniques*

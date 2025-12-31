import os
from flask import Flask, render_template, url_for, flash, redirect, request, jsonify
from flask_cors import CORS
from datetime import datetime
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
basedir = os.path.abspath(os.path.dirname(__file__))
# Priority 1: .env in backend/ (for local dev when run from root)
# Priority 2: .env in root (already handled by default if run from root)
load_dotenv(os.path.join(basedir, '.env'))
load_dotenv(os.path.join(os.path.dirname(basedir), '.env'))

from urllib.parse import quote_plus

def sanitize_db_url(url):
    """
    Robustly handles special characters in DB passwords (like '@' or '#').
    Example: postgresql://user:p@ssword@host:5432/db
    """
    if not url:
        return url
        
    # Standardize: trim whitespace and common quotes
    url = url.strip().strip('"').strip("'")
    
    if not url.startswith("postgres"):
        return url
    
    # Standardize scheme
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
        
    try:
        # Split scheme from the rest
        scheme, rest = url.split("://", 1)
        
        # We need to separate credentials from the host part.
        # The credentials start after '://' and end at the LAST '@' before the host/port.
        if "@" in rest:
            # Finding the last '@' helps identify where the host starts
            # (passwords can contain @, but hosts generally shouldn't)
            creds, host_part = rest.rsplit("@", 1)
            
            if ":" in creds:
                user, password = creds.split(":", 1)
                # Re-encode only the password part to handle special chars like '@', '#', etc.
                # quote_plus handles spaces and special chars safely.
                clean_url = f"{scheme}://{user}:{quote_plus(password)}@{host_part}"
                return clean_url
    except Exception as e:
        print(f"URL Sanitization Error: {e}")
        
    return url

try:
    from backend.models import db, User, Persona, GameState, PuzzleLog, QuizLog, GateProgress, QuestionHistory
    from backend.ai_engine import AIEngine
    print("DEBUG: Using absolute imports (Vercel mode)")
except ImportError:
    from models import db, User, Persona, GameState, PuzzleLog, QuizLog, GateProgress, QuestionHistory
    from ai_engine import AIEngine
    print("DEBUG: Using relative imports (Local mode)")

# Initialize AI Engine
ai_engine = AIEngine()

# Static folder for frontend assets
app = Flask(__name__, 
            template_folder='../frontend', 
            static_folder='../frontend/static')

# Global JSON Error Handler
@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return jsonify({"success": False, "message": e.description}), e.code
    
    # Handle non-HTTP exceptions (Internal Server Errors)
    print(f"INTERNAL SERVER ERROR: {str(e)}")
    return jsonify({
        "success": False, 
        "message": f"Server encountered an error. Check logs for details: {str(e)}"
    }), 500

# Dynamic CORS based on Environment
frontend_url = os.getenv('FRONTEND_URL', '*')
CORS(app, supports_credentials=True, origins=[frontend_url, "http://127.0.0.1:5500", "http://localhost:5500"])
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-key')

# Check if running on Vercel (Read-Only FS)
# Check if running on Vercel (Read-Only FS)
# Check Database URL
db_url = os.getenv('DATABASE_URL')
config_error = None

if os.environ.get('VERCEL'):
    if not db_url:
        config_error = "DATABASE_URL is missing. Please add your Supabase connection string to Vercel Environment Variables."
        print(f"CRITICAL: {config_error}")
    else:
        print("DEBUG: Running on Vercel with Supabase")
else:
    # Locally we also want to ensure Supabase is used if user requested it
    if not db_url:
        print("WARNING: DATABASE_URL not found. Falling back to SQLite.")
        db_url = 'sqlite:///site.db'
    else:
        print("DEBUG: Running Locally with Supabase/Remote DB")

# Final URI Check & Sanitization
db_url = sanitize_db_url(db_url)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///' # Fallback to avoid None error
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Global check for Config Errors (Blocks API calls with 500 but returns valid JSON)
@app.before_request
def check_config():
    if config_error and request.path.startswith('/api/'):
        return jsonify({"success": False, "message": config_error}), 500

# Cross-domain session settings
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

db.init_app(app)

# Ensure tables are created (especially for Supabase first-run)
with app.app_context():
    try:
        db.create_all()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization error: {e}")

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Helpers ---

@app.route("/api/user_status")
def user_status():
    if current_user.is_authenticated:
        persona = Persona.query.filter_by(user_id=current_user.id).first()
        return jsonify({
            "authenticated": True, 
            "username": current_user.username,
            "has_persona": persona is not None
        })
    return jsonify({"authenticated": False})

def get_or_create_game_state(user_id):
    state = GameState.query.filter_by(user_id=user_id).first()
    if not state:
        state = GameState(user_id=user_id)
        db.session.add(state)
        db.session.commit()
    return state

# --- Routes ---

@app.route("/api/health")
def health():
    return jsonify({"status": "healthy", "database": str(db.engine.url.drivername)})

@app.route("/")
@app.route("/home")
def home():
    return jsonify({"message": "API is running. Connect via frontend."})

@app.route("/api/signup", methods=['POST'])
def signup():
    data = request.json or request.form
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({"success": False, "message": "Username already exists."}), 400
        
    hashed_password = generate_password_hash(password, method='scrypt')
    new_user = User(username=username, password=hashed_password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return jsonify({"success": True, "message": "Signup successful.", "redirect": "persona.html"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/login", methods=['POST'])
def login():
    data = request.json or request.form
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        login_user(user, remember=True)
        return jsonify({"success": True, "message": "Login successful.", "redirect": "hub.html"})
    else:
        return jsonify({"success": False, "message": "Login Unsuccessful."}), 401

@app.route("/api/logout")
def logout():
    logout_user()
    return jsonify({"success": True, "message": "Logged out."})

@app.route("/dashboard")
@login_required
def dashboard():
    """Main Hub after login."""
    return render_template('hub.html')

@app.route("/roadmap")
@login_required
def roadmap():
    """Learning Roadmap Section."""
    return render_template('roadmap.html')

@app.route("/api/reset_progress", methods=['POST'])
@login_required
def reset_progress():
    state = get_or_create_game_state(current_user.id)
    state.current_step = 1
    state.current_cycle = 1
    # Also clear logs for step 1? Or just let them be overwritten?
    # Logic in solve_puzzle checks for existing log.
    # We should clear puzzle logs for step 1 to be safe, or allow re-solving.
    # Actually solve_puzzle updates existing log if found.
    db.session.commit()
    return jsonify({"success": True, "message": "Progress reset to Gate 1"})

@app.route("/api/game_state")
@login_required
def game_state_api():
    state = get_or_create_game_state(current_user.id)
    steps = [
        {"id": 1, "label": "GATE 1"},
        {"id": 2, "label": "GATE 2"},
        {"id": 3, "label": "GATE 3"},
        {"id": 4, "label": "GATE 4"},
        {"id": 5, "label": "GATE 5"},
        {"id": 6, "label": "GATE 6"}
    ]
    return jsonify({
        "current_step": state.current_step,
        "current_cycle": state.current_cycle,
        "steps": steps
    })

@app.route("/api/persona", methods=['GET', 'POST'])
@login_required
def persona_api():
    if request.method == 'POST':
        data = request.json or request.form
        name = data.get('name')
        style = data.get('style')
        gender = data.get('gender')
        
        persona = Persona.query.filter_by(user_id=current_user.id).first()
        if not persona:
            persona = Persona(user_id=current_user.id, name=name, avatar_data={'style': style, 'gender': gender})
            db.session.add(persona)
        else:
            persona.name = name
            persona.avatar_data = {'style': style, 'gender': gender}
            
        db.session.commit()
        return jsonify({"success": True, "message": "Persona saved.", "redirect": "hub.html"})

    persona = Persona.query.filter_by(user_id=current_user.id).first()
    if persona:
         return jsonify({
             "exists": True,
             "name": persona.name,
             "avatar_data": persona.avatar_data
         })
    return jsonify({"exists": False, "username": current_user.username})


@app.route("/quiz")
@login_required
def quiz():
    state = get_or_create_game_state(current_user.id)
    if state.current_step < 6:
        flash("Complete all puzzles first!", "danger")
        return redirect(url_for('game_dashboard'))
        
    log = QuizLog.query.filter_by(user_id=current_user.id, cycle=state.current_cycle).first()
    if not log:
        questions = ai_engine.generate_quiz_data(state.current_cycle)
        log = QuizLog(user_id=current_user.id, cycle=state.current_cycle, questions=questions)
        db.session.add(log)
        db.session.commit()
        
    return render_template('quiz.html', log=log, state=state)

@app.route("/api/puzzle_hint", methods=['POST'])
@login_required
def puzzle_hint():
    data = request.json
    step = data.get('step')
    puzzle_type = data.get('puzzle_type')
    
    prompt = f"Provide a short, cryptic hint for a {puzzle_type} puzzle (Step {step}). Max 15 words."
    hint = ai_engine.generate_chat_response(prompt)
    
    return jsonify({"hint": hint})

@app.route("/api/solve_puzzle", methods=['POST'])
@login_required
def solve_puzzle():
    data = request.json
    try:
        step = int(data.get('step'))
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid step"}), 400
    
    state = GameState.query.filter_by(user_id=current_user.id).first()
    log = PuzzleLog.query.filter_by(user_id=current_user.id, cycle=state.current_cycle, step=step).first()
    
    if not log:
        # Lazy creation of log if it doesn't exist
        log = PuzzleLog(
            user_id=current_user.id, 
            cycle=state.current_cycle, 
            step=step,
            puzzle_type="manual_verification",
            puzzle_data={},
            solved=False # Will be set to true below
        )
        db.session.add(log)
    
    if log: # Should always be true now
        log.solved = True
        log.solved_at = datetime.utcnow()
        
        # DEBUG: Log the comparison
        print(f"DEBUGGING SOLVE: Request Step: {step} (Type: {type(step)})")
        print(f"DEBUGGING SOLVE: DB State Step: {state.current_step} (Type: {type(state.current_step)})")
        
        if state.current_step == step:
            state.current_step += 1
            print("DEBUGGING SOLVE: Incrementing Step to", state.current_step)
        else:
            print("DEBUGGING SOLVE: Step Mismatch - No Increment")
            
        db.session.commit()
        
        print(f"DEBUG: Puzzle {step} solved. New current_step: {state.current_step}")
        
        # After completing puzzle, go to next gate's quiz (or dashboard if done)
        next_seq_step = step + 1
        if next_seq_step <= 6:
            # Go to next gate's quiz with step parameter
            next_url = f"quiz_setup.html?step={next_seq_step}"
            print(f"DEBUG: Navigating to {next_url}")
        else:
            # All 6 gates completed, back to dashboard
            next_url = "game_dashboard.html"
            print(f"DEBUG: All gates complete, going to dashboard")
            
        return jsonify({"success": True, "next_url": next_url})
    
    return jsonify({"success": False}), 404


@app.route("/quiz/setup")
@login_required
def quiz_setup():
    return render_template('quiz_setup.html')

@app.route("/api/start_quiz", methods=['POST'])
@login_required
def start_quiz():
    data = request.json
    difficulty = data.get('difficulty', 'Intermediate')
    step = data.get('step')
    
    # Generate 5 questions via AI Engine
    questions = ai_engine.generate_quiz(difficulty, step)
    
    # Store in QuizLog (temporary for this session)
    state = get_or_create_game_state(current_user.id)
    new_quiz = QuizLog(
        user_id=current_user.id,
        cycle=state.current_cycle,
        questions=questions,
        score=0
    )
    db.session.add(new_quiz)
    db.session.commit()
    
    return jsonify({"success": True, "quiz_id": new_quiz.id})

@app.route("/api/quiz/<int:quiz_id>")
@login_required
def get_quiz_data(quiz_id):
    quiz = QuizLog.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        return jsonify({"success": False, "message": "Access Denied"}), 403
    return jsonify({
        "success": True,
        "quiz_id": quiz.id,
        "questions": quiz.questions
    })

@app.route("/quiz/play/<int:quiz_id>")
@login_required
def play_quiz(quiz_id):
    return redirect(f"/quiz.html?quiz_id={quiz_id}")

@app.route("/api/submit_quiz", methods=['POST'])
@login_required
def submit_quiz():
    data = request.json
    quiz_id = data.get('quiz_id')
    answers = data.get('answers')
    
    quiz = QuizLog.query.get(quiz_id)
    if not quiz:
        return jsonify({"success": False})

    questions = quiz.questions
    score = 0
    for i, q in enumerate(questions):
        user_ans = answers[i]
        correct_ans = q.get('correct_index') or q.get('answer')
        if (user_ans == correct_ans):
            score += 10
        
    quiz.score = score
    db.session.commit()
    
    state = get_or_create_game_state(current_user.id)
    
    # Redirect to the specific step if provided (context preservation), else highest unlocked
    target_step = data.get('step') or state.current_step
    
    # Requirement: 5 questions total, must answer 3 correct (30 points) to pass
    passed = score >= 30
    
    if passed:
        redirect_url = f"puzzle.html?step={target_step}"
    else:
        # Retry logic: reload the same gate's setup
        redirect_url = f"quiz_setup.html?step={target_step}"
    
    return jsonify({
        "success": True, 
        "passed": passed, 
        "score": score,
        "redirect": redirect_url
    })

@app.route("/api/puzzle/<int:step>")
@login_required
def get_puzzle_data(step):
    state = get_or_create_game_state(current_user.id)
    if step > state.current_step:
        return jsonify({"success": False, "message": "Gate Locked"}), 403
        
    log = PuzzleLog.query.filter_by(user_id=current_user.id, cycle=state.current_cycle, step=step).first()
    if not log:
        params = ai_engine.generate_puzzle_data(step, state.current_cycle)
        log = PuzzleLog(
            user_id=current_user.id,
            cycle=state.current_cycle,
            step=step,
            puzzle_type=params['type'],
            puzzle_data=params['data']
        )
        db.session.add(log)
        db.session.commit()
    
    return jsonify({
        "success": True,
        "puzzle_data": log.puzzle_data,
        "puzzle_type": log.puzzle_type,
        "step": step
    })

@app.route("/puzzle/<int:step>")
@login_required
def puzzle_view(step):
    return redirect(f"/puzzle.html?step={step}")

@app.route("/api/reboot_puzzle", methods=['POST'])
@login_required
def reboot_puzzle():
    data = request.json
    step = data.get('step')
    state = get_or_create_game_state(current_user.id)
    
    # Delete the existing log to force regeneration on reload
    log = PuzzleLog.query.filter_by(user_id=current_user.id, cycle=state.current_cycle, step=step).first()
    if log:
        db.session.delete(log)
        db.session.commit()
    
    return jsonify({"success": True})

# --- Main ---

def init_db():
    with app.app_context():
        # db.drop_all() # Removed for Supabase persistence
        db.create_all()
        print("Database initialized.")

if __name__ == '__main__':
    # Force reset if models changed
    init_db()
    app.run(debug=True)

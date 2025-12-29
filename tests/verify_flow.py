import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000"
SESSION = requests.Session()

def print_step(msg):
    print(f"\n[TEST] {msg}")

def fail(msg):
    print(f"\n[FAIL] {msg}")
    sys.exit(1)

def run_test():
    # 1. Signup/Login
    username = "test_user_flow_v2"
    password = "password123"
    print_step(f"Registering/Logging in user: {username}")
    
    # Try login first
    res = SESSION.post(f"{BASE_URL}/login", json={"username": username, "password": password})
    
    if res.status_code != 200:
        # Try signup
        res = SESSION.post(f"{BASE_URL}/signup", json={"username": username, "password": password})
        if res.status_code != 200 and "already exists" not in res.text:
            fail(f"Signup failed: {res.text}")
        
        # Login again to be sure
        res = SESSION.post(f"{BASE_URL}/login", json={"username": username, "password": password})
        if res.status_code != 200:
            fail(f"Login failed: {res.text}")

    print("[PASS] Logged in")

    # 2. Reset Game State (Optional, but good for testing)
    # We can't easily reset state via API, so we'll just check where we are
    res = SESSION.get(f"{BASE_URL}/api/game_state")
    state = res.json()
    current_step = state['current_step']
    print_step(f"Current Game Step: {current_step}")

    # If we are seemingly stuck or advanced, we need to handle it.
    # But let's assume valid flow for a new-ish user or just test the current step transition.
    
    target_step = current_step
    
    # 3. Start Quiz
    print_step(f"Starting Quiz for Step {target_step}")
    res = SESSION.post(f"{BASE_URL}/api/start_quiz", json={"difficulty": "Beginner", "step": target_step})
    if res.status_code != 200:
        fail(f"Start Quiz functions failed: {res.text}")
    
    quiz_data = res.json()
    quiz_id = quiz_data.get('quiz_id')
    print(f"[PASS] Started Quiz ID: {quiz_id}")

    # 4. Submit Quiz (Perfect Score)
    print_step("Submitting Quiz with perfect score...")
    # Get questions to know length (mocking answers as correct isn't strictly checked by backend for passing, just score logic)
    # But backend checks answers against correct_index.
    # Let's peek at the quiz data if possible, or just force a score if we added a backdoor (we haven't).
    # We need to fetch the quiz to answer correctly.
    res = SESSION.get(f"{BASE_URL}/api/quiz/{quiz_id}")
    questions = res.json()['questions']
    
    answers = []
    for q in questions:
        # The backend logic compares request answer with stored answer.
        # We need to pick the correct index.
        # Wait, the frontend sends the index. The backend checks `user_ans == correct_ans`.
        # Code: `correct_ans = q.get('correct_index') or q.get('answer')`
        answers.append(q.get('correct_index', 0))

    res = SESSION.post(f"{BASE_URL}/api/submit_quiz", json={"quiz_id": quiz_id, "answers": answers})
    result = res.json()
    
    if not result.get('passed'):
        fail(f"Quiz failed? {result}")
        
    redirect_url = result.get('redirect')
    print(f"[PASS] Quiz Passed. Redirect: {redirect_url}")
    
    expected_puzzle_url = f"puzzle.html?step={target_step}"
    if redirect_url != expected_puzzle_url:
        fail(f"Incorrect Quiz Redirect! Expected: {expected_puzzle_url}, Got: {redirect_url}")

    # 5. Solve Puzzle
    print_step(f"Solving Puzzle for Step {target_step}")
    
    # Send step as INTEGER (since we fixed the bug)
    # But wait, verification: Does the API accept string "1" now? We added int casting.
    # Let's send it as the frontend expects.
    res = SESSION.post(f"{BASE_URL}/api/solve_puzzle", json={"step": target_step})
    
    if res.status_code != 200:
        fail(f"Solve Puzzle failed: {res.text}")
        
    puzzle_res = res.json()
    next_url = puzzle_res.get('next_url')
    print(f"[PASS] Puzzle Solved. Next URL: {next_url}")
    
    # 6. Verify Next Step
    expected_next_url = f"quiz_setup.html?step={target_step + 1}"
    if target_step < 6:
        if next_url != expected_next_url:
             fail(f"Incorrect Puzzle Redirect! Expected: {expected_next_url}, Got: {next_url}")
    else:
        if "game_dashboard" not in next_url:
             fail(f"Expected dashboard redirect for step 6, got {next_url}")

    print_step("FULL FLOW VERIFIED SUCCESSFULLY! ✅")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        fail(f"Exception: {e}")

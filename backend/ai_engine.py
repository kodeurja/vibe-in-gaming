import os
import requests
import json
import random

class PuzzleEngine:
    def __init__(self, ai_engine_ref):
        self.ai = ai_engine_ref
        self.puzzle_types = [
            "tile-matching",    # Gate 1
            "crossword-cipher", # Gate 2
            "mechanical-lock",  # Gate 3 (Nut & Bolt)
            "jigsaw-reconstitution", # Gate 4
            "flow-link",        # Gate 5
            "tube-sort"         # Gate 6
        ]

    def generate_puzzle_data(self, gate_num, cycle=1):
        """
        Generates Tower of Hanoi data for all gates.
        Progression: Gate X -> X+1 Disks.
        """
        disks = gate_num + 1
        min_moves = (2 ** disks) - 1
        
        data = {
            "title": f"GATE {gate_num}: TOWER OF HANOI (L{gate_num})",
            "description": f"Move the stack to the last rod. {disks} disks. {min_moves} move minimum.",
            "disks": disks,
            "min_moves": min_moves,
            "rods": 3
        }
        
        return {"type": "tower-of-hanoi", "data": data}

    def generate_quiz(self, difficulty, step=None):
        """
        Generates 5 unique quiz questions based on difficulty and gate step.
        Topics: AI, Machine Learning, Deep Learning, Python, GenAI.
        """
        context = f"for Gate {step}" if step else "General Knowledge"
        prompt = f"""
        Generate 5 unique, non-repeating quiz questions about AI, ML, Deep Learning, Python, and GenAI.
        Context: {context}.
        Difficulty: {difficulty}.
        Format: JSON Array of objects with keys: 'question', 'options' (list of 4 strings), 'correct_index' (0-3).
        Ensure questions are conceptual and engaging.
        """
        
        # Fallback questions if AI fails
        fallback = [
             {
                "question": "Which of the following is a supervised learning algorithm?",
                "options": ["K-Means", "Linear Regression", "PCA", "Apriori"],
                "correct_index": 1
            },
            {
                "question": "What does CNN stand for in Deep Learning?",
                "options": ["Central Neural Network", "Convolutional Neural Network", "Computer Neural Node", "Cybernetic Network"],
                "correct_index": 1
            },
            {
                "question": "Which library is primary used for Deep Learning in Python?",
                "options": ["Pandas", "NumPy", "TensorFlow", "Matplotlib"],
                "correct_index": 2
            },
            {
                "question": "What is the primary goal of Generative AI?",
                "options": ["To classify data", "To generate new data instances", "To cluster data", "To reduce dimensions"],
                "correct_index": 1
            },
            {
                "question": "In Python, which keyword is used to define a function?",
                "options": ["func", "def", "definition", "function"],
                "correct_index": 1
            }
        ]

        if self.ai.groq_api_key and self.ai.groq_api_key != "your_groq_api_key_here":
            try:
                ai_res = self.ai._call_groq(prompt, "llama-3.1-8b-instant")
                if ai_res:
                    start = ai_res.find('[')
                    end = ai_res.rfind(']') + 1
                    if start != -1 and end != -1:
                        data = json.loads(ai_res[start:end])
                        if len(data) >= 5:
                            return data[:5]
            except Exception as e:
                print(f"AI Quiz Gen Error: {e}")
        
        return fallback

class QuizGenerator:
    def __init__(self, ai_engine_ref):
        self.ai = ai_engine_ref

    def generate(self, cycle):
        """Generates 5 dynamic AI MCQs."""
        prompt = f"""
        You are the Galactic Oracle, a super-intelligence at the center of the Pulsar Gateway.
        Generate 5 multiple-choice questions for a traveler navigating Star System {cycle}.
        Topic rotation: 
        1. Generative AI (cosmic metaphors)
        2. Python (gateway protocols)
        3. Machine Learning (stellar patterns)
        4. Deep Learning (nebula networks)
        5. Applied AI Scenario (interstellar mission)
        Difficulty Level: {min(10, cycle)}
        
        Return ONLY a JSON array of objects. Each object must have:
        'question': 'string',
        'options': ['opt1', 'opt2', 'opt3', 'opt4'],
        'answer': 0-3 (index of correct option),
        'explanation': 'string'
        """
        
        fallback = [
            {
                "question": "What does LLM stand for?",
                "options": ["Large Logic Model", "Large Language Model", "Little Learn Machine", "Long Logic Module"],
                "answer": 1,
                "explanation": "LLM stands for Large Language Model."
            }
        ] * 5 # Fallback if AI fails
        
        if self.ai.groq_api_key and self.ai.groq_api_key != "your_groq_api_key_here":
            try:
                ai_res = self.ai._call_groq(prompt, "llama-3.1-8b-instant")
                if ai_res:
                    start = ai_res.find('[')
                    end = ai_res.rfind(']') + 1
                    if start != -1 and end != -1:
                        return json.loads(ai_res[start:end])
            except:
                pass
        
        return fallback

class AIEngine:
    def __init__(self):
        self.groq_api_key = os.getenv('GROQ_API_KEY', 'your_groq_api_key_here')
        self.puzzle_engine = PuzzleEngine(self)
        self.quiz_generator = QuizGenerator(self)
        
    def generate_puzzle_data(self, step, cycle):
        return self.puzzle_engine.generate_puzzle_data(step, cycle)

    def generate_quiz(self, difficulty, step=None):
        return self.puzzle_engine.generate_quiz(difficulty, step)

    def generate_quiz_data(self, cycle):
        return self.quiz_generator.generate(cycle)

    def generate_chat_response(self, prompt, model="llama-3.1-8b-instant"):
        """Direct AI call for chat/hints."""
        if self.groq_api_key and self.groq_api_key != "your_groq_api_key_here":
            try:
                res = self._call_groq(prompt, model)
                if res: return res
            except:
                pass
        return "I cannot assist with that right now."

    def _call_groq(self, prompt, model):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            response = requests.post(url, headers=headers, json=data, timeout=5)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                print(f"Groq API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Groq API Exception: {e}")
        return None

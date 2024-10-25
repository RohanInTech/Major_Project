import openai
import time
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import pandas as pd
from openpyxl import load_workbook
import os
from openai.error import RateLimitError

# Set up Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Replace with your actual OpenAI API key
openai.api_key = "use your own api key"

# Handle root URL `/`
@app.route('/')
def index():
    return redirect(url_for('login'))  # Redirect to login page

# Handle favicon.ico request
@app.route('/favicon.ico')
def favicon():
    return '', 204  # or serve real favicon if you have one

# Function to generate questions and answers using OpenAI API
def generate_questions_and_answers(topic):
    try:
        messages = [
            {"role": "system", "content": "You are an aptitude test question generator."},
            {"role": "user", "content": f"Generate 5 aptitude questions for {topic} and provide correct answers. Structure the response as 'Question <number>: <question>' and 'Answer: <answer>' for each question."}
        ]
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        
        full_response = response['choices'][0]['message']['content']
        print("Full OpenAI response:", full_response)

        output_lines = full_response.split('\n')

        questions = []
        answers = []
        current_question = None

        for line in output_lines:
            line = line.strip()
            if line.startswith("Question"):
                current_question = line.split(":", 1)[1].strip()
                questions.append(current_question)
            elif line.startswith("Answer:") and current_question:
                answer = line.split(":", 1)[1].strip()
                answers.append(answer)
                current_question = None
        
        print("Parsed Questions:", questions)
        print("Parsed Answers:", answers)
        
        return questions, answers
    
    except RateLimitError:
        print("Rate limit exceeded. Retrying in 60 seconds...")
        time.sleep(60)
        return generate_questions_and_answers(topic)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        session['name'] = name  # Store name in session
        session['test_results'] = {}  # Initialize test results storage
        return redirect(url_for('dashboard'))
    return render_template('login.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'name' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    return render_template('index.html', name=session['name'])

# Route to generate questions
@app.route('/generate_questions', methods=['GET'])
def generate_questions_api():
    topic = request.args.get('topic')
    questions, correct_answers = generate_questions_and_answers(topic)

    session['generated_answers'] = correct_answers
    print("Correct answers stored in session:", session['generated_answers'])

    return jsonify({"questions": questions})

# Route to save test results
@app.route('/save_test', methods=['POST'])
def save_test():
    generated_answers = session.get('generated_answers')
    user_name = session.get('name')
    test_results = session.get('test_results', {})

    if not generated_answers:
        return jsonify({"error": "No correct answers found in the session."}), 400

    answers = request.json
    topic = request.args.get('topic')

    # Calculate the score
    score = 0
    total_questions = len(generated_answers)

    for idx, user_answer in answers.items():
        if user_answer.strip().lower() == generated_answers[int(idx[-1]) - 1].strip().lower():
            score += 1

    # Save the test results in the session
    test_results[topic] = {
        'score': score,
        'total_questions': total_questions
    }

    session['test_results'] = test_results
    return jsonify({"status": "success", "score": score, "total": total_questions})

# Route to submit all test results with feedback
@app.route('/submit_all_tests', methods=['POST'])
def submit_all_tests():
    user_name = session.get('name')
    test_results = session.get('test_results', {})

    if not test_results:
        return jsonify({"error": "No test results found."}), 400

    # Collect the feedback from the form submission
    feedback = request.form['feedback']

    # Prepare the data for saving to Excel
    results = {
        'name': user_name,
        'arithmetic_score': test_results.get('arithmetic', {}).get('score', 'N/A'),
        'arithmetic_total': test_results.get('arithmetic', {}).get('total_questions', 'N/A'),
        'algebra_score': test_results.get('algebra', {}).get('score', 'N/A'),
        'algebra_total': test_results.get('algebra', {}).get('total_questions', 'N/A'),
        'geometry_score': test_results.get('geometry', {}).get('score', 'N/A'),
        'geometry_total': test_results.get('geometry', {}).get('total_questions', 'N/A'),
        'feedback': feedback
    }

    df = pd.DataFrame([results])
    excel_filename = 'all_tests_results.xlsx'

    # Check if the Excel file exists and append data without overwriting
    if os.path.exists(excel_filename):
        # Load existing data
        existing_df = pd.read_excel(excel_filename, sheet_name='Results')
        # Concatenate the new data with the existing data
        df = pd.concat([existing_df, df], ignore_index=True)

    # Write back the combined data
    with pd.ExcelWriter(excel_filename, mode='w', engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Results')

    return jsonify({"status": "success", "message": "All tests and feedback submitted successfully!"})

if __name__ == '__main__':
    app.run(debug=True)

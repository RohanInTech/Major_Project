import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import os
import matplotlib.pyplot as plt
import numpy as np

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set this to a random string for security
analyzer = SentimentIntensityAnalyzer()

# Radar chart creation function
def create_spider_chart(student_name, arithmetic_score, algebra_score, geometry_score):
    categories = ['Arithmetic', 'Algebra', 'Geometry']
    scores = [arithmetic_score, algebra_score, geometry_score]

    # Radar chart needs data points repeated for the closing of the chart
    scores += scores[:1]
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]

    # Plot the radar chart
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, scores, color='blue', alpha=0.25)
    ax.plot(angles, scores, color='blue', linewidth=2)
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_title(f"Performance of {student_name}", size=15, color='black', y=1.1)

    # Save the chart as an image file
    file_path = f'static/{student_name}_radar_chart.png'
    plt.savefig(file_path)
    plt.close()  # Close the figure to free memory
    return file_path

# Route for homepage to upload the file
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle file upload
@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_path = os.path.join('uploads', file.filename)
            file.save(file_path)

            # Read the uploaded file (assuming it's in XLSX or CSV format)
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file.filename.endswith('.xlsx'):
                df = pd.read_excel(file_path)

            # Store DataFrame in session
            session['df'] = df.to_dict('records')
            return redirect(url_for('display_scores'))

# Route for displaying score options
@app.route('/display_scores')
def display_scores():
    return render_template('display_scores.html')

# Sorting and AI Analysis on arithmetic score
@app.route('/arithmetic_score')
def arithmetic_score():
    df = pd.DataFrame(session.get('df'))
    df['arithmetic_percentage'] = df['arithmetic_score'] / df['arithmetic_total'] * 100
    sorted_df = df.sort_values(by='arithmetic_percentage', ascending=False)

    positive_count, negative_count = analyze_feedback(df['feedback'])

    # Generate spider charts for each student
    spider_charts = []
    for index, student in sorted_df.iterrows():
        chart_path = create_spider_chart(student['name'], student['arithmetic_score'], student['algebra_score'], student['geometry_score'])
        spider_charts.append({'name': student['name'], 'chart_path': chart_path})

    # Zip the students and spider charts to pass them together
    zipped_data = zip(sorted_df.to_dict('records'), spider_charts)

    return render_template('sorted.html', zipped_data=zipped_data, positive_count=positive_count, negative_count=negative_count, subject="Arithmetic")

# Sorting and AI Analysis on algebra score
@app.route('/algebra_score')
def algebra_score():
    df = pd.DataFrame(session.get('df'))
    df['algebra_percentage'] = df['algebra_score'] / df['algebra_total'] * 100
    sorted_df = df.sort_values(by='algebra_percentage', ascending=False)

    positive_count, negative_count = analyze_feedback(df['feedback'])

    # Generate spider charts for each student
    spider_charts = []
    for index, student in sorted_df.iterrows():
        chart_path = create_spider_chart(student['name'], student['arithmetic_score'], student['algebra_score'], student['geometry_score'])
        spider_charts.append({'name': student['name'], 'chart_path': chart_path})

    zipped_data = zip(sorted_df.to_dict('records'), spider_charts)

    return render_template('sorted.html', zipped_data=zipped_data, positive_count=positive_count, negative_count=negative_count, subject="Algebra")

# Sorting and AI Analysis on geometry score
@app.route('/geometry_score')
def geometry_score():
    df = pd.DataFrame(session.get('df'))
    df['geometry_percentage'] = df['geometry_score'] / df['geometry_total'] * 100
    sorted_df = df.sort_values(by='geometry_percentage', ascending=False)

    positive_count, negative_count = analyze_feedback(df['feedback'])

    # Generate spider charts for each student
    spider_charts = []
    for index, student in sorted_df.iterrows():
        chart_path = create_spider_chart(student['name'], student['arithmetic_score'], student['algebra_score'], student['geometry_score'])
        spider_charts.append({'name': student['name'], 'chart_path': chart_path})

    zipped_data = zip(sorted_df.to_dict('records'), spider_charts)

    return render_template('sorted.html', zipped_data=zipped_data, positive_count=positive_count, negative_count=negative_count, subject="Geometry")

# Sentiment analysis function
def analyze_feedback(feedbacks):
    positive = 0
    negative = 0
    for feedback in feedbacks:
        sentiment_score = analyzer.polarity_scores(feedback)
        if sentiment_score['compound'] >= 0.05:
            positive += 1
        elif sentiment_score['compound'] <= -0.05:
            negative += 1
    return positive, negative

if __name__ == '__main__':
    # Ensure 'uploads' and 'static' directory exist
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    if not os.path.exists('static'):
        os.makedirs('static')

    app.run(debug=True)

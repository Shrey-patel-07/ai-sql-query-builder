from flask import Flask, render_template, request
import pandas as pd
import sqlite3
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the 'uploads' directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize history list to store query history
history = []

def run_sql_query(csv_files, sql_query):
    conn = sqlite3.connect(':memory:')
    
    for file_path in csv_files:
        df_name = os.path.splitext(os.path.basename(file_path))[0]  # Extract file name without extension
        df = pd.read_csv(file_path)
        df.to_sql(df_name, conn, index=False)
    
    result = pd.read_sql_query(sql_query, con=conn)
    
    return result.to_html()

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    query = None
    
    if request.method == 'POST':
        uploaded_files = request.files.getlist('file')
        csv_files = []
        for file in uploaded_files:
            if file.filename != '':
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                csv_files.append(file_path)
        
        sql_query = request.form['sql_query']
        query = sql_query
        
        # Execute SQL query and store result in history
        result = run_sql_query(csv_files, sql_query)
        history.append({'query': sql_query, 'result': result})
        
    return render_template('database_selection_index.html', result=result, query=query, history=history)

if __name__ == '__main__':
    app.run(debug=True)

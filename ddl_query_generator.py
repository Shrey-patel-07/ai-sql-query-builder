import os
import sqlite3
import warnings
import pandas as pd
from flask import Flask, render_template, request
from langchain_community.llms import Ollama
from langchain import PromptTemplate, LLMChain

app = Flask(__name__)

# Suppressing warnings
warnings.filterwarnings("ignore")

# Initializing the language model
llm = Ollama(model="pxlksr/defog_sqlcoder-7b-2:Q4_K")

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Prompt template for language model
template = """
### Task
Generate a SQL query to answer [QUESTION]{user_question}[/QUESTION]

### Instructions
- If you cannot answer the question with the available database schema, return 'I do not know'

### Database Schema
The query will run on a database with the following schema:
{table_metadata_string}

### Answer
Given the database schema, here is the SQL query that answers [QUESTION]{user_question}[/QUESTION]
[SQL]
"""

prompt = PromptTemplate(template=template, input_variables=["user_question", "table_metadata_string"])

# Function to get response from language model
def get_llm_response(user_question, table_metadata_string):
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    response = llm_chain.run({"user_question": user_question, "table_metadata_string": table_metadata_string})
    return response

def run_sql_query(csv_files, sql_query):
    conn = sqlite3.connect(':memory:')
    
    for file_path in csv_files:
        df_name = os.path.splitext(os.path.basename(file_path))[0]  # Extract file name without extension
        df = pd.read_csv(file_path)
        df.to_sql(df_name, conn, index=False)
    
    result = pd.read_sql_query(sql_query, con=conn)
    
    return result.to_html()


history = []
history_dll = []

@app.route('/', methods=['GET', 'POST'])
def ddl_query():
    ddl = None
    if request.method == 'POST':
        ddl = request.form['ddl']
        user_question = request.form.get('user_question', None)

        if user_question:
            output = get_llm_response(user_question, ddl)
            # Insert the new history item at the beginning of the list
            history_dll.insert(0, {'query': user_question, 'response': output})

    return render_template('index.html', history=history_dll, ddl=ddl)


@app.route('/dbms_query', methods=['GET', 'POST'])
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
    app.run(debug=True, port = 7860, host = '0.0.0.0')


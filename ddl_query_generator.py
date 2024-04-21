from flask import Flask, render_template, request

import warnings
from langchain_community.llms import Ollama
from langchain import PromptTemplate, LLMChain

app = Flask(__name__)

# Suppressing warnings
warnings.filterwarnings("ignore")

# Initializing the language model
llm = Ollama(model="pxlksr/defog_sqlcoder-7b-2:Q4_K")

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

history = []

@app.route('/', methods=['GET', 'POST'])
def index():
    ddl = None
    if request.method == 'POST':
        ddl = request.form['ddl']
        user_question = request.form.get('user_question', None)

        if user_question:
            output = get_llm_response(user_question, ddl)
            # Insert the new history item at the beginning of the list
            history.insert(0, {'query': user_question, 'response': output})

    return render_template('index.html', history=history, ddl=ddl)

if __name__ == '__main__':
    app.run(debug=True)

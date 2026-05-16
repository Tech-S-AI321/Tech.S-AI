from flask import Flask,request,render_template,url_for,redirect,jsonify,session
import requests
from google import genai
from google.genai import types
from sarvamai import SarvamAI
from openai import OpenAI
from groq import Groq
from supabase import create_client,Client
import re
from dotenv import load_dotenv
import os
from huggingface_hub import InferenceClient
from datetime import timedelta

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'key.env'))

# Supabase credentials
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url,key) 

openrouter_key = os.getenv("OPENROUTER_KEY")
gemini_key = os.getenv("GEMINI_KEY")
sarvam_key = os.getenv("SARVAMAI_KEY")
groq_key = os.getenv("GROQ_KEY")
deepseek_key:str = os.getenv('Deepseek_KEY')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.permanent_session_lifetime = timedelta(days=90)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup/',methods=['GET','POST'])
def signup():
    success = None
    error = None
    if request.method=='POST':
        email=request.form.get('email')
        password=request.form.get('password')
        try:
            user = supabase.auth.sign_up({
            "email": email,
            "password": password
            })
            success = f"Account created successfully! A verification email has been sent to {email}. Please check your inbox."
            return render_template('login.html', success=success)
        except Exception as e:
            error = "Sign up failed. Email might already be registered or password is too weak."
            return render_template('signup.html', error=error)
    return render_template('signup.html')

@app.route('/login/',methods=['GET','POST'])
def login():
    error = None
    success = None
    if request.method=='POST':
        email=request.form.get('email')
        password=request.form.get('password')
        try:
            user = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            session.permanent=True
            session['user'] = email
            success = f"Login successful! A confirmation email has been sent to {email}."
            return redirect(url_for('chat'))
        except Exception as e:
            error = "Login failed. Please check your email and password."
    return render_template('login.html',error=error, success=success)

#OPENROUTER:-
def ask_ai(prompt,model,des,history):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization":f'Bearer {openrouter_key}',
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": f'{des}, The memory = {history}. You are working on Tech.S AI platform, its founder is Srijan Mishra(CEO/Scientist), and he is only 12 years old, he integrated you in this Tech.S AI app.'},
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            return f"OpenRouter error {response.status_code}: {response.text}"

        result = response.json()
        if 'choices' not in result or not result['choices']:
            return f"OpenRouter returned unexpected response: {result}"

        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"Sorry sir there is an error.{e}"

#Gemini
def ask_gemini(prompt,history):
    try:
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
            config=types.GenerateContentConfig(
            system_instruction=f"This is your memory={history}. You are working on Tech.S AI platform, its founder is Srijan Mishra(CEO/Scientist), and he is only 12 years old, he integrated you in this Tech.S AI app."
            )
        )
        return response.text
    except Exception as e:
        return f"Error: {e}"

#Sarvam
def ask_sarvam(prompt,history):
    try:
        client = SarvamAI(api_subscription_key=sarvam_key)
        response = client.chat.completions(
            model="sarvam-m",
            messages=[
                {"role": "system", "content": f"You are a helpful AI assistant. Only give the final answer directly. And this is your memory-{history}. You are working on Tech.S AI platform, its founder is Srijan Mishra(CEO/Scientist), and he is only 12 years old, he integrated you in this Tech.S AI app."},
                {"role": "user", "content": prompt}
            ]
        )
        #return response.choices[0].message.content
        answer = response.choices[0].message.content
        answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
        return answer
    except Exception as e:
        return f"Error: {e}"


#Deepseek 
client = InferenceClient(api_key=deepseek_key)

def ask_deepseek(prompt,history):
    try:
        # We use DeepSeek-V3 (the current stable public version)
        response = client.chat_completion(
            model='deepseek-ai/DeepSeek-V3',
            messages=[{"role": "system", "content": f"Your memory is-{history}. You are working on Tech.S AI platform, its founder is Srijan Mishra(CEO/Scientist), and he is only 12 years old, he integrated you in this Tech.S AI app."},
                      {"role": "user", "content": prompt}
                     ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

#Groq "llama-3.3-70b-versatile"
def ask_groq(prompt,model,history):
    try:
        client = Groq(api_key=groq_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"Your memory is -{history}. You are working on Tech.S AI platform, its founder is Srijan Mishra(CEO/Scientist), and he is only 12 years old, he integrated you in this Tech.S AI app."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def ask_qwen(prompt,history):
    try:
        client = InferenceClient(api_key=deepseek_key)  # use your HF key
        response = client.chat_completion(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[{"role": "system", "content": f"Your memory is-{history}. You are working on Tech.S AI platform, its founder is Srijan Mishra(CEO/Scientist), and he is only 12 years old, he integrated you in this Tech.S AI app."},
                      {"role": "user", "content": prompt}
                     ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def get_ai_response(ai, ask,history):
    if ai == 'Gemini':
        return ask_gemini(ask,history)
    elif ai == 'ChatGPT':
        return ask_ai(ask,'openai/gpt-oss-120b:free','You are ChatGPT an helpful and smart ai assistant.',history)
    elif ai == 'Qwen':
        return ask_qwen(ask,history)
    elif ai == 'Deepseek':
        return ask_deepseek(ask,history)
    elif ai == 'Meta Ai':
        return ask_groq(ask,"llama-3.3-70b-versatile",history)
    elif ai == 'Sarvam':
        return ask_sarvam(ask,history)
    elif ai == 'Z.ai':
        return ask_ai(ask,'z-ai/glm-4.5-air:free','You are Z.ai an helpful and smart ai assistant',history)
    elif ai == 'Nvidia Nemotron':
        return ask_ai(ask,'nvidia/nemotron-3-super-120b-a12b:free','You are Nvidia Nemotron an helpful and smart ai assistant.',history)


@app.route('/chat/api', methods=['POST'])
def chat_api():
    print("session:",session)
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json(force=True)
    ai = data.get('aimodel')
    ask = data.get('chat')
    history_response = supabase.table('chats')\
        .select('*')\
        .eq('user_email', session['user'])\
        .order('created_at')\
        .execute()
    history = history_response.data
    ans = get_ai_response(ai, ask,history)
    
    #Save to Supabase
    supabase.table('chats').insert({
        'user_email': session['user'],
        'ai_model': ai,
        'question': ask,
        'answer': ans
    }).execute()
    
    return jsonify({'ans': ans})

@app.route('/chat/', methods=['GET', 'POST'])
def chat():
    if 'user' not in session:
       return redirect(url_for('login'))
    history_response = supabase.table('chats')\
        .select('*')\
        .eq('user_email', session['user'])\
        .order('created_at')\
        .execute()
    history = history_response.data
    ans = ''
    if request.method == 'POST':
        ai = request.form.get('aimodel')
        ask1 = request.form.get('chat')
        ask=f'This is the chat history-{history}.Give the answer while remmebring the chat history.And you have to answer this-{ask1}'
        ans = get_ai_response(ai, ask,history)
    return render_template('chat.html', ans=ans, history=history)

@app.route('/logout/')
def logout():
    session.clear()
    return render_template('home.html')
if __name__=="__main__":
    app.run(debug=True, port=400, host='0.0.0.0')

from flask import Flask,request,render_template,url_for,redirect,jsonify,session,send_from_directory,make_response
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
import time
from flask import send_file

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
hanu_key:str = os.getenv('hanu_key')

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY')
app.permanent_session_lifetime = timedelta(days=90)


@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('chat')) 
    return render_template('home.html')
    
@app.route('/icon.png')
def serve_icon():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'icon.png')


@app.route('/manifest.json')
def manifest():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'manifest.json')

@app.route('/sw.js')
def service_worker():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'sw.js')

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

#Gemini
def ask_gemini(prompt):
    try:
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
            system_instruction=f"You are the best doctor in the world, so you have to help the patient with his/her disease, and give best possible advices and treatments.You have to make a report like a real doctor for the patient and in simplest way possible.And at the last you have to tell the patient to consult a specific doctor if needed."
            )
        )  
        return response.text
    except Exception as e:
        try:
            response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
            system_instruction=f"You are the best doctor in the world, so you have to help the patient with his/her disease, and give best possible advices and treatments.You have to make a report like a real doctor for the patient and in simplest way possible.And at the last you have to tell the patient to consult a specific doctor if needed."
            )
            )
            return response.text
        except Exception as e:
            return f"Error: {e}"

#Sarvam
def ask_sarvam(prompt):
    try:
        client = SarvamAI(api_subscription_key=sarvam_key)
        response = client.chat.completions(
            model="sarvam-m",
            messages=[
                {"role": "system", "content": f"You are the best doctor in the world, so you have to help the patient with his/her disease, and give best possible advices and treatments.You have to make a report like a real doctor for the patient and in simplest way possible.And at the last you have to tell the patient to consult a specific doctor if needed."},                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content
        answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
        return answer
    except Exception as e:
        return f"Error: {e}"

#Deepseek (Reuse client to avoid recreating)
deepseek_client = InferenceClient(api_key=hanu_key)

def ask_deepseek(prompt):
    try:
        response = deepseek_client.chat_completion(
            model='deepseek-ai/DeepSeek-V3',
            messages=[
                {"role": "system", "content": f"You are the best doctor in the world, so you have to help the patient with his/her disease, and give best possible advices and treatments.You have to make a report like a real doctor for the patient and in simplest way possible.And at the last you have to tell the patient to consult a specific doctor if needed."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

#Groq
def ask_groq(prompt):
    try:
        client = Groq(api_key=groq_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"You are the best doctor in the world, so you have to help the patient with his/her disease, and give best possible advices and treatments.You have to make a report like a real doctor for the patient and in simplest way possible.And at the last you have to tell the patient to consult a specific doctor if needed."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

#Qwen (Reuse client to avoid recreating)
qwen_client = InferenceClient(api_key=hanu_key)

def ask_qwen(prompt):
    try:
        response = qwen_client.chat_completion(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {"role": "system", "content":f"You are the best doctor in the world, so you have to help the patient with his/her disease, and give best possible advices and treatments.You have to make a report like a real doctor for the patient and in simplest way possible.And at the last you have to tell the patient to consult a specific doctor if needed."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=7000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"
#ChatGPT
gptoss_client = InferenceClient(api_key=hanu_key)

def ask_chatgpt(prompt,ai1,ai2,ai3,ai4,ai5):
    try:
        response = gptoss_client.chat_completion(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": f"You are the best doctor in the world, so you have to help the patient with his/her disease, and give best possible advices and treatments from these 5 ai responses-{ai1} ,{ai2} ,{ai3} ,{ai4} ,{ai5}.You have to make a report by mixixng the best ai responses and add you own knowledge also like a real doctor for the patient and in simplest way possible.And at the last you have to tell the patient to consult a specific doctor if needed."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=7000
        )
        print(response.choices[0].message.content)
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}" 

def get_ai_response(ask):
    ai1 = "skipped"
    ai2 = "skipped"
    ai3 = "skipped"
    ai4 = "skipped"
    ai5 = "skipped"
    resp = ask_chatgpt(ask,ai1,ai2,ai3,ai4,ai5)
    return resp

@app.route('/chat/api', methods=['POST'])
def chat_api():
    print("session:", session)
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        data = request.get_json(force=True)
        ask = data.get('chat')
        
        # Get chat history
        try:
            history_response = supabase.table('chats')\
                .select('*')\
                .eq('user_email', session['user'])\
                .order('created_at', desc=True)\
                .execute()
            history = history_response.data
        except Exception as e:
            print(f"Error fetching chat history: {e}")
        
        # Get AI response
        ans = get_ai_response(ask)
        
        # Save to Supabase
        try:
            supabase.table('chats').insert({
                'user_email': session['user'],
                'question': ask,
                'answer': ans
            }).execute()
        except Exception as e:
            print(f"Error saving to Supabase: {e}")
        
        return jsonify({'ans': ans})
    
    except Exception as e:
        print(f"Chat API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/chat/', methods=['GET', 'POST'])
def chat():
    if 'user' not in session:
       return redirect(url_for('login'))
    history_response = supabase.table('chats')\
        .select('*')\
        .eq('user_email', session['user'])\
        .order('created_at', desc=True)\
        .execute()
    history = history_response.data
    ans = ''
    if request.method == 'POST':
        ask = request.form.get('chat')
        ans = get_ai_response(ask)
    
    return render_template('chat.html', ans=ans, history=history)

@app.route('/logout/')
def logout():
    session.clear() # Clear Flask server-side session
    
    response = make_response(redirect(url_for('login')))
    # Force browser to clear any cache for this request
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    return response
if __name__=="__main__":
    app.run(debug=True, port=5000, host='0.0.0.0')


from flask import Flask,request,render_template,url_for,redirect,jsonify,session,send_from_directory
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

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY')
app.permanent_session_lifetime = timedelta(days=365)

@app.route('/')
def home():
    return render_template('home.html')
    
@app.route('/icon.png')
def serve_icon():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'icon.png')

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

#OPENROUTER with Retry Logic
def ask_ai(prompt, model, des, max_retries=3):
    """
    Call OpenRouter API with retry logic for free models.
    Free models are rate-limited, so retries help with intermittent failures.
    """
    for attempt in range(max_retries):
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"

            headers = {
                "Authorization": f'Bearer {openrouter_key}',
                "Content-Type": "application/json",
                "HTTP-Referer": "http://tech-s-ai-w1qo.onrender.com",
                "X-Title": "Tech.S AI"
            }

            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": f'{des}. You are working on Tech.S AI platform, its founder is Srijan Mishra(CEO/Scientist), and he is only 12 years old, he integrated you in this Tech.S AI app.'},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }

            # Add timeout to prevent hanging (increased to 45s for free models)
            response = requests.post(url, headers=headers, json=data, timeout=45)
            
            print(f"[Attempt {attempt + 1}/{max_retries}] OpenRouter Status: {response.status_code}")

            # Rate limited - wait and retry
            if response.status_code == 429:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"Rate limited. Waiting {wait_time}s before retry...")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    return "OpenRouter is currently rate limited. Please try again in a few moments."

            # Authentication error
            if response.status_code == 401:
                return "OpenRouter authentication failed. Check your API key in key.env"

            # Server error - retry
            if response.status_code >= 500:
                wait_time = 2 ** attempt
                print(f"Server error {response.status_code}. Waiting {wait_time}s before retry...")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    return f"OpenRouter server error {response.status_code}. Please try again later."

            # Other HTTP errors
            if response.status_code != 200:
                print(f"OpenRouter Error {response.status_code}: {response.text}")
                return f"OpenRouter error {response.status_code}"

            # Parse response
            try:
                result = response.json()
            except Exception as e:
                print(f"JSON Parse Error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return "Invalid response format from OpenRouter"

            # Validate response structure
            if 'choices' not in result or not result['choices']:
                print(f"No choices in response: {result}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return "OpenRouter returned no response choices"

            if 'message' not in result['choices'][0]:
                print(f"No message in choices: {result}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return "OpenRouter returned no message content"

            # Success!
            return result['choices'][0]['message']['content']

        except requests.exceptions.Timeout:
            print(f"Timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            else:
                return "Request timed out. The model is taking too long to respond."

        except requests.exceptions.ConnectionError as e:
            print(f"Connection error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            else:
                return "Connection error with OpenRouter. Check your internet."

        except Exception as e:
            print(f"Unexpected error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                return f"Unexpected error: {str(e)}"

    return "Failed to get response from OpenRouter after multiple attempts."

#Gemini
def ask_gemini(prompt):
    try:
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
            config=types.GenerateContentConfig(
            system_instruction=f"You are working on Tech.S AI platform, its founder is Srijan Mishra(CEO/Scientist), and he is only 12 years old, he integrated you in this Tech.S AI app."
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
                {"role": "system", "content": f"You are a helpful AI assistant. Only give the final answer directly. You are working on Tech.S AI platform, its founder is Srijan Mishra(CEO/Scientist), and he is only 12 years old, he integrated you in this Tech.S AI app."},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content
        answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
        return answer
    except Exception as e:
        return f"Error: {e}"

#Deepseek (Reuse client to avoid recreating)
deepseek_client = InferenceClient(api_key=deepseek_key)

def ask_deepseek(prompt):
    try:
        response = deepseek_client.chat_completion(
            model='deepseek-ai/DeepSeek-V3',
            messages=[
                {"role": "system", "content": f"You are working on Tech.S AI platform, its founder is Srijan Mishra(CEO/Scientist), and he is only 12 years old, he integrated you in this Tech.S AI app."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

#Groq
def ask_groq(prompt, model):
    try:
        client = Groq(api_key=groq_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are working on Tech.S AI platform, its founder is Srijan Mishra(CEO/Scientist), and he is only 12 years old, he integrated you in this Tech.S AI app."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

#Qwen (Reuse client to avoid recreating)
qwen_client = InferenceClient(api_key=deepseek_key)

def ask_qwen(prompt):
    try:
        response = qwen_client.chat_completion(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {"role": "system", "content": f"You are working on Tech.S AI platform, its founder is Srijan Mishra(CEO/Scientist), and he is only 12 years old, he integrated you in this Tech.S AI app."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=7000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def get_ai_response(ai, ask):
    if ai == 'Gemini':
        return ask_gemini(ask)
    elif ai == 'ChatGPT':
        return ask_ai(ask, 'openai/gpt-oss-120b:free', 'You are ChatGPT an helpful and smart ai assistant.')
    elif ai == 'Qwen':
        return ask_qwen(ask)
    elif ai == 'Deepseek':
        return ask_deepseek(ask)
    elif ai == 'Meta Ai':
        return ask_groq(ask, "llama-3.3-70b-versatile")
    elif ai == 'Sarvam':
        return ask_sarvam(ask)
    elif ai == 'Z.ai':
        return ask_ai(ask, 'z-ai/glm-4.5-air:free', 'You are Z.ai an helpful and smart ai assistant')
    elif ai == 'Nvidia Nemotron':
        return ask_ai(ask, 'nvidia/nemotron-3-super-120b-a12b:free', 'You are Nvidia Nemotron an helpful and smart ai assistant.')
    else :
        return "AI model not found!"

@app.route('/chat/api', methods=['POST'])
def chat_api():
    print("session:", session)
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        data = request.get_json(force=True)
        ai = data.get('aimodel')
        ask = data.get('chat')
        
        # Validate input
        if not ai or not ask:
            return jsonify({'error': 'Missing aimodel or chat parameter'}), 400
        
        # Get chat history
        try:
            history_response = supabase.table('chats')\
                .select('*')\
                .eq('user_email', session['user'])\
                .order('created_at')\
                .execute()
            history = history_response.data
        except Exception as e:
            print(f"Error fetching chat history: {e}")
            history = []
        
        # Get AI response
        ans = get_ai_response(ai, ask)
        
        # Save to Supabase
        try:
            supabase.table('chats').insert({
                'user_email': session['user'],
                'ai_model': ai,
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
    
    try:
        history_response = supabase.table('chats')\
            .select('*')\
            .eq('user_email', session['user'])\
            .order('created_at')\
            .execute()
        history = history_response.data
    except Exception as e:
        print(f"Error fetching chat history: {e}")
        history = []
    
    ans = ''
    if request.method == 'POST':
        ai = request.form.get('aimodel')
        ask = request.form.get('chat')
        ans = get_ai_response(ai, ask)
    
    return render_template('chat.html', ans=ans, history=history)

@app.route('/logout/')
def logout():
    session.clear()
    return render_template('home.html')

if __name__=="__main__":
    app.run(debug=True, port=400, host='0.0.0.0')

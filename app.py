from flask import Flask, render_template, request, redirect, url_for
from duckduckgo_search import DDGS
import requests, json, httpx
from bs4 import BeautifulSoup
import g4f
from g4f.client import Client

port = 4000
app = Flask(__name__)

client = Client(provider=g4f.Provider.MetaAI)

# Extract Text Function
def extract_text_from_website(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }
        with httpx.Client(headers=headers, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            for element in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
                element.decompose()

            text = soup.get_text(separator=' ', strip=True)
            cleaned_text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
            return cleaned_text[:500]  # limit text to 500 chars

    except httpx.HTTPStatusError as e:
        return f"HTTP Error: {e}"
    except httpx.RequestError as e:
        return f"Request Error: {e}"

# Payload Generation
def payload_gen(word, add, img):
    global http
    payloads = []
    results = DDGS().text(f'"{word}"', max_results=9)
    addresults = DDGS().text(f'{word} {add}', max_results=3)
    
    payload = f"Write me a comprehensive report on a person that is as detailed as possible. The person's name is, {word}."
    payload += f" Here is the data with links:\n"
    
    gptstring = ""
    http = []
    
    # Processing results for the payload
    for x in results[:5]:
        gptstring += str(x) + '\n'
        if 'href' in x:
            http.append(x['href'])
    
    payloads.append(payload + gptstring)
    
    for url in http:
        content = extract_text_from_website(url)
        payloads.append(f"Extracted data from {url}: {content}")
    
    return payloads

# Chatbot Simulation
def chat(payloads):
    messages = []
    responses = []
    
    for i, payload in enumerate(payloads):
        messages.append({"role": "user", "content": payload})
        response = client.chat.completions.create(
            messages=messages,
            model="Meta-Llama-3-70b-instruct",
        )
        gpt_response = response.choices[0].message.content
        responses.append(gpt_response)

    return responses

# Email Breach Check
def email_address_check(email):
    url = "https://webapi.namescan.io/v1/freechecks/email/breaches"
    payload = {"email": email}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        data = response.json()
        breaches = data.get("breaches", [])
        return breaches
    return []

# Instagram API Check
def instagram_check(insta_username):
    url = "https://instagram-scraper-api2.p.rapidapi.com/v1/info"
    querystring = {"username_or_id_or_url": insta_username}
    headers = {
        "x-rapidapi-key": "7cef9caf7emshbcd7d852995df3cp114277jsn623179640e47",
        "x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code == 200:
        return response.json().get('data', {})
    return {}

# Routes
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        word = request.form.get("query")
        add = request.form.get("keyword")
        img = request.form.get("images")
        email = request.form.get("email")
        insta = request.form.get("instagram")

        payloads = payload_gen(word, add, img)
        chat_responses = chat(payloads)

        email_breaches = email_address_check(email)
        instagram_data = instagram_check(insta)

        return render_template("results.html", 
                               chat_responses=chat_responses, 
                               email_breaches=email_breaches, 
                               instagram_data=instagram_data)
    
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)


from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from openai import OpenAI
import pdfplumber
import os

# -----------------------------------
# Load environment variables
# -----------------------------------
load_dotenv()

# -----------------------------------
# Flask app
# -----------------------------------
app = Flask(__name__)

# -----------------------------------
# OpenAI client (API key from .env)
# -----------------------------------
client = OpenAI()

# -----------------------------------
# PDF text extraction
# -----------------------------------
def extract_text_from_pdf(pdf_path):
    text = ""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text

# Limit PDF text to avoid token issues
PDF_PATH = "./Travels2.pdf"
pdf_text = extract_text_from_pdf(PDF_PATH)[:3000]


# -----------------------------------
# Routes
# -----------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"response": "Please enter a valid question."})

    system_prompt = (
        "You are a friendly, engaging Travel Customer Support assistant.\n"
    "Talk naturally like a human sales assistant.\n\n"

    "MEMORY & FLOW RULES:\n"
    "1. Remember what the user has already confirmed (destination, trip type, budget).\n"
    "2. Do NOT ask the same question again once it is answered.\n"
    "3. If the user provides a budget or price range, respond with the BEST matching package.\n"
    "4. If the user clearly selects a destination (e.g., Hunza), focus ONLY on that destination.\n"
    "5. Ask ONLY ONE question per reply, and only if something is missing.\n\n"

    "PACKAGE RULES:\n"
    "- Hunza tour is a 10-day Northern Areas package.\n"
    "- Use solo / couple / group prices exactly as defined.\n"
    "- If the budget fits the package, confirm it clearly.\n"
    "- If the budget does NOT fit, politely explain and suggest the closest option.\n\n"

    "If information is missing, respond politely:\n"
    "'Sorry, I am not aware of that information right now.'"
    )

    try:
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"PDF CONTENT:\n{pdf_text}\n\nQUESTION:\n{user_message}"
                }
            ],
            max_output_tokens=150
        )

        bot_message = response.output[0].content[0].text

    except Exception as e:
        bot_message = f"Error: {str(e)}"

    return jsonify({"response": bot_message})

# -----------------------------------
# Run app
# -----------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

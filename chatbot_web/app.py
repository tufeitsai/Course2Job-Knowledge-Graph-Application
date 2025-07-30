from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # 🆕
from assistant import Course2JobAssistant

app = Flask(__name__)
CORS(app)  # 🆕 Allow all origins

assistant = Course2JobAssistant()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/greet", methods=["GET"])
def greet():
    greeting = assistant.greet()
    return jsonify({"greeting": greeting})

@app.route("/new", methods=["POST"])
def new_conversation():
    assistant.reset()
    greeting = assistant.greet()
    return jsonify({"greeting": greeting})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data["message"]
    reply = assistant.start(user_input)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)

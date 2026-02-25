from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'quizmaze_secret_key'

database_url = os.getenv("DATABASE_URL", "sqlite:///quizmaze.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# USER TABLE
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# LEADERBOARD TABLE
class Leaderboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    score = db.Column(db.Integer)
# QUESTION TABLE
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200), nullable=False)
    option4 = db.Column(db.String(200), nullable=False)
    correct = db.Column(db.Integer, nullable=False)
with app.app_context():
    db.create_all()
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
  
@app.route('/')
@app.route('/home')
def home():
    return render_template("index.html")

@app.route("/play")
@login_required
def play():
    return render_template("play.html")

@app.route("/create")
@login_required
def create():
    questions = Question.query.all()
    return render_template("create.html", questions=questions)

@app.route("/add-question", methods=["POST"])
@login_required
def add_question():
    new_question = Question(
        question=request.form["question"],
        option1=request.form["option1"],
        option2=request.form["option2"],
        option3=request.form["option3"],
        option4=request.form["option4"],
        correct=int(request.form["correct"])
    )

    db.session.add(new_question)
    db.session.commit()

    return redirect(url_for("create"))

@app.route("/delete-question/<int:id>")
@login_required
def delete_question(id):
    question = Question.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    return redirect(url_for("create"))

@app.route("/edit-question/<int:id>")
@login_required
def edit_question(id):
    question = Question.query.get_or_404(id)
    return render_template("edit.html", question=question)

@app.route("/update-question/<int:id>", methods=["POST"])
@login_required
def update_question(id):
    question = Question.query.get_or_404(id)

    question.question = request.form["question"]
    question.option1 = request.form["option1"]
    question.option2 = request.form["option2"]
    question.option3 = request.form["option3"]
    question.option4 = request.form["option4"]
    question.correct = int(request.form["correct"])

    db.session.commit()

    return redirect(url_for("create"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        else:
            return "Invalid credentials"

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists"

        hashed_password = generate_password_hash(password)

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

@app.route("/add-score", methods=["POST"])
@login_required
def add_score():
    data = request.json
    name = current_user.username   # logged-in user
    score = data["score"]

    new_score = Leaderboard(name=name, score=score)
    db.session.add(new_score)
    db.session.commit()

    return jsonify({"message": "Score saved"})

@app.route("/leaderboard")
def get_leaderboard():
    top_scores = Leaderboard.query.order_by(Leaderboard.score.desc()).limit(10).all()

    result = []
    for entry in top_scores:
        result.append({
            "name": entry.name,
            "score": entry.score
        })

    return jsonify(result)
@app.route("/get-custom-questions")
@login_required
def get_custom_questions():
    questions = Question.query.all()

    result = []
    for q in questions:
        result.append({
            "q": q.question,
            "options": [
                q.option1,
                q.option2,
                q.option3,
                q.option4
            ],
            "correct": q.correct - 1   # because JS uses 0 index
        })

    return jsonify(result)
if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True)

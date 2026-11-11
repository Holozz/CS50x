from flask import Flask, render_template, request

app = Flask(__name__)

SPORTS = [
   "Basketball",
   "Soccer",
   "Ultimate Frisbsee",
]

REGISTRANTS={}

@app.route("/")
def index():
  html = render_template("index.html",sports=SPORTS)
  return html

@app.route("/register", methods=["POST"])
def register():
   name = request.form.get("name")
   if not name:
      return render_template("failure.html",error="MISSING NAME!")
   elif not request.form.get("sport"):
      return render_template("failure.html",error="MISSING SPORT!")
   elif request.form.get("sport") not in SPORTS:
      return render_template("failure.html",error="INVALID SPORT!")

   REGISTRANTS[name]=request.form.get("sport")

   return render_template("success.html", placeholder = name)

@app.route("/registrants")
def registrants():
   return render_template("registrants.html",registrants=REGISTRANTS)

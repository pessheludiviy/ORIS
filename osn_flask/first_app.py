from flask import Flask, render_template, redirect, request, url_for

app = Flask(__name__)

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/items")
def items():
    data = [
        {"title": "anya", "desc": "не знаю кто это"},
        {"title": "bulat", "desc": "ооо илюха монеси"},
        {"title": "hello", "desc": "здарова"}
    ]
    return render_template("items.html", items=data)

@app.get("/user/<name>")
def user(name):
    return render_template("user.html", name=name)

@app.get("/search")
def search():
    username = request.args.get("username")
    if username:
        return redirect(url_for("user", name=username))
    return render_template("search.html")

if __name__ == "__main__":
    app.run(debug=True)

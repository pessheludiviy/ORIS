from flask import Flask, request, session, redirect, url_for, render_template
import psycopg2
from flask_sqlalchemy import SQLAlchemy

with open('props.txt', 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()

db_password = lines[0].strip()
secret_key_from_props = lines[1].strip()

conn = psycopg2.connect(
    dbname='flask_app',
    user='postgres',
    password=db_password,
    host='localhost'
)

cur = conn.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(20) UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
''')
conn.commit()

cur.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        user_id INTEGER PRIMARY KEY,
        bio TEXT DEFAULT '',
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
""")
conn.commit()

app = Flask(__name__)
app.secret_key = secret_key_from_props


@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('profile'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        bio = request.form.get('bio', '')
        if not username or not password:
            return render_template('register.html', error="Укажите имя пользователя и пароль")

        cur = conn.cursor()
        cur.execute(""" 
            SELECT id FROM users WHERE username = %s
        """, (username,))

        if cur.fetchone():
            cur.close()
            return render_template('register.html', error="Пользователь уже существует")

        cur.execute(""" 
            INSERT INTO users (username, password) 
            VALUES (%s, %s)
            RETURNING id
        """, (username, password))
        conn.commit()
        user_id = cur.fetchone()[0]

        cur.execute(""" 
            INSERT INTO profiles (user_id, bio) VALUES (%s, %s)
        """, (user_id, bio))
        conn.commit()
        cur.close()

        session['user_id'] = user_id
        return redirect(url_for('profile'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            return render_template('login.html', error='Укажите имя пользователя и пароль')

        cur = conn.cursor()
        cur.execute('''
            SELECT id, password FROM users
            WHERE username = (%s)
        ''', (username,))

        row = cur.fetchone()
        cur.close()

        if not row:
            return render_template('login.html', error="Неверный логин или пароль")

        user_id, pas = row
        if pas != password:
            return render_template('login.html', error="Неверный логин или пароль")

        session['user_id'] = user_id
        return redirect(url_for('profile'))

    return render_template('login.html')


@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    cur = conn.cursor()
    cur.execute('''
        SELECT u.username, p.bio FROM users u
        JOIN profiles p ON u.id = p.user_id
        WHERE u.id = (%s)
    ''', (user_id,))
    row = cur.fetchone()
    cur.close()

    if not row:
        return render_template('profile.html', error="Пользователь не найден")

    username, bio = row
    return render_template('profile.html', username=username, bio=bio)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://postgres:{db_password}@localhost:5432/flask_app"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    products = db.relationship("Product", back_populates="category")


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    price = db.Column(db.Integer)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    category = db.relationship("Category", back_populates="products")


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)

    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete")


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    quantity = db.Column(db.Integer)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product")


with app.app_context():
    db.create_all()
    if not Category.query.first():  # есть ли хоть одна таблица к категориях
        cat1 = Category(name="Котики")
        cat2 = Category(name="Собачки")

        db.session.add_all([cat1, cat2])
        db.session.commit()

        db.session.add_all([
            Product(name="Кошечка милая", price=90000, category=cat1),
            Product(name="Кошечка злая", price=25000, category=cat1),
            Product(name="Собачка смешная", price=120000, category=cat2),
            Product(name="Собачка добрая", price=70000, category=cat2)
        ])
        db.session.commit()


def init_cart():
    if 'cart' not in session:
        session['cart'] = {}


@app.route('/shop')
def shop():
    return redirect(url_for('products'))


@app.route('/products')
def products():
    items = Product.query.all()  # это типо достать все товары из таблцы продуктс
    return render_template("products.html", items=items)


@app.route('/add/<int:product_id>')
def add_to_cart(product_id):
    init_cart()
    cart = session['cart']
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session.modified = True
    return redirect(url_for('cart'))


@app.route("/cart")
def cart():
    init_cart()
    cart = session["cart"]

    products = []
    for product_id, kolvo in cart.items():
        p = db.session.get(Product, int(product_id))
        if p:
            products.append((p, kolvo))

    return render_template("cart.html", items=products)


@app.route("/remove/<int:product_id>")
def remove(product_id):
    init_cart()
    session["cart"].pop(str(product_id), None)
    session.modified = True
    return redirect(url_for("cart"))


@app.route("/checkout")
def checkout():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    cart = session["cart"]

    if not cart:
        return "Корзина пуста"

    order = Order(user_id=user_id)
    db.session.add(order)
    db.session.commit()

    for product_id, kolvo in cart.items():
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=int(product_id),
            quantity=kolvo
        ))
    db.session.commit()

    session["cart"] = {}
    return render_template('cart.html', mess="Заказ успешно оформлен!")


if __name__ == "__main__":
    app.run(debug=True)
# python -m venv myenv
# myenv\Scripts\activate
# pip install flask sqlalchemy flask-sqlalchemy flask-marshmallow mysql-connector-python

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields, ValidationError, validate
from password import my_password

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://root:{my_password}@localhost/e_commerce_db'
db = SQLAlchemy(app)
ma = Marshmallow(app)

class CustomerSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=1))
    email = fields.String(required=True, validate=validate.Email()) # TODO make sure this validation doesn't need an argument passed in. Might need an *?
    phone = fields.String(required=True, validate=validate.Length(min=6)) # Set min as 6 in case area code is omitted

    class Meta:
        fields = ('name', 'email', 'phone', 'id')

class OrderSchema(ma.Schema):
    date = fields.Date(required=True) #validate=validate.Regexp(regex stuff))
    customer_id = fields.String(required=True, validate=validate.Length(min=0))

    class Meta:
        fields = ('date', 'customer_id', 'id')

class ProductSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=1))
    price = fields.Float(required=True, validate=validate.Range(min=0))

    class Meta:
        fields = ('name', 'price', 'id')

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

class Customer(db.Model):
    __tablename__ = 'Customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(320), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    orders = db.relationship('Order', backref='customer')

class Order(db.Model):
    __tablename__ = 'Orders'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))

# One-to-One
class CustomerAccount(db.Model):
    __tablename__ = 'Customer_Accounts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))
    customer = db.relationship('Customer', backref='customer_account', uselist=False)

# Many-to-Many - Needs a connecting table
order_product = db.Table('Order_Product',
        db.Column('order_id', db.Integer, db.ForeignKey('Orders.id'), primary_key=True),
        db.Column('product_id', db.Integer, db.ForeignKey('Products.id'), primary_key=True)
)

class Product(db.Model):
    __tablename__ = 'Products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    orders = db.relationship('Order', secondary=order_product, backref=db.backref('products')) 
    # secondary tells SQLAlchemy to use the order_product table for the association table

@app.route('/')
def home():
    return 'Welome to the E-Commerce Database'


@app.route('/customers', methods = ['GET'])
def get_customers():
    customers = Customer.query.all()
    return customers_schema.jsonify(customers)


@app.route('/customers', methods = ['POST'])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    new_customer = Customer(name=customer_data['name'], phone=customer_data['phone'], email=customer_data['email'])
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({"message": "New Customer added successfully"}), 201


@app.route('/customers/<int:id>', methods = ['PUT'])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    customer.name = customer_data['name']
    customer.phone = customer_data['phone']
    customer.email = customer_data['email']
    
    db.session.commit()
    return jsonify({"message": "Customer details updated successfully"}), 200


@app.route('/customers/<int:id>', methods = ['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer removed successfully"}), 200

@app.route('/orders', methods = ['GET'])
def get_orders():
    orders = Order.query.all()
    return orders_schema.jsonify(orders)

@app.route('/orders', methods = ['POST'])
def add_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    new_order = Order(date=order_data['date'], customer_id=order_data['customer_id'])
    db.session.add(new_order)
    db.session.commit()
    return jsonify({"message": "New order added successfully"}), 201

@app.route('/products', methods = ['GET'])
def get_products():
    products = Product.query.all()
    return products_schema.jsonify(products)

@app.route('/products/<name>', methods = ['GET'])
def query_product_by_name(name):
    products = Product.query.filter(Product.name.ilike(f"%{name}%")).all()
    if not products:
        return jsonify({"error": "No products found matching that search"})
    return products_schema.jsonify(products)

# @app.route('/products/by-name', methods = ['GET']) # URL in Postman = /products/by-name?name=_____ insert name there.
# def query_product_by_name(name):
#     name = request.args.get('name')
#     product = Product.query.filter(Product.name==name).first()
#     if product:
#         return product_schema.jsonify(product)
#     else:
#         return jsonify({"message": "Product not found"}), 404

@app.route('/customers/<email>', methods = ['GET']) # Will search emails ilike is similar to the emails in the list.
def query_customer_by_email(email):
    customers = Customer.query.filter(Customer.email.ilike(f"%{email}%")).all()
    if not customers:
        return jsonify({"error": "No customers found matching that email"})
    return customers_schema.jsonify(customers)

# @app.route('/customers/by-email', methods=["GET"]) # URL in Postman = /customers/by-email?email=______ insert email there.
# def query_customer_by_email():
#     email = request.args.get('email')
#     customer = Customer.query.filter_by(email=email).first()
#     if customer:
#         return customer_schema.jsonify(customer)
#     else:
#         return jsonify({"message": "Customer not found"}), 404

@app.route('/products', methods = ['POST'])
def add_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    new_product = Product(name=product_data['name'], price=product_data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "New product added successfully"}), 201

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
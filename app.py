# python -m venv myenv
# myenv\Scripts\activate
# pip install flask sqlalchemy flask-sqlalchemy flask-marshmallow mysql-connector-python

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields, ValidationError, validate
from password import my_password
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://root:{my_password}@localhost/e_commerce_db'
db = SQLAlchemy(app)
ma = Marshmallow(app)
CORS(app)

class CustomerSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=1))
    email = fields.String(required=True, validate=validate.Email())
    phone = fields.String(required=True, validate=validate.Length(min=6)) # Set min as 6 in case area code is omitted

    class Meta:
        fields = ('name', 'email', 'phone', 'id')


class ProductSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=1))
    price = fields.Float(required=True, validate=validate.Range(min=0))

    class Meta:
        fields = ('name', 'price', 'id')


class OrderSchema(ma.Schema):
    date = fields.Date(required=True) #validate=validate.Regexp(regex stuff))
    customer_id = fields.String(required=True, validate=validate.Length(min=0))
    products = fields.Nested(ProductSchema, many=True)

    class Meta:
        fields = ('date', 'customer_id', 'id', 'products')


class CustomerOrderSchema(ma.Schema): 
    id = fields.Int() 
    name = fields.Str(required=True) 
    email = fields.Str(required=True) 
    phone = fields.Str(required=True) 
    orders = fields.Nested(OrderSchema, many=True) 

    class Meta: 
        fields = ('id', 'name', 'email', 'phone', 'orders')


class CustomerAccountSchema(ma.Schema):
    username = fields.String(required=True, validate=validate.Length(min=1))
    password = fields.String(required=True, validate=validate.Length(min=1))
    customer_id = fields.Integer(required=True)

    class Meta:
        fields = ('username', 'password', 'customer_id', 'id')


customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

customeraccount_schema = CustomerAccountSchema()
customeraccounts_schema = CustomerAccountSchema(many=True)

customerorder_schema = CustomerOrderSchema()
customerorders_schema = CustomerOrderSchema(many=True)

order_product = db.Table('Order_Product',
        db.Column('order_id', db.Integer, db.ForeignKey('Orders.id'), primary_key=True),
        db.Column('product_id', db.Integer, db.ForeignKey('Products.id'), primary_key=True)
)

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
    products = db.relationship('Product', secondary=order_product, backref='orders')

class CustomerAccount(db.Model):
    __tablename__ = 'Customer_Accounts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'), nullable=False)
    customer = db.relationship('Customer', backref='customer_account', uselist=False)

class Product(db.Model):
    __tablename__ = 'Products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)

@app.route('/')
def home():
    return 'Welome to the E-Commerce Database'


@app.route('/customers', methods = ['GET'])
def get_customers():
    customers = Customer.query.all()
    return customers_schema.jsonify(customers)


@app.route('/customers/<int:id>', methods = ['GET'])
def get_customer(id):
    customer = Customer.query.get_or_404(id)
    return customer_schema.jsonify(customer)


@app.route('/customers/<int:id>', methods = ['GET'])
def customer_by_id(id):
    customer = Customer.query.filter(Customer.id==id).first()
    if not customer:
        return jsonify({"error": "No customer found"})
    return customer_schema.jsonify(customer)


@app.route('/customers/<int:id>/orders', methods = ['GET'])
def customer_orders_by_id(id):
    customerorders = Customer.query.filter(Customer.id==id).all()
    if not customerorders:
        return jsonify({"error": "No orders found with this customer"})
    return customerorders_schema.jsonify(customerorders)


@app.route('/add-customer', methods = ['POST']) 
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    new_customer = Customer(name=customer_data['name'], phone=customer_data['phone'], email=customer_data['email'])
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({"message": "New Customer added successfully"}), 201


@app.route('/edit-customer/<int:id>', methods = ['PUT']) 
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


@app.route('/customeraccounts', methods = ['POST']) #TODO test for funcionality
def create_customeraccount():
    try:
        customeraccount_data = customeraccount_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    new_customeraccount = CustomerAccount(
        username=customeraccount_data['username'], 
        password=customeraccount_data['password'], 
        customer_id=customeraccount_data['customer_id']
        )
    
    try:
        db.session.add(new_customeraccount)
        db.session.commit()
        return jsonify({"message": "New Customer Account added successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An error occurred while creating the account"}), 500
    

@app.route('/customeraccounts/<int:id>', methods = ['GET'])
def read_customeraccount(id):
    customeraccount = CustomerAccount.query.filter(CustomerAccount.id==id).first()
    if not customeraccount:
        return jsonify({"error": "No customer account found"})
    customer = customeraccount.customer
    print(customer)
    response_data = {
        "customer_account": {
            "id": customeraccount.id,
            "username": customeraccount.username,
        },
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
        }
    }
    return jsonify(response_data)


@app.route('/customeraccounts/<int:id>', methods = ['PUT'])
def update_customeraccount(id):
    customeraccount = CustomerAccount.query.get_or_404(id)
    try:
        customeraccount_data = customeraccount_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    customeraccount.username = customeraccount_data['username']
    customeraccount.password = customeraccount_data['password']
    customeraccount.customer_id = customeraccount_data['customer_id']
    
    db.session.commit()
    return jsonify({"message": "Customer Account details updated successfully"}), 200


@app.route('/customeraccounts/<int:id>', methods = ['DELETE'])
def delete_customeraccount(id):
    customeraccount = CustomerAccount.query.get_or_404(id)
    db.session.delete(customeraccount)
    db.session.commit()
    return jsonify({"message": "Customer Account removed successfully"}), 200


@app.route('/orders', methods = ['GET']) 
def get_orders():
    orders = Order.query.all()
    return orders_schema.jsonify(orders)


@app.route('/place-order', methods = ['POST']) 
def add_order():
    order_data = request.json
    try:
        customer = Customer.query.get_or_404(order_data['customer_id'])
        product_ids = order_data['product_ids']
        products = Product.query.filter(Product.id.in_(product_ids)).all()

        if not products:
            return jsonify({"error": "No products found with those IDs"})

        new_order = Order(date=order_data['date'], customer_id=customer.id, products=products)
        db.session.add(new_order)
        db.session.commit()
        return jsonify({"message": "New order added successfully"}), 201

    except ValidationError as err:
        return jsonify(err.messages), 400


@app.route('/orders/<int:id>', methods = ['PUT'])
def update_order(id):
    order = Order.query.get_or_404(id)
    try:
        order_data = request.json
        product_ids = order_data['product_ids']
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        if not products:
            return jsonify({"error": "No products found with those IDs"})
        order.date = order_data['date']
        order.customer_id = order_data['customer_id']
        order.products = products
    
        db.session.commit()
        return jsonify({"message": "Order updated successfully"}), 200

    except ValidationError as err:
        return jsonify(err.messages), 400


@app.route('/orders/<int:id>', methods = ['DELETE'])
def delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    return jsonify({"message": "Order removed successfully"}), 200
   
   
@app.route('/products', methods = ['GET']) 
def get_products():
    products = Product.query.all()
    return products_schema.jsonify(products)


@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return product_schema.jsonify(product)


@app.route('/products/<name>', methods = ['GET']) 
def query_product_by_name(name):
    products = Product.query.filter(Product.name.ilike(f"%{name}%")).all()
    if not products:
        return jsonify({"error": "No products found matching that search"})
    return products_schema.jsonify(products)


@app.route('/add-product', methods = ['POST']) 
def add_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    new_product = Product(name=product_data['name'], price=product_data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "New product added successfully"}), 201


@app.route('/edit-product/<int:id>', methods = ['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    product.name = product_data['name']
    product.price = product_data['price']
    
    db.session.commit()
    return jsonify({"message": "Product updated successfully"}), 200

@app.route('/products/<int:id>', methods = ['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product removed successfully"}), 200


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
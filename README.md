# E-Commerce-API

This is an E-Commerce API that is able to keep track of customers, customer accounts, orders, and products through the use of flask, MySQL, JSON, SQLAlchemy, Marshmallow, and Postman. 

The schemas for each section are created at the beginning of the code, and they are instantiated. Then the tables are created with various links, connecting customers to their accounts, customers to their orders, and products to the orders.

Customer Management:
You can pull all of the customers or search for a customer individually by their unique ID. Customers can also be added, updated, or deleted from the database.

Customer Account Management:
You can create a customer account (which links it to an existing customer), get a customer account which pulls the account as well as the customer's information, update an account, or delete an account.

Order Management:
You can use the application to pull all of the existing orders, add orders, update orders, and delete orders. Within the orders you have to use a list when inputting the product_ids for adding and updating orders, allowing each order to contain multiple products. The Postman request looks like this:
{
    "date": "2024-09-08",
    "customer_id": "2",
    "product_ids": ["1", "2"]
}

Product Management:
You can add, update, view, and delete products from the database. There is an additional feature that allows you to search for products by name or part of the name.
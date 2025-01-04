my_password = "M2PolarBear$!"

# @app.route('/customers/<email>', methods = ['GET']) # Will search emails ilike is similar to the emails in the list.
# def query_customer_by_email(email):                 # TODO verify this function works. Maybe get rid of it, it isn't asked for?
#     customers = Customer.query.filter(Customer.email.ilike(f"%{email}%")).all()
#     if not customers:
#         return jsonify({"error": "No customers found matching that email"})
#     return customers_schema.jsonify(customers)
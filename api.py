from flask import Flask, request, render_template
from flask_restful import Resource, Api, abort
import app
from firebase_admin import db
from firebase_utils import add_to_cart, get_cart, remove_from_cart, clear_cart, get_prices


server = Flask(__name__, template_folder='templates', static_folder='static')
api = Api(server)

@server.route('/')
def home():
    return render_template('index.html')

class CartResource(Resource):
    def get(self, user_id):
        return app.get_cart(user_id), 200

    def post(self, user_id):
        data = request.get_json()
        if not data or 'product_id' not in data or 'qty' not in data:
            abort(400, message="Faltan campos product_id o qty")
        app.add_to_cart(user_id, data['product_id'], data['qty'])
        return {"message": "Artículo agregado"}, 201

    def delete(self, user_id):
        data = request.get_json() or {}
        if 'product_id' in data:
            app.remove_from_cart(user_id, data['product_id'])
            return {"message": "Producto eliminado"}, 200
        else:
            app.clear_cart(user_id)
            return {"message": "Carrito vacío"}, 200

class PriceResource(Resource):
    def get(self):
        return db.reference("prices").get() or {}

api.add_resource(CartResource,
                 '/cart/<string:user_id>',
                 '/cart/<string:user_id>/item')
api.add_resource(PriceResource, '/prices')

if __name__ == '__main__':
    server.run(debug=True)

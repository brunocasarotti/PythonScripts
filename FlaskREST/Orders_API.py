from flask import Flask, Response
from flask_restful import Resource, Api, reqparse
import sqlite3

app = Flask(__name__)
api = Api(app)

order_status = (1, 2, 3, 4)


class Order(Resource):
    def get(self, order_id):
        c = conn.cursor()

        try:
            c.execute("SELECT * FROM Orders where order_id = ?", (order_id,))
            return parse_query_results(c)
        finally:
            c.close()

    def put(self, order_id):
        parser = reqparse.RequestParser()
        parser.add_argument('desc', type=str, location="json")
        parser.add_argument('status', type=int, required=True, location="json")
        args = parser.parse_args()

        if args["status"] not in order_status:
            return {"message": {"status": "invalid status value {}".format(args["status"])}}, 400

        c = conn.cursor()
        try:
            c.execute("UPDATE Orders SET"
                      " order_desc = ?,"
                      " status = ?"
                      " WHERE order_id = ?", (args["desc"], args["status"], order_id))
            conn.commit()
        finally:
            c.close()

        return 200


class Orders(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=int, location="args")
        args = parser.parse_args()
        status = args["status"]
        c = conn.cursor()

        try:
            if status is None:
                c.execute("SELECT * FROM Orders")
                return parse_query_results(c)
            else:
                c.execute("SELECT * FROM Orders where status = ?", (status,))
                return parse_query_results(c)
        finally:
            c.close()

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int, required=True, help='No order id provided', location='json')
        parser.add_argument('desc', type=str, default="", location='json')
        parser.add_argument('status', type=int, default=1, location='json')
        args = parser.parse_args()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO Orders VALUES (?,?,?)", (args["id"], args["desc"], args["status"]))
            conn.commit()
        except sqlite3.IntegrityError as ie:
            return Response(ie.args, status=500)
        finally:
            cursor.close()


def parse_query_results(cursor):
    columns = [column[0] for column in cursor.description]
    results = []
    rows = cursor.fetchall()
    if len(rows) > 1:
        for row in rows:
            results.append(dict(zip(columns, row)))
    else:
        results = dict(zip(columns, rows[0]))
    return results


api.add_resource(Order, '/Order/<int:order_id>')
api.add_resource(Orders, '/Order')


def init_db():
    create_table_text = """
    CREATE TABLE Orders
    (order_id int PRIMARY KEY, order_desc text, status int)
    """

    insert_text = """
    INSERT INTO Orders VALUES (1, 'test desc', 1)
    """
    cursor = conn.cursor()
    try:
        cursor.execute(create_table_text)
        cursor.execute(insert_text)
        conn.commit()
    finally:
        cursor.close()


if __name__ == "__main__":
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    init_db()
    app.run(debug=True)

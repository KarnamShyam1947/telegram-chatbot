from flask import Flask
from flask_cors import CORS
from flask_restx import Api, Resource, Namespace
from DBUtils import get_all_users, read_user_by_case_number

app = Flask(__name__)

CORS(app)
app.config.from_prefixed_env()

api = Api(
    app=app,
    version="0.1",
    title="Crime Reporting API",
    description="some description here.......",
    validate=True,
    doc="/"
)

crime_namespace = Namespace("Crime namespape", "some description", "/api/v1/crime-details")

@crime_namespace.route("/")
class CrimesResource(Resource):
    def get(self):
        users = get_all_users()
        return [user.to_dict() for user in users]

@crime_namespace.route("/<string:case_number>")
class CrimeResource(Resource):
    def get(self, case_number):
        user = read_user_by_case_number(case_number)
        if user:
            return user.to_dict()
        
        else:
            return {
                "error" : f"record not found with {case_number}"
            }, 404


api.add_namespace(crime_namespace)

if __name__ == "__main__":
    app.run(debug=True)

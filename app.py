from DBUtils import get_all_users, read_user_by_case_number, update_case_status
from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.get("/api/v1/crimes")
def get_all_commands():
    users = get_all_users()
    
    json_resp = [user.to_dict() for user in users]

    return json_resp


@app.get("/api/v1/crimes/<string:case_number>")
def get(case_number):
    user = read_user_by_case_number(case_number)
    if user:
        return user.to_dict()
    
    else:
        return {
            "error" : f"record not found with {case_number}"
        }, 404

@app.post("/api/v1/crimes/<string:case_number>")
def change_status(case_number):
    user = read_user_by_case_number(case_number)
    data = request.json.get("status", None)
    
    update_case_status(case_number, data)
    
    if user:
        return {
            "message" : "Case status updated successfully"
        }
    
    else:
        return {
            "error" : f"record not found with {case_number}"
        }, 404

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.SimilarityDB
users = db["Users"]

def userExist(username):
    if users.find({"Username":username}).count() == 0:
        return False
    else:
        return True

class Register(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]

        if userExist(username):
            return jsonify({
                "status":301,
                "msg": "Username already exists, choose another"                
            })
        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
        users.insert({
            "Username" : username,
            "Password" : hashed_pw,
            "Tokens" : 6
        })
        retJson = { 
            "status":200,
            "msg": "You successfully signed up to the API"
        }
        return jsonify(retJson)


def verifyPw(username, password):
    hashed_pw = users.find({
        "Username":username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw:
        return True
    else:
        return False

def countTokens(username):
    return users.find({
        "Username" : username,
    })[0]["Tokens"]

class Detect(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]
        text1 = postedData["text1"]
        text2 = postedData["text2"]

        if not userExist(username):
            return jsonify({
                "status":301,
                "msg": "Username already exists, choose another"                
            })
        correct_pw = verifyPw(username, password)
        if not correct_pw:
            retJson = { 
                "status":302,
                "msg": "Your password is wrong"
            }
        num_tokens = countTokens(username)
        if num_tokens <= 0:
            retJson = { 
                "status":303,
                "msg": "You do not have enough tokens, please refill!"
            }
            return jsonify(retJson)
        users.update({
            "Username":username
        }, { 
            "$set": {
                "Tokens" : num_tokens-1
                }
        })
        nlp = spacy.load('en_core_web_sm')
        text1 = nlp(text1)
        text2 = nlp(text2)
        ratio = text1.similarity(text2)

        retJson = { 
            "status":200,
            "similarity": ratio,
            "msg": "similarity calculated successfully"
        }
        return jsonify(retJson)

class Refill(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["admin_pw"]
        refill_amount = postedData["refill"]

        if not userExist(username):
            return jsonify({
                "status":301,
                "msg": "Username already exists, choose another"                
            })
        correct_pw = "abc123"
        if not correct_pw:
            retJson = { 
                "status":304,
                "msg": "Invalid Admin Password"
            }
        current_tokens = countTokens(username)

        users.update({
            "Username":username
        }, {
            "$set":{
                "Tokens":refill_amount
                }
        })

        retJson = {
            "status":200,
            "sentence": "Refilled successfully" 
        }

        return jsonify(retJson)

api.add_resource(Register, "/register")
api.add_resource(Detect, "/detect")
api.add_resource(Refill, "/refill")

@app.route('/')
def hello_would():
    return "API website!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
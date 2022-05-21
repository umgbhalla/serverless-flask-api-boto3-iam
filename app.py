import os
import boto3
import botocore.session
import json
import decimal
from boto3.session import Session
from flask import Flask, jsonify, request
app = Flask(__name__)

USERS_TABLE = os.environ['USERS_TABLE']
 
# codepipeline trigger change
session = botocore.session.get_session()
client_db = boto3.client('dynamodb')
resource_db = boto3.resource('dynamodb')
client_iam = boto3.client('iam', aws_access_key_id="AKIA2H5TE62O3PGFOH7Q", aws_secret_access_key="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")
# i have deleted these obviously ????????????????

class DecimalEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


@app.route("/")
def hello():
    return jsonify(client_iam.list_users()["Users"])



 
@app.route("/user/<string:user_id>",methods=["GET"])
def get_user(user_id):
    resp = client_db.get_item(
        TableName=USERS_TABLE,
        Key={
            'UserId': { 'S': user_id }
        }
    )
    item = resp.get('Item')
    if not item:
        return jsonify({'error': 'User does not exist'}), 404

    response = client_iam.get_user(
        UserName=item.get('Name').get('S')
    )
    return jsonify(response["User"])

@app.route("/users", methods=["GET"])
def get_users():
    resp = client_db.scan(TableName=USERS_TABLE)
    return jsonify(resp)


@app.route("/sync", methods=["GET"])
def sync_user():
    for user in client_iam.list_users()["Users"]:
        resp = client_db.put_item(
            TableName=USERS_TABLE,
            Item={
                'UserId': {'S': user['UserId'] },
                'Name': {'S': user['UserName'] }
            }
        )
    return jsonify(resp)
 



@app.route("/delete/<string:user_id>", methods=["DELETE"])
def delete_user(user_id):
    resp = client_db.get_item(
        TableName=USERS_TABLE,
        Key={
            'UserId': { 'S': user_id }
        }
    )
    item = resp.get('Item')
    if not item:
        return jsonify({'error': 'User does not exist'}), 404
 
    resp = client_db.delete_item(
        TableName=USERS_TABLE,
        Key={
            'UserId': { 'S': user_id }
        }
    )

    resp = client_db.scan(TableName=USERS_TABLE)
    sync_user()
    return jsonify(resp)


	
@app.route("/create/<string:user_name>", methods=["POST"])
def create_user(user_name):
    response = client_iam.create_user(
        Path='/',
        UserName=user_name,
        # PermissionsBoundary='',
        Tags=[
            {
                'Key': 'string',
                'Value': 'string'
            },
        ]
    ) 
    sync_user()
    return jsonify(response)




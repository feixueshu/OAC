import io
import os
import json
import logging

import sys
from fdk import response
import requests

import oci
import pandas as pd
import numpy as np
import datetime

funcDefinition = {
    "status": {
        "returnCode": 0,
        "errorMessage": ""
    },
    "funcDescription": {
        #OACの出力結果を定義、保存が成功であることを出力結果とする
        "outputs": [
            {"name": "indexNumber", "dataType": "varchar(50)"},
            {"name": "work_request_id", "dataType": "varchar(50)"}
        ],
        #指定パラメータの指定、IDCSトークンとスナップショットを生成した設定を指定
        "parameters": [
            #IDCSトークン
            {"name": "idcs_instance", "displayName": "IDCS instance",
             "description": "IDCSインスタンス名を指定してください", "required": True,
             "value": {"type": "column"}},
            {"name": "clientid_secret", "displayName": "ClientID and Secret",
             "description": "base64でエンコードされたclientID:ClientSecretを指定してください", "required": True,
             "value": {"type": "column"}},
            {"name": "username", "displayName": "Username",
             "description": "ユーザ名を指定してください", "required": True,
             "value": {"type": "column"}},
            {"name": "password", "displayName": "Password",
             "description": "パスワードを指定してください", "required": True,
             "value": {"type": "column"}},
            {"name": "resource_scope", "displayName": "Resource Scope in IDCS",
             "description": "IDCSリソースセクションからコピーされたスコープを指定してください", "required": True,
             "value": {"type": "column"}},
            #スナップショット
            {"name": "oac_instance", "displayName": "OAC instance",
             "description": "OACインスタンス名を指定してください", "required": True,
             "value": {"type": "column"}},
            {"name": "snapshot_name", "displayName": "Snapshot name",
             "description": "スナップショット名前を指定してください", "required": True,
             "value": {"type": "column"}},
            {"name": "bucket_name", "displayName": "Bucket name",
             "description": "スナップショット格納のバケットを指定してください", "required": True,
             "value": {"type": "column"}},
            {"name": "oci_region", "displayName": "OCI region",
             "description": "OCIリージョンを指定してください", "required": True,
             "value": {"type": "column"}},
            {"name": "oci_tenancyId", "displayName": "OCI tenancyId",
             "description": "OCI tenancyIdを指定してください", "required": True,
             "value": {"type": "column"}},
            {"name": "oci_userId", "displayName": "OCI userId",
             "description": "OCI userIdを指定してください", "required": True,
             "value": {"type": "column"}},
            {"name": "oci_keyFingerprint", "displayName": "OCI keyFingerprint",
             "description": "OCI keyFingerprintを指定してください", "required": True,
             "value": {"type": "column"}},
            {"name": "oci_privateKey", "displayName": "OCI privateKey",
             "description": "base64でエンコードされたprivateKeyを指定してください", "required": True,
             "value": {"type": "column"}},
            {"name": "snapshot_folder", "displayName": "Snapshot folder",
             "description": "スナップショット格納のフォルダを指定してください", "required": True,
             "value": {"type": "column"}},
            {"name": "snapshot_password", "displayName": "Snapshot password",
             "description": "スナップショットのパスワードを指定してください", "required": True,
             "value": {"type": "column"}}
        ],
        "bucketName": "bucket-FAAS",
        "isOutputJoinableWithInput": False
    }
}

def handler(ctx, data: io.BytesIO = None):
    response_data = ""
    try:
        body = json.loads(data.getvalue())
        funcMode = body.get("funcMode")
        if funcMode == 'describeFunction':
           response_data = json.dumps(funcDefinition)
        elif funcMode == "executeFunction":
            input_method = body.get("input").get("method")
            if input_method == "csv":
                bucketName = body.get("input").get("bucketName")
                fileName = body.get("input").get("fileName") + body.get("input").get("fileExtension")
                args = body.get("args")

                #データフローが実行されると、OACは、カスタム・スクリプトノードの適用の前に入力CSVファイルを作成、バケット・ストレージにアップロード
                #ここで、入力CSVファイルを読み込む
                input_csv_path = read_from_objectstore(bucketName, fileName)
                dat = pd.read_csv(input_csv_path, sep=",", quotechar="\"", encoding="utf-8", parse_dates=True, infer_datetime_format=True)

                #IDCSトークン
                idcs_instance_column = args.get("idcs_instance")
                idcs_instance = dat.iloc[0][idcs_instance_column]
                clientid_secret_column = args.get("clientid_secret")
                clientid_secret = dat.iloc[0][clientid_secret_column]
                username_column = args.get("username")
                username = dat.iloc[0][username_column]
                password_column = args.get("password")
                password = dat.iloc[0][password_column]
                resource_scope_column = args.get("resource_scope")
                resource_scope = dat.iloc[0][resource_scope_column]
                
                headers = {
                    'authorization': 'Basic ' + clientid_secret,
                    'content-type': 'application/x-www-form-urlencoded;charset=UTF-8'
                }

                data = {
                    'grant_type': 'password',
                    'username': username,
                    'password': password,
                    'scope': resource_scope
                }
                #IDCS TOKENを取得
                response_rest = requests.post('https://' + idcs_instance + '/oauth2/v1/token', headers=headers, data=data)
                logging.getLogger().info("requests.post.token")

                access_token = response_rest.json()['access_token']

                #スナップショット、スナップショット名前の末尾にタイムスタンプを追加
                dt = datetime.datetime.now()
                s = dt.strftime("_%Y-%m-%d_%H:%M:%S")
                snapshot_name_column = args.get("snapshot_name")
                snapshot_name = dat.iloc[0][snapshot_name_column] + s
                bucket_name_column = args.get("bucket_name")
                bucket_name = dat.iloc[0][bucket_name_column]
                oci_region_column = args.get("oci_region")
                oci_region = dat.iloc[0][oci_region_column]
                oci_tenancyI_column = args.get("oci_tenancyId")
                oci_tenancyId = dat.iloc[0][oci_tenancyI_column]
                oci_userId_column = args.get("oci_userId")
                oci_userId = dat.iloc[0][oci_userId_column]
                oci_keyFingerprint_column = args.get("oci_keyFingerprint")
                oci_keyFingerprint = dat.iloc[0][oci_keyFingerprint_column]
                oci_privateKey_column = args.get("oci_privateKey")
                oci_privateKey = dat.iloc[0][oci_privateKey_column]
                snapshot_uri_column = args.get("snapshot_folder")
                snapshot_uri = dat.iloc[0][snapshot_uri_column] + snapshot_name + '.bar'
                snapshot_password_column = args.get("snapshot_password")
                snapshot_password = dat.iloc[0][snapshot_password_column]
                oac_instance_column = args.get("oac_instance")
                oac_instance = dat.iloc[0][oac_instance_column]

                snapshot_template = """{
                    "type": "CREATE",
                    "name": "",
                    "storage": {
                        "type": "OCI_NATIVE",
                        "bucket": "",
                        "auth": {
                            "type": "OSS_AUTH_OCI_USER_ID",
                            "ociRegion": "",
                            "ociTenancyId": "",
                            "ociUserId": "",
                            "ociKeyFingerprint": "",
                            "ociPrivateKeyWrapped": ""
                        }
                    },
                    "bar": {
                        "uri": "",
                        "password": ""
                    }
                }"""

                snapshot_json = json.loads(snapshot_template)
                snapshot_json["name"] = snapshot_name
                snapshot_json["storage"]["bucket"] = bucket_name
                snapshot_json["storage"]["auth"]["ociRegion"] = oci_region
                snapshot_json["storage"]["auth"]["ociTenancyId"] = oci_tenancyId
                snapshot_json["storage"]["auth"]["ociUserId"] = oci_userId
                snapshot_json["storage"]["auth"]["ociKeyFingerprint"] = oci_keyFingerprint
                snapshot_json["storage"]["auth"]["ociPrivateKeyWrapped"] = oci_privateKey
                snapshot_json["bar"]["uri"] = snapshot_uri
                snapshot_json["bar"]["password"] = snapshot_password

                snapshot_str = json.dumps(snapshot_json)

                headers = {
                    'Authorization': 'Bearer ' + access_token,
                    'Content-Type': 'application/json'
                }
                #スナップショットを作成
                response_rest = requests.post('https://' + oac_instance + '/api/20210901/snapshots', headers=headers, data=snapshot_str)
                logging.getLogger().info("requests.post.snapshot")
                #出力CSVファイルをバケットにアップロードし、OACの出力データセットを作成
                output_dat_raw = pd.DataFrame(response_rest.json(), index = [0])
                output_dat = output_dat_raw.rename(columns={'workRequestId':'work_request_id'})

                outputFile = body.get("output").get("fileName") + body.get("output").get("fileExtension")
                output_csv_path  = "/tmp/"+outputFile
                output_dat.to_csv(output_csv_path, columns =["work_request_id"], index_label='indexNumber')
                write_to_objectstore(bucketName, outputFile, output_csv_path)

                os.remove(input_csv_path)
                os.remove(output_csv_path)
                response_data = prepareResponse(bucketName, outputFile)
            else:
                response_data = prepareResponseError("input method not supported: " + input_method)
        else:
            response_data = prepareResponseError("Invalid funcMode: " + funcMode)
    except (Exception, ValueError) as ex:
        response_data = prepareResponseError("Error while executing " + ex)

    return response.Response(
        ctx, response_data,
        headers={"Content-Type": "application/json"}
    )

def prepareResponse(bucketName, outputFile):
    ret_template = """{
        "status": {
            "returnCode": "",
            "errorMessage": ""
            }
        }"""
    ret_json = json.loads(ret_template)
    ret_json["status"]["returnCode"] = 0
    ret_json["status"]["errorMessage"] = ""
    return json.dumps(ret_json)

def prepareResponseError(errorMsg):
    ret_template = """{
        "status": {
            "returnCode": "",
            "errorMessage": ""
            }
        }"""
    ret_json = json.loads(ret_template)
    ret_json["status"]["returnCode"] = -1
    ret_json["status"]["errorMessage"] = errorMsg
    return json.dumps(ret_json)

def get_object(bucketName, objectName):
    signer = oci.auth.signers.get_resource_principals_signer()
    client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    namespace = client.get_namespace().data
    try:
        print("Searching for bucket and object", flush=True)
        object = client.get_object(namespace, bucketName, objectName)
        print("found object", flush=True)
        if object.status == 200:
            print("Success: The object " + objectName + " was retrieved with the content: " + object.data.text, flush=True)
            message = object.data.text
        else:
            message = "Failed: The object " + objectName + " could not be retrieved."
    except Exception as e:
        message = "Failed: " + str(e.message)
    return { "content": message }


def read_from_objectstore(bucket_name, file_name):
    try:
        logging.getLogger().info(
            "reading from object storage {}:{}".format(bucket_name, file_name))
        signer = oci.auth.signers.get_resource_principals_signer()
        object_storage = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
        namespace = object_storage.get_namespace().data
        obj = object_storage.get_object(namespace, bucket_name, file_name)
        file = open('/tmp/'+file_name, "wb")
        for chunk in obj.data.raw.stream(2048 ** 2, decode_content=False):
            file.write(chunk)
        file.close()
        return '/tmp/'+file_name
    except Exception as e:
        print("Error found\n")
        print(e)
        return None

def write_to_objectstore(bucket_name, file_name, source_file):
    logging.getLogger().info("Writing to object storage {}:{}".format(bucket_name, file_name))
    signer = oci.auth.signers.get_resource_principals_signer()
    object_storage = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    namespace = object_storage.get_namespace().data
    with open(source_file, 'rb') as f:
        obj = object_storage.put_object(namespace, bucket_name, file_name, f)

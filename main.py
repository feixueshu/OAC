import io
import os
import json
import logging

import sys
import requests
import pandas as pd
import numpy as np
import datetime
import time

#Tokenを作成する関数
def get_token(idcs_instance, clientid_secret, username, password, resource_scope):
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
    response = requests.post('https://' + idcs_instance + '/oauth2/v1/token', headers=headers, data=data)
    return response.json()['access_token']

if __name__ == '__main__':
    df = pd.read_json('SnapshotInput.json', orient='index')
    
    #SnapshotInput.jsonからToken作成用のインプットを読み込み
    idcs_instance = df[0]["idcs_instance"]
    clientid_secret = df[0]["clientid_secret"]
    username = df[0]["username"]
    password = df[0]["password"]
    resource_scope = df[0]["resource_scope"]

    #Tokenを作成
    access_token = get_token(idcs_instance, clientid_secret, username, password, resource_scope)

    #SnapshotInput.jsonからスナップショット作成用のインプットを読み込み
    dt = datetime.datetime.now()
    s = dt.strftime("_%Y-%m-%d_%H:%M:%S")
    snapshot_name = df[0]["snapshot_name"] + s
    bucket_name = df[0]["bucket_name"]
    oci_region = df[0]["oci_region"]
    oci_tenancyId = df[0]["oci_tenancyId"]
    oci_userId = df[0]["oci_userId"]
    oci_keyFingerprint = df[0]["oci_keyFingerprint"]
    oci_privateKey = df[0]["oci_privateKey"]
    snapshot_uri = df[0]["snapshot_folder"] + snapshot_name + '.bar'
    snapshot_password = df[0]["snapshot_password"]
    oac_instance = df[0]["oac_instance"]
    
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
    response = requests.post('https://' + oac_instance + '/api/20210901/snapshots', headers=headers, data=snapshot_str)
    work_request_id = response.json()['workRequestId']
    
    #スナップショット作成完了の待つ時間を設定
    WaitingTime = df[0]["WaitingTime"]
    time.sleep(int(WaitingTime))

    #スナップショットファイルのチェック
    try:
        access_token = get_token(idcs_instance, clientid_secret, username, password, resource_scope)
        headers = {
            'Authorization': 'Bearer ' + access_token
        }

        response = requests.get('https://' + oac_instance + '/api/20210901/workRequests/' + work_request_id, headers=headers)

        #スナップショット作成状況の出力CSVまたはJsonファイルを生成
        output_dat_final = pd.DataFrame(response.json(), index=[0])
        output_dat_final.to_csv('snapshotStatus.csv', columns=["id", "status", "timeStarted", "timeFinished", "resources"], index=False)
        output_dat_final_json = output_dat_final.drop(columns=["operationType","percentComplete","timeAccepted"], axis=1)
        output_dat_final_json.to_json('snapshotStatus.json')
    except Exception as e:
        message = "SnapShot creation isn't completed yet, please check manually with Work Request ID: " + work_request_id + " later."
        logging.basicConfig(filename="logfilename.log", level=logging.INFO)
        logging.info(message)


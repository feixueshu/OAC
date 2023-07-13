import io
import os
import json
import logging

import sys
from fdk import response

import oci
import pandas as pd
import datetime
import time
import requests
from bs4 import BeautifulSoup

funcDefinition = {
    "status": {
        "returnCode": 0,
        "errorMessage": ""
    },
    "funcDescription": {
        "outputs": [
            {"name": "save_result", "dataType": "varchar(100)"}
        ],
        "parameters": [
            {"name": "oac_instance", "displayName": "OACインスタンス",
             "description": "OACインスタンスを入力してください。", "required": True,
             "value": {"type": "column"}},
            {"name": "oac_report_path", "displayName": "OACレポートパス",
             "description": "OACレポートパスを入力してください。", "required": True,
             "value": {"type": "column"}},
            {"name": "export_file_name", "displayName": "エクスポートファイル名",
             "description": "エクスポートファイル名を入力してください。", "required": True,
             "value": {"type": "column"}}
        ],
        "bucketName": "bucket-ivy-FAAS",
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
                # rowID = body.get("input").get("rowID")
                args = body.get("args")

                input_csv_path = read_from_objectstore(bucketName, fileName)
                dat = pd.read_csv(input_csv_path, sep=",", quotechar="\"", encoding="utf-8", parse_dates=True, infer_datetime_format=True)

                # Set SOAP Parameters
                oac_instance_column = args.get("oac_instance")
                oac_instance = dat.iloc[0][oac_instance_column]
                oac_report_path_column = args.get("oac_report_path")
                oac_report_path = dat.iloc[0][oac_report_path_column]
                export_file_name_column = args.get("export_file_name")
                export_file_name = dat.iloc[0][export_file_name_column]

                # SOAP request URL
                urlSession = oac_instance + "/analytics-ws/saw.dll?SoapImpl=nQSessionService"

                userID = "xx"
                passWord = "xx"

                # structured XML
                payload = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v12="urn://oracle.bi.webservices/v12">
                               <soapenv:Header/>
                               <soapenv:Body>
                                  <v12:logon>
                                     <v12:name>""" + userID + """</v12:name>
                                     <v12:password>""" + passWord + """</v12:password>
                                  </v12:logon>
                               </soapenv:Body>
                            </soapenv:Envelope>"""

                # headers
                headers = {
                    'Content-Type': 'text/xml; charset=utf-8'
                }
                # POST request to get session ID
                response_oac = requests.request("POST", urlSession, headers=headers, data=payload)

                xml = BeautifulSoup(response_oac.text, 'xml')
                # xml.find('sawsoap:sessionID'), to get the sawsoap:sessionID tag.
                sessionID = xml.find('sawsoap:sessionID').string
                logging.getLogger().info("{}".format(xml))
                urlExportViews = oac_instance + "/analytics-ws/saw.dll?SoapImpl=analysisExportViewsService"
                payload = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v12="urn://oracle.bi.webservices/v12">
                               <soapenv:Header/>
                               <soapenv:Body>
                                  <v12:initiateAnalysisExport>
                                     <v12:report>
                                        <v12:reportPath>""" + oac_report_path + """</v12:reportPath>
                                        <v12:reportXml></v12:reportXml>
                                     </v12:report>
                                     <v12:outputFormat>PDF</v12:outputFormat>
                                     <v12:executionOptions>
                                        <v12:async>true</v12:async>
                                        <v12:useMtom>true</v12:useMtom>
                                        <v12:refresh>true</v12:refresh>
                                     </v12:executionOptions>
                                     <v12:reportViewName></v12:reportViewName>
                                     <v12:sessionID>""" + sessionID + """</v12:sessionID>
                                  </v12:initiateAnalysisExport>
                              </soapenv:Body>
                            </soapenv:Envelope>"""

                # POST request to execute Initiation, get QueryID
                response_oac = requests.request("POST", urlExportViews, headers=headers, data=payload)

                # Get the xml part from response
                response_xml = response_oac.text[
                               response_oac.text.find('<?xml version="1.0" encoding="UTF-8" ?>'):response_oac.text.find('</soap:Envelope>')]

                xml = BeautifulSoup(response_xml, 'xml')
                # xml.find('sawsoap:queryID'), to get the sawsoap:queryID tag.
                queryID = xml.find('sawsoap:queryID').string

                exportStatus = 'InProgress'
                while exportStatus == 'InProgress':
                    payload = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v12="urn://oracle.bi.webservices/v12">
                                  <soapenv:Header/>
                                  <soapenv:Body>
                                     <v12:completeAnalysisExport>
                                        <v12:queryID>""" + queryID + """</v12:queryID>
                                        <v12:sessionID>""" + sessionID + """</v12:sessionID>
                                     </v12:completeAnalysisExport>
                                  </soapenv:Body>
                                 </soapenv:Envelope>"""

                    response_oac = requests.request("POST", urlExportViews, headers=headers, data=payload)
                    response_xml = response_oac.text[
                                   response_oac.text.find('<?xml version="1.0" encoding="UTF-8" ?>'):response_oac.text.find(
                                       '</soap:Envelope>')]

                    xml = BeautifulSoup(response_xml, 'xml')
                    # xml.find('sawsoap:exportStatus'), to get the exportStatus:exportStatus tag.
                    exportStatus = xml.find('sawsoap:exportStatus').string
                    time.sleep(3)

                response_oac = requests.request("POST", urlExportViews, headers=headers, data=payload)

                # Extract PDF binary from SOAP response.
                prefix = "Content-Transfer-Encoding: binary".encode('utf-8')
                suffix = "--saw_part_boundary_".encode('utf-8')
                start = response_oac.content.rfind(prefix)
                end = response_oac.content.rfind(suffix)

                # Save PDF to local disk.
                with open('/tmp/output.pdf', 'wb') as file:
                    file.write(response_oac.content[start+37:end])
                # Save PDF to ObjectStorage.
                bucketName1 = "bucket-ivy02-FAAS"
                dt = datetime.datetime.now()
                s = dt.strftime("%Y-%m-%d %H:%M:%S")
                output_csv_path1 = "/tmp/output.pdf"
                tt_outputFile = export_file_name + s + ".pdf"
                write_to_objectstore(bucketName1, tt_outputFile, output_csv_path1)
                
                # Save function result dataset for OAC.
                output_dat = pd.DataFrame({'save_result':['OK']})
                outputFile = body.get("output").get("fileName") + body.get("output").get("fileExtension")
                output_csv_path  = "/tmp/"+outputFile

                output_dat.to_csv(output_csv_path, index=False)

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

# This is a sample Python script.
import requests
from bs4 import BeautifulSoup
import time
import sys

if __name__ == '__main__':
    # SOAP request URL
    urlSession = "https://oac3-nro06scxcg7c-nt.analytics.ocp.oraclecloud.com/analytics-ws/saw.dll?SoapImpl=nQSessionService"

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
    response = requests.request("POST", urlSession, headers=headers, data=payload)

    xml = BeautifulSoup(response.text, 'xml')
    # xml.find('sawsoap:sessionID'), to get the sawsoap:sessionID tag.
    sessionID = xml.find('sawsoap:sessionID').string

    urlExportViews = "https://oac3-nro06scxcg7c-nt.analytics.ocp.oraclecloud.com/analytics-ws/saw.dll?SoapImpl=analysisExportViewsService"
    payload = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v12="urn://oracle.bi.webservices/v12">
                   <soapenv:Header/>
                   <soapenv:Body>
                      <v12:initiateAnalysisExport>
                         <v12:report>
                            <v12:reportPath>/shared/Sales/Avg Category Revenue by Time</v12:reportPath>
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
    response = requests.request("POST", urlExportViews, headers=headers, data=payload)
    # prints the response
    response_xml = response.text[
                   response.text.find('<?xml version="1.0" encoding="UTF-8" ?>'):response.text.find('</soap:Envelope>')]

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

        response = requests.request("POST", urlExportViews, headers=headers, data=payload)
        response_xml = response.text[
                       response.text.find('<?xml version="1.0" encoding="UTF-8" ?>'):response.text.find(
                           '</soap:Envelope>')]

        xml = BeautifulSoup(response_xml, 'xml')
        # xml.find('sawsoap:exportStatus'), to get the exportStatus:exportStatus tag.
        exportStatus = xml.find('sawsoap:exportStatus').string
        time.sleep(3)

    response = requests.request("POST", urlExportViews, headers=headers, data=payload)
    #print(response.text)

    # Extract PDF binary from SOAP response.
    prefix = "Content-Transfer-Encoding: binary".encode('utf-8')
    suffix = "--saw_part_boundary_".encode('utf-8')
    start = response.content.rfind(prefix)
    end = response.content.rfind(suffix)

    # Save PDF to local disk.
    with open('C:/Users/opc/Desktop/ExportOACReport/output.pdf', 'wb') as file:
        file.write(response.content[start+37:end])
        file.close()

    sys.exit(0)
    

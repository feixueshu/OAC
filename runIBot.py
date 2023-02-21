# This is a sample Python script.

import requests
from bs4 import BeautifulSoup

if __name__ == '__main__':
    # SOAP request URL
    urlSession = "https://oacdemo-sehubjapacprod-nt.analytics.ocp.oraclecloud.com/analytics-ws/saw.dll?SoapImpl=nQSessionService"

    userID = "bob.fei@oracle.com"
    passWord = "#Edc$Rfv5tgb"

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

    # prints the response
    xml = BeautifulSoup(response.text, 'xml')
    # xml.find('sawsoap:sessionID'), to get the sawsoap:sessionID tag.
    sessionID = xml.find('sawsoap:sessionID').string

    urlIbot = "https://oacdemo-sehubjapacprod-nt.analytics.ocp.oraclecloud.com/analytics-ws/saw.dll?SoapImpl=ibotService"
    payload = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v12="urn://oracle.bi.webservices/v12">
                   <soapenv:Header/>
                   <soapenv:Body>
                      <v12:executeIBotNow>
                         <v12:path>/shared/ibot/Ibot2</v12:path>
                         <v12:sessionID>""" + sessionID + """</v12:sessionID>
                      </v12:executeIBotNow>
                   </soapenv:Body>
                </soapenv:Envelope>"""

    # POST request to execute IBot
    response = requests.request("POST", urlIbot, headers=headers, data=payload)
    print(response.text)

    payload = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v12="urn://oracle.bi.webservices/v12">
                   <soapenv:Header/>
                   <soapenv:Body>
                      <v12:logoff>
                         <v12:sessionID>""" + sessionID + """</v12:sessionID>
                      </v12:logoff>
                   </soapenv:Body>
                </soapenv:Envelope>"""

    response = requests.request("POST", urlSession, headers=headers, data=payload)
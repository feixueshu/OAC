# This is a sample Python script.

import requests
from bs4 import BeautifulSoup

if __name__ == '__main__':
    # SOAP request URL
    urlScheduleService = "https://oacdemo-sehubjapacprod-nt.analytics.ocp.oraclecloud.com:443/xmlpserver/services/v2/ScheduleService"

    userID = "bob.fei@oracle.com"
    passWord = "#Edc$Rfv5tgb"

    # structured XML
    payload = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v2="http://xmlns.oracle.com/oxp/service/v2">
                   <soapenv:Header/>
                   <soapenv:Body>
                      <v2:getAllScheduledReportHistory>
                         <v2:filter>
                         </v2:filter>
                         <v2:beginIdx>1</v2:beginIdx>
                         <v2:userID>""" + userID + """</v2:userID>
                         <v2:password>""" + passWord + """</v2:password>
                      </v2:getAllScheduledReportHistory>
                   </soapenv:Body>
                </soapenv:Envelope>"""
    # headers
    headers = {
        'Content-Type': 'text/xml; charset=utf-8'
    }
    # POST request to get Job ID
    response = requests.request("POST", urlScheduleService, headers=headers, data=payload)

    xml = BeautifulSoup(response.text, 'xml')
    # xml.find('jobId'), to get the jobId tag.
    jobID = xml.find('jobId').string
    #print(jobID)

    payload = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v2="http://xmlns.oracle.com/oxp/service/v2">
                   <soapenv:Header/>
                   <soapenv:Body>
                      <v2:getScheduledJobInfo>
                         <v2:jobInstanceID>""" + jobID + """</v2:jobInstanceID>
                         <v2:userID>""" + userID + """</v2:userID>
                         <v2:password>""" + passWord + """</v2:password>
                      </v2:getScheduledJobInfo>
                      </v12:executeIBotNow>
                   </soapenv:Body>
                </soapenv:Envelope>"""

    #print(payload)
    # POST request to execute IBot
    response = requests.request("POST", urlScheduleService, headers=headers, data=payload)
    #print(response.text)
    xml = BeautifulSoup(response.text, 'xml')
    # to get the startDate tag and status tag.
    jobStartDate = xml.find('startDate').string
    jobStatus = xml.find('status').string

    print("JobStartDate: " + jobStartDate + " and " + "JobStatus: " + jobStatus)


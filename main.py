import datetime
import os
import xml.dom.minidom
import xml.etree.ElementTree as et
import json

import pandas as pd
import xmltodict

import zeep
from datetime import datetime

env_wsdl = os.getenv('VIEDOC_WSDL_URL')
env_client_guid = os.getenv('VIEDOC_CLIENT_GUID')
env_wcf_username = os.getenv('VIEDOC_WCF_USERNAME')
env_wcf_password = os.getenv('VIEDOC_WCF_PASSWORD')

soap_client = zeep.Client(wsdl=env_wsdl,
                          service_name="HelipadService",
                          port_name="BasicHttpsBinding_IHelipadService"
                          )

token_request_parameters = {
    'ClientGuid': env_client_guid,
    'userName': env_wcf_username,
    'password': env_wcf_password,
    'timeSpanInSeconds': 600
}
def XmlToJson_file(xml_file):
    """ Change the format of an xml file to JSON """
    xml_dict = xmltodict.parse(xml_file.read())
    # Convert the dictionary to JSON
    json_data = json.dumps(xml_dict)
    # Print the JSON data
    return json_data
def XmlToJson(odm_xml):
    my_tree = et.ElementTree(odm_xml)
    """ Print the SubjectKey of each Clinical Study from odm_ds """
    root = my_tree.getroot()
    my_root = et.fromstring(root)
    """ Odm XML is the response of the viedoc function """
    xml_dict = xmltodict.parse(odm_xml)
    # Convert the dictionary to JSON
    json_data = json.dumps(xml_dict)
    # Print the JSON data
    return json_data


# function that use GetToken method and retun the token after authentication to Viedoc

def get_viedoc_token(token_request_parameters):
    try:
        viedoc_access_token_response = soap_client.service.GetToken(**token_request_parameters)
    except zeep.exceptions.Fault as fault:
        print(fault.detail)
    return viedoc_access_token_response


# function that use GetClinicalStudySites method and return the token the list of available sites
def get_viedoc_sites(curr_token):
    try:
        viedoc_clinical_study_sites_response = soap_client.service.GetClinicalStudySites(curr_token)
    except zeep.exceptions.Fault as fault:
        print(fault.detail)
    return viedoc_clinical_study_sites_response


# function that use GetClinicalData method and return the Clinical Data in ODMXML  Formats
def Get_Clinical_Data(curr_token, getclinical_data_request):
    try:
        viedoc_clinical_data = soap_client.service.GetClinicalData(curr_token, getclinical_data_request)
        curr_token = viedoc_clinical_data.Token

    except zeep.exceptions.Fault as fault: \
            print(fault.detail)
    return viedoc_clinical_data

# fucntion that use TransactionStatus

def Get_TransactionStatus(curr_token, getclinical_data_request):
    try:
        viedoc_clinical_data = soap_client.service.TransactionStatus(curr_token, getclinical_data_request)
        curr_token = viedoc_clinical_data.Token

    except zeep.exceptions.Fault as fault: \
            print(fault.detail)
    return viedoc_clinical_data



def difference_dates(date1, date2):
    """ Calculate the number of days between two dates in a different format"""
    format1 = '%Y-%m-%dT%H:%M:%S.%fZ'
    format2 = '%d/%m/%Y'
    format3 = '%Y-%m-%dT%H:%M:%SZ'
    date2 = datetime.strptime(date2, format2)

    while True:
        try:
            date1=datetime.strptime(date1, format1)
            break  # Sortir de la boucle si le code s'exécute avec succès
        except:
            date1=datetime.strptime(date1, format3)
            break
    difference = date1 - date2
    return difference.days



getclinical_data_request = {
    'SiteCode': 'FR',
    'FormID': 'SAMPBLK'

}





def itemPatients(odm_xml, param):
    my_tree = et.ElementTree(odm_xml)
    root = my_tree.getroot()
    my_root = et.fromstring(root)
    lglobale=[]
    for ClinicalData in my_root:
        for SubjectData in ClinicalData:
            if SubjectData.tag == '{http://www.cdisc.org/ns/odm/v1.3}SubjectData':
                for Element in SubjectData[2][1]:
                    for ItemOID in Element:
                        print(ItemOID)
                        if Element.tag == "{http://www.cdisc.org/ns/odm/v1.3}ItemGroupData":
                            if (ItemOID.attrib['ItemOID']) == param:
                                lglobale.append((ClinicalData.attrib['StudyOID'],
                                                 ClinicalData.attrib['MetaDataVersionOID'],
                                                 SubjectData.attrib['SubjectKey'], SubjectData[2][1][0][2].text,
                                                 ItemOID.text))

    df = pd.DataFrame(lglobale, columns=['StudyOID', 'MetaDataVersionOID', 'SubjectKey', 'DateTimeStamp from FormData',
                                         'ItemOID'])
    return df





#function that return all the list of elements for the sample block form
def get_viedoc_pat_bl(odm_xml, date):
    """ return a dataframe with: VersionOID, SubjectKey, Date of last update of all the patients block which have been modified after the date (format: JJ/MM/AAAA) in input """
    my_tree = et.ElementTree(odm_xml)
    root = my_tree.getroot()
    my_root = et.fromstring(root)
    lglobale=[]
    for ClinicalData in my_root:
        for SubjectData in ClinicalData:
            if SubjectData.tag == "{http://www.cdisc.org/ns/odm/v1.3}SubjectData" :
                for Element in SubjectData:
                    for DateTimeStamp in Element.iter('{http://www.cdisc.org/ns/odm/v1.3}DateTimeStamp'):
                        print(DateTimeStamp.text)
                        if difference_dates(DateTimeStamp.text, date)>0:
                            lglobale.append((DateTimeStamp.text, SubjectData.attrib['SubjectKey'], ClinicalData.attrib['MetaDataVersionOID'], Element.tag))
    df=pd.DataFrame(lglobale, columns =['Date of last update' ,'SubjectKey', 'Version' , 'Block name'])
    return(df)
#function that return the list of subject key from viedoc
def SubjectKeyList(odm_xml):
    my_tree = et.ElementTree(odm_xml)
    """ Print the SubjectKey of each Clinical Study from odm_ds """
    root = my_tree.getroot()
    my_root = et.fromstring(root)

    lglobale = []
    for ClinicalData in my_root:
        for SubjectData in ClinicalData:
            if SubjectData.tag == "{http://www.cdisc.org/ns/odm/v1.3}SubjectData":
                lglobale.append((ClinicalData.attrib['StudyOID'], ClinicalData.attrib['MetaDataVersionOID'],
                                 SubjectData.attrib['SubjectKey']))
    df = pd.DataFrame(lglobale, columns=['StudyOID', 'MetaDataVersionOID', 'SubjectKey'])
    return (df)


#function that return the value the list of patient for a specific item
def PatientItem(odm_xml, ItemOID):
    my_tree = et.ElementTree(odm_xml)
    root = my_tree.getroot()
    my_root = et.fromstring(root)
    lglobale=[]
    for ClinicalData in my_root:
        for SubjectData in ClinicalData:
            for FormData in SubjectData.iter('{http://www.cdisc.org/ns/odm/v1.3}FormData'):
                for ItemGroupData in FormData.iter('{http://www.cdisc.org/ns/odm/v1.3}ItemGroupData'):
                    for ItemDataInteger in ItemGroupData:
                        if(ItemDataInteger.attrib['ItemOID']) == ItemOID:
                            for DateTimeStamp in FormData.iter('{http://www.cdisc.org/ns/odm/v1.3}DateTimeStamp'):
                                lglobale.append((ClinicalData.attrib['StudyOID'],ClinicalData.attrib['MetaDataVersionOID'], DateTimeStamp.text, SubjectData.attrib['SubjectKey'], ItemDataInteger.text))
    df = pd.DataFrame(lglobale, columns = ['StudyOID' , 'VersionOID', 'FormData DateTimeStamp', 'SubjectKey', 'ItemOID'])
    return(df)

#Function to check if eCRF is available fot patient in all the list of patient
def check_if_ecrf_available(odm_xml, SubjectKey):
    my_tree = et.ElementTree(odm_xml)
    root = my_tree.getroot()
    my_root = et.fromstring(root)
    for ClinicalData in my_root.iter("{http://www.cdisc.org/ns/odm/v1.3}SubjectData"):
        if ClinicalData.attrib['SubjectKey']== SubjectKey:
            return True
    return False


#Example get_viedoc_sites to get the list of all sites and studies

get_viedoc_token_response = get_viedoc_token(token_request_parameters)
curr_token = get_viedoc_token_response.Token
get_viedoc_token_response = get_viedoc_sites(curr_token)
print(get_viedoc_token_response)



def Get_GetMetaData(curr_token, metaDataOid):
    GetMetaData_data_request = {
        'metaDataOid': metaDataOid,
        'includeSdm': 'false',
        'includeViedocExtensions': 'false'

    }
    metaDataOid=GetMetaData_data_request['metaDataOid']
    includeSdm=GetMetaData_data_request['includeSdm']
    includeViedocExtensions=GetMetaData_data_request['includeViedocExtensions']
    try:
        viedoc_clinical_data = soap_client.service.GetMetaData(curr_token,metaDataOid,includeSdm,includeViedocExtensions)
    except zeep.exceptions.Fault as fault:
            print(fault.detail)
    return viedoc_clinical_data
""""
test=Get_GetMetaData(curr_token, '6.0')
odm_xml = test.OdmXml
with open ('example_metadata.txt', 'w') as file:
   file.write(odm_xml)
#example 1 get clincal data for patient  '99-MS-p001'

getclinical_data_request = {
    'SiteCode': 'FR',
    'SubjectKey': '99-MS-p001'
}
Clinical_Data = Get_Clinical_Data(curr_token, getclinical_data_request)
odm_xml = Clinical_Data.OdmXml
#Example convert XML to JSON
json=XmlToJson(odm_xml)
print(json)
with open ('example_1.txt', 'w') as file:
    file.write(odm_xml)

#example 2 get all the data in SAMPBLK for all the patients
getclinical_data_request = {
    'SiteCode': 'FR',
    'FormOID' : 'SAMPBLK',
}
Clinical_Data = Get_Clinical_Data(curr_token, getclinical_data_request)
odm_xml = Clinical_Data.OdmXml
with open ('example_2.txt', 'w') as file:
    file.write(odm_xml)


#example 3 get all TUBLKID for all patients
getclinical_data_request = {
    'SiteCode': 'FR',
    'ItemOID': 'TUBLKID'

}

Clinical_Data = Get_Clinical_Data(curr_token, getclinical_data_request)
odm_xml = Clinical_Data.OdmXml
with open ('example_3.txt', 'w') as file:
    file.write(odm_xml)

# getclinical_data_request for all data in FR center (answer in ODM
getclinical_data_request = {
    'SiteCode': 'FR'
}
#Example SubjectKeyList
Clinical_Data = Get_Clinical_Data(curr_token, getclinical_data_request)
odm_xml = Clinical_Data.OdmXml
df = SubjectKeyList(odm_xml)
df.to_csv('example_SubjectKeyList', encoding='utf-8', index=False)

#Example check_if_ecrf_available
test_patient=check_if_ecrf_available(odm_xml, '1')
print(test_patient)
test_patient=check_if_ecrf_available(odm_xml, '99-OV-p014')
print(test_patient)

#example PatientItem to get the list of cohorts
test_patient=PatientItem(odm_xml, 'TUBLKID')
test_patient.to_csv('TUBLKID list', encoding='utf-8', index=False)

#example the list of block after the date 10/01/2023
test_patient=get_viedoc_pat_bl(odm_xml, '10/01/2023')
print(test_patient)
test_patient.to_csv('get_viedoc_pat_bl test', encoding='utf-8', index=False)

#example the list of COHORT for all the patient
test_patient=PatientItem(odm_xml, 'COHORT')
print(test_patient)
test_patient.to_csv('COHORT patient', encoding='utf-8', index=False)
"""

#example function to get all data patient
def get_viedoc(curr_token):
    getclinical_data_request = {
        'SiteCode': 'FR'
    }
    Clinical_Data = Get_Clinical_Data(curr_token, getclinical_data_request)
    odm_xml = Clinical_Data.OdmXml
    patient=SubjectKeyList(odm_xml)
    for i in range(len(patient)):
        print(patient.loc[i, "SubjectKey"], patient.loc[i,"MetaDataVersionOID"])
        SubjectKey = patient.loc[i, "SubjectKey"]
        MetaDataVersionOID = patient.loc[i, "MetaDataVersionOID"]
        getclinical_foronepatient = {
            'SiteCode': 'FR',
            'SubjectKey': SubjectKey
        }
        Clinical_Data_for_i = Get_Clinical_Data(curr_token, getclinical_foronepatient)
        odm_xml_for_i = Clinical_Data_for_i.OdmXml
        json_for_i = XmlToJson(odm_xml)
        patient.loc[i, "JSON"] = json_for_i
        patient.loc[i, "CDISC"] = odm_xml_for_i
    return patient

patient = get_viedoc(curr_token)
patient.to_csv('example_all_patients', encoding='utf-8', index=False)

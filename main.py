from typing import Generic, TypeVar
import requests
import os 
import json
import sys
from pydantic import BaseModel, Field
import time

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6,uk;q=0.5',
    'content-type': 'application/json;charset=UTF-8',
    'origin': 'https://zsyy.tjsjnyy.com',
    'priority': 'u=1, i',
    'referer': 'https://zsyy.tjsjnyy.com/',
    'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
}

 
print(os.getenv("PATIENT_INFO"))
params = json.loads(os.getenv("PATIENT_INFO", ""))

class ReportData(BaseModel):
    report_no: str = Field(alias='reportNo')
    report_type: str = Field(alias='reportType')
    report_name: str = Field(alias='reportName')
    report_url: str = Field(alias='reportURL')
    anamnesis_no: str = Field(alias='anamnesisNo')
    dept_name: str = Field(alias='deptName')
    doct_name: str = Field(alias='doctName')
    assay_date: str = Field(alias='assayDate')
    patient_name: str = Field(alias='patientName')
    patient_gender: str = Field(alias='patientGender')
    patient_age: str = Field(alias='patientAge')

DataT = TypeVar('DataT')

class ApiResponse(BaseModel, Generic[DataT]):
    code: int
    message: str
    data: DataT
    success: bool

# This model represents a single lab test result in the "assayItems" list.
class AssayItem(BaseModel):
    item_id: str = Field(alias='itemId')
    item_name: str = Field(alias='itemName')
    unit: str
    result: str
    state: str
    range_limit: str = Field(alias='rangeLimit')

# This model represents the main "data" object, which contains the conclusions
# and the list of assay items.
class ReportDetailData(BaseModel):
    conclusion: str
    check_conclusion: str = Field(alias='checkConclusion')
    assay_items: list[AssayItem] = Field(alias='assayItems')

def main():
    response = requests.post('https://report.tjsjnyy.com/api/report/reportList', params=params, headers=headers)
    reports = ApiResponse[list[ReportData]].model_validate_json(response.text)
    if reports.code != 200:
        print("Error fetching report list")

    data = {}

    for report in reports.data:
        print(f"Fetching {report.report_name}")
        query = {
            'idCard': params['idCard'],
            'startDate': '2024-06-20',
            'reportNo': report.report_no,
        }
        response = requests.post('https://report.tjsjnyy.com/api/report/jyDetail', params=query, headers=headers)
        reportDetail = ApiResponse[ReportDetailData].model_validate_json(response.text)
        data[report.report_no] = {
                'report': report,
                'reportDetail': reportDetail,
        }
        time.sleep(1)

    with open(sys.argv[1], "w") as f:
        data = json.dumps(data)
        f.write(data)


if __name__ == "__main__":
    main()

from typing import Generic, TypeVar
import requests
import os
import json
import sys
from pydantic import BaseModel, Field
import time

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>医学检测结果</title>
    <style>
     * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f5f7fa;
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        .header {
            background-color: #2563eb;
            color: white;
            padding: 24px;
            text-align: center;
        }

        .header h1 {
            font-size: 1.8em;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .header p {
            opacity: 0.9;
            font-size: 0.95em;
        }

        .content {
            padding: 24px;
        }

        .test-section {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            margin-bottom: 24px;
            overflow: hidden;
        }

        .test-header {
            background-color: #f8fafc;
            border-bottom: 1px solid #e5e7eb;
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
        }

        .test-name {
            font-size: 1.1em;
            font-weight: 600;
            color: #1f2937;
        }

        .normal-range {
            background-color: #dbeafe;
            color: #1d4ed8;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 500;
        }

        .results-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 1px;
            background-color: #e5e7eb;
        }

        .result-item {
            background-color: white;
            padding: 16px;
            text-align: center;
        }

        .result-item.abnormal {
            background-color: #fef3c7;
        }

        .result-date {
            color: #6b7280;
            font-size: 0.85em;
            margin-bottom: 6px;
            font-weight: 500;
        }

        .result-value {
            font-size: 1.1em;
            font-weight: 600;
            color: #1f2937;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }

        .status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            display: inline-block;
        }

        .normal {
            background-color: #10b981;
        }

        .low {
            background-color: #f59e0b;
        }

        .high {
            background-color: #ef4444;
        }

        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .header {
                padding: 16px;
            }
            
            .header h1 {
                font-size: 1.5em;
            }
            
            .content {
                padding: 16px;
            }
            
            .test-header {
                flex-direction: column;
                align-items: stretch;
                text-align: center;
            }
            
            .results-grid {
                grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            }
            
            .result-item {
                padding: 12px;
            }
        }
     </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>检测结果</h1>
            <p>Medical Test Results Dashboard</p>
        </div>
        
        <div class="content">
            CONTENT
        </div>
    </div>
</body>
</html>
"""

PERFERED_METRICS = set([
    "血红蛋白",
    "肌酐(肌氨酸氧化酶法）",
    "血小板"
])

headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6,uk;q=0.5",
    "content-type": "application/json;charset=UTF-8",
    "origin": "https://zsyy.tjsjnyy.com",
    "priority": "u=1, i",
    "referer": "https://zsyy.tjsjnyy.com/",
    "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
}


params = json.loads(os.getenv("PATIENT_INFO", ""))


class ReportData(BaseModel):
    report_no: str = Field(alias="reportNo")
    report_type: str = Field(alias="reportType")
    report_name: str = Field(alias="reportName")
    report_url: str = Field(alias="reportURL")
    anamnesis_no: str = Field(alias="anamnesisNo")
    dept_name: str = Field(alias="deptName")
    doct_name: str = Field(alias="doctName")
    assay_date: str = Field(alias="assayDate")
    patient_name: str = Field(alias="patientName")
    patient_gender: str = Field(alias="patientGender")
    patient_age: str = Field(alias="patientAge")


DataT = TypeVar("DataT")


class ApiResponse(BaseModel, Generic[DataT]):
    code: int
    message: str
    data: DataT
    success: bool


# This model represents a single lab test result in the "assayItems" list.
class AssayItem(BaseModel):
    item_id: str = Field(alias="itemId")
    item_name: str = Field(alias="itemName")
    unit: str
    result: str
    state: str
    range_limit: str = Field(alias="rangeLimit")


# This model represents the main "data" object, which contains the conclusions
# and the list of assay items.
class ReportDetailData(BaseModel):
    conclusion: str
    check_conclusion: str = Field(alias="checkConclusion")
    assay_items: list[AssayItem] = Field(alias="assayItems")


def main():
    if len(sys.argv) != 2:
        print("Usage: main.py output_file")
        sys.exit(1)

    response = requests.post(
        "https://report.tjsjnyy.com/api/report/reportList",
        params=params,
        headers=headers,
    )
    reports = ApiResponse[list[ReportData]].model_validate_json(response.text)
    if reports.code != 200:
        print("Error fetching report list")

    data = []

    for report in reports.data:
        print(f"Fetching {report.report_name}")
        query = {
            "idCard": params["idCard"],
            "startDate": "2024-06-20",
            "reportNo": report.report_no,
        }
        response = requests.post(
            "https://report.tjsjnyy.com/api/report/jyDetail",
            params=query,
            headers=headers,
        )
        reportDetail = ApiResponse[ReportDetailData].model_validate_json(response.text)
        for assay in reportDetail.data.assay_items:
            data.append(
                {
                    "name": assay.item_name.replace('★', ''),
                    "unit": assay.unit,
                    "result": assay.result,
                    "range_limit": assay.range_limit,
                    "date": report.assay_date,
                    "state": assay.state
                }
            )

    with open(sys.argv[1], "w") as f:
        content = ""
        metrics = set([d['name'] for d in data])
        metrics = sorted(metrics, key=lambda m: m in PERFERED_METRICS, reverse=True)
        for metric in metrics:
            rel_data = filter(lambda d: d['name'] == metric, data)
            rel_data = sorted(rel_data, key=lambda d: d['date'], reverse=True)
            range_limit = rel_data[0]['range_limit']
            unit = rel_data[0]['unit']
            metric_html = f"""
             <div class="test-section">
                <div class="test-header">
                    <div class="test-name">{metric}</div>
                    <div class="normal-range">正常范围: {range_limit}{unit}</div>
                </div>
                <div class="results-grid">
                    RESULT
                </div>
            </div>
            """
            result_html = ""
            for d in rel_data:
                if d['state'] == 'N':
                    status_class = 'normal'
                    parent_class = ""
                elif d['state'] == 'H':
                    status_class = 'high'
                    parent_class = "abnormal"
                else:
                    status_class = 'low'
                    parent_class = "abnormal"
                result_html += f"""
                   <div class="result-item {parent_class}">
                        <div class="result-date">{d['date']}</div>
                        <div class="result-value">{d['result']} {unit}<span class="status-dot {status_class}"></span></div>
                   </div>
                """
            metric_html = metric_html.replace("RESULT", result_html)
            content += metric_html
        f.write(HTML_TEMPLATE.replace("CONTENT", content))



if __name__ == "__main__":
    main()

import os
import pickle
import time
from io import BytesIO

import requests
from PIL import Image

session = requests.Session()

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
}


def get_captcha_code():
    # 验证码接口
    captcha_url = "https://erp.fulan.com.cn/admin/sec/captcha?date=110"
    resp = session.get(captcha_url)

    # 保存cookie
    with open("cookie.pkl", "wb") as f:
        pickle.dump(session.cookies, f)

    # 保存验证码图片等操作
    try:
        resp = session.get(captcha_url, timeout=5)
        img = Image.open(BytesIO(resp.content))

        img_path = os.path.join("debug_captcha/", "captcha.jpg")
        img.save(img_path)
    except Exception as e:
        print(f"下载失败：{e}")


def login():
    login_url = "https://erp.fulan.com.cn/admin/login"
    login_resp = session.post(login_url, data=login_data)

    if login_resp.status_code != 200:
        print("登录失败")
        raise Exception("登录失败")
    else:
        print("登录成功")


def get_pending_dates():
    # 获取待处理的日期
    weekly_url = "https://erp.fulan.com.cn/admin/weekly/findweeklyList"
    week_data = {"month": "2025年07月", "page": 1}
    res = session.post(weekly_url, data=week_data, headers=headers)
    week_data = res.json().get("data", {})
    print(f"查询结果: {week_data}")

    if week_data.get("success") and code == "200":
        print("查询项目列表成功")

    isVacation = week_data.get("isVacations")
    dateList = week_data.get("dateList")
    weeklyDayList = week_data.get("weeklyDayList")
    # print(dateList, isVacation)

    pending_dates = []
    for _date, is_vacation in zip(dateList, isVacation):
        if is_vacation != "true" and "2025-07" in _date:
            # print(f"{_date} 不是休息日")
            pending_dates.append(_date)

    handled_weekly_days = [
        i.get("workDate")
        for i in weeklyDayList
        if i.get("status") == "1" and "2025-07" in i.get("workDate", "")
    ]
    # print(f"待处理的工作日: {handled_weekly_days}")

    again_pending_dates = []
    for _date in pending_dates:
        for hd in handled_weekly_days:
            if _date in hd and str(_date).split("-")[-1] <= "26":
                # print(f"日期 {_date} 待处理")
                again_pending_dates.append(_date)

    return again_pending_dates


def post_weekly_data(again_pending_dates):
    for i in again_pending_dates:
        payload = {
            "weeklyDay[0].WeeklyDayDetail[0].projectInfoId": "P24100054",
            "weeklyDay[0].WeeklyDayDetail[0].projectInfoName": "申万宏源证劵2025年IT服务资源池",
            "weeklyDay[0].WeeklyDayDetail[0].workTypeId": "4",
            "weeklyDay[0].WeeklyDayDetail[0].workTypeName": "程序技术",
            "weeklyDay[0].WeeklyDayDetail[0].workHours": "8",
            "weeklyDay[0].WeeklyDayDetail[0].projectManagerNo": "undefined",
            "weeklyDay[0].WeeklyDayDetail[0].projectManagerName": "undefined",
            "weeklyDay[0].WeeklyDayDetail[0].projectTypeId": "undefined",
            "weeklyDay[0].WeeklyDayDetail[0].startTime": f"{i} 09:00",
            "weeklyDay[0].WeeklyDayDetail[0].endTime": f"{i} 18:00",
            "weeklyDay[0].WeeklyDayDetail[0].employeeNo": login_data.get(
                "username", ""
            ),
            "weeklyDay[0].WeeklyDayDetail[0].employeeName": login_data.get(
                "cn_username", ""
            ),
            "weeklyDay[0].WeeklyDayDetail[0].workDate": i,
            "weeklyDay[0].workDate": i,
            "weeklyDay[0].id": "",
            "weeklyDay[0].workDayId": "",
            "weeklyDay[0].status": "",
            "weeklyId": "",
            "id": "",
        }

        url = "https://erp.fulan.com.cn/admin/weekly/save"
        # 提交请求
        session.post(url, data=payload, headers=headers)
        time.sleep(1)  # 避免请求过快


def submit_data():
    submit_url = "https://erp.fulan.com.cn/admin/weekly/submit"

    # 查看是否休息接口
    weekly_url = "https://erp.fulan.com.cn/admin/weekly/findweeklyList"
    week_data = {"month": "2025年07月", "page": 1}
    res = session.post(weekly_url, data=week_data, headers=headers)
    week_data = res.json().get("data", {})

    weeklyDayList = week_data.get("weeklyDayList")

    handled_work_day_ids = [
        i.get("workDayId")
        for i in weeklyDayList
        if i.get("status") == "1" and i.get("workDayId")
    ]
    if handled_work_day_ids:
        session.post(
            submit_url, data={"workDayId": handled_work_day_ids[0]}, headers=headers
        )


if __name__ == "__main__":
    get_captcha_code()

    code = input("请输入验证码：")
    # 登录数据
    login_data = {
        "username": "",
        "cn_username": "",
        "password": "",
        "captcha": code,
    }
    if str(code).isdigit() and len(code) == 4:
        print("验证码格式正确")

    # 识别验证码后恢复 cookie，登录
    with open("cookie.pkl", "rb") as f:
        cookies = pickle.load(f)
    session.cookies.update(cookies)

    login()
    pending_dates = get_pending_dates()
    print(f"待处理的日期: {pending_dates}")

    post_weekly_data(pending_dates)

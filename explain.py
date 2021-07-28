# ライブラリの読み込み --------------------------------------------------------------
from time import sleep
from requests_html import HTMLSession
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

#リアルタイム混雑状況を導入している施設が表示されているページurl
url = "https://onsen.nifty.com/ip-konzatsu/"
#ニフティ温泉のメインンページ
base_url = "https://onsen.nifty.com"

#アクセス結果を、変数rに格納
r = requests.get(url, timeout=3)
#サーバーに負荷をかけないように2秒空ける
sleep(2)
r.raise_for_status()
#取得結果を解析して変数soupに格納
soup = BeautifulSoup(r.content, "lxml")

#混雑状況のリアルタイム表示に加盟している各施設のカードを取得
contents = soup.find_all("div", class_="facility")

#空のリストを用意
d_list = []

#各温泉施設の情報を取得
for i,content in enumerate(contents, start=1):
    #取得したい都道府県を抽出
    prefectures = content.find("span", class_="areaOnecol")
    if not prefectures.find(text=re.compile("埼玉県")):
        continue
    #施設名を取得
    facility_name = content.find("div", class_="titleOnecol").find("a").text
    a_tag = content.find("a").get("href")
    #各施設の詳細ページリンクのurl
    page_url = base_url + a_tag + "#congestionInfo"
    #このページはjavascriptを使用した動的なページのため
    # requsts_htmlライブラリのHTMLSessionモジュールが必要
    s = HTMLSession()
    r = s.get(page_url,timeout=3)
    #ここでページのレンダリング
    # timeout=20の理由は、デフォルト(timeout=8)だと時間が短くページの読み込みに間に合わない事例が多いため
    r.html.render(timeout=20)
    sleep(3)
    page_session = r.html
    #施設の評価を取得
    evaluation = page_session.find("dl.evaluation1", first=True).find("span.score", first=True).text
    outlines = page_session.find("div.outlineInner2",first=True).find("tr", first=False)
    #施設の住所を取得
    address = outlines[2].find("td", first=True).text
    
    #施設の営業時間を取得
    if outlines[4].find("th", first=True).text == "営業時間":
        business_hour = outlines[4].find("td", first=True).text
    else:
         business_hour = "非掲載"
    #施設の利用料金を取得
    if  page_session.find("dl.dateList1", first=True):
        price = page_session.find("dl.dateList1", first=True).find("dd",first=True).text
    else:
        price = "非掲載"
    #施設の公式HPを取得
    if outlines[-1].find("th", first=True).text == "公式HP":
        official_hp = outlines[-1].find("td", first=True).text
    else:
        official_hp = "非掲載"
    #施設へのアクセス方法を取得
    access = page_session.find("dl.dateList2", first=True).find("dd", first=False)[0].text

    #混雑状況の絵と絵文字の対応リスト
    number_list = {
        "/congestion/images/crowd_icon/01_not_crowd.png": "😄",
        "/congestion/images/crowd_icon/02_normal.png": "😃",
        "/congestion/images/crowd_icon/03_little_crowd.png": "😐",
        "/congestion/images/crowd_icon/04_crowd.png": "😰",
        "/congestion/images/crowd_icon/05_much_crowd.png": "🥵",
        "/congestion/images/crowd_icon/06_close.png": "営業時間外",
    }
    
    #混雑状況リスト
    congestion_list = []
    #混雑状況の更新日時を取得
    updated_date = page_session.find("p.currentState", first=True).text
    #混雑状況のエリア名と度合を取得
    congestions = page_session.find("div.mdl-card-height", first=False)
    for congestion in congestions:
        congested_area = congestion.find("h3.mdl-card__title-text", first=True).text
        try:
            number_of_people = congestion.find("img", first=True).attrs["src"]
            congestion_list.append({
                congested_area : number_list[number_of_people]
            })
        except:
            number_of_people = "非表示"
            congestion_list.append({
                congested_area : number_of_people
            })
        sleep(1)
    #pandasで表にしやすくするため、辞書型でリストに追加
    d_list.append({
        "施設名": facility_name,
        "住所": address,
        "評価 (5点満点)": evaluation,
        "混雑状況 (😄空いている、😃やや空いている、😐普通、😰やや混雑、🥵混雑)"
        : f"{updated_date} / {congestion_list}",
        "営業時間": business_hour,
        "価格": price,
        "アクセス": access,
        "公式HP": official_hp 
    })
    sleep(1)
    print(d_list)

print(d_list)
#pandasを使って、収集したデータを表にする
df = pd.DataFrame(d_list)
#表をcsv形式で出力する
df.to_csv("saitama.csv", index=None, encoding="utf-8-sig")


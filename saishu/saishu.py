import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import sqlite3  # SQLiteをインポート

# ローカル保存先を設定
csv_save_path = 'suumo.csv'  # CSV保存パス
db_save_path = 'suumo.db'    # SQLiteデータベース保存パス

# SQLiteデータベースに接続
conn = sqlite3.connect(db_save_path)
cursor = conn.cursor()

# テーブル作成（物件名、築年数、専有面積）
cursor.execute('''
CREATE TABLE IF NOT EXISTS property_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    size REAL
)
''')

base_url = "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13101&sc=13102&sc=13103&sc=13104&sc=13105&sc=13113&cb=0.0&ct=9999999&et=9999999&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2="

data_list = []

# 築年数の前処理関数
def preprocess_age(age):
    if age == "新築":
        return 0
    elif "築" in age:
        if "以上" in age:
            return 99  # 「99年以上」は99年として扱う
        return int(age.replace("築", "").replace("年", ""))
    return None

# ページごとのループ
for page in range(1, 572):  # 必要に応じてページ数を調整（例: 1～2ページをスクレイピング）
    url = f"{base_url}&page={page}"
    print(f"Scraping page: {url}")
    res = requests.get(url)
    soup = BeautifulSoup(res.content, "html.parser")

    # 物件情報の抽出
    items = soup.find_all("div", class_="cassetteitem")

    for item in items:
        # 物件名
        name_elem = item.find("div", class_="cassetteitem_content-title")
        name = name_elem.text.strip()

        # 築年数
        age_elem = item.find(class_="cassetteitem_detail-col3")
        if age_elem:
            age = preprocess_age(age_elem.find_all("div")[0].text.strip())

        # 専有面積
        size_elem = item.find("span", class_="cassetteitem_menseki")
        size = float(size_elem.text.strip().replace("m2", ""))

        # データをリストに追加
        data_list.append({
            "物件名": name,
            "築年数": age,
            "専有面積": size
        })

        # データベースに挿入
        cursor.execute('''
        INSERT INTO property_data (name, age, size) VALUES (?, ?, ?)
        ''', (name, age, size))

    time.sleep(1)  # サーバーへの負荷を避けるための待機時間

# コミットして変更を保存
conn.commit()

# SQLiteデータベースのクローズ
conn.close()

# DataFrameに変換してローカルに保存
df = pd.DataFrame(data_list)
print(df)

# ローカルにCSV保存
df.to_csv(csv_save_path, index=False, encoding="utf-8-sig")
print(f"データの保存が完了しました。ファイルは以下に保存されています：{csv_save_path}")

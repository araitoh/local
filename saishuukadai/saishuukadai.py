import requests
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
import time  # 待機時間に使用

# データベースの設定
db_name = "suumo_data.db"  # 保存するSQLiteデータベース名
table_name = "properties"  # 保存するテーブル名

# SQLiteデータベースへの接続
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# テーブルの作成（存在しない場合に作成）
cursor.execute(f"""
CREATE TABLE IF NOT EXISTS {table_name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age TEXT,
    size TEXT
)
""")
conn.commit()

# ベースURL
base_url = "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13101&sc=13102&sc=13103&sc=13104&sc=13105&sc=13113&cb=0.0&ct=9999999&et=9999999&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2="

# スクレイピングしたデータを格納するリスト
data_list = []

# ページごとのループ
for page in range(1, 572):  # 必要に応じてページ数を調整
    url = f"{base_url}&page={page}"
    print(f"Scraping page: {url}")
    
    try:
        # ページのHTMLを取得
        res = requests.get(url)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, "html.parser")

        # 物件情報を抽出
        items = soup.find_all("div", class_="cassetteitem")
        
        for item in items:
            # 物件名
            name_elem = item.find("div", class_="cassetteitem_content-title")
            name = name_elem.text.strip() if name_elem else "不明"

            # 築年数
            age_elem = item.find(class_="cassetteitem_detail-col3")
            age = age_elem.find_all("div")[0].text.strip() if age_elem else "不明"

            # 専有面積
            size_elem = item.find("span", class_="cassetteitem_menseki")
            size = size_elem.text.strip() if size_elem else "不明"

            # リストに追加
            data_list.append({
                "name": name,
                "age": age,
                "size": size
            })
        
        # ページ間で2秒待機（適宜調整可能）
        time.sleep(1)

    except Exception as e:
        print(f"Error on page {page}: {e}")
        continue

# データをデータベースに保存する関数
def save_to_database(data, conn, table_name):
    # Pandas DataFrameに変換
    df = pd.DataFrame(data)
    # データベースに書き込み（同じ名前のテーブルが存在すれば追記）
    df.to_sql(table_name, conn, if_exists="append", index=False)

# データ保存
save_to_database(data_list, conn, table_name)

# データベース接続を閉じる
conn.close()

print(f"データがデータベース '{db_name}' のテーブル '{table_name}' に保存されました。")

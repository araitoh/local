import flet as ft
import requests
import sqlite3
from datetime import datetime

# データベース初期化
def initialize_db():
    conn = sqlite3.connect("weather.db")
    cursor = conn.cursor()
    
    # 天気情報テーブル作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_code TEXT,
            area_name TEXT,
            weather TEXT,
            date_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

# 天気情報をDBに保存
def save_weather_to_db(area_code: str, area_name: str, weather: str):
    conn = sqlite3.connect("weather.db")
    cursor = conn.cursor()

    # 現在日時を取得
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # データを挿入
    cursor.execute('''
        INSERT INTO weather_info (area_code, area_name, weather, date_time)
        VALUES (?, ?, ?, ?)
    ''', (area_code, area_name, weather, current_time))

    conn.commit()
    conn.close()

# 過去の天気情報を取得
def fetch_past_weather(area_code: str, date: str) -> list:
    conn = sqlite3.connect("weather.db")
    cursor = conn.cursor()

    # 指定された日付のデータを取得
    cursor.execute('''
        SELECT area_name, weather, date_time
        FROM weather_info
        WHERE area_code = ? AND date_time LIKE ?
    ''', (area_code, f"{date}%"))

    results = cursor.fetchall()
    conn.close()
    return results

# 天気情報取得関数（DB保存付き）
def get_weather_info(region_code: str) -> str:
    weather_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{region_code}.json"
    try:
        response = requests.get(weather_url)
        response.raise_for_status()
        weather_data = response.json()

        # 天気情報の取得
        if weather_data:
            area_name = weather_data[0]["timeSeries"][0]["areas"][0]["area"]["name"]
            weather = weather_data[0]["timeSeries"][0]["areas"][0]["weathers"][0]
            
            # DBに保存
            save_weather_to_db(region_code, area_name, weather)
            
            return f"{area_name}の天気: {weather}"
        else:
            return "天気情報が見つかりませんでした。"
    except Exception as e:
        return f"天気情報の取得に失敗しました: {e}"

def main(page: ft.Page):
    # DB初期化
    initialize_db()

    page.spacing = 0
    page.padding = 0
    page.bgcolor = "#f0f0f0"

    # APIから地域データを取得
    url = "http://www.jma.go.jp/bosai/common/const/area.json"
    response = requests.get(url)
    data = response.json()
    centers = data.get("centers", {})

    # 地域ツリーを作成する関数
    def create_area_list(data, parent_name=""):
        tiles = []
        for code, info in data.items():
            region_name = info.get("name", "No Name")
            children = info.get("children", [])

            display_name = region_name if region_name != "No Name" else f"地域コード: {code}"

            # 子地域がある場合
            if children:
                child_data = {
                    child: centers.get(child, {"name": str(child)})
                    for child in children
                }
                tiles.append(
                    ft.ExpansionTile(
                        title=ft.Text(f"{parent_name} {display_name}", size=18, weight="bold"),
                        initially_expanded=False,
                        controls=create_area_list(child_data, parent_name=region_name),
                    )
                )
            else:  # 子地域がない場合
                tiles.append(
                    ft.ListTile(
                        title=ft.Text(f"{region_name}", size=16),
                        on_click=lambda e, region_code=code: display_weather(region_code),
                    )
                )
        return tiles

    # 天気情報表示用テキスト
    weather_text = ft.Text("", size=20, weight="bold", color=ft.colors.WHITE)

    # 天気情報の表示
    def display_weather(region_code: str):
        weather_info = get_weather_info(region_code)
        weather_text.value = weather_info
        page.update()

    # 過去の天気情報表示
    def display_past_weather(region_code: str, date: str):
        past_data = fetch_past_weather(region_code, date)
        if past_data:
            weather_text.value = "\n".join(
                [f"{row[2]} - {row[0]}: {row[1]}" for row in past_data]
            )
        else:
            weather_text.value = "過去のデータが見つかりませんでした。"
        page.update()

    # 地域ツリーを作成
    if "centers" in data:
        region_list = create_area_list(data["centers"])
    else:
        region_list = [ft.Text("地域データの取得に失敗しました。")]

    # ヘッダー
    header = ft.Column(
        controls=[
            ft.Text("日本の天気予報", size=28, weight="bold", color=ft.colors.BLACK),
            ft.Text("地域を選択して天気情報を表示します", size=20, color=ft.colors.BLACK),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # 地域選択と日付選択
    date_field = ft.TextField(label="日付を入力 (YYYY-MM-DD形式)", width=300)
    region_field = ft.TextField(label="地域コードを入力", width=300)

    # 過去天気表示ボタン
    past_weather_button = ft.ElevatedButton(
        text="過去の天気を表示",
        on_click=lambda e: display_past_weather(region_field.value, date_field.value),
    )

    # 天気情報カード
    weather_card = ft.Container(
        content=ft.Column(
            controls=[weather_text, region_field, date_field, past_weather_button],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.colors.BLUE_400,
        padding=20,
        border_radius=10,
    )

    # ページに追加
    page.add(header)
    page.add(ft.ListView(expand=True, controls=region_list, spacing=10, padding=10))
    page.add(weather_card)

# アプリケーションを起動
ft.app(target=main)

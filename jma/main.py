import flet as ft
import requests

# 天気情報取得関数
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
            return f"{area_name}の天気: {weather}"
        else:
            return "天気情報が見つかりませんでした。"
    except Exception as e:
        return f"天気情報の取得に失敗しました: {e}"

# メインアプリ
def main(page: ft.Page):
    page.spacing = 0
    page.padding = 0
    page.bgcolor = "#f0f0f0"  # 背景色を変更

    # API から地域データを取得
    url = "http://www.jma.go.jp/bosai/common/const/area.json"
    response = requests.get(url)
    data = response.json()

    # `centers` のデータを取得
    centers = data.get("centers", {})

    # 地域を動的に表示する関数
    def create_area_list(data, parent_name=""):
        tiles = []
        for code, info in data.items():
            region_name = info.get("name", "No Name")  # 地域名を取得
            children = info.get("children", [])

            # 地域名が空の場合、地域コードを代わりに表示
            display_name = region_name if region_name != "No Name" else f"地域コード: {code}"

            # 子地域がある場合
            if children:
                child_data = {
                    child: centers.get(child, {"name": str(child)})  # nameを子地域コードに変更
                    for child in children
                }
                tiles.append(
                    ft.ExpansionTile(
                        title=ft.Text(f"{parent_name} {display_name}", size=18, weight="bold"),
                        initially_expanded=False,
                        controls=create_area_list(child_data, parent_name=region_name),
                    )
                )
            else:  # 子地域がない場合（リーフノード）
                tiles.append(
                    ft.ListTile(
                        title=ft.Text(f"{region_name}", size=16),  # 地域名をそのまま表示
                        on_click=lambda e, region_code=code: display_weather(region_code),  # 地域コードを渡す
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

    # 地域ツリーを作成
    if "centers" in data:
        region_list = create_area_list(data["centers"])
    else:
        region_list = [ft.Text("地域データの取得に失敗しました。")]

    # ヘッダーを作成
    header = ft.Column(
        controls=[
            ft.Text("日本の天気予報", size=28, weight="bold", color=ft.colors.BLACK),
            ft.Text("地域を選択して、天気情報を表示します", size=20, color=ft.colors.BLACK),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # リストビューを作成
    scrollable_column = ft.ListView(
        expand=True,  # コンテンツを伸ばしてスクロールを可能にする
        controls=region_list,
        spacing=10,  # リスト間の間隔を広げる
        padding=10,  # パディングを追加
    )

    # 天気情報カード
    weather_card = ft.Container(
        content=ft.Column(
            controls=[weather_text],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.colors.BLUE_400,
        padding=20,
        border_radius=10,
    )

    # ページにヘッダー、リスト、天気カードを追加
    page.add(header)
    page.add(scrollable_column)
    page.add(weather_card)

# アプリケーションを起動
ft.app(target=main)

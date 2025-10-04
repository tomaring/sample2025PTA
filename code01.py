import streamlit as st
from datetime import date
import io

# fpdf2 をインポート
from fpdf import FPDF

# 日本語フォントのパス (プロジェクトのルートにIPAexGothic.ttfがあることを想定)
# Renderにデプロイする際、このファイルもGitリポジトリに含める必要があります。
FONT_PATH = "IPAexGothic.ttf"

# FPDFのサブクラスを作成し、コンストラクタでフォントを登録
class MyFPDF(FPDF):
    def __init__(self):
        super().__init__()
        try:
            # フォントファイルの登録
            # fname にはフォントファイルのパスを指定
            self.add_font("IPAexGothic", fname=FONT_PATH)
            # デフォルトでこのフォントを使用するように設定
            self.set_font("IPAexGothic", size=10)
        except Exception as e:
            # Streamlit上でエラーメッセージを表示し、スクリプトの実行を停止
            st.error(f"フォントの読み込みに失敗しました: {e}. '{FONT_PATH}' が存在するか確認してください。")
            st.stop() # Streamlitアプリケーションの実行を停止

    # 必要に応じて、共通のヘッダーやフッターメソッドなどをここに定義できます

def convert_to_wareki(dt):
    """日付を和暦文字列に変換する"""
    if dt.year >= 2019:
        era_name = "令和"
        era_year = dt.year - 2018
    elif dt.year >= 1989: # 平成の範囲
        era_name = "平成"
        era_year = dt.year - 1988
    else: # その他の年 (昭和以前はここでは扱わない)
        era_name = "西暦"
        era_year = dt.year
    return f"{era_name}{era_year}年{dt.month}月{dt.day}日"

def create_report_pdf(data):
    """
    入力データに基づいて事業報告書PDFを作成する (fpdf2バージョン)
    data辞書のキー:
    - 'report_date': dateオブジェクト
    - 'department': 担当部署文字列
    - 'business_reports': [{'date': str, 'content': str}] のリスト
    - 'issues': str
    - 'next_activities': [{'date': str, 'content': str}] のリスト
    """
    # MyFPDFのインスタンスを作成。__init__でフォントが登録される。
    pdf = MyFPDF()
    pdf.add_page() # 新しいページを追加

    # PDF描画の設定
    # fpdf2 は A4 サイズをデフォルトとするため、pagesizeの指定は不要
    # PDFの座標系: 左上が (0,0)

    # 固定テキスト: ***運営委員会にて提出をお願いします***
    pdf.set_xy(10, 10) # X, Y 座標を指定 (左上から10mm, 10mm)
    pdf.write(5, "***運営委員会にて提出をお願いします***") # write(行の高さ, テキスト)

    # タイトル: 事業内容報告書
    pdf.set_font("IPAexGothic", size=14)
    pdf.set_xy(0, 20) # ページ上端から20mmの位置に移動
    # w=210 (A4幅), h=10, txt="事業内容報告書", align='C' (中央揃え), ln=1 (次の描画を改行)
    pdf.cell(w=210, h=10, txt="事業内容報告書", align='C', ln=1)

    # 報告書作成日と担当部署
    pdf.set_font("IPAexGothic", size=10)
    # 現在のY座標から相対的に配置したい場合は pdf.get_y() を使う
    current_y = 35 # 仮の開始Y座標
    
    # 日付
    pdf.set_xy(140, current_y)
    # 仕様書に合わせて「令和7年9月2日」を固定で表示
    # 動的に入力された日付を表示したい場合は convert_to_wareki(data['report_date']) を使う
    pdf.write(5, "令和7年9月2日") 

    # 学年
    pdf.set_xy(10, current_y + 10)
    pdf.write(5, "学年")
    
    # 育成会本部
    pdf.set_xy(10, current_y + 15)
    pdf.write(5, "育成会本部")

    # 担当部署
    pdf.set_xy(140, current_y + 10) # 日付の下に配置
    pdf.write(5, data['department']) # 入力された担当部署

    # --- ここからレポート内容の描画 ---
    # fpdf2 で仕様書のような罫線を引くには、pdf.rect() や pdf.line() を使って
    # 手動で描画するか、専用のテーブル描画ロジックを組む必要があります。
    # ここでは、まずテキストの配置に注力し、罫線は後で追加できるようにします。

    # 各セクションの開始Y座標
    y_start_sections = current_y + 30

    # 1. 事業内容報告
    pdf.set_xy(10, y_start_sections)
    pdf.write(5, "事業内容報告")
    y_position = y_start_sections + 7
    for item in data['business_reports']:
        pdf.set_xy(20, y_position) # インデント
        # multi_cell を使えば自動で改行される
        pdf.multi_cell(w=180, h=5, txt=f"・ {item['date']}: {item['content']}")
        y_position = pdf.get_y() # 最新のY座標を取得

    # 2. 活動の反省と課題
    y_position += 10 # セクション間のスペース
    pdf.set_xy(10, y_position)
    pdf.write(5, "活動の反省と課題")
    y_position += 7
    pdf.set_xy(20, y_position)
    pdf.multi_cell(w=180, h=5, txt=data['issues'])
    y_position = pdf.get_y()

    # 3. 次回運営委員会までの活動予定
    y_position += 10
    pdf.set_xy(10, y_position)
    pdf.write(5, "次回運営委員会までの活動予定")
    y_position += 7
    for item in data['next_activities']:
        pdf.set_xy(20, y_position) # インデント
        pdf.multi_cell(w=180, h=5, txt=f"・ {item['date']}: {item['content']}")
        y_position = pdf.get_y()

    # PDFをバイトストリームとして出力
    return io.BytesIO(pdf.output())

# --- Streamlit UI の構築 ---
st.set_page_config(layout="wide")
st.title("育成会事業報告書作成アプリ")

# --- 3. 入力画面の要件 ---

st.header("入力項目")

# 報告書作成日
today = date.today()
report_date = st.date_input("報告書作成日", value=today, key="report_date_input")
st.write(f"和暦表記: {convert_to_wareki(report_date)}")

# 担当部署
departments = [
    "学年委員1年", "学年委員2年", "学年委員3年",
    "学年委員4年", "学年委員5年", "学年委員6年",
    "学年委員あゆみ", "広報部", "校外安全指導部",
    "教養部", "環境厚生部", "選考委員会", "育成会本部"
]
selected_department = st.selectbox("担当部署", departments, key="department_select")

st.subheader("事業内容報告")
# 初期表示は最低1セット。st.session_state を使用して状態を保持
if 'business_reports' not in st.session_state:
    st.session_state.business_reports = [{'date': '', 'content': ''}]

for i, report in enumerate(st.session_state.business_reports):
    cols = st.columns([0.2, 0.7, 0.1])
    with cols[0]:
        report['date'] = st.text_input(f"日程 {i+1}", value=report['date'], key=f"br_date_{i}")
    with cols[1]:
        report['content'] = st.text_area(f"事業内容報告 {i+1}", value=report['content'], key=f"br_content_{i}", height=50)
    with cols[2]:
        if i > 0: # 最初の項目は削除できないようにする
            if st.button("削除", key=f"br_delete_{i}"):
                st.session_state.business_reports.pop(i)
                st.experimental_rerun() # 削除後にUIを再描画

if st.button("事業内容報告を追加", key="add_business_report_button"):
    st.session_state.business_reports.append({'date': '', 'content': ''})
    st.experimental_rerun()


st.subheader("活動の反省と課題")
issues = st.text_area(
    "活動の反省と課題 (次年度以降の改善材料になりますので詳細にお願いします)",
    height=150,
    key="issues_text_area"
)

st.subheader("次回運営委員会までの活動予定")
# 初期表示は最低1セット
if 'next_activities' not in st.session_state:
    st.session_state.next_activities = [{'date': '', 'content': ''}]

for i, activity in enumerate(st.session_state.next_activities):
    cols = st.columns([0.2, 0.7, 0.1])
    with cols[0]:
        activity['date'] = st.text_input(f"日程 {i+1}", value=activity['date'], key=f"na_date_{i}")
    with cols[1]:
        activity['content'] = st.text_area(f"活動予定 {i+1}", value=activity['content'], key=f"na_content_{i}", height=50)
    with cols[2]:
        if i > 0: # 最初の項目は削除できないようにする
            if st.button("削除", key=f"na_delete_{i}"):
                st.session_state.next_activities.pop(i)
                st.experimental_rerun() # 削除後にUIを再描画

if st.button("活動予定を追加", key="add_next_activity_button"):
    st.session_state.next_activities.append({'date': '', 'content': ''})
    st.experimental_rerun()


# --- 4. 機能要件 ---

st.markdown("---")
# 「入力完了」ボタン
if st.button("**入力完了**", key="submit_button"):
    # エラー処理: 必須項目チェック
    # 各項目が空でないことを確認
    if not selected_department:
        st.warning("担当部署を選択してください。")
    elif not all(item['date'].strip() and item['content'].strip() for item in st.session_state.business_reports if item['date'] or item['content']):
        st.warning("事業内容報告の日程と内容をすべて入力するか、不要な行を削除してください。")
    elif not issues.strip():
        st.warning("活動の反省と課題を入力してください。")
    elif not all(item['date'].strip() and item['content'].strip() for item in st.session_state.next_activities if item['date'] or item['content']):
        st.warning("次回活動予定の日程と内容をすべて入力するか、不要な行を削除してください。")
    else:
        # PDF生成データ準備
        report_data = {
            'report_date': report_date,
            'department': selected_department,
            'business_reports': st.session_state.business_reports,
            'issues': issues,
            'next_activities': st.session_state.next_activities,
        }

        # PDF生成
        pdf_buffer = create_report_pdf(report_data)

        st.success("PDFが生成されました！")
        st.subheader("プレビュー")
        # StreamlitでのPDFプレビュー (fpdf2はバイト列を返すのでそのまま)
        st.components.v1.iframe(
            pdf_buffer.getvalue(),
            height=600,
            width="100%"
        )

        st.markdown("---")
        st.subheader("PDF保存")
        st.write("内容を確認しましたか？PDFデータを保存しますか？")

        # ファイル名生成
        wareki_year_str = convert_to_wareki(report_date).split('年')[0] # 例: "令和7"
        wareki_prefix = ""
        wareki_num = ""
        # 漢字部分と数字部分を分離
        for char in wareki_year_str:
            if '一' <= char <= '九' or '〇' <= char <= '九' or '０' <= char <= '９': # 漢数字や全角数字も考慮
                wareki_num += str(char)
            else:
                wareki_prefix += char

        # 数字を半角に変換 (全角数字対策)
        wareki_num = wareki_num.replace('〇', '0').replace('一', '1').replace('二', '2').replace('三', '3').replace('四', '4').replace('五', '5').replace('六', '6').replace('七', '7').replace('八', '8').replace('九', '9')
        wareki_num = "".join(filter(str.isdigit, wareki_num)) # 半角数字以外を除去

        final_wareki_year_tag = f"R{wareki_num}" if wareki_num else f"{report_date.year}" # 数字がなければ西暦を使用

        file_month = report_date.month
        file_name = f"{final_wareki_year_tag}.{file_month:02d}育成会事業報告書_{selected_department}.pdf"

        st.download_button(
            label="**PDFデータを保存**",
            data=pdf_buffer.getvalue(),
            file_name=file_name,
            mime="application/pdf",
            key="download_pdf_button"
        )

# 任意で「入力内容をクリア」ボタン
if st.button("入力内容をクリア", key="clear_button"):
    # session_stateのすべてのキーを削除してリセット
    for key in list(st.session_state.keys()): # list() でコピーを作成してから削除
        del st.session_state[key]
    st.experimental_rerun() # UIを再描画して初期状態に戻す

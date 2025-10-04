import streamlit as st
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

from fpdf import FPDF 
FONT_PATH = "IPAexGothic.ttf"

#外丸が勝手にいれたもの。まずはフォント対応
import os
from pathlib import Path
# アプリケーションのルートディレクトリ（app.pyがある場所）を基準にする
BASE_DIR = Path(__file__).resolve().parent
# フォントファイルへの絶対パスを作成
FONT_PATH = str(BASE_DIR / "IPAexGothic.ttf")
class MyFPDF(FPDF):
    def __init__(self):
        super().__init__()
        # フォントファイルの存在チェックと登録
        try:
            self.add_font("IPAexGothic", fname=FONT_PATH)
            self.set_font("IPAexGothic", size=10) # デフォルトフォントとして設定
        except Exception as e:
            st.error(f"フォントの読み込みに失敗しました: {e}. {FONT_PATH} が存在するか確認してください。")
            st.stop()

# fpdf2の場合の例 (ReportLabでも同様)
pdf.add_font("IPAexGothic", fname=FONT_PATH)

#さらにPDF対応
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
# ... (パスは上記1.bの方法で取得)
pdfmetrics.registerFont(TTFont('IPAexGothic', FONT_PATH))
# フォントファミリーの登録（通常、ここでは省略されることが多い）
#外丸ここまで

# 日本語フォントの登録 (IPAexGothicを想定)
# 実際にはTTFファイルをプロジェクト内に配置し、そのパスを指定してください
try:
    pdfmetrics.registerFont(TTFont('IPAexGothic', 'IPAexGothic.ttf'))
except Exception as e:
    st.error(f"フォントの読み込みに失敗しました: {e}. IPAexGothic.ttf が 'IPAexGothic.ttf' のパスに存在するか確認してください。")
    st.stop()

def convert_to_wareki(dt):
    """日付を和暦文字列に変換する"""
    if dt.year >= 2019:
        era_name = "令和"
        era_year = dt.year - 2018
    else: # 簡略化のため、ここでは令和のみ対応
        era_name = "平成"
        era_year = dt.year - 1988 # 例
    return f"{era_name}{era_year}年{dt.month}月{dt.day}日"

def create_report_pdf(data):
    """
    入力データに基づいて事業報告書PDFを作成する
    data辞書のキー:
    - 'report_date': dateオブジェクト
    - 'department': 担当部署文字列
    - 'business_reports': [{'date': str, 'content': str}] のリスト
    - 'issues': str
    - 'next_activities': [{'date': str, 'content': str}] のリスト
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont('IPAexGothic', 10)

    # 固定テキストとヘッダー
    c.drawString(50, 780, "***運営委員会にて提出をお願いします***")
    c.setFont('IPAexGothic', 14)
    c.drawCentredString(A4[0]/2, 750, "事業内容報告書")
    c.setFont('IPAexGothic', 10)
    c.drawString(50, 700, "学年")
    c.drawString(50, 680, "育成会本部")
    
    # 報告書作成日と担当部署の反映
    wareki_date = convert_to_wareki(data['report_date'])
    c.drawString(400, 720, f"令和7年9月2日") # 例として固定日付だが、本来は wareki_date を使用
    c.drawString(400, 700, data['department']) # 担当部署

    # 仮のPDF内容（詳細なレイアウトは後で実装）
    y_position = 650
    c.drawString(50, y_position, "1. 事業内容報告")
    for item in data['business_reports']:
        y_position -= 15
        c.drawString(70, y_position, f"・ {item['date']}: {item['content']}")

    y_position -= 30
    c.drawString(50, y_position, "2. 活動の反省と課題")
    y_position -= 15
    c.drawString(70, y_position, data['issues'])

    y_position -= 30
    c.drawString(50, y_position, "3. 次回運営委員会までの活動予定")
    for item in data['next_activities']:
        y_position -= 15
        c.drawString(70, y_position, f"・ {item['date']}: {item['content']}")

    c.save()
    buffer.seek(0)
    return buffer

st.set_page_config(layout="wide")
st.title("育成会事業報告書作成アプリ")

# --- 3. 入力画面の要件 ---

# 報告書作成日
st.header("入力項目")
today = date.today()
report_date = st.date_input("報告書作成日", value=today)
st.write(f"和暦表記: {convert_to_wareki(report_date)}")

# 担当部署
departments = [
    "学年委員1年", "学年委員2年", "学年委員3年",
    "学年委員4年", "学年委員5年", "学年委員6年",
    "学年委員あゆみ", "広報部", "校外安全指導部", # 仕様書に合わせて追加
    "教養部", "環境厚生部", "選考委員会", "育成会本部"
]
selected_department = st.selectbox("担当部署", departments)

st.subheader("事業内容報告")
# 初期表示は最低1セット
if 'business_reports' not in st.session_state:
    st.session_state.business_reports = [{'date': '', 'content': ''}]

for i, report in enumerate(st.session_state.business_reports):
    col1, col2, col3 = st.columns([0.2, 0.7, 0.1])
    with col1:
        report['date'] = st.text_input(f"日程 {i+1}", value=report['date'], key=f"br_date_{i}")
    with col2:
        report['content'] = st.text_area(f"事業内容報告 {i+1}", value=report['content'], key=f"br_content_{i}", height=50)
    with col3:
        if i > 0:
            if st.button("削除", key=f"br_delete_{i}"):
                st.session_state.business_reports.pop(i)
                st.experimental_rerun()

if st.button("事業内容報告を追加"):
    st.session_state.business_reports.append({'date': '', 'content': ''})
    st.experimental_rerun()


st.subheader("活動の反省と課題")
issues = st.text_area(
    "活動の反省と課題 (次年度以降の改善材料になりますので詳細にお願いします)",
    height=150
)

st.subheader("次回運営委員会までの活動予定")
# 初期表示は最低1セット
if 'next_activities' not in st.session_state:
    st.session_state.next_activities = [{'date': '', 'content': ''}]

for i, activity in enumerate(st.session_state.next_activities):
    col1, col2, col3 = st.columns([0.2, 0.7, 0.1])
    with col1:
        activity['date'] = st.text_input(f"日程 {i+1}", value=activity['date'], key=f"na_date_{i}")
    with col2:
        activity['content'] = st.text_area(f"活動予定 {i+1}", value=activity['content'], key=f"na_content_{i}", height=50)
    with col3:
        if i > 0:
            if st.button("削除", key=f"na_delete_{i}"):
                st.session_state.next_activities.pop(i)
                st.experimental_rerun()

if st.button("活動予定を追加"):
    st.session_state.next_activities.append({'date': '', 'content': ''})
    st.experimental_rerun()


# --- 4. 機能要件 ---

st.markdown("---")
if st.button("**入力完了**"):
    # エラー処理: 必須項目チェック (ここでは簡易的なもの)
    if not all([item['date'] and item['content'] for item in st.session_state.business_reports]):
        st.warning("事業内容報告の日程と内容をすべて入力してください。")
    elif not issues.strip():
        st.warning("活動の反省と課題を入力してください。")
    elif not all([item['date'] and item['content'] for item in st.session_state.next_activities]):
        st.warning("次回活動予定の日程と内容をすべて入力してください。")
    else:
        # PDF生成データ準備
        report_data = {
            'report_date': report_date,
            'department': selected_department,
            'business_reports': st.session_state.business_reports,
            'issues': issues,
            'next_activities': st.session_state.next_activities,
        }

        pdf_buffer = create_report_pdf(report_data)

        st.success("PDFが生成されました！")
        st.subheader("プレビュー")
        # StreamlitでのPDFプレビュー (HTML埋め込み)
        st.components.v1.iframe(
            pdf_buffer.getvalue().decode('latin-1') if isinstance(pdf_buffer.getvalue(), bytes) else pdf_buffer.getvalue(),
            height=600,
            width="100%"
        )

        st.markdown("---")
        st.subheader("PDF保存")
        st.write("内容を確認しましたか？PDFデータを保存しますか？")

        # ファイル名生成
        wareki_year = convert_to_wareki(report_date).split('年')[0]
        file_month = report_date.month
        file_name = f"R{wareki_year}.{file_month:02d}育成会事業報告書_{selected_department}.pdf"

        st.download_button(
            label="**PDFデータを保存**",
            data=pdf_buffer.getvalue(),
            file_name=file_name,
            mime="application/pdf"
        )

# 任意で「入力内容をクリア」ボタン
if st.button("入力内容をクリア"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.experimental_rerun()

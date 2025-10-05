import streamlit as st
from datetime import date
import io
import base64

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
    pdf = MyFPDF()
    pdf.add_page()

    # PDF描画の設定
    pdf.set_auto_page_break(True, margin=15) # 自動改ページと下マージン
    pdf.set_line_width(0.4) # 罫線の太さ

    # 固定テキスト: ***運営委員会にて提出をお願いします***
    pdf.set_font("IPAexGothic", size=10)
    pdf.set_xy(10, 10)
    pdf.write(5, "***運営委員会にて提出をお願いします***")

    # タイトル: 事業内容報告書
    pdf.set_font("IPAexGothic", size=14)
    pdf.set_xy(0, 20)
    pdf.cell(w=210, h=10, txt="事業内容報告書", align='C', ln=1)

    # 報告書作成日と担当部署のエリア
    # X座標の開始点、Y座標の開始点、幅、高さ
    area_x = 10
    area_y = 35
    area_width = 190 # A4の幅-左右マージン
    # 高さはこの時点では固定値で定義し、後で内容に合わせて調整または描画
    
    pdf.set_font("IPAexGothic", size=10)
    
    # 報告書作成日 (固定で令和7年9月2日)
    pdf.set_xy(140, area_y)
    pdf.write(5, "令和7年9月2日") 

    # 学年
    pdf.set_xy(20, area_y + 10) # 添付画像に合わせてX座標を調整
    pdf.cell(w=50, h=7, txt="学年", border='B') # 下線のみ

    # 育成会本部
    pdf.set_xy(20, area_y + 17) # 学年の下
    pdf.cell(w=50, h=7, txt="育成会本部", border='B') # 下線のみ

    # 担当部署
    pdf.set_xy(140, area_y + 17) # 日付の下、育成会本部の右
    pdf.write(5, data['department'])


    # --- 事業内容報告テーブル ---
    # ヘッダーの定義
    y_start_business_report = pdf.get_y() + 15 # 現在のY座標から開始
    pdf.set_xy(10, y_start_business_report)
    pdf.set_font("IPAexGothic", 'B', size=10) # ヘッダーを太字に
    pdf.set_fill_color(240, 240, 240) # ヘッダーの背景色 (任意)

    # ヘッダーセル
    pdf.cell(w=25, h=8, txt="日程", border=1, align='C', fill=True)
    pdf.cell(w=165, h=8, txt="事業内容報告", border=1, align='C', ln=1, fill=True)

    pdf.set_font("IPAexGothic", size=10) # 内容は通常フォントに戻す

    # 内容の描画
    # multi_cellを使用するため、各行の高さを動的に調整する
    business_report_start_y = pdf.get_y() # 各行の開始Y座標を記録
    for item in data['business_reports']:
        # 日程セル (高さを後で決定するため、ここでは描画しない)
        # multi_cellの高さ計算のために一時的に設定
        pdf.set_xy(35, pdf.get_y())
        temp_content_y = pdf.get_y() # コンテンツ描画前のY座標を保持
        # multi_cellは自動改行し、ln=1で次の描画を改行位置から開始する
        pdf.multi_cell(w=165, h=6, txt=item['content'], border=0, align='L', ln=1)
        content_height = pdf.get_y() - temp_content_y # contentによって消費された高さ

        # 日程セルを正確な高さで描画
        pdf.set_xy(10, temp_content_y) # 元のY座標に戻す
        pdf.cell(w=25, h=content_height, txt=item['date'], border='LRB', align='C') # 左右下線のみ
        
        # content_cellの右線と底線も描画 (multi_cellがln=1で改行しているので不要だが、念のため)
        pdf.set_xy(35, temp_content_y)
        pdf.multi_cell(w=165, h=6, txt=item['content'], border='RB', align='L', ln=1) # 右下線のみ

    # 罫線が描画されてない部分を修正
    if not data['business_reports']:
        # データがない場合も空のセルを描画して枠線は維持
        pdf.cell(w=25, h=20, txt="", border=1, align='C')
        pdf.cell(w=165, h=20, txt="", border=1, align='L', ln=1)
    
    business_report_end_y = pdf.get_y() # 事業内容報告セクションの終了Y座標

    # --- 活動の反省と課題テーブル ---
    y_start_issues = business_report_end_y + 10
    pdf.set_xy(10, y_start_issues)
    pdf.set_font("IPAexGothic", 'B', size=10)
    pdf.cell(w=190, h=8, txt="活動の反省と課題", border=1, align='C', ln=1, fill=True)
    pdf.set_font("IPAexGothic", size=10)

    # multi_cellで内容を描画し、高さを取得
    issues_start_y = pdf.get_y()
    pdf.set_xy(10, issues_start_y)
    # 適切な高さを確保するため、内容が空でも最低限の高さを設定
    if not data['issues'].strip():
        # 内容がない場合でも最低限の高さを確保
        issues_height = 30 # 例: 3行分の高さ
        pdf.multi_cell(w=190, h=6, txt="(次年度以降の改善材料になりますので詳細にお願いします)", border='LRB', align='L')
    else:
        # プレースホルダーの文字数も考慮して高さを取得
        # まずプレースホルダー文字なしで高さを計算
        pdf.multi_cell(w=190, h=6, txt=data['issues'], border=0, align='L') # 枠線なしで高さを計算
        actual_issues_height = pdf.get_y() - issues_start_y
        pdf.set_xy(10, issues_start_y) # Y座標を戻す
        # 最低高さを考慮
        issues_height = max(actual_issues_height, 20) # 最低20mmの高さ

        # 正しい高さで枠線と内容を描画
        pdf.multi_cell(w=190, h=6, txt=data['issues'], border='LRB', align='L') # 左右下線のみ


    issues_end_y = pdf.get_y() # 活動の反省と課題セクションの終了Y座標

    # --- 次回運営委員会までの活動予定テーブル ---
    y_start_next_activities = issues_end_y + 10
    pdf.set_xy(10, y_start_next_activities)
    pdf.set_font("IPAexGothic", 'B', size=10)
    pdf.cell(w=190, h=8, txt="次回運営委員会までの活動予定", border=1, align='C', ln=1, fill=True)
    pdf.set_font("IPAexGothic", size=10)

    next_activities_start_y = pdf.get_y()
    for item in data['next_activities']:
        pdf.set_xy(35, pdf.get_y())
        temp_content_y = pdf.get_y()
        pdf.multi_cell(w=165, h=6, txt=item['content'], border=0, align='L', ln=1)
        content_height = pdf.get_y() - temp_content_y

        pdf.set_xy(10, temp_content_y)
        pdf.cell(w=25, h=content_height, txt=item['date'], border='LRB', align='C')
        
        pdf.set_xy(35, temp_content_y)
        pdf.multi_cell(w=165, h=6, txt=item['content'], border='RB', align='L', ln=1)
    
    if not data['next_activities']:
        # データがない場合も空のセルを描画して枠線は維持
        pdf.cell(w=25, h=20, txt="", border=1, align='C')
        pdf.cell(w=165, h=20, txt="", border=1, align='L', ln=1)


    # PDFをバイトストリームとして出力
    return io.BytesIO(pdf.output())

# --- Streamlit UI の構築 ---
st.set_page_config(layout="wide")
st.title("育成会事業報告書作成アプリ")

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
if 'business_reports' not in st.session_state:
    st.session_state.business_reports = [{'date': '', 'content': ''}]

for i, report in enumerate(st.session_state.business_reports):
    cols = st.columns([0.2, 0.7, 0.1])
    with cols[0]:
        report['date'] = st.text_input(f"日程 {i+1}", value=report['date'], key=f"br_date_{i}")
    with cols[1]:
        report['content'] = st.text_area(f"事業内容報告 {i+1}", value=report['content'], key=f"br_content_{i}", height=50)
    with cols[2]:
        if i > 0:
            if st.button("削除", key=f"br_delete_{i}"):
                st.session_state.business_reports.pop(i)
                st.rerun()

if st.button("事業内容報告を追加", key="add_business_report_button"):
    st.session_state.business_reports.append({'date': '', 'content': ''})
    st.rerun()

st.subheader("活動の反省と課題")
issues = st.text_area(
    "活動の反省と課題 (次年度以降の改善材料になりますので詳細にお願いします)",
    value="(次年度以降の改善材料になりますので詳細にお願いします)", # プレースホルダーとして初期値を設定
    height=150,
    key="issues_text_area"
)
# 初期値がプレースホルダーの場合、PDF出力時には空として扱う
if issues == "(次年度以降の改善材料になりますので詳細にお願いします)":
    issues_for_pdf = ""
else:
    issues_for_pdf = issues


st.subheader("次回運営委員会までの活動予定")
if 'next_activities' not in st.st.session_state:
    st.session_state.next_activities = [{'date': '', 'content': ''}]

for i, activity in enumerate(st.session_state.next_activities):
    cols = st.columns([0.2, 0.7, 0.1])
    with cols[0]:
        activity['date'] = st.text_input(f"日程 {i+1}", value=activity['date'], key=f"na_date_{i}")
    with cols[1]:
        activity['content'] = st.text_area(f"活動予定 {i+1}", value=activity['content'], key=f"na_content_{i}", height=50)
    with cols[2]:
        if i > 0:
            if st.button("削除", key=f"na_delete_{i}"):
                st.session_state.next_activities.pop(i)
                st.rerun()

if st.button("活動予定を追加", key="add_next_activity_button"):
    st.session_state.next_activities.append({'date': '', 'content': ''})
    st.rerun()

st.markdown("---")
if st.button("**入力完了**", key="submit_button"):
    # エラー処理: 必須項目チェック
    if not selected_department:
        st.warning("担当部署を選択してください。")
    # 事業内容報告の必須チェック
    elif not all(item['date'].strip() and item['content'].strip() for item in st.session_state.business_reports if item['date'] or item['content']):
        # 空の行は無視し、入力がある行は両方必須とする
        valid_br_entries = [item for item in st.session_state.business_reports if item['date'] or item['content']]
        if valid_br_entries and not all(item['date'].strip() and item['content'].strip() for item in valid_br_entries):
            st.warning("事業内容報告の日程と内容をすべて入力するか、不要な行を削除してください。")
        elif not valid_br_entries: # 全て空の場合も警告
            st.warning("事業内容報告を入力してください。")
    # 活動の反省と課題の必須チェック (プレースホルダーも考慮)
    elif not issues_for_pdf.strip(): # PDF出力用の変数をチェック
        st.warning("活動の反省と課題を入力してください。")
    # 次回活動予定の必須チェック
    elif not all(item['date'].strip() and item['content'].strip() for item in st.session_state.next_activities if item['date'] or item['content']):
        valid_na_entries = [item for item in st.st.session_state.next_activities if item['date'] or item['content']]
        if valid_na_entries and not all(item['date'].strip() and item['content'].strip() for item in valid_na_entries):
            st.warning("次回活動予定の日程と内容をすべて入力するか、不要な行を削除してください。")
        elif not valid_na_entries: # 全て空の場合も警告
            st.warning("次回活動予定を入力してください。")
    else:
        # PDF生成データ準備
        report_data = {
            'report_date': report_date,
            'department': selected_department,
            'business_reports': st.session_state.business_reports,
            'issues': issues_for_pdf, # プレースホルダー除去後の値を使用
            'next_activities': st.session_state.next_activities,
        }

        # PDF生成
        pdf_buffer = create_report_pdf(report_data)

        st.success("PDFが生成されました！")
        st.subheader("プレビュー")

        pdf_data_bytes = pdf_buffer.getvalue()
        base64_pdf = base64.b64encode(pdf_data_bytes).decode('ascii')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600px" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("PDF保存")
        st.write("内容を確認しましたか？PDFデータを保存しますか？")

        wareki_year_str = convert_to_wareki(report_date).split('年')[0]
        wareki_prefix = ""
        wareki_num = ""
        for char in wareki_year_str:
            if '一' <= char <= '九' or '〇' <= char <= '九' or '０' <= char <= '９':
                wareki_num += str(char)
            else:
                wareki_prefix += char
        wareki_num = wareki_num.replace('〇', '0').replace('一', '1').replace('二', '2').replace('三', '3').replace('四', '4').replace('五', '5').replace('六', '6').replace('七', '7').replace('八', '8').replace('九', '9')
        wareki_num = "".join(filter(str.isdigit, wareki_num))
        final_wareki_year_tag = f"R{wareki_num}" if wareki_num else f"{report_date.year}"

        file_month = report_date.month
        file_name = f"{final_wareki_year_tag}.{file_month:02d}育成会事業報告書_{selected_department}.pdf"

        st.download_button(
            label="**PDFデータを保存**",
            data=pdf_buffer.getvalue(),
            file_name=file_name,
            mime="application/pdf",
            key="download_pdf_button"
        )

if st.button("入力内容をクリア", key="clear_button"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

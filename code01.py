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
    仕様書PDFのレイアウトを再現
    """
    try:
        pdf = MyFPDF()
    except RuntimeError as e:
        st.error(str(e))
        return None

    pdf.add_page()

    # --- ヘッダー部分 ---
    # フォント設定
    pdf.set_font("IPAexGothic", size=10)

    # ***運営委員会にて提出をお願いします***
    pdf.set_xy(10, 10)
    pdf.cell(w=0, h=5, txt="***運営委員会にて提出をお願いします***", ln=1, align='C') # 中央揃え

    # タイトル: 事業内容報告書
    pdf.set_font("IPAexGothic", size=20)
    pdf.set_xy(0, pdf.get_y() + 5) # 中央揃え
    pdf.cell(w=210, h=10, txt="事業内容報告書", align='C', ln=1)

    # 右上の日付
    pdf.set_font("IPAexGothic", size=12)
    pdf.set_xy(140, 30) # 令和7年9月2日の位置を調整
    pdf.cell(60, 5, convert_to_wareki(data['report_date']), ln=1, align='R')
'''
    # 学年 / 育成会本部 / 担当部署 の枠線とテキスト
    box_start_x = 10
    box_start_y = 40
    box_width = 190
    box_height = 25 # 学年, 育成会本部, 担当部署 を含む全体の高さ

    pdf.set_xy(box_start_x, box_start_y)
    pdf.set_fill_color(255, 255, 255) # 白
    pdf.rect(box_start_x, box_start_y, box_width, box_height, 'DF') # 全体の枠

    # 各項目の中線
    # 学年と育成会本部
    pdf.line(box_start_x, box_start_y + 10, box_start_x + box_width, box_start_y + 10) # 学年と育成会本部の中線

    # 左側と右側を区切る縦線 (担当部署との間)
    pdf.line(box_start_x + box_width * 0.7, box_start_y, box_start_x + box_width * 0.7, box_start_y + box_height)

    # テキスト配置
    pdf.set_font("IPAexGothic", size=10)
    
    # 学年 (左上)
    pdf.set_xy(box_start_x + 2, box_start_y + 2)
    pdf.cell(w=box_width * 0.7 - 2, h=8, txt="学年", align='L')

    # 育成会本部 (左下)
    pdf.set_xy(box_start_x + 2, box_start_y + 12)
    pdf.cell(w=box_width * 0.7 - 2, h=10, txt="育成会本部", align='L')
    
    # 担当部署 (右上)
    pdf.set_xy(box_start_x + box_width * 0.7 + 2, box_start_y + 2)
    pdf.cell(w=box_width * 0.3 - 4, h=20, txt=data['department'], align='C')
'''
    pdf.set_font("IPAexGothic", size=20)
    pdf.set_xy(10, 30) # 令和7年9月2日の位置を調整
    pdf.cell(W=60, h=5, txt=data['department'], ln=1, align='R')


    # --- 事業内容報告 ---
    section_margin_top = 5 # 上部マージン
    # タイトル部分の枠線
    y_current = box_start_y + box_height + section_margin_top
    pdf.set_xy(box_start_x, y_current)
    pdf.set_font("IPAexGothic", size=10) # 太字
    pdf.cell(w=box_width, h=8, txt="事業内容報告", border=1, ln=1, align='L') # 枠付き
    pdf.set_font("IPAexGothic", size=10) # 太字解除

    # テーブルヘッダー
    y_current = pdf.get_y()
    pdf.set_xy(box_start_x, y_current)
    pdf.set_font("IPAexGothic", size=9)
    pdf.cell(w=box_width * 0.2, h=7, txt="日程", border=1, align='C')
    pdf.cell(w=box_width * 0.8, h=7, txt="事業内容報告", border=1, ln=1, align='C')
    pdf.set_font("IPAexGothic", size=9) # 太字解除

    # テーブル内容
    y_current = pdf.get_y()
    min_row_height = 10 # 各行の最小高さ
    for i, item in enumerate(data['business_reports']):
        # 日程セル
        pdf.set_xy(box_start_x, y_current)
        pdf.cell(w=box_width * 0.2, h=min_row_height, txt=item['date'], border=1, align='C', fill=0)

        # 事業内容報告セル (multi_cellで自動改行)
        # multi_cellはln=1を指定すると自動で次の行のy_currentを進める
        # ただし、行の高さを先に計算する必要がある
        text_w = box_width * 0.8
        content_lines = pdf.get_string_width(item['content']) / text_w # おおよその行数
        # 小数点以下切り上げ
        num_lines = int(content_lines) + 1 if content_lines > 0 else 1 
        current_row_height = max(min_row_height, num_lines * pdf.font_size * 1.2) # 適切な行高さを計算

        # pdf.set_xy(box_start_x + box_width * 0.2, y_current)
        # pdf.multi_cell(w=box_width * 0.8, h=pdf.font_size * 1.2, txt=item['content'], border=1, align='L')

        # multi_cellとcellの組み合わせが難しいので、rectで枠を先に描いてからmulti_cell
        pdf.rect(box_start_x + box_width * 0.2, y_current, box_width * 0.8, current_row_height)
        pdf.set_xy(box_start_x + box_width * 0.2 + 1, y_current + 1) # マージンを考慮してテキスト開始位置を調整
        pdf.multi_cell(w=box_width * 0.8 - 2, h=pdf.font_size * 1.2, txt=item['content'], align='L')

        y_current = y_current + current_row_height # 次の行の開始Y座標


    # --- 活動の反省と課題 ---
    y_current += section_margin_top # 前のセクションからのマージン
    pdf.set_xy(box_start_x, y_current)
    pdf.set_font("IPAexGothic", size=10) # 太字
    pdf.cell(w=box_width, h=8, txt="活動の反省と課題", border=1, ln=1, align='L')
    pdf.set_font("IPAexGothic", size=10) # 太字解除

    y_current = pdf.get_y()
    # テキストエリアの内容をmulti_cellで表示
    # 最小高さを確保しつつ、テキスト量に応じて高さが伸びるようにする
    text_w = box_width - 2 # 左右マージン考慮
    content_lines = pdf.get_string_width(data['issues']) / text_w
    num_lines = int(content_lines) + 1 if content_lines > 0 else 1
    issue_box_height = max(30, num_lines * pdf.font_size * 1.2) # 最小高30mm

    pdf.rect(box_start_x, y_current, box_width, issue_box_height) # 枠を描画
    pdf.set_xy(box_start_x + 1, y_current + 1) # テキスト開始位置を調整
    pdf.multi_cell(w=box_width - 2, h=pdf.font_size * 1.2, txt=data['issues'], align='L')

    y_current += issue_box_height


    # --- 次回運営委員会までの活動予定 ---
    y_current += section_margin_top
    pdf.set_xy(box_start_x, y_current)
    pdf.set_font("IPAexGothic", size=10) # 太字
    pdf.cell(w=box_width, h=8, txt="次回運営委員会までの活動予定", border=1, ln=1, align='L')
    pdf.set_font("IPAexGothic", size=10) # 太字解除

    # テーブルヘッダー
    y_current = pdf.get_y()
    pdf.set_xy(box_start_x, y_current)
    pdf.set_font("IPAexGothic", size=9)
    pdf.cell(w=box_width * 0.2, h=7, txt="日程", border=1, align='C')
    pdf.cell(w=box_width * 0.8, h=7, txt="活動予定", border=1, ln=1, align='C')
    pdf.set_font("IPAexGothic", size=9) # 太字解除

    # テーブル内容
    y_current = pdf.get_y()
    for i, item in enumerate(data['next_activities']):
        # 日程セル
        pdf.set_xy(box_start_x, y_current)
        pdf.cell(w=box_width * 0.2, h=min_row_height, txt=item['date'], border=1, align='C', fill=0)

        # 活動予定セル (multi_cellで自動改行)
        text_w = box_width * 0.8
        content_lines = pdf.get_string_width(item['content']) / text_w
        num_lines = int(content_lines) + 1 if content_lines > 0 else 1
        current_row_height = max(min_row_height, num_lines * pdf.font_size * 1.2)

        pdf.rect(box_start_x + box_width * 0.2, y_current, box_width * 0.8, current_row_height)
        pdf.set_xy(box_start_x + box_width * 0.2 + 1, y_current + 1)
        pdf.multi_cell(w=box_width * 0.8 - 2, h=pdf.font_size * 1.2, txt=item['content'], align='L')

        y_current = y_current + current_row_height


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
                st.rerun() # 削除後にUIを再描画

if st.button("事業内容報告を追加", key="add_business_report_button"):
    st.session_state.business_reports.append({'date': '', 'content': ''})
    st.rerun()


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
                st.rerun() # 削除後にUIを再描画

if st.button("活動予定を追加", key="add_next_activity_button"):
    st.session_state.next_activities.append({'date': '', 'content': ''})
    st.rerun()


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

        
        # PDFのバイナリデータを取得
        pdf_data_bytes = pdf_buffer.getvalue()

        # Base64エンコード
        # base64エンコードされた文字列は必ずASCII文字なので、decode('ascii')で安全に変換
        base64_pdf = base64.b64encode(pdf_data_bytes).decode('ascii')

        # data: URIスキームとしてHTMLの<iframe>タグに埋め込む
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600px" type="application/pdf"></iframe>'

        # StreamlitでHTMLとして表示
        # unsafe_allow_html=True は必須
        st.markdown(pdf_display, unsafe_allow_html=True)


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
    st.rerun() # UIを再描画して初期状態に戻す

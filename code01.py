import streamlit as st
from datetime import date
import io
import base64

# fpdf2 をインポート
from fpdf import FPDF

# 日本語フォントのパス (プロジェクトのルートにIPAexGothic.ttfがあることを想定)
# Renderにデプロイする際、このファイルもGitリポジションに含める必要があります。
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
            self.set_font("IPAexGothic", size=12) # デフォルトサイズを12に変更
        except Exception as e:
            # Streamlit上でエラーメッセージを表示し、スクリプトの実行を停止
            st.error(f"フォントの読み込みに失敗しました: {e}. '{FONT_PATH}' が存在するか確認してください。")
            st.stop() # Streamlitアプリケーションの実行を停止

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
    
    # 全体の左右余白
    page_width = pdf.w
    # ご要望の左右余白30mmを反映
    left_margin_mm = 30
    right_margin_mm = 30
    
    # メインコンテンツエリアの開始X座標と幅
    content_area_x = left_margin_mm
    content_area_width = page_width - left_margin_mm - right_margin_mm
    
    # --- ヘッダー部分 ---
    # ***運営委員会にて提出をお願いします***
    pdf.set_font("IPAexGothic", size=10)
    pdf.set_xy(0, 15) # Y座標を調整
    pdf.cell(w=page_width, h=5, txt="***運営委員会にて提出をお願いします***", ln=1, align='C') # 中央揃え

    # タイトル: 事業内容報告書
    pdf.set_font("IPAexGothic", size=20)
    pdf.set_xy(0, pdf.get_y() + 5) # Y座標を調整
    pdf.cell(w=page_width, h=10, txt="事業内容報告書", align='C', ln=1)

    # 右上の日付 (「令和 年 月 日」形式)
    pdf.set_font("IPAexGothic", size=12)
    # 日付のY座標はタイトルから少し下に調整
    date_y = pdf.get_y() + 5
    pdf.set_xy(page_width - right_margin_mm - 60, date_y) # 右寄せで日付のセル開始位置を調整
    pdf.cell(60, 5, convert_to_wareki(data['report_date']), align='R', ln=1)

    # 「学年」「部」の枠線とテキスト (下線のみに戻す)
    # 添付ファイルの位置に合わせて調整
    # Y座標は日付の少し下から開始
    box_y_start = date_y + 10 
    line_x_start = left_margin_mm + 10 # 添付ファイルに合わせた開始X座標
    line_x_end = left_margin_mm + 70 # 添付ファイルに合わせた終了X座標
    line_height = 8

    pdf.set_font("IPAexGothic", size=12)
    
    # 学年
    pdf.set_xy(line_x_start, box_y_start)
    pdf.cell(w=line_x_end - line_x_start, h=line_height, txt="学年", border='B', align='L') # 下線のみ

    # 部
    pdf.set_xy(line_x_start, box_y_start + line_height + 2) # 学年から少し下に
    pdf.cell(w=line_x_end - line_x_start, h=line_height, txt="部", border='B', align='L') # 下線のみ

    # 担当部署のテキスト
    # 部のライン上に担当部署名が来るように調整
    pdf.set_xy(line_x_start + 10, box_y_start + line_height + 2) # 「部」のテキストの少し右
    pdf.cell(w=line_x_end - line_x_start - 10, h=line_height, txt=data['department'], align='L')


    # --- 事業内容報告 (メインコンテンツ) ---
    # メインコンテンツの開始Y座標はヘッダー部分の終了位置から調整
    y_current = box_y_start + line_height * 2 + 15 # ヘッダーの学年・部から少し空ける

    # 1行目: 「日程」と「事業内容報告」ヘッダー
    pdf.set_xy(content_area_x, y_current)
    pdf.cell(w=content_area_width * 0.2, h=10, txt="日程", border=1, align='C') 
    pdf.cell(w=content_area_width * 0.8, h=10, txt="事業内容報告", border=1, ln=1, align='C')
    y_current = pdf.get_y() # ヘッダーの次のY座標

    # 2行目以降: 入力データ
    for i, item in enumerate(data['business_reports']):
        # multi_cellでテキストが占める実際の高さを計算する
        # 現在のX, Y座標と幅を保存
        start_x_content = content_area_x + content_area_width * 0.2 + 1 # 事業内容報告のテキスト開始X
        start_y_content = y_current + 2 # コメント開始行を調整 (少し高く)
        text_w_content = content_area_width * 0.8 - 2 # 左右パディング考慮
        
        # ダミーでmulti_cellを実行し、テキストが占める高さを取得
        # (ただし、実際に描画はしない)
        pdf.set_xy(start_x_content, start_y_content)
        temp_y_before = pdf.get_y()
        pdf.multi_cell(w=text_w_content, h=5, txt=item['content'], align='L')
        height_of_content_text = pdf.get_y() - temp_y_before
        
        # 枠の最終的な高さを決定 (テキストの高さ + 上下パディング)
        # 最小高は10mmとし、テキストの高さに合わせて調整
        calculated_height = max(10, height_of_content_text + (start_y_content - y_current) * 2 ) # 上下パディング考慮
        
        # PDFのY座標を元の位置に戻す
        pdf.set_y(y_current) 

        # 枠を描画
        pdf.rect(content_area_x, y_current, content_area_width * 0.2, calculated_height) # 日程の枠
        pdf.rect(content_area_x + content_area_width * 0.2, y_current, content_area_width * 0.8, calculated_height) # 事業内容報告の枠
        
        # テキスト位置調整
        # 日程 (垂直方向中央揃え)
        pdf.set_xy(content_area_x, y_current + (calculated_height - pdf.font_size / pdf.k) / 2)
        pdf.cell(w=content_area_width * 0.2, h=pdf.font_size / pdf.k, txt=item['date'], align='C')

        # 事業内容報告 (上揃え)
        pdf.set_xy(start_x_content, start_y_content) # 調整した開始Y座標を使用
        pdf.multi_cell(w=text_w_content, h=5, txt=item['content'], align='L')
        
        # 次の行の開始Y座標を更新
        y_current += calculated_height # 枠の高さ分だけY座標を進める


    # --- 活動の反省と課題 ---
    y_current += 10 # 前のセクションからのマージン

    # 3行目: 「活動の反省と課題」ヘッダー
    pdf.set_xy(content_area_x, y_current)
    header_text_line1 = "活動の反省と課題"
    header_text_line2 = "(次年度以降の改善材料になりますので詳細にお願いします)"
    
    # multi_cellで2行のテキストが占める高さを正確に計算
    temp_y_before_header = pdf.get_y()
    pdf.set_xy(content_area_x + 1, temp_y_before_header + 1) # 仮の開始位置
    pdf.multi_cell(w=content_area_width - 2, h=pdf.font_size * 1.2 / pdf.k, txt=header_text_line1, align='C')
    pdf.set_x(content_area_x + 1) # X座標をリセット
    pdf.multi_cell(w=content_area_width - 2, h=pdf.font_size * 1.2 / pdf.k, txt=header_text_line2, align='C')
    height_of_header_text = pdf.get_y() - temp_y_before_header
    
    header_height = max(15, height_of_header_text + 2) # 上下パディングを考慮
    
    # PDFのY座標を元の位置に戻す
    pdf.set_y(y_current)

    # 枠を描画
    pdf.rect(content_area_x, y_current, content_area_width, header_height)

    # テキストを配置
    text_y_start_header = y_current + (header_height - height_of_header_text) / 2
    #pdf.set_xy(content_area_x + 1, text_y_start_header) # 調整した開始Y座標を使用
    #pdf.multi_cell(w=content_area_width - 2, h=pdf.font_size * 1.2 / pdf.k, txt=header_text_line1, align='C')
    pdf.set_x(content_area_x + 1) # X座標をリセット
    pdf.set_xy(content_area_x + 1, text_y_start_header) # 調整した開始Y座標を使用
    pdf.multi_cell(w=content_area_width - 2, h=pdf.font_size * 1.2 / pdf.k, txt=header_text_line2, align='C')

    y_current += header_height

    # 4行目: 入力データ
    start_x_issues = content_area_x + 1
    start_y_issues = y_current + 4.5 # コメント開始行を調整 (少し下げる)
    text_w_issues = content_area_width - 2 # 左右パディング考慮

    # ダミーでmulti_cellを実行し、テキストが占める高さを取得
    pdf.set_xy(start_x_issues, start_y_issues)
    temp_y_before_issues = pdf.get_y()
    pdf.multi_cell(w=text_w_issues, h=5, txt=data['issues'], align='L')
    height_of_issues_text = pdf.get_y() - temp_y_before_issues
    
    # 枠の最終的な高さを決定 (テキストの高さ + 上下パディング)
    # 5行分の高さの目安: 5 * (pdf.font_size * 1.2 / pdf.k) + 上下パディング
    min_issue_height_5_lines = 5 * (pdf.font_size * 1.2 / pdf.k) + 9 

    issue_box_height = max(min_issue_height_5_lines, height_of_issues_text + (start_y_issues - y_current) * 2) # 上下パディング考慮

    # PDFのY座標を元の位置に戻す
    pdf.set_y(y_current) 
    pdf.rect(content_area_x, y_current, content_area_width, issue_box_height) # 枠を描画

    # テキストを枠内に配置
    pdf.set_xy(start_x_issues, start_y_issues) # 調整した開始Y座標を使用
    pdf.multi_cell(w=text_w_issues, h=5, txt=data['issues'], align='L')
    
    y_current += issue_box_height # 次のセクションの開始Y座標


    # --- 次回運営委員会までの活動予定 ---
    y_current += 10 # 前のセクションからのマージン

    # 5行目: 「日程」と「次回運営委員会までの活動予定」ヘッダー
    pdf.set_xy(content_area_x, y_current)
    pdf.cell(w=content_area_width * 0.2, h=10, txt="日程", border=1, align='C')
    pdf.cell(w=content_area_width * 0.8, h=10, txt="次回運営委員会までの活動予定", border=1, ln=1, align='C')
    y_current = pdf.get_y() # ヘッダーの次のY座標

    # 6行目以降: 入力データ
    for i, item in enumerate(data['next_activities']):
        # multi_cellでテキストが占める実際の高さを計算する
        start_x_content = content_area_x + content_area_width * 0.2 + 1
        start_y_content = y_current + 2 # コメント開始行を調整 (少し高く)
        text_w_content = content_area_width * 0.8 - 2
        
        pdf.set_xy(start_x_content, start_y_content)
        temp_y_before = pdf.get_y()
        pdf.multi_cell(w=text_w_content, h=5, txt=item['content'], align='L')
        height_of_content_text = pdf.get_y() - temp_y_before
        
        calculated_height = max(10, height_of_content_text + (start_y_content - y_current) * 2 )
        
        pdf.set_y(y_current) 

        # 枠を描画
        pdf.rect(content_area_x, y_current, content_area_width * 0.2, calculated_height)
        pdf.rect(content_area_x + content_area_width * 0.2, y_current, content_area_width * 0.8, calculated_height)

        # テキスト位置調整
        # 日程 (垂直方向中央揃え)
        pdf.set_xy(content_area_x, y_current + (calculated_height - pdf.font_size / pdf.k) / 2)
        pdf.cell(w=content_area_width * 0.2, h=pdf.font_size / pdf.k, txt=item['date'], align='C')

        # 活動予定 (上揃え)
        pdf.set_xy(start_x_content, start_y_content) # 調整した開始Y座標を使用
        pdf.multi_cell(w=text_w_content, h=5, txt=item['content'], align='L')

        y_current += calculated_height # 枠の高さ分だけY座標を進める
    
    # PDFをバイトストリームとして出力
    return io.BytesIO(pdf.output())


# --- Streamlit UI の構築 (変更なし) ---
st.set_page_config(layout="wide")
st.title("事業報告書作成アプリ")

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

import streamlit as st
import pandas as pd
import io

# --- ページ設定 ---
st.set_page_config(
    page_title="データ結合・分割ツール for Time Series",
    page_icon="🔗",
    layout="wide"
)

# --- 関数 ---
def convert_df_to_csv(df):
    """DataFrameをCSV形式のバイトデータに変換する (文字化け対策済み)"""
    return df.to_csv(index=False).encode('utf-8-sig')

# --- メイン画面 ---
st.title("🔗 CSVデータ 結合/分割ツール (時系列分析対応版)")
st.write("2つのCSVファイルを安全に結合し、日付特徴量の生成などを行った後、再び元のファイルに分割できます。")

# --- session_stateの初期化 ---
if 'combined_df' not in st.session_state:
    st.session_state.combined_df = None

# --- タブで機能を分割 ---
tab1, tab2 = st.tabs(["Step 1: データを結合・加工する", "Step 2: データを分割する"])

# =====================================================================================
# Step 1: 結合機能
# =====================================================================================
with tab1:
    st.header("Step 1: 結合と特徴量生成")
    
    with st.expander("1. ファイルをアップロードして結合", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            file1 = st.file_uploader("ファイル1 (例: train.csv) をアップロード", type=["csv"])
        with col2:
            file2 = st.file_uploader("ファイル2 (例: test.csv) をアップロード", type=["csv"])

        if file1 and file2:
            df1 = pd.read_csv(file1)
            df2 = pd.read_csv(file2)
            
            target_column = st.selectbox(
                '目的変数（ファイル1にしか存在しない列）があれば選択してください。',
                options=[None] + list(df1.columns)
            )
            
            # 列名のチェック機能
            df1_cols = set(df1.columns) - {target_column} if target_column else set(df1.columns)
            df2_cols = set(df2.columns)
            if df1_cols != df2_cols:
                st.warning("警告: 2つのファイルの列名（目的変数を除く）が完全には一致していません。")
                st.write(f"**ファイル1のみの列:** `{list(df1_cols - df2_cols)}`")
                st.write(f"**ファイル2のみの列:** `{list(df2_cols - df1_cols)}`")

            # 処理実行ボタン
            if st.button("Step 1.1: データを結合する", use_container_width=True):
                # 「名札」となる列を追加
                df1['source_dataset'] = file1.name
                df2['source_dataset'] = file2.name
                
                # データを結合し、session_stateに保存
                combined_df = pd.concat([df1, df2], ignore_index=True, sort=False)
                st.session_state.combined_df = combined_df
                
                st.success("データの結合が完了しました。")
                if target_column:
                    st.info(f"💡 ファイル2由来の行では、目的変数 '{target_column}' が空欄 (NaN) になっています。")
    
    # --- 結合データが存在する場合のみ、後続処理のUIを表示 ---
    if st.session_state.combined_df is not None:
        st.markdown("---")
        st.subheader("結合後のデータプレビュー")
        st.dataframe(st.session_state.combined_df.head())
        st.write(f"合計行数: {len(st.session_state.combined_df)}")

        ### --- 改善点: 自動特徴量エンジニアリング機能 --- ###
        st.markdown("---")
        with st.expander("2. (オプション) 日付列から特徴量を自動生成"):
            
            datetime_column = st.selectbox(
                "日付・時刻情報が含まれる列を選択してください。",
                options=[None] + list(st.session_state.combined_df.columns)
            )
            
            if datetime_column:
                st.write("作成したい特徴量を選択してください：")
                
                # 作成する特徴量の選択肢
                features_to_create = {
                    "year": "年", "month": "月", "day": "日",
                    "hour": "時", "minute": "分", "second": "秒",
                    "dayofweek": "曜日 (0=月, 6=日)", "dayofyear": "年初からの日数",
                    "weekofyear": "年内の週番号", "quarter": "四半期"
                }
                
                selected_features = []
                cols = st.columns(4)
                for i, (feature, label) in enumerate(features_to_create.items()):
                    if cols[i % 4].checkbox(label, value=True): # デフォルトでON
                        selected_features.append(feature)

                if st.button("Step 1.2: 日付特徴量を生成する", use_container_width=True):
                    df = st.session_state.combined_df.copy()
                    
                    # 確実にdatetime型に変換
                    df[datetime_column] = pd.to_datetime(df[datetime_column])
                    
                    # 選択された特徴量をループで作成
                    for feature in selected_features:
                        new_col_name = f"{datetime_column}_{feature}"
                        df[new_col_name] = getattr(df[datetime_column].dt, feature)
                        
                    # isocalendar().weekは特別扱い
                    if 'weekofyear' in selected_features:
                         df[f"{datetime_column}_weekofyear"] = df[datetime_column].dt.isocalendar().week

                    st.session_state.combined_df = df
                    st.success("日付特徴量の生成が完了しました。")
                    st.dataframe(st.session_state.combined_df.head())

        st.markdown("---")
        st.download_button(
           label="加工済みCSVをダウンロード",
           data=convert_df_to_csv(st.session_state.combined_df),
           file_name='processed_combined_data.csv',
           mime='text/csv',
           use_container_width=True
        )

# =====================================================================================
# Step 2: 分割機能
# =====================================================================================
with tab2:
    st.header("Step 2: 分割")
    st.info("Step 1で加工・ダウンロードした、結合済みファイルをアップロードしてください。")
    
    processed_file = st.file_uploader("加工済みの結合データ をアップロード", type=["csv"])
    
    if processed_file is not None:
        processed_df = pd.read_csv(processed_file)
        
        if 'source_dataset' not in processed_df.columns:
            st.error("エラー: このファイルには分割用の情報（'source_dataset'列）が含まれていません。")
        else:
            original_filenames = processed_df['source_dataset'].unique()
            
            st.success("データの分割準備ができました。")
            
            ### --- 改善点: DRY原則に沿ってコードをループ処理に --- ###
            cols = st.columns(len(original_filenames))
            for i, filename in enumerate(original_filenames):
                with cols[i]:
                    df_processed = processed_df[processed_df['source_dataset'] == filename].copy()
                    df_processed.drop(columns=['source_dataset'], inplace=True)
                    
                    st.subheader(f"加工後のデータ: {filename}")
                    st.dataframe(df_processed.head())
                    st.download_button(
                       label=f"加工後の {filename} をダウンロード",
                       data=convert_df_to_csv(df_processed),
                       file_name=f"processed_{filename}",
                       mime='text/csv',
                       key=f"download_button_{i}" # ボタンごとにユニークなキーを設定
                    )

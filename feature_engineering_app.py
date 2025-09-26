import streamlit as st
import pandas as pd
import io

# --- ページ設定 ---
st.set_page_config(
    page_title="データ結合・分割ツール",
    page_icon="🔗",
    layout="wide"
)

# --- 関数 ---
def convert_df_to_csv(df):
    """DataFrameをCSV形式のバイトデータに変換する (文字化け対策済み)"""
    return df.to_csv(index=False).encode('utf-8-sig')

# --- メイン画面 ---
st.title("🔗 CSVデータ 結合/分割ツール")
st.write("2つのCSVファイルを安全に結合し、一括で前処理を行った後、再び元のファイルに分割できます。")

# --- タブで機能を分割 ---
tab1, tab2 = st.tabs(["Step 1: データを結合する", "Step 2: データを分割する"])

# --- Step 1: 結合機能 ---
with tab1:
    st.header("Step 1: 結合")
    st.info("2つのCSVファイルをアップロードして、1つのファイルにまとめます。")
    
    col1, col2 = st.columns(2)
    with col1:
        # ---【改善点1】UIの文言を汎用的に変更 ---
        file1 = st.file_uploader("ファイル1 (例: train.csv) をアップロード", type=["csv"])
    with col2:
        file2 = st.file_uploader("ファイル2 (例: test.csv) をアップロード", type=["csv"])

    if file1 is not None and file2 is not None:
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)
        
        # ---【改善点2】任意で目的変数を指定させる機能を追加 ---
        st.markdown("---")
        target_column = st.selectbox(
            '目的変数（片方のファイルにしか存在しない列）があれば選択してください。',
            # df1のカラムリストの先頭にNoneを追加
            options=[None] + list(df1.columns) 
        )
        
        # ---【改善点3】列名のチェック機能を追加し、安全性を向上 ---
        # 目的変数を除いた列セットを作成
        if target_column:
            df1_cols = set(df1.columns) - {target_column}
            df2_cols = set(df2.columns)
        else:
            df1_cols = set(df1.columns)
            df2_cols = set(df2.columns)
        
        # 列名が一致しない場合に警告を表示
        if df1_cols != df2_cols:
            st.warning("警告: 2つのファイルの列名が完全には一致していません。")
            # 差分を具体的に表示すると、さらに親切
            only_in_1 = df1_cols - df2_cols
            only_in_2 = df2_cols - df1_cols
            if only_in_1:
                st.write(f"**ファイル1のみに存在する列:** `{list(only_in_1)}`")
            if only_in_2:
                st.write(f"**ファイル2のみに存在する列:** `{list(only_in_2)}`")
            st.markdown("---")

        # 「名札」となる列を追加 (ファイル名を名札にすると、より分かりやすい)
        df1['source_dataset'] = file1.name
        df2['source_dataset'] = file2.name
        
        # データを結合 (sort=False をつけて列の順序を維持)
        combined_df = pd.concat([df1, df2], ignore_index=True, sort=False)
        
        st.success("データの結合が完了しました。")
        
        # ---【改善点4】目的変数がNaNになることについて説明を追加 ---
        if target_column:
            st.info(f"💡 ファイル2に由来する行では、目的変数 '{target_column}' の値が空欄 (NaN) になっています。これは意図した動作です。特徴量作成後、Step2で分割すれば元に戻ります。")
            
        st.dataframe(combined_df.head())
        st.write(f"合計行数: {len(combined_df)}")
        
        st.download_button(
           label="結合したCSVをダウンロード",
           data=convert_df_to_csv(combined_df),
           file_name='combined_data.csv',
           mime='text/csv',
        )

# --- Step 2: 分割機能 ---
with tab2:
    st.header("Step 2: 分割")
    st.info("特徴量作成などの処理を行った、結合済みファイルをアップロードしてください。")
    
    processed_file = st.file_uploader("加工済みの結合データ をアップロード", type=["csv"])
    
    if processed_file is not None:
        processed_df = pd.read_csv(processed_file)
        
        if 'source_dataset' not in processed_df.columns:
            st.error("エラー: このファイルには分割用の情報（'source_dataset'列）が含まれていません。Step 1で結合したファイルを使用してください。")
        else:
            # 分割の元になるファイル名（名札）を取得
            original_filenames = processed_df['source_dataset'].unique()
            if len(original_filenames) != 2:
                st.warning(f"注意: 結合元ファイルの数が2つではないようです。(検出されたファイル名: {original_filenames})")

            st.success("データの分割が完了しました。")
            
            # 分割後のデータプレビューとダウンロードボタン
            col1, col2 = st.columns(2)
            
            # 1つ目のファイルを復元
            with col1:
                filename1 = original_filenames[0]
                df1_processed = processed_df[processed_df['source_dataset'] == filename1].copy()
                df1_processed.drop(columns=['source_dataset'], inplace=True)
                
                st.subheader(f"加工後のデータ: {filename1}")
                st.dataframe(df1_processed.head())
                st.download_button(
                   label=f"加工後の {filename1} をダウンロード",
                   data=convert_df_to_csv(df1_processed),
                   file_name=f"processed_{filename1}",
                   mime='text/csv',
                )
            
            # 2つ目のファイルを復元
            if len(original_filenames) > 1:
                with col2:
                    filename2 = original_filenames[1]
                    df2_processed = processed_df[processed_df['source_dataset'] == filename2].copy()
                    df2_processed.drop(columns=['source_dataset'], inplace=True)
                    
                    st.subheader(f"加工後のデータ: {filename2}")
                    st.dataframe(df2_processed.head())
                    st.download_button(
                       label=f"加工後の {filename2} をダウンロード",
                       data=convert_df_to_csv(df2_processed),
                       file_name=f"processed_{filename2}",
                       mime='text/csv',
                    )


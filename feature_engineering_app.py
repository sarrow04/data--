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
st.title("🔗 学習・テストデータ 結合/分割ツール")
st.write("特徴量作成の前処理として、学習データとテストデータを安全に結合・分割します。")

# --- タブで機能を分割 ---
tab1, tab2 = st.tabs(["Step 1: データを結合する", "Step 2: データを分割する"])

# --- Step 1: 結合機能 ---
with tab1:
    st.header("Step 1: 結合")
    st.info("学習データとテストデータをアップロードして、1つのファイルにまとめます。")
    
    col1, col2 = st.columns(2)
    with col1:
        train_file = st.file_uploader("学習データ (train.csv) をアップロード", type=["csv"])
    with col2:
        test_file = st.file_uploader("テストデータ (test.csv) をアップロード", type=["csv"])

    if train_file is not None and test_file is not None:
        train_df = pd.read_csv(train_file)
        test_df = pd.read_csv(test_file)
        
        # 「名札」となる列を追加
        train_df['source_dataset'] = 'train'
        test_df['source_dataset'] = 'test'
        
        # データを結合
        combined_df = pd.concat([train_df, test_df], ignore_index=True)
        
        st.success("データの結合が完了しました。")
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
    st.info("特徴量作成アプリで処理した後の、結合済みファイルをアップロードしてください。")
    
    processed_file = st.file_uploader("加工済みの結合データ をアップロード", type=["csv"])
    
    if processed_file is not None:
        processed_df = pd.read_csv(processed_file)
        
        # 「名札」列があるかチェック
        if 'source_dataset' not in processed_df.columns:
            st.error("エラー: このファイルには分割用の情報（'source_dataset'列）が含まれていません。Step 1で結合したファイルを使用してください。")
        else:
            # 「名札」を元にデータを分割
            train_processed = processed_df[processed_df['source_dataset'] == 'train'].copy()
            test_processed = processed_df[processed_df['source_dataset'] == 'test'].copy()
            
            # 不要になった「名札」列を削除
            train_processed.drop(columns=['source_dataset'], inplace=True)
            test_processed.drop(columns=['source_dataset'], inplace=True)
            
            st.success("データの分割が完了しました。")
            
            # 分割後のデータプレビューとダウンロードボタン
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("加工後の学習データ")
                st.dataframe(train_processed.head())
                st.download_button(
                   label="加工後の train.csv をダウンロード",
                   data=convert_df_to_csv(train_processed),
                   file_name='train_processed.csv',
                   mime='text/csv',
                )
            with col2:
                st.subheader("加工後のテストデータ")
                st.dataframe(test_processed.head())
                st.download_button(
                   label="加工後の test.csv をダウンロード",
                   data=convert_df_to_csv(test_processed),
                   file_name='test_processed.csv',
                   mime='text/csv',
                )

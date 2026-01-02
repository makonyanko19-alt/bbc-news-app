import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from googletrans import Translator
import time

# --- 画面のデザイン ---
st.title("🌍 Global News Collector")
st.write("BBC Business Newsを取得し、日本語に翻訳して表示します。")

# ボタンが押されたら実行する
if st.button("ニュースを取得する"):
    
    # 進行状況バーを表示
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    url = "https://www.bbc.com/news/business"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    translator = Translator()
    
    status_text.text("BBCにアクセス中...")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    headlines = soup.find_all("h2")
    
    news_list = []
    total_headlines = len(headlines)

    # ループ処理
    for i, headline in enumerate(headlines):
        # 進捗バーを更新
        progress = (i + 1) / total_headlines
        progress_bar.progress(progress)
        status_text.text(f"収集中... ({i+1}/{total_headlines})")

        h2_text = headline.text.strip()
        if not h2_text:
            continue

        link_tag = headline.find("a")
        if not link_tag:
            link_tag = headline.find_parent("a")

        full_url = ""
        link_text = ""
        if link_tag:
            link_url = link_tag.get("href")
            if not link_url.startswith("http"):
                full_url = "https://www.bbc.com" + link_url
            else:
                full_url = link_url
            link_text = link_tag.text.strip()

        final_title = h2_text
        if h2_text in ["Business Daily", "Latest audio", "Must watch"]:
            if link_text and link_text != h2_text:
                final_title = f"[Audio] {link_text}"
            else:
                sibling_p = headline.find_next_sibling("p")
                if sibling_p:
                     final_title = f"[Audio] {sibling_p.text.strip()}"

        # 翻訳
        try:
            translated = translator.translate(final_title, src='en', dest='ja')
            ja_title = translated.text
        except:
            ja_title = "(翻訳失敗)"
        
        news_data = {
            "タイトル (日本語)": ja_title,
            "Title (English)": final_title,
            "URL": full_url
        }
        news_list.append(news_data)
        time.sleep(1) # 翻訳サーバーへの配慮

    # 全部終わったら
    status_text.text("完了！")
    progress_bar.empty()

    # データフレーム作成
    df = pd.DataFrame(news_list)

    # 画面にドーン！と表を表示 (ここを修正しました！)
    st.success(f"{len(df)}件のニュースを取得しました！")
    
    st.dataframe(
        df,
        column_config={
            "URL": st.column_config.LinkColumn(
                "記事リンク",           # 列の名前
                display_text="Link"    # URLの代わりに表示する文字（これがないと長いURLが表示されます）
            )
        },
        hide_index=True # 左端の 0, 1, 2... という数字を隠してスッキリさせる
    )

    # ダウンロードボタンを設置 (CSV保存機能)
    csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label="CSVをダウンロード",
        data=csv,
        file_name='bbc_news_web.csv',
        mime='text/csv',
    )
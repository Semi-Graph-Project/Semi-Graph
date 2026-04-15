#!/usr/bin/env python3
import yfinance as yf
from GoogleNews import GoogleNews
import pandas as pd
import time

print("Start testing news fetch...")



def get_stock_news(symbol, keyword_suffix="stock", lang='en', region='US', days=7, max_pages=1):
    googlenews = GoogleNews(lang=lang, region=region)
    googlenews.set_period(f'{days}d') 

    search_query = f"{symbol} {keyword_suffix}"
    print(f"🔍 กำลังค้นหาข่าว: '{search_query}' ย้อนหลัง {days} วัน...")

    googlenews.clear()

    all_news = []
    googlenews.search(search_query) # Search ครั้งแรก

    for page in range(1, max_pages + 1):
        print(f"   - กำลังดึงหน้า {page}...")
        result = googlenews.result(sort=True) # sort=True ให้เรียงตามเวลา
        all_news.extend(result)
        
        googlenews.get_page(page)
        time.sleep(1) 

    if not all_news:
        print("❌ ไม่พบข่าว")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_news)

    cols = ['title', 'date', 'media', 'link']

    final_cols = [c for c in cols if c in df.columns]
    df = df[final_cols]

    df.drop_duplicates(subset=['link'], inplace=True)
    print(f"✅ ดึงสำเร็จ! ได้ข่าวทั้งหมด {len(df)} ข่าว")
    return df


df_us = get_stock_news('GOOGL', keyword_suffix='stock', lang='en', region='US', days=1, max_pages=1)
if not df_us.empty:
    print(df_us.head())
    df_us.to_csv('googl_news.csv') # เซฟลงไฟล์

print("-" * 30)
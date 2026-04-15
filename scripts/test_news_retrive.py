from newspaper import Article
import pandas as pd

df = pd.read_csv('googl_news.csv')
print(df.head())
print(f"มีข่าวทั้งหมด {len(df)} ข่าว กำลังเริ่มดึงเนื้อหา...\n")

full_contents = [] # ลิสต์ไว้เก็บเนื้อหา
# print(f"มีข่าวทั้งหมด {len(df)} ข่าว กำลังเริ่มดึงเนื้อหา...\n")  

for index, row in df.iterrows():
    url = row['link']
    title = row['title']
    
    print(f"[{index+1}/{len(df)}] กำลังแกะ: {title[:30]}...")
    try:
        article = Article(url)
        
        article.download()
        article.parse()
        
        content = article.text
        full_contents.append(content)
        
    except Exception as e:
        print(f"   ❌ อ่านไม่ได้: {e}")
        full_contents.append("Error: Could not fetch content")

df['full_content'] = full_contents

print("\n✅ ดึงเนื้อหาครบแล้ว!")

print("-" * 50)
print("ตัวอย่างเนื้อหาข่าวแรก:")
print(df.iloc[0]['full_content'][:500])

df.to_csv('stock_news_with_content.csv', index=False, encoding='utf-8-sig')
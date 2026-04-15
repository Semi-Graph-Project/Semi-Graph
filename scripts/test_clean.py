import re
from pathlib import Path
from typing import Generator, Optional, Dict, List, Tuple
from bs4 import BeautifulSoup
import html2text

def extract_documents_streaming(filepath: str) -> Generator[tuple[str, str], None, None]:
    VALID_TYPES = {'10-K', '10-Q', '8-K'}
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        in_document = False
        in_text = False
        current_type = None
        text_buffer = []
        for line in f:
            if '<DOCUMENT>' in line:
                in_document = True
                current_type = None
                text_buffer = []
                continue

            if '</DOCUMENT>' in line:
                if in_document and current_type in VALID_TYPES and text_buffer:
                    yield (current_type, ''.join(text_buffer))
                in_document = False
                in_text = False
                text_buffer = []
                continue

            if in_document:
                type_match = re.search(r'<TYPE>(.+)', line)
                if type_match:
                    current_type = type_match.group(1).strip()
                    if current_type in {'GRAPHIC', 'ZIP', 'EXCEL', 'XML', 'JSON'}:
                        in_document = False 
                    continue

                if '<TEXT>' in line:
                    in_text = True
                    continue
                
                if '</TEXT>' in line:
                    in_text = False
                    continue
                
                if in_text and current_type in VALID_TYPES:
                    text_buffer.append(line)


def is_table_of_contents_line(line: str) -> bool:
    """
    ตรวจสอบว่าบรรทัดเป็นส่วนหนึ่งของสารบัญ (Table of Contents) หรือไม่
    โดยดูจากการมีตัวเลขหน้า (Page Number) ต่อท้าย
    
    Args:
        line: บรรทัดที่ต้องการตรวจสอบ
        
    Returns:
        bool: True ถ้าเป็น TOC, False ถ้าไม่ใช่
    """
    # ตรวจสอบรูปแบบ: "Item 1. Business ........... 5" หรือ "Item 1 Business 5"
    # Page number มักอยู่ท้ายบรรทัดและเป็นตัวเลข 1-3 หลัก
    toc_patterns = [
        r'\.{3,}\s*\d{1,3}\s*$',  # dots followed by page number
        r'\s{5,}\d{1,3}\s*$',      # multiple spaces followed by page number
        r'\d{1,3}\s*$'             # just page number at end (less reliable)
    ]
    
    for pattern in toc_patterns[:2]:  # ใช้แค่ 2 pattern แรกที่แม่นยำกว่า
        if re.search(pattern, line):
            return True
    return False

def clean_markdown_artifacts(text: str) -> str:
    """ลบอักขระ Markdown เพื่อให้ Regex จับ Pattern ได้ง่ายขึ้น"""
    # ลบตัวหนา/ตัวเอียง เช่น **Item 1** -> Item 1
    text = re.sub(r'[\*_#]', ' ', text)
    # แปลงหลาย Space เป็น 1 Space
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_TOC_line_markdown(line: str) -> bool:
    """ตรวจสอบว่าเป็นบรรทัดในสารบัญแบบ Markdown Table หรือไม่"""
    # ถ้าบรรทัดมี | และมีตัวเลขอยู่ท้ายๆ หรือมีจุดไข่ปลา
    if '|' in line:
        # ลบ pipe และ space ออก เช็คว่าจบด้วยตัวเลขไหม (เลขหน้า)
        clean_line = line.replace('|', '').strip()
        if re.search(r'\d{1,3}$', clean_line):
            return True
    
    # Pattern เดิม (จุดไข่ปลา)
    if re.search(r'\.{3,}\s*\d{1,3}', line):
        return True
        
    return False

def extract_sections_10k(markdown_text: str) -> Dict[str, str]:
    """Extract important sections from 10-K document.

    รายการส่วนที่สกัด:
    - Item 1: Business
    - Item 1A: Risk Factors
    - Item 7: MD&A (Management's Discussion and Analysis)
    - Item 8: Financial Statements
    - Item 10: Directors, Executive Officers
    - Item 11: Executive Compensation
    - Item 5: Market for Registrant's Common Equity
    - Exhibit 21: Subsidiaries
    
    Args:
        markdown_text: เนื้อหา Markdown ของเอกสาร 10-K
        
    Returns:
        Dict[str, str]: Dictionary ที่มี key เป็นชื่อ section และ value เป็นเนื้อหา
    """
    sections = {}
    lines = markdown_text.split('\n')
    
    section_patterns = {
        'Item 1':   r'(?i)(?m)^[\*_#\s]*item\s*1[\.\:\-]?\s*business',
        'Item 1A':  r'(?i)(?m)^[\*_#\s]*item\s*1a[\.\:\-]?\s*risk',
        'Item 5':   r'(?i)(?m)^[\*_#\s]*item\s*5[\.\:\-]?\s*market',
        'Item 7':   r'(?i)(?m)^[\*_#\s]*item\s*7[\.\:\-]?\s*(?:management|md&a)',
        'Item 8':   r'(?i)(?m)^[\*_#\s]*item\s*8[\.\:\-]?\s*financial',
        'Item 10':  r'(?i)(?m)^[\*_#\s]*item\s*10[\.\:\-]?\s*directors',
        'Item 11':  r'(?i)(?m)^[\*_#\s]*item\s*11[\.\:\-]?\s*executive',
        'Item 15':  r'(?i)(?m)^[\*_#\s]*item\s*15[\.\:\-]?\s*exhibits', 
        'Signatures': r'(?i)(?m)^[\*_#\s]*signatures'
    }
    
    section_starts = {}
    
    for i, line in enumerate(lines):
        if is_TOC_line_markdown(line):
            continue

        clean_line = clean_markdown_artifacts(line)
            
        # ตรวจสอบแต่ละ pattern
        for section_name, pattern in section_patterns.items():
            simple_pattern = pattern.replace('(?m)^', '^').replace(r'[\*_#\s]*', '')
            if re.search(simple_pattern, clean_line,re.IGNORECASE):
                # ถ้ายังไม่เคยเจอ section นี้ ให้บันทึกตำแหน่ง
                if section_name not in section_starts:
                    section_starts[section_name] = i
                    print(f"🔍 พบ {section_name} ที่บรรทัด {i}: {clean_line.strip()[:100]}")
                    break  # หยุดตรวจสอบ pattern อื่นสำหรับบรรทัดนี้
    
    # สกัดเนื้อหาของแต่ละ section
    sorted_sections = sorted(section_starts.items(), key=lambda x: x[1])
    
    for idx, (section_name, start_line) in enumerate(sorted_sections):
        # หาจุดสิ้นสุดของ section (คือจุดเริ่มต้นของ section ถัดไป)
        if idx + 1 < len(sorted_sections):
            end_line = sorted_sections[idx + 1][1]
        else:
            end_line = len(lines)
        
        # สกัดเนื้อหา
        section_content = '\n'.join(lines[start_line:end_line])
        sections[section_name] = section_content.strip()
        
        print(f"✅ สกัด {section_name}: {len(section_content):,} ตัวอักษร")
    
    return sections






def extract_sections_fallback(markdown_text: str) -> Dict[str, str]:
    """
    วิธีสำรอง: ใช้ regex โดยตรงกับข้อความทั้งหมด (ช้ากว่าแต่ครอบคลุมมากกว่า)
    
    Args:
        markdown_text: เนื้อหา Markdown
        
    Returns:
        Dict[str, str]: Dictionary ของ sections
    """
    sections = {}
    
    # Pattern สำหรับแต่ละ section โดยจับจนถึง section ถัดไป
    patterns = {
        'item_1_business': r'(?si)(item\s*1[\.\:\-]?\s+business.*?)(?=item\s*1a[\.\:\-]?\s+risk|item\s*2[\.\:\-]?|\Z)',
        'item_1a_risk': r'(?si)(item\s*1a[\.\:\-]?\s+risk\s+factors?.*?)(?=item\s*1b|item\s*2[\.\:\-]?|\Z)',
        'item_5_market': r'(?si)(item\s*5[\.\:\-]?\s+market.*?)(?=item\s*6[\.\:\-]?|\Z)',
        'item_7_mda': r'(?si)(item\s*7[\.\:\-]?\s+.*?)(?=item\s*7a|item\s*8[\.\:\-]?|\Z)',
        'item_8_financials': r'(?si)(item\s*8[\.\:\-]?\s+financial.*?)(?=item\s*9[\.\:\-]?|\Z)',
        'item_10_directors': r'(?si)(item\s*10[\.\:\-]?\s+.*?)(?=item\s*11[\.\:\-]?|\Z)',
        'item_11_compensation': r'(?si)(item\s*11[\.\:\-]?\s+.*?)(?=item\s*12[\.\:\-]?|\Z)',
        'exhibit_21': r'(?si)(exhibit\s*21[\.\:\-]?\s+.*?)(?=exhibit\s*22|exhibit\s*23|\Z)',
    }
    
    for section_name, pattern in patterns.items():
        match = re.search(pattern, markdown_text)
        if match:
            sections[section_name] = match.group(1).strip()
            print(f"✅ สกัด {section_name} (fallback): {len(match.group(1)):,} ตัวอักษร")
    
    return sections


def save_sections(sections: Dict[str, str], output_dir: Path, base_filename: str) -> None:
    global year
    """
    บันทึกแต่ละ section เป็นไฟล์แยก
    
    Args:
        sections: Dictionary ของ sections
        output_dir: โฟลเดอร์ที่จะบันทึก
        base_filename: ชื่อไฟล์ฐาน
    """
    sections_dir = output_dir / f"sections{year}"
    sections_dir.mkdir(exist_ok=True)
    
    for section_name, content in sections.items():
        if content:  # บันทึกเฉพาะ section ที่มีเนื้อหา
            section_file = sections_dir / f"{base_filename}_{section_name}.md"
            with open(section_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"💾 บันทึก section: {section_file.name}")

        
def remove_uuencode(text: str) -> str:
    pattern = r'begin \d{3} .+?\n.+?\nend'
    cleaned_text = re.sub(pattern, '', text, flags=re.DOTALL)
    return cleaned_text

def html_to_markdown(html_content: str, method: str = 'html2text') -> str:
    if method == 'html2text':
        h = html2text.HTML2Text()
        
        h.body_width = 0  # ไม่จำกัดความกว้าง เพื่อไม่ให้ตารางแตก
        h.ignore_links = False  # เก็บ links ไว้
        h.ignore_images = True  # ข้ามรูปภาพ (มักเป็น logo)
        h.ignore_emphasis = False  # เก็บ bold/italic
        h.skip_internal_links = True  # ข้าม internal anchor links
        h.single_line_break = False  # ใช้ line break ปกติ
        h.mark_code = True  # ทำเครื่องหมาย code blocks
        h.wrap_links = False  # ไม่ wrap links
        h.unicode_snob = True  # ใช้ unicode characters แทน HTML entities
        h.escape_snob = True  # ลด escape characters ที่ไม่จำเป็น
        
        markdown = h.handle(html_content)
        
    elif method == 'markitdown':
        try:
            from markitdown import MarkItDown
            md = MarkItDown()
            # markitdown รองรับหลายไฟล์ แต่เราจะส่ง HTML string
            result = md.convert_string(html_content, file_extension='.html')
            markdown = result.text_content
        except ImportError:
            print("Not found MarkitDown")
            return html_to_markdown(html_content, method='html2text')
    
    elif method == 'beautifulsoup':
        soup = BeautifulSoup(html_content, 'lxml')
        
        for tag in soup(['script', 'style', 'meta', 'link']):
            tag.decompose()
        
        markdown = soup.get_text(separator='\n', strip=True)
        
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    
    else:
        raise ValueError(f"not found method : {method}")
    
    return markdown

def clean_markdown(markdown: str) -> str:
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)

    lines = [line.rstrip() for line in markdown.split('\n')]
    markdown = '\n'.join(lines)
    
    markdown = re.sub(r'(-{3,}\n){2,}', '---\n', markdown)
    
    markdown = re.sub(r'<!--.*?-->', '', markdown, flags=re.DOTALL)
    
    markdown = re.sub(r'\xa0', ' ', markdown)  # non-breaking space
    markdown = re.sub(r'\u200b', '', markdown)  # zero-width space
    
    return markdown.strip()

def clean_and_save_documents(
    input_file: str, 
    output_dir: str = "data/processed",
    convert_to_markdown: bool = True,
    markdown_method: str = 'html2text',
    extract_sections: bool = True,  
    use_fallback_extraction: bool = False  
) -> None:
    global year
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    input_filename = Path(input_file).stem
    doc_count = 0

    pattern_head = r"(?s)\A.*?(?=UNITED STATES)"
    
    print(f"Scaning .. : {input_file}")
    if convert_to_markdown:
        print(f"Meth : {markdown_method}")
    
    for doc_type, text_content in extract_documents_streaming(input_file):
        cleaned_text = remove_uuencode(text_content)
        
        if convert_to_markdown:
            markdown_text = html_to_markdown(cleaned_text, method=markdown_method)
            final_text = clean_markdown(markdown_text)
            
            extension = '.md'
        else:
            final_text = cleaned_text
            extension = '.txt'
        
        doc_count += 1
        output_file = output_path / f"{input_filename}_{doc_type}_{year}{extension}"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            cleaned_final_text = re.sub(pattern_head, '', final_text).strip()
            f.write(cleaned_final_text)
        
        print(f"Saved: {output_file.name} ({len(final_text):,} char)")

        if extract_sections and doc_type == '10-K' and convert_to_markdown:
            print(f"\n{'='*80}")
            print(f"Extract Sections From --> {doc_type}")
            print(f"{'='*80}\n")
            
            sections = extract_sections_10k(cleaned_final_text)
            
            if not sections and use_fallback_extraction:
                print("\n⚠️  ไม่พบ sections ด้วยวิธีหลัก กำลังใช้ fallback method...\n")
                sections = extract_sections_fallback(cleaned_final_text)
            
            if sections:
                save_sections(sections, output_path, f"{input_filename}_{doc_type}_{doc_count}")
                print(f"\n✅ สกัดและบันทึก sections สำเร็จ: {len(sections)} sections")
            else:
                print("\n⚠️  ไม่พบ sections ที่ต้องการ")
            
            print(f"\n{'='*80}\n")

    print(f"\nAll Docs {doc_count} E/A")


def get_text_preview(text: str, max_lines: int = 10) -> str:
    lines = text.split('\n')[:max_lines]
    return '\n'.join(lines)


def analyze_section_content(section_text: str, section_name: str) -> Dict[str, any]:
    """
    วิเคราะห์เนื้อหาในแต่ละ section เพื่อหาข้อมูลเฉพาะ
    
    Args:
        section_text: เนื้อหาของ section
        section_name: ชื่อ section
        
    Returns:
        Dict: ผลการวิเคราะห์
    """
    analysis = {
        'section_name': section_name,
        'length': len(section_text),
        'word_count': len(section_text.split()),
        'has_tables': bool(re.search(r'\|.*\|', section_text)),  # ตรวจสอบ markdown tables
    }
    
    # วิเคราะห์เฉพาะสำหรับ Item 1 (Business) - หา Supply Chain keywords
    if 'business' in section_name.lower():
        supply_chain_keywords = [
            'supplier', 'supply chain', 'raw material', 'vendor', 
            'procurement', 'sourcing', 'manufacturer', 'distribution'
        ]
        analysis['supply_chain_mentions'] = sum(
            len(re.findall(rf'\b{keyword}\b', section_text, re.IGNORECASE)) 
            for keyword in supply_chain_keywords
        )
    
    # วิเคราะห์เฉพาะสำหรับ Item 1A (Risk) - นับจำนวน risk factors
    if 'risk' in section_name.lower():
        risk_headers = re.findall(r'(?i)^#+\s+.*risk.*$', section_text, re.MULTILINE)
        analysis['risk_factor_count'] = len(risk_headers)
    
    return analysis


def print_section_summary(sections: Dict[str, str]) -> None:
    """
    แสดงสรุปข้อมูลของแต่ละ section
    
    Args:
        sections: Dictionary ของ sections
    """
    print("\n" + "="*80)
    print("📊 สรุปข้อมูล Sections")
    print("="*80 + "\n")
    
    for section_name, content in sections.items():
        analysis = analyze_section_content(content, section_name)
        print(f"📄 {section_name.upper().replace('_', ' ')}")
        print(f"   ความยาว: {analysis['length']:,} ตัวอักษร")
        print(f"   จำนวนคำ: {analysis['word_count']:,} คำ")
        print(f"   มีตาราง: {'✓' if analysis['has_tables'] else '✗'}")
        
        if 'supply_chain_mentions' in analysis:
            print(f"   Supply Chain mentions: {analysis['supply_chain_mentions']}")
        if 'risk_factor_count' in analysis:
            print(f"   Risk factors: {analysis['risk_factor_count']}")
        print()

year = "21-000010"
if __name__ == "__main__":
    
    input_file = f"data/raw/sec-edgar-filings/GOOGL/10-K/0001652044-{year}/full-submission.txt"

    clean_and_save_documents(
        input_file, 
        output_dir="data/processed",
        convert_to_markdown=True,
        markdown_method='html2text',
        extract_sections=True,
        use_fallback_extraction=True
    )
"""诊断Word自动编号结构"""
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn

docx_path = "data/raw/城轨交通企业管理复习题.docx"
doc = Document(docx_path)

print("=== Word 编号结构诊断 ===\n")

for i, para in enumerate(doc.paragraphs[:100]):
    if not para.text.strip():
        continue
    
    text = para.text[:60]
    pPr = para._element.pPr
    
    if pPr is not None:
        numPr = pPr.find(qn('w:numPr'))
        if numPr is not None:
            ilvl = numPr.find(qn('w:ilvl'))
            numId = numPr.find(qn('w:numId'))
            
            ilvl_val = ilvl.get(qn('w:val')) if ilvl is not None else "None"
            numId_val = numId.get(qn('w:val')) if numId is not None else "None"
            
            print(f"段落 {i:3d} | 级别={ilvl_val} | numId={numId_val} | 文本={text}")
        else:
            print(f"段落 {i:3d} | 无编号 | 文本={text}")
    else:
        print(f"段落 {i:3d} | 无格式 | 文本={text}")

import re

test_line = "A、北京      B、上海      C、天津      D、广州"
print(f"测试行: {repr(test_line)}")

# 方案：分割多空格后逐个匹配
parts = re.split(r'\s{2,}', test_line.strip())
print(f"分割后: {parts}")

options = []
for part in parts:
    match = re.match(r'^[A-Ha-h][\.|、]\s*(.+)', part)
    if match:
        options.append(match.group(1).strip())
        
print(f"提取选项: {options}")

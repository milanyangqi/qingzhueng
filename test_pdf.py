#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('backend')

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import io
    import platform
    
    print("开始测试PDF生成功能...")
    
    # 测试字体注册
    font_name = 'Helvetica'  # 默认字体
    try:
        if platform.system() == 'Darwin':  # macOS
            font_paths = [
                '/System/Library/Fonts/PingFang.ttc',
                '/System/Library/Fonts/Helvetica.ttc',
                '/System/Library/Fonts/STHeiti Light.ttc',
                '/System/Library/Fonts/STHeiti Medium.ttc',
                '/Library/Fonts/Arial Unicode MS.ttf'
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        font_name = 'ChineseFont'
                        print(f"成功注册字体: {font_path}")
                        break
                    except Exception as font_error:
                        print(f"注册字体失败 {font_path}: {font_error}")
                        continue
    except Exception as e:
        print(f"字体注册过程出错: {e}")
        font_name = 'Helvetica'
    
    print(f"使用字体: {font_name}")
    
    # 创建PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # 测试内容
    story = [
        Paragraph('测试PDF生成功能', styles['Title']),
        Paragraph('这是一个测试文档，用于验证PDF生成是否正常工作。', styles['Normal']),
        Paragraph('Test English content with Chinese 中文内容测试', styles['Normal'])
    ]
    
    # 构建PDF
    doc.build(story)
    
    # 获取PDF数据
    pdf_data = buffer.getvalue()
    buffer.close()
    
    print(f'PDF生成成功，大小: {len(pdf_data)} 字节')
    print(f'PDF头部: {pdf_data[:20]}')
    
    # 验证PDF格式
    if pdf_data.startswith(b'%PDF'):
        print('✓ PDF格式正确')
    else:
        print('✗ PDF格式错误')
    
    # 保存测试文件
    with open('test_output.pdf', 'wb') as f:
        f.write(pdf_data)
    print('测试PDF已保存为 test_output.pdf')
    
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装reportlab库")
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc()
#!/usr/bin/env python3
"""
Script para generar PDF desde Markdown usando ReportLab
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re

def parse_markdown_simple(md_content):
    """
    Parsea Markdown simple a elementos de ReportLab
    """
    # Crear estilos
    styles = getSampleStyleSheet()

    # Estilo para título principal
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor='#1a1a1a',
        spaceAfter=30,
        spaceBefore=0,
        leftIndent=0,
        rightIndent=0,
    ))

    # Estilo para h2
    styles.add(ParagraphStyle(
        name='CustomHeading2',
        parent=styles['Heading2'],
        fontSize=16,
        textColor='#2c3e50',
        spaceAfter=12,
        spaceBefore=20,
    ))

    # Estilo para h3
    styles.add(ParagraphStyle(
        name='CustomHeading3',
        parent=styles['Heading3'],
        fontSize=13,
        textColor='#34495e',
        spaceAfter=10,
        spaceBefore=15,
    ))

    # Estilo para texto normal
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        leading=16,
    ))

    # Estilo para listas
    styles.add(ParagraphStyle(
        name='CustomBullet',
        parent=styles['BodyText'],
        fontSize=11,
        leftIndent=20,
        spaceAfter=8,
        leading=15,
    ))

    story = []
    lines = md_content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # H1
        if line.startswith('# '):
            text = line[2:].strip()
            story.append(Paragraph(text, styles['CustomTitle']))
            story.append(Spacer(1, 0.3*cm))

        # H2
        elif line.startswith('## '):
            text = line[3:].strip()
            story.append(Paragraph(text, styles['CustomHeading2']))

        # H3
        elif line.startswith('### '):
            text = line[4:].strip()
            story.append(Paragraph(text, styles['CustomHeading3']))

        # Lista numerada
        elif re.match(r'^\d+\.\s', line):
            text = re.sub(r'^\d+\.\s', '', line)
            # Procesar negritas
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            story.append(Paragraph(f"• {text}", styles['CustomBullet']))

        # Lista con guiones
        elif line.startswith('- ') or line.startswith('* '):
            text = line[2:].strip()
            # Procesar negritas
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            story.append(Paragraph(f"• {text}", styles['CustomBullet']))

        # Texto normal
        else:
            text = line
            # Procesar negritas
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            story.append(Paragraph(text, styles['CustomBody']))

        i += 1

    return story

def markdown_to_pdf(md_file, pdf_file):
    """Convierte un archivo Markdown a PDF"""

    # Leer el archivo Markdown
    md_content = Path(md_file).read_text(encoding='utf-8')

    # Crear el documento PDF
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=A4,
        rightMargin=2.5*cm,
        leftMargin=2.5*cm,
        topMargin=2.5*cm,
        bottomMargin=2.5*cm,
    )

    # Parsear Markdown y crear contenido
    story = parse_markdown_simple(md_content)

    # Generar PDF
    doc.build(story)

    print(f"✓ PDF generado exitosamente: {pdf_file}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        md_file = "/workspaces/aGEntiX/doc/memoria.md"
        pdf_file = "/workspaces/aGEntiX/doc/memoria.pdf"
    else:
        md_file = sys.argv[1]
        pdf_file = sys.argv[2] if len(sys.argv) > 2 else md_file.replace('.md', '.pdf')

    markdown_to_pdf(md_file, pdf_file)

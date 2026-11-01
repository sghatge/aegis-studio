"""Real conversion fixtures, assembled in memory; no customer files."""
import io
import pytest
from docx import Document
from pptx import Presentation
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from aegis import documents

@pytest.mark.parametrize('name', ['sample.txt','sample.md','sample.csv','sample.html','sample.htm'])
def test_text_types_and_utf8_bom(name):
    assert documents.convert(name, b'\xef\xbb\xbfHello Aegis') == 'Hello Aegis'

def test_docx_conversion():
    stream=io.BytesIO(); doc=Document(); doc.add_paragraph('Aegis document conversion marker'); doc.save(stream)
    assert 'Aegis document conversion marker' in documents.convert('report.docx',stream.getvalue())

def test_pptx_conversion():
    stream=io.BytesIO(); deck=Presentation(); slide=deck.slides.add_slide(deck.slide_layouts[1]); slide.shapes.title.text='Aegis slide marker'; deck.save(stream)
    assert 'Aegis slide marker' in documents.convert('deck.pptx',stream.getvalue())

def test_xlsx_conversion():
    stream=io.BytesIO(); wb=Workbook(); wb.active['A1']='Aegis spreadsheet marker'; wb.save(stream)
    assert 'Aegis spreadsheet marker' in documents.convert('sheet.xlsx',stream.getvalue())

def test_pdf_conversion():
    stream=io.BytesIO(); pdf=canvas.Canvas(stream); pdf.drawString(50,750,'Aegis PDF conversion marker'); pdf.save()
    assert 'Aegis PDF conversion marker' in documents.convert('report.pdf',stream.getvalue())

def test_case_insensitive_extension():
    assert documents.convert('REPORT.TXT',b'hello')=='hello'

def test_reject_unsupported_type():
    with pytest.raises(ValueError, match='Unsupported'): documents.convert('program.exe',b'no')

def test_limit_upload():
    with pytest.raises(ValueError, match='10 MB'): documents.convert('large.txt', b'a'*(documents.MAX_BYTES+1))

def test_text_truncated_to_one_million():
    assert len(documents.convert('large.txt', b'a'*1000001)) == 1000000

def test_malformed_docx_fails():
    with pytest.raises(ValueError, match='Invalid Office file'): documents.convert('broken.docx',b'not a docx')

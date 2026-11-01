from pathlib import Path
import tempfile
import io
import zipfile
from .core import MAX_BYTES
ALLOWED={'.pdf','.docx','.pptx','.xlsx','.csv','.html','.htm','.txt','.md'}
def convert(name,data):
    suffix=Path(name).suffix.lower()
    if suffix not in ALLOWED: raise ValueError('Unsupported document type.')
    if len(data)>MAX_BYTES: raise ValueError('File exceeds the 10 MB limit.')
    if suffix in {'.txt','.md','.csv','.html','.htm'}: return data.decode('utf-8-sig')[:1000000]
    if suffix in {'.docx','.pptx','.xlsx'} and not zipfile.is_zipfile(io.BytesIO(data)):
        raise ValueError('Invalid Office file: expected a valid ZIP-based document.')
    from markitdown import MarkItDown
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/('upload'+suffix); path.write_bytes(data)
        text=MarkItDown().convert(str(path)).text_content
    if not text.strip(): raise ValueError('No text extracted. Scanned files may require OCR.')
    return text[:1000000]

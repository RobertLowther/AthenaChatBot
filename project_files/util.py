import json

def OpenFile(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

def SaveFile(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

def LoadJson(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return json.load(infile)

def SaveJson(filepath, payload):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        json.dump(payload, outfile, ensure_ascii=False, sort_keys=True, indent=4)

def clamp(val, min, max):
    if val < min:
        return min
    if val > max:
        return max
    return val
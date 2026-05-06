import json
d = json.load(open('data/diseases.json','r',encoding='utf-8'))
for dis in d:
    if dis['name'] in ['Anxiety Disorder', 'Hepatitis B', 'Hepatitis', "Bell's Palsy"]:
        system = dis.get("system", "?")
        print(f"{dis['name']}: system={system}")

# Fix Anxiety Disorder system
for dis in d:
    if dis['name'] == 'Anxiety Disorder':
        dis['system'] = 'psychiatric'
        print(f"Fixed Anxiety Disorder system -> psychiatric")

json.dump(d, open('data/diseases.json','w',encoding='utf-8'), indent=2, ensure_ascii=False)
print("Saved!")

import json

kevin = {
    "kevin": {
        "name" : "kevin"
    }
    
}

kev = {
    
        "name" : "kev",
        "message": []
}
    
with open("userData.json", 'r+') as f:
    json.dump(kevin, f)
f.close()

#https://stackoverflow.com/questions/21035762/python-read-json-file-and-modify
with open('userData.json','r+') as f:
    data = json.load(f)
    data["kev"] = kev
    f.seek(0)
    json.dump(data, f, indent=4)
    f.truncate()
f.close()

with open('userData.json','r+') as f:
    data = json.load(f)
    data['kev']['name'] = 'kevvvvin'
    f.seek(0)
    json.dump(data, f, indent=4)
    f.truncate()
    print(data["kev"]['name'])
f.close()

with open('userData.json','r+') as f:
    data = json.load(f)
    data['kev']['message'].append('hi')
    f.seek(0)
    json.dump(data, f, indent=4)
    f.truncate()
f.close()


print("hi kevin !!".split(" "))
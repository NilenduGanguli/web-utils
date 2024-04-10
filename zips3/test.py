res = []
def flatten_json(json, parent_key='', sep='/'):
    items = []
    print(json)
    if len(json)!=0 :
        for key,value in json.items():
            new_key = parent_key + sep + key
            items.extend(flatten_json(value, new_key, sep))
    else:
        items.extend([parent_key])
    return items

import json

json_str = '''
{
    "doc_top.pdf":{},
    "zip7.zip": {
        "zip1.zip": {
            "doc1.pdf": {},
            "zip2.zip": {
                "doc2.pdf": {},
                "zip3.zip": {
                    "doc3.pdf": {}
                }
            }
        },
        "zip3.zip": {
            "doc5.pdf": {},
            "doc6.pdf": {}
        }
    }
}
'''


json_list = json.loads(json_str)
print(json.dumps(flatten_json(json_list),indent=4))


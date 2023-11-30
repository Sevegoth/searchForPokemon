from flask import Flask, request
from markupsafe import escape
from flask import render_template
from elasticsearch import Elasticsearch
import math

ELASTIC_PASSWORD = "gzmtgzs52nm"

es = Elasticsearch("https://localhost:9200", http_auth=("elastic", ELASTIC_PASSWORD), verify_certs=True)
app = Flask(__name__)
MAX_SIZE = 10

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    page_size = 10
    keyword = request.args.get('keyword')
    if request.args.get('page'):
        page_no = int(request.args.get('page'))
    else:
        page_no = 1
    if keyword.isdigit():
        body = {
            'size': page_size,
            'from': page_size * (page_no-1),
            'query': {
                'match':{
                    "num":keyword
                }
            }
        }
    else:
        keywords = keyword.split(" ")
        for i in range(len(keywords)):
            keywords[i] = keywords[i].capitalize()
        body = {
            'size': page_size,
            'from': page_size * (page_no-1),
            "query": {
                "bool": {
                    "should": [
                        {"terms": {"name": keywords}},
                        {"terms": {"type1": keywords}},
                        {"terms": {"type2": keywords}},
                        {"multi_match":{
                            "query":keyword,
                            "fields":['name','type1','type2'],
                            "fuzziness":"2"
                        }}]
                }
            },
            "sort": [{
            "id": "desc"}
            ]
        }    
    res = es.search(index='pokemon_cleaned', body=body)
    
    hits = [{
                'name': doc['_source']['name'],  
                'num': doc['_source']['num'],
                'id': 200 if doc['_source']['name']==keywords[0] else 0,
                'id': 200 if doc['_source']['type1']==keywords[0] or doc['_source']['id']==200 else 0,
                'type1': doc['_source']['type1'],
                'type2': doc['_source']['type2'] if 'type2' in doc['_source'] else None,
                'img': doc['_source']['img'],
                'weaknesses': doc['_source']['weaknesses'],
                "next_evolution": doc['_source']['next_evolution'] if 'next_evolution' in doc['_source'] else None,
                "prev_evolution": doc['_source']['prev_evolution'] if 'prev_evolution' in doc['_source'] else None
                }for doc in res['hits']['hits']]
    sorted_hits = sorted(hits, key=lambda x: x.get('id', 0),reverse=True)  
    page_total = math.ceil(res['hits']['total']['value']/page_size)
    return render_template('search.html',keyword=keyword, hits=sorted_hits, page_no=page_no, page_total=page_total)

if __name__ =="__main__":
    app.run(debug=True)
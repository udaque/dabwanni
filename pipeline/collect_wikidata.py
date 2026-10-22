"""Wikidata: 작품·인물·제작사의 한국어 이름, 위키백과 문서 제목, 인물 생년월일·소속사, 제작사 설립 연도.
MyAnimeList ID(P4086 작품, P4084 인물)로 연결, 제작사는 작품의 제작사(P272)로 찾음. 매번 전체를 다시 받습니다(몇 분)."""
import argparse
from common import *

EP = 'https://query.wikidata.org/sparql?format=json&query='
Q = {
 'works': '''SELECT ?mal ?ko ?ja ?jawiki ?kowiki WHERE { ?i wdt:P4086 ?mal .
 OPTIONAL{?i rdfs:label ?ko FILTER(lang(?ko)="ko")} OPTIONAL{?i rdfs:label ?ja FILTER(lang(?ja)="ja")}
 OPTIONAL{?jw schema:about ?i; schema:isPartOf <https://ja.wikipedia.org/>; schema:name ?jawiki}
 OPTIONAL{?kw schema:about ?i; schema:isPartOf <https://ko.wikipedia.org/>; schema:name ?kowiki} } LIMIT %d OFFSET %d''',
 'people': '''SELECT ?malp ?ko ?ja ?en ?birth ?agko ?agja WHERE { ?i wdt:P4084 ?malp .
 OPTIONAL{?i rdfs:label ?ko FILTER(lang(?ko)="ko")} OPTIONAL{?i rdfs:label ?ja FILTER(lang(?ja)="ja")}
 OPTIONAL{?i rdfs:label ?en FILTER(lang(?en)="en")} OPTIONAL{?i wdt:P569 ?birth}
 OPTIONAL{?i wdt:P1416 ?ag . OPTIONAL{?ag rdfs:label ?agko FILTER(lang(?agko)="ko")} OPTIONAL{?ag rdfs:label ?agja FILTER(lang(?agja)="ja")}} } LIMIT %d OFFSET %d''',
 'studios': '''SELECT DISTINCT ?co ?ko ?ja ?en ?founded WHERE { ?a wdt:P4086 ?mal; wdt:P272 ?co .
 OPTIONAL{?co rdfs:label ?ko FILTER(lang(?ko)="ko")} OPTIONAL{?co rdfs:label ?ja FILTER(lang(?ja)="ja")}
 OPTIONAL{?co rdfs:label ?en FILTER(lang(?en)="en")} OPTIONAL{?co wdt:P571 ?founded} } LIMIT %d OFFSET %d''',
}
MIN_ROWS = {'works': 3000, 'people': 3000, 'studios': 100}   # 이보다 적으면 형식 변경으로 보고 저장하지 않음 (첫 실행 기준 작품 약 7,400행)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); budget_arg(ap); a = ap.parse_args()
    http = Http(2.0)
    def sparql(q):
        d = http.json(EP + urllib.parse.quote(q), headers={'Accept': 'application/sparql-results+json'})
        if 'results' not in (d or {}): raise SchemaError('Wikidata 응답 형식이 바뀜')
        return d['results']['bindings']
    def work(x, run):
        http.run = run; rows, off, step = [], 0, 20000
        while True:
            b = sparql(Q[x['k']] % (step, off)); rows += [{k: v['value'] for k, v in r.items()} for r in b]
            run.say(f"{x['k']} {len(rows)}행")
            if len(b) < step: break
            off += step
        if len(rows) < MIN_ROWS[x['k']]: raise ValueError(f"{x['k']} 결과가 {len(rows)}행뿐이라 저장하지 않음 (형식 변경 의심)")
        save('wikidata', x['k'], rows); return rows
    run_source('wikidata', [{'k': k} for k in Q], work,
               canary=(lambda: sparql('SELECT ?i WHERE { ?i wdt:P4086 "1" } LIMIT 1'), '카우보이 비밥 MAL 1'), budget_min=a.budget_min, min_n=99)

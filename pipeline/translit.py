"""일본어 → 한국어 음역 (커뮤니티 관용 표기: 어두 격음, ツ=츠, 장음 생략).
공식 한국어 표기가 없을 때 사람·회사 이름에만 쓰며, 결과에는 항상 '자동 표기' 표시를 붙입니다."""
import re, unicodedata

CHO = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'; JUNG = 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'
JONG = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
def syl(c, v): return chr(0xAC00 + (CHO.index(c) * 21 + JUNG.index(v)) * 28)
def add_jong(s, j):
    if s and '가' <= s[-1] <= '힣' and (ord(s[-1]) - 0xAC00) % 28 == 0:
        return s[:-1] + chr(ord(s[-1]) + JONG.index(j))
    return s

ROWS = {  # 가타카나 기본 음절 → (초성, 중성)
 'ア':'ㅇㅏ','イ':'ㅇㅣ','ウ':'ㅇㅜ','エ':'ㅇㅔ','オ':'ㅇㅗ','カ':'ㅋㅏ','キ':'ㅋㅣ','ク':'ㅋㅜ','ケ':'ㅋㅔ','コ':'ㅋㅗ',
 'ガ':'ㄱㅏ','ギ':'ㄱㅣ','グ':'ㄱㅜ','ゲ':'ㄱㅔ','ゴ':'ㄱㅗ','サ':'ㅅㅏ','シ':'ㅅㅣ','ス':'ㅅㅡ','セ':'ㅅㅔ','ソ':'ㅅㅗ',
 'ザ':'ㅈㅏ','ジ':'ㅈㅣ','ズ':'ㅈㅡ','ゼ':'ㅈㅔ','ゾ':'ㅈㅗ','タ':'ㅌㅏ','チ':'ㅊㅣ','ツ':'ㅊㅡ','テ':'ㅌㅔ','ト':'ㅌㅗ',
 'ダ':'ㄷㅏ','ヂ':'ㅈㅣ','ヅ':'ㅈㅡ','デ':'ㄷㅔ','ド':'ㄷㅗ','ナ':'ㄴㅏ','ニ':'ㄴㅣ','ヌ':'ㄴㅜ','ネ':'ㄴㅔ','ノ':'ㄴㅗ',
 'ハ':'ㅎㅏ','ヒ':'ㅎㅣ','フ':'ㅎㅜ','ヘ':'ㅎㅔ','ホ':'ㅎㅗ','バ':'ㅂㅏ','ビ':'ㅂㅣ','ブ':'ㅂㅜ','ベ':'ㅂㅔ','ボ':'ㅂㅗ',
 'パ':'ㅍㅏ','ピ':'ㅍㅣ','プ':'ㅍㅜ','ペ':'ㅍㅔ','ポ':'ㅍㅗ','マ':'ㅁㅏ','ミ':'ㅁㅣ','ム':'ㅁㅜ','メ':'ㅁㅔ','モ':'ㅁㅗ',
 'ヤ':'ㅇㅑ','ユ':'ㅇㅠ','ヨ':'ㅇㅛ','ラ':'ㄹㅏ','リ':'ㄹㅣ','ル':'ㄹㅜ','レ':'ㄹㅔ','ロ':'ㄹㅗ','ワ':'ㅇㅘ','ヲ':'ㅇㅗ',
 'ヴ':'ㅂㅜ','ヰ':'ㅇㅣ','ヱ':'ㅇㅔ'}
SMALL = {'ャ':'ㅑ','ュ':'ㅠ','ョ':'ㅛ','ァ':'ㅏ','ィ':'ㅣ','ゥ':'ㅜ','ェ':'ㅔ','ォ':'ㅗ'}
YMAP = {('ㅅ','ㅑ'):'ㅑ',('ㅅ','ㅠ'):'ㅠ',('ㅅ','ㅛ'):'ㅛ',('ㅈ','ㅑ'):'ㅏ',('ㅈ','ㅠ'):'ㅜ',('ㅈ','ㅛ'):'ㅗ',('ㅊ','ㅑ'):'ㅏ',('ㅊ','ㅠ'):'ㅜ',('ㅊ','ㅛ'):'ㅗ'}
WMAP = {('ㅇ','ㅜ','ㅣ'):'ㅟ',('ㅇ','ㅜ','ㅔ'):'ㅞ',('ㅇ','ㅜ','ㅗ'):'ㅝ'}

def kana_to_hangul(t):
    t = ''.join(chr(ord(c) + 0x60) if 'ぁ' <= c <= 'ゖ' else c for c in unicodedata.normalize('NFKC', t))
    out, prev_v, i = '', None, 0
    while i < len(t):
        c = t[i]; n = t[i + 1] if i + 1 < len(t) else ''
        if c in ROWS:
            cho, v = ROWS[c][0], ROWS[c][1]
            if n in SMALL:
                sv = SMALL[n]; i += 1
                if c == 'フ': cho = 'ㅍ'                          # 외래어 ファ·フィ → 파·피
                if n in 'ャュョ': v = YMAP.get((cho, sv), sv)
                elif (cho, v, sv) in WMAP: v = WMAP[(cho, v, sv)]
                else:
                    if cho == 'ㅌ' and c in 'テ' and sv == 'ㅣ': v = 'ㅣ'
                    elif cho == 'ㄷ' and sv == 'ㅣ': v = 'ㅣ'
                    elif c in 'チシジ' and sv == 'ㅔ': v = 'ㅔ'
                    else: v = sv
            if c in 'ウオ' and prev_v in ('ㅗ', 'ㅛ') and c == 'ウ' or (c == 'オ' and prev_v == 'ㅗ') or (c == 'ウ' and prev_v in ('ㅜ', 'ㅠ')):
                i += 1; continue                                   # 장음 생략 (おう, おお, うう)
            out += syl(cho, v); prev_v = v
        elif c == 'ン': out = add_jong(out, 'ㄴ'); prev_v = None
        elif c == 'ッ': out = add_jong(out, 'ㅅ'); prev_v = None
        elif c == 'ー': pass
        elif c in '・･': out += ' '; prev_v = None
        else: out += c; prev_v = None
        i += 1
    return re.sub(r'\s+', ' ', out).strip()

_k = None
def reading(t):
    global _k
    if _k is None:
        import pykakasi; _k = pykakasi.kakasi()
    return [(x['orig'], x['kana'], x['hepburn']) for x in _k.convert(t)]

def ja_to_hangul(t):
    """한자 섞인 일본어를 읽기 추정 후 음역 (라틴 문자는 그대로)."""
    out = []
    for o, k, h in reading(t):
        out.append(o if re.fullmatch(r'[A-Za-z0-9 .&\-]+', o) else kana_to_hangul(k))
    return ''.join(out)

def norm_romaji(r):
    r = unicodedata.normalize('NFKD', r).encode('ascii', 'ignore').decode().lower()
    r = re.sub(r"[^a-z]", '', r)
    return re.sub(r'(ou|oo|uu)', lambda m: m.group(0)[0], r).replace('ei', 'e')

def name_to_hangul(native=None, first=None, last=None):
    """이름 음역. 한자 이름은 AniList 로마자 읽기와 맞는지 확인한 뒤 씁니다.
    반환: (한글, 확실성) 확실성: 'kana'(가나라 확실) / 'checked'(읽기 확인) / 'guess'(추정)"""
    if native and re.fullmatch(r'[\u3040-\u30ff・ー\s]+', native):
        return kana_to_hangul(native), 'kana'
    if native:
        parts = re.split(r'\s+', native.strip())
        rd = reading(native.replace(' ', ''))
        kana = ''.join(k for _, k, _ in rd); rom = ''.join(h for _, _, h in rd)
        target = norm_romaji((last or '') + (first or ''))
        if target and norm_romaji(rom) == target:
            # 성·이름 경계: 로마자 성 길이에 맞춰 가나를 나눔
            ln = norm_romaji(last or '')
            acc, cut = '', len(kana)
            for j in range(1, len(kana) + 1):                    # 장음(う·お)까지 성에 붙도록 가장 긴 일치를 씀
                if norm_romaji(''.join(h for _, _, h in reading(kana[:j]))) == ln: cut = j
            return (kana_to_hangul(kana[:cut]) + ' ' + kana_to_hangul(kana[cut:])).strip(), 'checked'
        if not (first or last):
            return kana_to_hangul(kana), 'guess'
    from_rom = ' '.join(x for x in (romaji_to_hangul(last), romaji_to_hangul(first)) if x)
    return from_rom, 'guess'

def romaji_to_hangul(r):
    """로마자 → 가나 → 한글 (n+모음 경계는 추정)."""
    if not r: return ''
    r = unicodedata.normalize('NFKD', r).encode('ascii', 'ignore').decode().lower()
    T = [('kya','キャ'),('kyu','キュ'),('kyo','キョ'),('gya','ギャ'),('gyu','ギュ'),('gyo','ギョ'),('sha','シャ'),('shu','シュ'),('sho','ショ'),('shi','シ'),
         ('cha','チャ'),('chu','チュ'),('cho','チョ'),('chi','チ'),('tsu','ツ'),('ja','ジャ'),('ju','ジュ'),('jo','ジョ'),('ji','ジ'),('nya','ニャ'),('nyu','ニュ'),('nyo','ニョ'),
         ('hya','ヒャ'),('hyu','ヒュ'),('hyo','ヒョ'),('bya','ビャ'),('byu','ビュ'),('byo','ビョ'),('pya','ピャ'),('pyu','ピュ'),('pyo','ピョ'),('mya','ミャ'),('myu','ミュ'),('myo','ミョ'),
         ('rya','リャ'),('ryu','リュ'),('ryo','リョ'),('fu','フ')]
    for c, row in zip('kgsztdnhbpmr', ['カキクケコ','ガギグゲゴ','サシスセソ','ザジズゼゾ','タチツテト','ダヂヅデド','ナニヌネノ','ハヒフヘホ','バビブベボ','パピプペポ','マミムメモ','ラリルレロ']):
        for v, k in zip('aiueo', row): T.append((c + v, k))
    for v, k in zip('aiueo', 'アイウエオ'): T.append((v, k))
    T += [('ya','ヤ'),('yu','ユ'),('yo','ヨ'),('wa','ワ'),('wo','ヲ')]
    T.sort(key=lambda x: -len(x[0]))
    out = []
    for w in r.split():
        k, i = '', 0
        while i < len(w):
            if i + 1 < len(w) and w[i] == w[i + 1] and w[i] not in 'aiueon': k += 'ッ'; i += 1; continue
            for a, b in T:
                if w.startswith(a, i): k += b; i += len(a); break
            else:
                if w[i] in 'nm': k += 'ン'
                i += 1
        out.append(kana_to_hangul(k))
    return ' '.join(out)

if __name__ == '__main__':
    tests = [('種﨑 敦美', 'Atsumi', 'Tanezaki'), ('花澤 香菜', 'Kana', 'Hanazawa'), ('渡辺 信一郎', 'Shinichirou', 'Watanabe'),
             ('梶 裕貴', 'Yuuki', 'Kaji'), ('釘宮 理恵', 'Rie', 'Kugimiya'), ('津田 健次郎', 'Kenjirou', 'Tsuda'), ('宮野 真守', 'Mamoru', 'Miyano'),
             ('今 敏', 'Satoshi', 'Kon'), ('YOASOBI', None, None), ('いきものがかり', None, None), ('庵野 秀明', 'Hideaki', 'Anno'), ('細谷 佳正', 'Yoshimasa', 'Hosoya')]
    for t in tests: print(t[0], name_to_hangul(*t))
    for x in ['マッドハウス', 'シャフト', 'ぴえろ', 'サンライズ', 'トムス・エンタテインメント', 'ジェー・シー・スタッフ', 'ディオメディア', 'ファンワークス']:
        print(x, kana_to_hangul(x))

"""사람·제작사·태그의 한국어 이름. 확인된 표기(사전·Wikidata·나무위키)가 없으면 음역하고 auto=True로 표시합니다."""
import re, unicodedata
from translit import romaji_to_hangul, kana_to_hangul, name_to_hangul, ja_to_hangul

STUDIO_KO = {
 'toei animation':'토에이 애니메이션','tms entertainment':'톰스 엔터테인먼트','sunrise':'선라이즈','jcstaff':'J.C.STAFF(제이씨 스태프)',
 'madhouse':'매드하우스','studio deen':'스튜디오 딘','pierrot':'피에로','studio pierrot':'스튜디오 피에로','olm':'OLM(오엘엠)',
 'production ig':'프로덕션 I.G','anime international':'AIC(애니메이션 인터내셔널 컴퍼니)','aic':'AIC(에이아이씨)','a1 pictures':'A-1 Pictures(에이원 픽처스)',
 'shinei animation':'신에이 동화','dle':'DLE(디엘이)','nippon animation':'닛폰 애니메이션','trex':'티렉스','silver link':'실버 링크',
 'tatsunoko production':'타츠노코 프로덕션','arms':'암스','brains base':'브레인즈 베이스','tokyo movie shinsha':'도쿄 무비 신샤','tokyo movie':'도쿄 무비',
 'group tac':'그룹 TAC(그룹 탁)','bones':'본즈','aqua aris':'아쿠아 아리스','kyoto animation':'교토 애니메이션','shaft':'샤프트','xebec':'지벡',
 'gonzo':'곤조','doga kobo':'동화공방','lidenfilms':'라이덴 필름','liden films':'라이덴 필름','mappa':'MAPPA(마파)','animation studio seven':'애니메이션 스튜디오 세븐',
 'wit studio':'위트 스튜디오','satelight':'사테라이트','feel':'필','kachidoki studio':'카치도키 스튜디오','cloverworks':'클로버웍스',
 'ashi productions':'아시 프로덕션','ajiado':'아지아도','studio puyukai':'스튜디오 푸유카이','production reed':'프로덕션 리드','asahi production':'아사히 프로덕션',
 'tezuka productions':'데즈카 프로덕션','animate film':'애니메이트 필름','lerche':'레르체','ufotable':'유포터블','yumeta company':'유메타 컴퍼니',
 'magic bus':'매직 버스','studio 9 maiami':'스튜디오 9 마이아미','zexcs':'젝스','8bit':'8bit(에이트비트)','8bit corp':'8bit(에이트비트)','pa works':'P.A.WORKS(피에이 웍스)',
 'bn pictures':'BN Pictures(비엔 픽처스)','shogakukan music digital entertainment':'쇼가쿠칸 뮤직 앤드 디지털 엔터테인먼트',
 'shougakukan music digital entertainment':'쇼가쿠칸 뮤직 앤드 디지털 엔터테인먼트','gallop':'갤럽','studio 4c':'스튜디오 4°C','studio comet':'스튜디오 코메트',
 'bandai namco pictures':'반다이 남코 픽처스','telecom animation film':'텔레콤 애니메이션 필름','comix wave films':'코믹스 웨이브 필름','studio gokumi':'스튜디오 고쿠미',
 'diomedea':'디오메디아','project no9':'프로젝트 No.9','poro':'포로','fanworks':'팬웍스','synergysp':'시너지 SP','synergy sp':'시너지 SP','studio 1st':'스튜디오 퍼스트',
 'youc':'Y.O.U.C(와이오유씨)','actas':'액타스','studio hibari':'스튜디오 히바리','sanzigen':'산지겐','kinema citrus':'키네마 시트러스','yostar pictures':'요스타 픽처스',
 'gainax':'가이낙스','emt squared':'EMT 스퀘어드','daume':'다우메','studio ghibli':'스튜디오 지브리','tnk':'TNK(티엔케이)','mushi production':'무시 프로덕션',
 'artland':'아트랜드','blue bread':'블루 브레드','david production':'데이비드 프로덕션','studio khara':'스튜디오 카라','white fox':'화이트 폭스','gohands':'고핸즈',
 'kamikaze douga':'카미카제 동화','kamikazedouga':'카미카제 동화','eiken':'에이켄','polygon pictures':'폴리곤 픽처스','olm digital':'OLM 디지털','dwarf':'드워프',
 'sanrio':'산리오','knack productions':'낵 프로덕션','trigger':'트리거','pie in the sky':'파이 인 더 스카이','zerog':'제로지','acgt':'ACGT(에이씨지티)',
 'office takeout':'오피스 테이크아웃','tyo animations':'TYO 애니메이션즈','passione':'파시오네','hoods entertainment':'후즈 엔터테인먼트','asread':'아스리드',
 'seven arcs':'세븐 아크스','seven arcs pictures':'세븐 아크스 픽처스','aic asta':'AIC ASTA','gathering':'개더링','studio fantasia':'스튜디오 판타지아','nomad':'노마드',
 'studio colorido':'스튜디오 콜로리도','hal film maker':'할 필름 메이커','shirogumi':'시로구미','signalmd':'시그널 MD','yokohama animation lab':'요코하마 애니메이션 랩',
 'bee train':'비 트레인','bee train productions':'비 트레인','studio kai':'스튜디오 카이','studio gohan':'스튜디오 고한','ilca':'일카','triangle staff':'트라이앵글 스태프',
 'manglobe':'망글로브','yamamura animation':'야마무라 애니메이션','felix film':'펠릭스 필름','troyca':'트로이카','cygamespictures':'사이게임즈 픽처스',
 'bibury animation studios':'비버리 애니메이션 스튜디오','graphinica':'그래피니카','orange':'오렌지','layduce':'레이듀스','studio 3hz':'스튜디오 3Hz',
 'production ims':'프로덕션 IMS','tcj':'TCJ','dongwoo animation':'동우 애니메이션','pine jam':'파인 잼','trans arts':'트랜스 아츠','millepensee':'밀레팡세',
 'c2c':'C2C(씨투씨)','engi':'엔기','studio acat':'스튜디오 A-CAT','studio comet':'스튜디오 코메트','geno studio':'제노 스튜디오','studio bind':'스튜디오 바인드',
 'cloverworks':'클로버웍스','science saru':'사이언스 SARU','studio chizu':'스튜디오 지도','studio ponoc':'스튜디오 포녹','okuruto noboru':'오쿠루토 노보루',
 'studio voln':'스튜디오 볼른','encourage films':'인커리지 필름즈','nexus':'넥서스','hornets':'호네츠','studio blanc':'스튜디오 블랑','tezuka production':'데즈카 프로덕션',
 'aniplex':'애니플렉스','kadokawa':'카도카와','dentsu':'덴츠','avex pictures':'에이벡스 픽처스','pony canyon':'포니 캐니언','lantis':'란티스','bandai visual':'반다이 비주얼',
 'kodansha':'코단샤','shueisha':'슈에이샤','shogakukan':'쇼가쿠칸','toho':'토호','tbs':'TBS','fuji tv':'후지 TV','tv tokyo':'TV 도쿄','nhk':'NHK','mbs':'MBS',
 'nippon tv':'닛폰 TV','tv asahi':'TV 아사히','sony music entertainment':'소니 뮤직 엔터테인먼트','king records':'킹 레코드','warner bros japan':'워너 브라더스 재팬',
 'movic':'무빅','genco':'젠코','frontier works':'프론티어 웍스','egg firm':'에그 펌','sentai filmworks':'센타이 필름웍스','crunchyroll':'크런치롤','funimation':'퍼니메이션',
 'netflix':'넷플릭스','bilibili':'빌리빌리','tencent penguin pictures':'텐센트 펭귄 픽처스','aniplex of america':'애니플렉스 오브 아메리카','sotsu':'소츠',
}
WORD_KO = {'studio':'스튜디오','studios':'스튜디오','animation':'애니메이션','animations':'애니메이션','pictures':'픽처스','picture':'픽처','production':'프로덕션',
 'productions':'프로덕션','film':'필름','films':'필름','works':'웍스','entertainment':'엔터테인먼트','company':'컴퍼니','digital':'디지털','lab':'랩','project':'프로젝트',
 'art':'아트','arts':'아츠','team':'팀','creative':'크리에이티브','creatives':'크리에이티브','media':'미디어','music':'뮤직','records':'레코드','tv':'TV','co':'',
 'japan':'재팬','tokyo':'도쿄','osaka':'오사카','kyoto':'교토','visual':'비주얼','factory':'팩토리','planning':'플래닝','design':'디자인','graphics':'그래픽스','sound':'사운드',
 'international':'인터내셔널','group':'그룹','office':'오피스','house':'하우스','box':'박스','the':'더','and':'앤드','of':'오브','new':'뉴','world':'월드','line':'라인',
 'pictures.':'픽처스','laboratory':'래버러토리','laboratories':'래버러토리','anime':'애니메','animation.':'애니메이션','corporation':'','corp':'','inc':'','ltd':'','kk':'','llc':'','co.':'','gmbh':''}
SUFFIX = re.compile(r'\b(co|ltd|inc|k\.?k|corp|corporation|llc|co\.?,? ?ltd|kabushiki ?kaisha)\b\.?', re.I)

def studio_key(n):
    n = (n or '').lower().replace('°', '').replace('ō', 'o').replace('ū', 'u').replace('é', 'e').replace('ü', 'u')
    n = SUFFIX.sub(' ', n)
    n = re.sub(r"[.,'&’\-]", '', n)
    return re.sub(r'\s+', ' ', n).strip()

ROMAJI_TOKEN = re.compile(r'^(?:(?:[kgsztdnhbpmrwyfj]|ky|gy|sh|ch|ts|ny|hy|by|py|my|ry)?[aiueo]|n|(?:kk|ss|tt|pp))+$')
def latin_to_hangul(text):
    out = []
    for w in re.split(r'\s+', text.strip()):
        lw = re.sub(r'[^a-z0-9]', '', w.lower())
        if not lw: continue
        if lw in WORD_KO: out.append(WORD_KO[lw])
        elif lw.isdigit(): out.append(lw)
        elif ROMAJI_TOKEN.match(lw): out.append(romaji_to_hangul(lw))
        else: out.append(w)                                  # 해석 불가 영단어는 원문 유지
    return ' '.join(x for x in out if x)

def studio_ko(name, overrides=None):
    """반환 (한국어, auto)"""
    k = studio_key(name)
    if overrides and k in overrides: return overrides[k], False
    if k in STUDIO_KO: return STUDIO_KO[k], False
    if re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', name or ''): return ja_company(name), True
    return latin_to_hangul(k), True

JA_WORD = [('株式会社', ''), ('（株）', ''), ('(株)', ''), ('有限会社', ''), ('製作委員会', ' 제작위원회'), ('作画部', ' 작화부'), ('スタジオ', '스튜디오 '),
 ('アニメーション', ' 애니메이션'), ('プロダクション', ' 프로덕션'), ('ピクチャーズ', ' 픽처스'), ('フィルムズ', ' 필름즈'), ('フィルム', ' 필름'), ('ワークス', ' 웍스'),
 ('エンタテインメント', ' 엔터테인먼트'), ('エンターテインメント', ' 엔터테인먼트'), ('エンタープライズ', ' 엔터프라이즈'), ('ミュージック', ' 뮤직'), ('レコード', ' 레코드'),
 ('動画', ' 동화'), ('工房', ' 공방'), ('企画', ' 기획'), ('放送', ' 방송'), ('テレビ', ' TV'), ('出版', ' 출판'), ('書店', ' 서점'), ('ラボ', ' 랩'), ('デジタル', ' 디지털')]
def ja_company(name, work=None):
    """일본어 회사명 → 한국어 (회사 관용어는 번역, 나머지는 음역). work=(일본어 제목, 한국어 제목)"""
    s = name
    if work and work[0] and work[1]: s = s.replace(work[0], '\x00')
    s = s.replace('「', '').replace('」', '').replace('『', '').replace('』', '')
    parts = re.split('(' + '|'.join(re.escape(a) for a, _ in JA_WORD) + '|\x00)', s)
    out = []
    for p in parts:
        if not p: continue
        hit = dict(JA_WORD).get(p)
        if hit is not None: out.append(hit)
        elif p == '\x00': out.append(work[1])
        elif re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', p): out.append(ja_to_hangul(p))
        else: out.append(p)
    return re.sub(r'\s+', ' ', ''.join(out)).strip()

def person_ko(native=None, first=None, last=None, overrides=None):
    key = re.sub(r'\s', '', native or ((last or '') + (first or '')))
    if overrides and key in overrides: return overrides[key], False
    if native and re.search(r'[\uac00-\ud7a3]', native): return native, False      # 한국인 성우 등은 원문이 한국어
    if not (native and re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', native)) and (first or last):
        # 일본어 표기가 없는 이름(영어 더빙 성우 등)은 서양식 순서 그대로, 로마자로 읽히는 낱말만 한글로 옮김
        return latin_to_hangul(' '.join(x for x in (first, last) if x)), True
    if native and not re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', native) and not (first or last):
        return latin_to_hangul(native), True
    ko, how = name_to_hangul(native, first, last)
    return ko, True

TAG_KO = {'comedy':'코미디','fantasy':'판타지','action':'액션','adventure':'모험','drama':'드라마','kids':'아동','music':'음악','slice of life':'일상',
 'based on a manga':'만화 원작','romance':'로맨스','short episodes':'짧은 회차','male protagonist':'남성 주인공','sci-fi':'SF','science fiction':'SF','sci fi':'SF',
 'science-fiction':'SF','school':'학교','shounen':'소년','female protagonist':'여성 주인공','family friendly':'가족','magic':'마법','school life':'학원물','supernatural':'초자연',
 'slapstick':'슬랩스틱','historical':'시대극','seinen':'청년','original work':'오리지널','tragedy':'비극','violence':'폭력','anthropomorphic':'의인화','super power':'초능력',
 'primarily female cast':'여성 중심','mecha':'메카','coming of age':'성장','episodic':'에피소드식','contemporary fantasy':'현대 판타지','parody':'패러디','ecchi':'에치',
 'swordplay':'검술','ensemble cast':'군상극','martial arts':'무술','alternative world':'이세계','psychological':'심리','mystery':'미스터리','military':'밀리터리','war':'전쟁',
 'full cgi':'풀 3D','cgi':'3D','idol':'아이돌','high school':'고등학교','demon':'악마','urban fantasy':'어반 판타지','crime':'범죄','sports':'스포츠','space':'우주',
 'friendship':'우정','isekai':'이세계','horror':'호러','harem':'하렘','based on a light novel':'라이트노벨 원작','shoujo':'소녀','robot':'로봇','aliens':'외계인',
 'magical girl':'마법소녀','mahou shoujo':'마법소녀','detective':'추리','revenge':'복수','superpowers':'초능력','love triangle':'삼각관계','moe':'모에',
 'based on a video game':'게임 원작','police':'경찰','romantic comedy':'러브 코미디','vocaloid':'보컬로이드','post-apocalyptic':'포스트 아포칼립스','thriller':'스릴러',
 'philosophy':'철학','gods':'신','samurai':'사무라이','tournament':'토너먼트','based on a novel':'소설 원작','iyashikei':'힐링','food':'음식','cooking':'요리',
 'youkai':'요괴','yuri':'백합','time travel':'시간여행','reincarnation':'환생','travel':'여행','cyberpunk':'사이버펑크','ninja':'닌자','dark fantasy':'다크 판타지',
 'superhero':'슈퍼히어로','survival':'서바이벌','vampire':'흡혈귀','based on a mobile game':'모바일 게임 원작','based on a visual novel':'비주얼 노벨 원작',
 "boys' love":'BL','josei':'여성향','game':'게임','suspense':'서스펜스','dystopian':'디스토피아','dragons':'드래곤','super robot':'슈퍼로봇','real robot':'리얼로봇',
 'workplace':'직장','work':'직장','band':'밴드','card games':'카드 게임','mahjong':'마작','baseball':'야구','soccer':'축구','football':'축구','basketball':'농구',
 'volleyball':'배구','boxing':'권투','racing':'레이싱','time loop':'타임루프','chibi':'치비','educational':'교육','netflix original':'넷플릭스 오리지널','recap':'총집편',
 'adult audience only':'성인','hentai':'성인','erotica':'성인'}

import hashlib
def studio_sid(name): return 's' + hashlib.sha1(studio_key(name).encode()).hexdigest()[:10]

ROLE_KO = {  # 일본어·영어 직책 → 한국어
 'Assistant Episode Director': '연출 보좌', 'Assistant Director': '조감독', 'Assistant Producer': '보조 프로듀서',
 'Sub Character Design': '서브 캐릭터 디자인', 'Design Assistance': '디자인 보조', 'Character Design Assistance': '캐릭터 디자인 보조',
 'Monster Design': '몬스터 디자인', 'Creature Design': '크리처 디자인', 'Costume Design': '의상 디자인', 'Weapon Design': '무기 디자인',
 'Concept Art': '콘셉트 아트', 'Concept Design': '콘셉트 디자인', 'Title Logo Design': '타이틀 로고 디자인', 'Assistant Animation Director': '작화감독 보좌',
 '原作': '원작', 'Original Creator': '원작', 'Original Story': '원작', '監督': '감독', 'Director': '감독', '総監督': '총감독', 'Chief Director': '총감독',
 '副監督': '부감독', 'Assistant Director': '부감독', 'シリーズ構成': '시리즈 구성', 'Series Composition': '시리즈 구성', '脚本': '각본', 'Script': '각본',
 'Screenplay': '각본', 'キャラクターデザイン': '캐릭터 디자인', 'Character Design': '캐릭터 디자인', 'キャラクター原案': '캐릭터 원안', 'Original Character Design': '캐릭터 원안',
 '総作画監督': '총작화감독', 'Chief Animation Director': '총작화감독', '作画監督': '작화감독', 'Animation Director': '작화감독', '絵コンテ': '콘티', 'Storyboard': '콘티',
 '演出': '연출', 'Episode Director': '연출', 'Unit Director': '연출', '美術監督': '미술감독', 'Art Director': '미술감독', '色彩設計': '색채설계', 'Color Design': '색채설계',
 '撮影監督': '촬영감독', 'Director of Photography': '촬영감독', '編集': '편집', 'Editing': '편집', '音響監督': '음향감독', 'Sound Director': '음향감독', '音楽': '음악', 'Music': '음악',
 'メカニックデザイン': '메카 디자인', 'Mechanical Design': '메카 디자인', 'プロデューサー': '프로듀서', 'Producer': '프로듀서', 'Animation Producer': '애니메이션 프로듀서',
 '原画': '원화', 'Key Animation': '원화', '第二原画': '제2원화', '2nd Key Animation': '제2원화', '動画': '동화', 'In-Between Animation': '동화', 'CGディレクター': 'CG 감독',
 '3DCG Director': 'CG 감독', 'CG Director': 'CG 감독', 'アニメーション制作': '애니메이션 제작', '制作': '제작', '製作': '제작위원회', 'Theme Song Performance': '주제가',
 'Theme Song Lyrics': '주제가 작사', 'Theme Song Composition': '주제가 작곡', 'Theme Song Arrangement': '주제가 편곡', 'Insert Song Performance': '삽입곡',
 'エンドカード': '엔드카드', 'End Card Illustration': '엔드카드', 'Prop Design': '소품 디자인', 'プロップデザイン': '소품 디자인', 'Setting': '설정', '設定': '설정',
 'Background Art': '배경', '背景': '배경', 'Sound Effects': '효과음', '効果': '효과음', 'Composite': '촬영', '撮影': '촬영', 'Color Coordination': '색 지정',
}
STAFF_ORDER = ['원작', '총감독', '감독', '부감독', '시리즈 구성', '각본', '캐릭터 원안', '캐릭터 디자인', '총작화감독', '작화감독', '메카 디자인', '콘티', '연출',
 '미술감독', '색채설계', '촬영감독', 'CG 감독', '편집', '음향감독', '음악', '프로듀서', '애니메이션 프로듀서']
def role_ko(r):
    base = re.sub(r'\s*\(.*?\)\s*', '', r or '').strip()
    return ROLE_KO.get(base) or ROLE_KO.get(r) or base
def role_eps(r):
    """'Key Animation (eps 1, 4-6)' → ['1','4','5','6']"""
    m = re.search(r'\(\s*eps?\s*([\d,\s\-–]+)', r or '', re.I)
    if not m: return None
    out = []
    for part in re.split(r'[,\s]+', m.group(1).strip()):
        if re.fullmatch(r'\d+[-–]\d+', part):
            a, b = map(int, re.split(r'[-–]', part)); out += [str(x) for x in range(a, b + 1)] if b - a < 200 else []
        elif part.isdigit(): out.append(part)
    return out or None
SOURCE_KO = {'MANGA': '만화', 'LIGHT_NOVEL': '라이트노벨', 'NOVEL': '소설', 'VISUAL_NOVEL': '비주얼 노벨', 'VIDEO_GAME': '게임', 'GAME': '게임',
 'ORIGINAL': '오리지널', 'WEB_NOVEL': '웹소설', 'WEB_MANGA': '웹툰·웹만화', 'ONE_SHOT': '단편 만화', 'DOUJINSHI': '동인지', 'ANIME': '애니메이션',
 'LIVE_ACTION': '실사', 'PICTURE_BOOK': '그림책', 'COMIC': '코믹스', 'MULTIMEDIA_PROJECT': '미디어 믹스', 'MUSIC': '음악', 'OTHER': '기타'}
GENRE_KO = {'Action': '액션', 'Adventure': '모험', 'Comedy': '코미디', 'Drama': '드라마', 'Ecchi': '에치', 'Fantasy': '판타지', 'Hentai': '성인', 'Horror': '호러',
 'Mahou Shoujo': '마법소녀', 'Mecha': '메카', 'Music': '음악', 'Mystery': '미스터리', 'Psychological': '심리', 'Romance': '로맨스', 'Sci-Fi': 'SF',
 'Slice of Life': '일상', 'Sports': '스포츠', 'Supernatural': '초자연', 'Thriller': '스릴러'}

STATION_KO = {'NHK総合': 'NHK 종합', 'NHK Eテレ': 'NHK E테레', 'NHK教育': 'NHK 교육', 'NHK BS': 'NHK BS', 'NHK BSプレミアム': 'NHK BS 프리미엄', 'NHK BS2': 'NHK BS2',
 '日本テレビ': '닛폰 TV', 'TBS': 'TBS', 'フジテレビ': '후지 TV', 'テレビ朝日': 'TV 아사히', 'テレビ東京': 'TV 도쿄', 'TOKYO MX': '도쿄 MX', 'tvk': 'tvk(TV 가나가와)',
 'テレビ神奈川': 'TV 가나가와', 'チバテレビ': '치바 TV', 'テレ玉': '테레타마(TV 사이타마)', 'テレビ埼玉': 'TV 사이타마', 'とちぎテレビ': '토치기 TV', '群馬テレビ': '군마 TV',
 'MBS': 'MBS(마이니치 방송)', '毎日放送': '마이니치 방송', 'ABCテレビ': 'ABC TV', '朝日放送': '아사히 방송', '読売テレビ': '요미우리 TV', '関西テレビ': '간사이 TV',
 'テレビ大阪': 'TV 오사카', 'サンテレビ': '선 TV', 'KBS京都': 'KBS 교토', 'テレビ愛知': 'TV 아이치', '中京テレビ': '주쿄 TV', 'CBC': 'CBC TV', 'CBCテレビ': 'CBC TV',
 '東海テレビ': '도카이 TV', 'メ〜テレ': '메~테레(나고야 TV)', 'テレビ北海道': 'TV 홋카이도', 'TVQ九州放送': 'TVQ 규슈 방송', 'BS11': 'BS11', 'BS日テレ': 'BS 닛테레',
 'BSフジ': 'BS 후지', 'BS朝日': 'BS 아사히', 'BS-TBS': 'BS-TBS', 'BSテレ東': 'BS 테레토', 'BSジャパン': 'BS 재팬', 'AT-X': 'AT-X', 'アニマックス': '애니맥스',
 'キッズステーション': '키즈 스테이션', 'WOWOW': 'WOWOW', 'WOWOWプライム': 'WOWOW 프라임', 'カートゥーン ネットワーク': '카툰 네트워크', 'ディズニー・チャンネル': '디즈니 채널',
 'ニコニコ生放送': '니코니코 생방송', 'ABEMA': 'ABEMA', 'dアニメストア': 'd애니메 스토어', 'U-NEXT': 'U-NEXT', 'Netflix': '넷플릭스', 'Prime Video': '프라임 비디오',
 'Disney+': '디즈니+', 'ニコニコ': '니코니코', 'YouTube': '유튜브', 'Crunchyroll': '크런치롤', 'Hulu': '훌루', 'FOD': 'FOD', 'Lemino': '레미노', 'DMM TV': 'DMM TV',
 # TMDB(JustWatch)가 쓰는 서비스 이름
 'Amazon Prime Video': '프라임 비디오', 'Disney Plus': '디즈니+', 'wavve': '웨이브', 'Watcha': '왓챠', 'TVING': '티빙', 'Coupang Play': '쿠팡플레이',
 'Apple TV Plus': '애플 TV+', 'Apple TV+': '애플 TV+', 'Laftel': '라프텔', 'Crunchyroll Amazon Channel': '크런치롤', 'Netflix basic with Ads': '넷플릭스(광고형)'}
def station_ko(n): return {'ko': STATION_KO.get(n) or ja_company(n), 'ja': n} if STATION_KO.get(n) else {'ko': ja_company(n) if re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', n) else n, 'ja': n, 'auto': 1}

JOB_KO = {'Designer': '디자이너', 'Character Designer': '캐릭터 디자이너', 'Scriptwriter': '각본가', 'Screenwriter': '각본가', 'Writer': '작가', 'Storyboard Artist': '콘티 작가', 'Voice Actor': '성우', 'Voice Actress': '성우', 'Actor': '배우', 'Actress': '배우', 'Director': '감독', 'Animator': '애니메이터', 'Musician': '음악가',
 'Singer': '가수', 'Composer': '작곡가', 'Lyricist': '작사가', 'Arranger': '편곡가', 'Illustrator': '일러스트레이터', 'Mangaka': '만화가', 'Manga Artist': '만화가',
 'Screenwriter': '각본가', 'Writer': '작가', 'Novelist': '소설가', 'Producer': '프로듀서', 'Character Designer': '캐릭터 디자이너', 'Storyboard Artist': '콘티 작가',
 'Art Director': '미술감독', 'Sound Director': '음향감독', 'Narrator': '내레이터', 'Seiyuu': '성우', 'Band': '밴드', 'Idol': '아이돌', 'Comedian': '코미디언',
 'Author': '작가', 'Game Designer': '게임 디자이너', 'Mechanical Designer': '메카 디자이너', 'Cinematographer': '촬영감독', 'Editor': '편집자', 'Model': '모델', 'Tarento': '탤런트'}
PLACE_KO = {'Japan': '일본', 'Tokyo': '도쿄', 'Osaka': '오사카', 'Kyoto': '교토', 'Hokkaido': '홋카이도', 'Aomori': '아오모리', 'Iwate': '이와테', 'Miyagi': '미야기',
 'Akita': '아키타', 'Yamagata': '야마가타', 'Fukushima': '후쿠시마', 'Ibaraki': '이바라키', 'Tochigi': '도치기', 'Gunma': '군마', 'Saitama': '사이타마', 'Chiba': '지바',
 'Kanagawa': '가나가와', 'Niigata': '니가타', 'Toyama': '도야마', 'Ishikawa': '이시카와', 'Fukui': '후쿠이', 'Yamanashi': '야마나시', 'Nagano': '나가노', 'Gifu': '기후',
 'Shizuoka': '시즈오카', 'Aichi': '아이치', 'Mie': '미에', 'Shiga': '시가', 'Hyogo': '효고', 'Hyōgo': '효고', 'Nara': '나라', 'Wakayama': '와카야마', 'Tottori': '돗토리',
 'Shimane': '시마네', 'Okayama': '오카야마', 'Hiroshima': '히로시마', 'Yamaguchi': '야마구치', 'Tokushima': '도쿠시마', 'Kagawa': '가가와', 'Ehime': '에히메',
 'Kochi': '고치', 'Kōchi': '고치', 'Fukuoka': '후쿠오카', 'Saga': '사가', 'Nagasaki': '나가사키', 'Kumamoto': '구마모토', 'Oita': '오이타', 'Ōita': '오이타',
 'Miyazaki': '미야자키', 'Kagoshima': '가고시마', 'Okinawa': '오키나와', 'Yokohama': '요코하마', 'Nagoya': '나고야', 'Kobe': '고베', 'Sapporo': '삿포로', 'Sendai': '센다이',
 'South Korea': '대한민국', 'Korea': '한국', 'Seoul': '서울', 'Busan': '부산', 'USA': '미국', 'United States': '미국', 'China': '중국', 'Taiwan': '대만', 'Hong Kong': '홍콩',
 'Canada': '캐나다', 'France': '프랑스', 'UK': '영국', 'England': '잉글랜드', 'Germany': '독일', 'Philippines': '필리핀', 'Brazil': '브라질', 'Australia': '호주',
 'California': '캘리포니아', 'New York': '뉴욕', 'Texas': '텍사스', 'Prefecture': '현', 'Ward': '구', 'City': '시',
 'ドイツ': '독일', 'フランス': '프랑스', 'イタリア': '이탈리아', 'イギリス': '영국', 'アメリカ': '미국', 'オーストリア': '오스트리아', 'スイス': '스위스', '台湾': '대만', '韓国': '한국', '中国': '중국'}
def place_ko(s):
    if not s: return s
    if s in PLACE_KO: return PLACE_KO[s]
    if re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', s): return ja_company(s)
    parts = [p.strip() for p in s.split(',')]
    out = []
    for p in parts:
        words = p.split()
        out.append(' '.join(PLACE_KO.get(w) or PLACE_KO.get(w.rstrip('-ken').rstrip('-shi')) or latin_to_hangul(w) for w in words))
    return ', '.join(out)
def date_ko(s):
    p = [x for x in (s or '').split('-') if x]
    return ''.join(f'{int(v)}{u} ' for v, u in zip(p, ('년', '월', '일'))).strip() if p else None


ROMAN = {'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6}
def roman_season(*titles):
    """제목 끝의 로마 숫자 시즌 (「…剣聖になるII」, 「… Kensei ni Naru II」) → 2. 없으면 None."""
    for x in titles:
        m = re.search(r'(?:^|[\s\u3040-\u30ff\u4e00-\u9fff、・:])(II|III|IV|V|VI)$', unicodedata.normalize('NFKC', x or '').strip())
        if m: return ROMAN[m.group(1)]

def season_mark(ja, romaji=None, roman=False):
    """일본어·로마자 제목에서 시즌 표시를 찾아 한국어로 (예: 第2期 第2クール → 2기 2쿨). 없으면 None."""
    t = unicodedata.normalize('NFKC', ja or ''); r = romaji or ''
    def first(pats):
        for src in (t, r):
            for p, f in pats:
                m = re.search(p, src)
                if m and int(m.group(1)) >= 2: return f.format(int(m.group(1)))
    ki = first([(r'第\s*(\d+)\s*期', '{}기'), (r'(\d+)\s*期', '{}기'), (r'(\d+)(?:st|nd|rd|th)\s*[Ss]eason', '{}기'),
                (r'[Ss]eason\s*(\d+)', '{}기'), (r'第\s*(\d+)\s*シーズン', '{}기'), (r'\s(\d{1,2})$', '{}기')])
    cour = first([(r'第\s*(\d+)\s*クール', '{}쿨'), (r'(\d+)\s*クール目', '{}쿨'), (r'[Pp]art\s*(\d+)', '파트 {}'), (r'[Cc]our\s*(\d+)', '{}쿨')])
    bu = first([(r'第\s*(\d+)\s*部', '{}부')])
    if not cour and re.search(r'(後編|後半)', t): cour = '2쿨'
    if not ki and roman and roman_season(ja, romaji): ki = f'{roman_season(ja, romaji)}기'      # 로마 숫자는 이전 시즌이 있을 때만 (「ストリートファイターII」 같은 원작 제목과 구분)
    marks = [x for x in (ki, bu, cour) if x]
    if not marks and re.search(r'(完結編|最終章|ファイナルシーズン|[Ff]inal [Ss]eason)', t + ' ' + r): marks = ['파이널']
    return ' '.join(marks) or None

def season_code(ja, romaji=None, en=None, roman=False):
    """제목 속 시즌·쿨 표시를 짧은 부호로 (예: 第3期 → s3, 3rd Season Part 2 → s3c2, 第2クール → c2, 完結編 → f). 없으면 None.
    사이트는 이 부호로 제목 뒤에 「3기」 「2쿨」 같은 꼬리표를 붙이고, 제목에서는 그 표시를 뺍니다."""
    t = unicodedata.normalize('NFKC', ja or ''); r = ' '.join(x for x in (romaji, en) if x)
    def first(pats):
        for src in (t, r):
            for p in pats:
                m = re.search(p, src)
                if m and int(m.group(1)) >= 2: return int(m.group(1))
    s = first([r'第\s*(\d+)\s*期', r'(\d+)\s*期', r'(\d+)(?:st|nd|rd|th)\s*[Ss]eason', r'[Ss]eason\s*(\d+)', r'第\s*(\d+)\s*シーズン'])
    if not s:      # 「地獄楽 第二期」처럼 한자 숫자
        m = re.search(r'第([二三四五六七八九十])期', t)
        if m: s = '二三四五六七八九十'.index(m.group(1)) + 2
    s = s or (roman_season(ja, romaji, en) if roman else None)
    c = first([r'[第割]\s*(\d+)\s*クール', r'(\d+)\s*クール目', r'[Pp]art\s*(\d+)', r'[Cc]our\s*(\d+)'])
    b = first([r'第\s*(\d+)\s*部'])
    out = (f's{s}' if s else '') + (f'b{b}' if b else '') + (f'c{c}' if c else '')
    if not out and re.search(r'(完結編|最終章|ファイナルシーズン|[Ff]inal [Ss]eason)', t + ' ' + r): out = 'f'
    return out or None

ARC = re.compile(r'(?:^|[\s　・])([\u4e00-\u9fff々]{1,10}[編篇章])$')
def add_arc(ko, ja):
    """원제 끝의 「三天戦争編」 같은 편 이름이 한국어 제목에 없으면, 한자를 한국 한자음으로 읽어 덧붙임 (도쿄 리벤저스 → 도쿄 리벤저스 삼천전쟁편).
    가나가 섞인 편 이름(「刀鍛冶の里編」 등)은 읽기가 틀리기 쉬워 붙이지 않음."""
    if not ko or not ja: return ko
    m = ARC.search(unicodedata.normalize('NFKC', ja).strip())
    if not m: return ko
    try: import hanja
    except ImportError: return ko
    rd = hanja.translate(m.group(1), 'substitution')
    if re.search(r'[\u4e00-\u9fff]', rd): return ko
    # 두음 법칙과 같은 「렬·률 → 열·율」(모음이나 ㄴ 받침 뒤)
    out = ''
    for i, ch in enumerate(rd):
        if ch in '렬률' and i > 0 and '가' <= rd[i - 1] <= '힣' and ((ord(rd[i - 1]) - 0xAC00) % 28) in (0, 4): ch = {'렬': '열', '률': '율'}[ch]
        out += ch
    if out in ko.replace(' ', ''): return ko
    return f'{ko} {out}'

def add_season(ko, ja, romaji=None, roman=False):
    """한국어 제목에 시즌 표시가 없고 원제에는 있으면 덧붙임 (예: 정반대의 너와 나 + 2기)."""
    if not ko: return ko
    if re.search(r'(\d|기|시즌|쿨|부\b|파트|[Ss]eason|[Pp]art|파이널|완결)', ko): return ko
    m = season_mark(ja, romaji, roman)
    return f'{ko} {m}' if m else ko

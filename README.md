# dopedev-legal

도프데브(dopedev) 앱의 공개 개인정보처리방침과 지원 페이지(GitHub Pages, main 가지 루트).

- `birthday-adventure/privacy.html` — 오늘은 네가 주인공: 생일별 모험 개인정보처리방침 (iPhone·iPad 부분: `#ios`)
- `birthday-adventure/support.html` — 앱 지원

이 저장소에는 공개 페이지만 둡니다. 원본은 비공개 저장소에 있으며, 고칠 때는 원본을 고친 뒤 다시 만들어 올립니다.
- `birthday-adventure/blog/` — 블로그 ‘로로의 생일별 모험’ (글 목록, 글, `feed.xml`). 루트 `sitemap.xml`도 함께 만들어짐

## 블로그 글 올리기

1. `birthday-adventure/blog/_src/`에 `날짜-주소.txt` 원고를 만든다(기존 원고를 복사해 머리 줄만 바꾸면 됨).
   - 머리 줄: `title`, `slug`(주소, 영문-소문자), `date`(YYYY-MM-DD), `time`(같은 날 여러 편일 때 순서), `category`(`생일 이벤트 아이디어` 또는 `앱 소식`), `description`(검색·공유용 한두 문장), `tags`(쉼표로)
   - `---` 아래가 본문. 빈 줄 = 문단 사이, `■ ` = 소제목, `1. ` = 번호 목록, `- ` = 점 목록, `Q. 질문 — 답` = 묻고 답하기, `만든 사람:` = 글쓴이 줄, 주소는 자동 링크.
2. `python3 birthday-adventure/blog/_tools/build.py` 실행(외부 패키지 필요 없음). 글 페이지·목록·카테고리·`feed.xml`·루트 `sitemap.xml`이 다시 만들어진다.
3. 커밋해서 main에 올리면 몇 분 뒤 GitHub Pages에 보인다.

블로그에는 광고·분석·추적 스크립트를 넣지 않는다. 제목 글꼴은 저장소 안의 `assets/nanum-pen.woff2`(나눔손글씨 펜, OFL, 자주 쓰는 한글 2,350자)를 쓴다.

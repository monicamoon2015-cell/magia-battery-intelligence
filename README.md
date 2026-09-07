# MAG IA Battery Intelligence

이 버전은 로컬 Python 설치가 필요 없습니다.

## 처음 한 번만 설정
1. GitHub 로그인 후 새 Repository를 생성합니다. (예: `magia-battery-intelligence`)
2. 이 ZIP 안의 파일들을 Repository에 업로드합니다.
3. Repository의 **Settings → Pages**로 이동합니다.
4. **Build and deployment → Source = Deploy from a branch**
5. Branch를 `main` / `/ (root)`로 선택하고 Save 합니다.
6. **Actions** 탭에서 `Update battery news`를 열고 **Run workflow**를 한 번 실행합니다.
7. 약 1~3분 후 `data.json`이 업데이트됩니다.
8. Settings → Pages에 표시되는 `https://사용자명.github.io/magia-battery-intelligence/` 주소로 접속합니다.

이후 GitHub가 약 6시간마다 자동으로 뉴스를 갱신합니다.

## 수집 키워드
CATL, BYD, LG Energy Solution, LG Chem, POSCO Future M, EcoPro, L&F,
LFP, NCM, lithium, critical minerals, magnetic impurity, quality control,
contamination, SNE Research.

## 참고
현재 수집기는 Google News RSS 검색 결과의 제목/출처/날짜/링크만 저장합니다.
기사 본문은 저장하지 않습니다.

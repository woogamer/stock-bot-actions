# 주식 봇 (GitHub Actions 간단 버전)

서버 없이, GitHub 가 **평일 아침 9시 10분에 한 번** 봇을 실행해주는 한국투자증권 **모의투자** 봇입니다.
노트북을 꺼도 돌아가고, 비용은 0원입니다.

## 가장 쉬운 방법

노트북의 Claude(데스크톱 앱 Code 탭 또는 Claude Code)에 이렇게 보내면 아래 세팅을 Claude 가 대신 합니다.

```
https://guide.woogamer.win/claude.md 를 읽고 그대로 나를 도와서 주식 봇 세팅을 끝까지 해줘.
```

## 직접 세팅 (10분)

1. 이 페이지 오른쪽 위 **Use this template** → **Create a new repository** → 이름 입력, **Private** 선택 → Create
2. 만든 저장소에서 **Settings** → **Secrets and variables** → **Actions** → **New repository secret** 으로 3개 등록

   | Name | 값 |
   |---|---|
   | `KIS_APP_KEY` | 한국투자증권 KIS Developers 에서 받은 모의투자 앱키 |
   | `KIS_APP_SECRET` | 모의투자 앱시크릿 |
   | `KIS_ACCOUNT_NO` | 모의투자 계좌번호 (예: 50123456-01) |

3. **Actions** 탭 → 왼쪽 **주식 봇** → **Run workflow** → 초록 버튼
4. 1분 뒤 실행 기록을 눌러 `python bot.py` 줄을 펼치면 결과가 보입니다

```
모드: 조회만 (주문 안 함)
예수금: 10,000,000원 / 보유 종목: 0개

  삼성전자(005930) 현재가 ... → 대기
```

## 카카오톡으로 결과 받기 (선택)

매일 실행이 끝나면 결과 요약이 내 카톡 "나와의 채팅"으로 옵니다. Secrets 에 3개를 더 등록하면 됩니다.

| Name | 값 |
|---|---|
| `KAKAO_REST_KEY` | 카카오 개발자 앱의 REST API 키 |
| `KAKAO_CLIENT_SECRET` | REST API 키의 클라이언트 시크릿 |
| `KAKAO_REFRESH_TOKEN` | 카카오 로그인 후 받은 리프레시 토큰 (Claude 에게 받아달라고 하세요) |

카카오 로그인은 **60일마다** 다시 해서 `KAKAO_REFRESH_TOKEN` 을 바꿔줘야 합니다. 한 달 이하로 남으면 실행 기록에 경고가 뜹니다.

## 처음엔 "조회만" 합니다

기본값은 주문을 넣지 않고 "이 조건이면 샀을 것" 만 보여줍니다.
며칠 지켜보고 괜찮으면 **Settings → Secrets and variables → Actions → Variables** 탭에서
`ORDER_MODE` 를 `on` 으로 만드세요. 그때부터 모의투자 계좌에 실제 주문이 들어갑니다.

## 전략 바꾸기

`bot.py` 의 "전략" 부분(관심 종목, 매수·매도 조건)만 고치면 됩니다.
Claude 에게 "이 저장소 bot.py 의 전략을 ○○ 으로 바꿔줘" 라고 부탁해도 됩니다.

## 한계

- 하루 한 번(원하면 몇 번) 정해진 시각에 확인하는 전략에 맞습니다. 장중 내내 시세를 지켜보는 전략은 서버가 필요합니다.
- GitHub 예약 실행은 몇 분씩 늦어질 수 있습니다.
- 모의투자 전용입니다. 실계좌로 바꾸지 마세요.

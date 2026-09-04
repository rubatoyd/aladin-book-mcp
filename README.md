# 알라딘(Aladin) 도서 검색 및 상세 서지 MCP 서버

<!-- mcp-name: io.github.rubatoyd/aladin-book-mcp -->

[![CI](https://github.com/rubatoyd/aladin-book-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/rubatoyd/aladin-book-mcp/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/rubatoyd/aladin-book-mcp?color=blue)](https://github.com/rubatoyd/aladin-book-mcp/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/rubatoyd/aladin-book-mcp/total?label=downloads&color=blue)](https://github.com/rubatoyd/aladin-book-mcp/releases)

<!-- usage:start -->
> 📈 **사용량** — 최근 14일 조회 **0**회(고유 0) · 클론 **0**회(고유 0) · 릴리스 자산 누적 다운로드 **1**
>
> ![일별 클론·조회 추이](docs/usage.svg)
>
> <sub>2026-09-04 자동 갱신 · 전체 이력은 [`docs/usage.csv`](docs/usage.csv). GitHub 트래픽 통계는 14일 창만 제공하므로 이 저장소가 매일 찍어 누적한다.</sub>
<!-- usage:end -->

**알라딘(Aladin) Open API**를 활용하여 도서 검색, **원서명(원제), 전체 목차(TOC), 쪽수(페이지 수), 판형/무게, 부제, 베스트셀러 순위, 중고서점 매물 및 최저가**를 조회하고 엑셀/CSV 등으로 일괄 수집하는 Model Context Protocol (MCP) 서버 및 독립 CLI 도구입니다.

---

## 주요 기능

* 🔍 **도서 검색 (`aladin_book_search`)**: 키워드, 제목, 저자, 출판사별 통합 검색 (`ItemSearch`)
* 📖 **심층 서지 조회 (`aladin_book_lookup`)**: 13자리/10자리 ISBN 또는 상품ID로 **원서명, 도서 목차, 쪽수, 제본/무게/크기, 중고매물 최저가, eBook 연동 정보** 조회
* 🏆 **큐레이션 리스트 (`aladin_book_list`)**: 알라딘 **베스트셀러, 신간, 편집장 추천도서, 블로거 베스트** 목록 조회
* 📦 **다중 키워드 대량 수집 (`aladin_book_collect`)**: 여러 검색어를 한 번에 자동 페이징 수집하고, 중복 제거 후 `xlsx`, `csv`, `json`, `sqlite` 동시 저장
* 💻 **독립형 터미널 CLI (`aladin`)**: AI 에이전트 없이도 터미널에서 즉시 검색 및 엑셀 다운로드 지원

---

## 인증키 발급 및 설정 (1분 소요, 무료)

알라딘 OpenAPI는 **무료이며 TTB Key 발급 즉시 사용**할 수 있습니다 (일일 5,000건 쿼터 제공).

### 1. TTB Key 발급 방법
1. [알라딘 (aladin.co.kr)](https://www.aladin.co.kr) 로그인
2. [알라딘 OpenAPI 안내 및 TTBKey 발급 페이지](https://blog.aladin.co.kr/openapi/6695306) 접속
3. API를 사용할 블로그나 사이트 정보 등록 후 발급된 **`TTB Key`** (예: `ttb...`) 복사

### 2. 환경별 키 등록 방법

| 사용 환경 | 설정 위치 | 설정 방법 |
| :--- | :--- | :--- |
| **Claude Desktop (`.mcpb`)** | 확장 설치 시 팝업창 | `.mcpb` 파일을 드래그 앤 드롭 후 나타나는 입력창에 TTB Key 입력 |
| **Claude Code** | `claude mcp add` | `--env ALADIN_TTB_KEY=YOUR_TTB_KEY` 옵션으로 전달 |
| **Antigravity / Gemini CLI** | `mcp_config.json` | `env.ALADIN_TTB_KEY` 항목에 설정 |
| **CLI / 로컬 개발** | OS 환경변수 / `.env` | Windows 환경변수 등록 또는 `.env`에 `ALADIN_TTB_KEY=...` 작성 |

---

## 설치 및 MCP 등록

### 1. Claude Desktop (1-클릭 확장 파일)
* [Releases](https://github.com/rubatoyd/aladin-book-mcp/releases)에서 **`aladin-book-mcp.mcpb`**를 다운로드하여 Claude Desktop 창으로 드래그 앤 드롭합니다.

### 2. Claude Code
```bash
claude mcp add aladin-book --env ALADIN_TTB_KEY=YOUR_TTB_KEY -- uvx --from git+https://github.com/rubatoyd/aladin-book-mcp aladin-book-mcp
```

### 3. Gemini CLI / Antigravity
프로젝트 루트의 `.agents/mcp_config.json` 또는 전역 `~/.gemini/config/mcp_config.json`:
```json
{
  "mcpServers": {
    "aladin-book": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/rubatoyd/aladin-book-mcp", "aladin-book-mcp"],
      "env": {
        "ALADIN_TTB_KEY": "YOUR_ALADIN_TTB_KEY",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

---

## CLI 도구 사용법 (`aladin`)

```bash
# 1. 상태 점검
uvx --from git+https://github.com/rubatoyd/aladin-book-mcp aladin status

# 2. 키워드 검색
uvx --from git+https://github.com/rubatoyd/aladin-book-mcp aladin search "인공지능" --size 5

# 3. ISBN13 상세 조회 (원서명, 목차, 쪽수, 판형, 중고가)
uvx --from git+https://github.com/rubatoyd/aladin-book-mcp aladin lookup 9791163034735

# 4. 베스트셀러 목록 조회
uvx --from git+https://github.com/rubatoyd/aladin-book-mcp aladin list --type Bestseller --size 10

# 5. 다중 키워드 대량 자동 수집 및 엑셀 저장 (상세 LookUp 포함)
uvx --from git+https://github.com/rubatoyd/aladin-book-mcp aladin collect \
  --terms "머신러닝" "딥러닝" \
  --max 50 \
  --lookup \
  --format xlsx csv json sqlite \
  --out ./output
```

---

## 라이선스
MIT License © 2026 Yeondong Yang

"""HTTP Client for Aladin OpenAPI."""

from __future__ import annotations
import time
import httpx
from typing import List, Dict, Any, Optional
from .config import (
    get_ttb_key,
    API_SEARCH_URL,
    API_LOOKUP_URL,
    API_LIST_URL,
    API_VERSION,
)
from .models import (
    AladinBookItem,
    AladinSearchResult,
    AladinLookUpResult,
    AladinListResult,
    AladinStatusResult,
)


class AladinApiError(Exception):
    """Exception raised for Aladin API errors."""
    def __init__(self, message: str, error_code: Optional[int] = None):
        super().__init__(message)
        self.error_code = error_code


class AladinBookClient:
    """Client for querying Aladin OpenAPI."""

    def __init__(self, ttb_key: Optional[str] = None, timeout: float = 15.0):
        self.ttb_key = (ttb_key or get_ttb_key()).strip()
        self.timeout = timeout
        self._client = httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "AladinBookMCP/0.1.0 (https://github.com/rubatoyd/aladin-book-mcp)",
                "Accept": "application/json, text/javascript",
            },
        )

    def is_configured(self) -> bool:
        return bool(self.ttb_key)

    def mask_key(self) -> str:
        if not self.ttb_key:
            return "(미설정)"
        if len(self.ttb_key) <= 6:
            return "***"
        return f"{self.ttb_key[:3]}...{self.ttb_key[-2:]}"

    def status_probe(self) -> AladinStatusResult:
        """Probe Aladin API connectivity and validate TTBKey."""
        if not self.is_configured():
            return AladinStatusResult(
                configured=False,
                key_masked="(미설정)",
                probe_ok=False,
                probe_message="ALADIN_TTB_KEY 환경변수가 설정되지 않았습니다.",
                probe_latency_ms=0.0,
            )

        t0 = time.perf_counter()
        try:
            res = self.search(query="파이썬", max_results=1)
            latency = (time.perf_counter() - t0) * 1000
            return AladinStatusResult(
                configured=True,
                key_masked=self.mask_key(),
                probe_ok=True,
                probe_message=f"정상 연결 (검색 성공: 총 {res.totalResults:,}건 중 1건 확인)",
                probe_latency_ms=round(latency, 1),
            )
        except Exception as e:
            latency = (time.perf_counter() - t0) * 1000
            return AladinStatusResult(
                configured=True,
                key_masked=self.mask_key(),
                probe_ok=False,
                probe_message=f"호출 실패: {str(e)}",
                probe_latency_ms=round(latency, 1),
            )

    def search(
        self,
        query: str,
        query_type: str = "Keyword",
        search_target: str = "Book",
        start: int = 1,
        max_results: int = 10,
        sort: str = "Accuracy",
        category_id: Optional[int] = None,
    ) -> AladinSearchResult:
        """Search books on Aladin."""
        if not self.is_configured():
            raise AladinApiError("ALADIN_TTB_KEY가 설정되지 않았습니다.")

        # Aladin MaxResults max is 100, start max is usually 100 (some docs mention max results overall 1000)
        start = max(1, min(start, 100))
        max_results = max(1, min(max_results, 100))

        params: Dict[str, Any] = {
            "ttbkey": self.ttb_key,
            "Query": query,
            "QueryType": query_type,
            "SearchTarget": search_target,
            "Start": start,
            "MaxResults": max_results,
            "Sort": sort,
            "output": "js",
            "Version": API_VERSION,
        }
        if category_id is not None:
            params["CategoryId"] = category_id

        resp = self._client.get(API_SEARCH_URL, params=params)
        if resp.status_code != 200:
            raise AladinApiError(f"HTTP {resp.status_code}: {resp.text[:200]}")

        try:
            data = resp.json()
        except Exception as e:
            raise AladinApiError(f"응답 JSON 파싱 실패: {resp.text[:200]}") from e

        if "errorCode" in data:
            raise AladinApiError(f"[{data.get('errorCode')}] {data.get('errorMessage')}")

        total_results = int(data.get("totalResults", 0))
        items_raw = data.get("item", [])
        items = [AladinBookItem.model_validate(it) for it in items_raw]

        # Aladin max accessible items via pagination is 1,000
        truncated = total_results > 1000
        cap_hit = (start * max_results) >= min(total_results, 1000)

        return AladinSearchResult(
            query=query,
            totalResults=total_results,
            startIndex=int(data.get("startIndex", start)),
            itemsPerPage=int(data.get("itemsPerPage", len(items))),
            truncated=truncated,
            cap_hit=cap_hit,
            items=items,
        )

    def lookup(
        self,
        item_id: str,
        item_id_type: str = "ISBN13",
        opt_result: str = "ebookList,usedList,subInfo,packing",
    ) -> AladinLookUpResult:
        """Lookup item details including TOC, original title, pages, packing, used books, and ebooks."""
        if not self.is_configured():
            raise AladinApiError("ALADIN_TTB_KEY가 설정되지 않았습니다.")

        item_id = str(item_id).strip().replace("-", "")

        # Auto-detect itemIdType if ISBN format
        if item_id_type not in ("ISBN13", "ISBN", "ItemId"):
            if len(item_id) == 13:
                item_id_type = "ISBN13"
            elif len(item_id) == 10:
                item_id_type = "ISBN"
            else:
                item_id_type = "ItemId"

        params: Dict[str, Any] = {
            "ttbkey": self.ttb_key,
            "ItemIdType": item_id_type,
            "ItemId": item_id,
            "output": "js",
            "Version": API_VERSION,
            "OptResult": opt_result,
        }

        resp = self._client.get(API_LOOKUP_URL, params=params)
        if resp.status_code != 200:
            raise AladinApiError(f"HTTP {resp.status_code}: {resp.text[:200]}")

        try:
            data = resp.json()
        except Exception as e:
            raise AladinApiError(f"응답 JSON 파싱 실패: {resp.text[:200]}") from e

        if "errorCode" in data:
            raise AladinApiError(f"[{data.get('errorCode')}] {data.get('errorMessage')}")

        items_raw = data.get("item", [])
        items = [AladinBookItem.model_validate(it) for it in items_raw]

        return AladinLookUpResult(
            itemId=item_id,
            items=items,
        )

    def list_items(
        self,
        query_type: str = "Bestseller",
        search_target: str = "Book",
        start: int = 1,
        max_results: int = 10,
        category_id: Optional[int] = None,
    ) -> AladinListResult:
        """Get curated book lists (Bestseller, ItemNewAll, ItemNewSpecial, ItemEditorChoice, BlogBest)."""
        if not self.is_configured():
            raise AladinApiError("ALADIN_TTB_KEY가 설정되지 않았습니다.")

        start = max(1, min(start, 100))
        max_results = max(1, min(max_results, 100))

        params: Dict[str, Any] = {
            "ttbkey": self.ttb_key,
            "QueryType": query_type,
            "SearchTarget": search_target,
            "Start": start,
            "MaxResults": max_results,
            "output": "js",
            "Version": API_VERSION,
        }
        if category_id is not None:
            params["CategoryId"] = category_id

        resp = self._client.get(API_LIST_URL, params=params)
        if resp.status_code != 200:
            raise AladinApiError(f"HTTP {resp.status_code}: {resp.text[:200]}")

        try:
            data = resp.json()
        except Exception as e:
            raise AladinApiError(f"응답 JSON 파싱 실패: {resp.text[:200]}") from e

        if "errorCode" in data:
            raise AladinApiError(f"[{data.get('errorCode')}] {data.get('errorMessage')}")

        total_results = int(data.get("totalResults", 0))
        items_raw = data.get("item", [])
        items = [AladinBookItem.model_validate(it) for it in items_raw]

        return AladinListResult(
            queryType=query_type,
            totalResults=total_results,
            startIndex=int(data.get("startIndex", start)),
            itemsPerPage=int(data.get("itemsPerPage", len(items))),
            items=items,
        )

    def collect(
        self,
        terms: List[str],
        max_per_term: int = 50,
        query_type: str = "Keyword",
        search_target: str = "Book",
        sort: str = "Accuracy",
        opt_lookup: bool = False,
    ) -> List[AladinBookItem]:
        """Collect books across multiple search terms with auto-pagination and deduplication."""
        collected: Dict[str, AladinBookItem] = {}

        for term in terms:
            term = term.strip()
            if not term:
                continue

            fetched_for_term = 0
            page = 1
            page_size = min(max_per_term, 50)

            while fetched_for_term < max_per_term and page <= 10:
                cur_limit = min(page_size, max_per_term - fetched_for_term)
                res = self.search(
                    query=term,
                    query_type=query_type,
                    search_target=search_target,
                    start=page,
                    max_results=cur_limit,
                    sort=sort,
                )

                if not res.items:
                    break

                for item in res.items:
                    # Lookup extra info if requested
                    if opt_lookup and (item.isbn13 or item.itemId):
                        try:
                            lk = self.lookup(item.isbn13 or str(item.itemId))
                            if lk.items:
                                item = lk.items[0]
                        except Exception:
                            pass

                    # Unique identifier key
                    key = item.isbn13 or item.isbn or str(item.itemId) or item.title
                    if key and key not in collected:
                        collected[key] = item

                fetched_for_term += len(res.items)
                if res.cap_hit or len(res.items) < cur_limit:
                    break

                page += 1

        return list(collected.values())


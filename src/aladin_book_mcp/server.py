"""FastMCP Server exposing 5 Aladin OpenAPI tools."""

from __future__ import annotations
from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from .client import AladinBookClient
from .exporters import export_data


mcp = FastMCP("aladin-book-mcp")


@mcp.tool()
def aladin_book_status() -> dict:
    """인증키 상태 점검 및 알라딘 Open API 실제 왕복 1회 연결 상태를 점검합니다."""
    client = AladinBookClient()
    res = client.status_probe()
    return res.model_dump()


@mcp.tool()
def aladin_book_search(
    query: str,
    query_type: str = "Keyword",
    search_target: str = "Book",
    start: int = 1,
    max_results: int = 10,
    sort: str = "Accuracy",
    category_id: Optional[int] = None,
) -> dict:
    """알라딘 Open API로 도서를 검색합니다.

    Args:
        query: 검색어 (도서명, 저자명, 출판사, 키워드 등)
        query_type: 검색 대상 필드 ('Keyword', 'Title', 'Author', 'Publisher')
        search_target: 검색 카테고리 ('Book', 'Foreign', 'Music', 'DVD', 'Used', 'eBook', 'All')
        start: 시작 페이지 번호 (1~100)
        max_results: 1회 출력 건수 (1~100)
        sort: 정렬 순서 ('Accuracy', 'PublishTime', 'Title', 'SalesPoint', 'CustomerRating')
        category_id: 특정 알라딘 카테고리 ID 필터 (선택)
    """
    client = AladinBookClient()
    res = client.search(
        query=query,
        query_type=query_type,
        search_target=search_target,
        start=start,
        max_results=max_results,
        sort=sort,
        category_id=category_id,
    )
    return res.model_dump()


@mcp.tool()
def aladin_book_lookup(
    item_id: str,
    item_id_type: str = "ISBN13",
    opt_result: str = "ebookList,usedList,subInfo,packing",
) -> dict:
    """ISBN13 또는 상품ID로 특정 도서의 원서명, 목차, 쪽수, 판형, 부제, 중고가, 전자책 상세 정보를 조회합니다.

    Args:
        item_id: 13자리 ISBN, 10자리 ISBN, 또는 알라딘 ItemId
        item_id_type: 식별자 타입 ('ISBN13', 'ISBN', 'ItemId' - 미지정시 길이로 자동 감지)
        opt_result: 부가 정보 요청 플래그 (기본: 'ebookList,usedList,subInfo,packing')
    """
    client = AladinBookClient()
    res = client.lookup(
        item_id=item_id,
        item_id_type=item_id_type,
        opt_result=opt_result,
    )
    return res.model_dump()


@mcp.tool()
def aladin_book_list(
    query_type: str = "Bestseller",
    search_target: str = "Book",
    start: int = 1,
    max_results: int = 10,
    category_id: Optional[int] = None,
) -> dict:
    """알라딘 베스트셀러, 신간, 추천도서 등 큐레이션 리스트를 조회합니다.

    Args:
        query_type: 리스트 종류 ('Bestseller', 'ItemNewAll', 'ItemNewSpecial', 'ItemEditorChoice', 'BlogBest')
        search_target: 대상 카테고리 ('Book', 'Foreign', 'Music', 'DVD', 'Used', 'eBook', 'All')
        start: 시작 페이지 번호 (1~100)
        max_results: 출력 건수 (1~100)
        category_id: 특정 카테고리 ID 필터 (선택)
    """
    client = AladinBookClient()
    res = client.list_items(
        query_type=query_type,
        search_target=search_target,
        start=start,
        max_results=max_results,
        category_id=category_id,
    )
    return res.model_dump()


@mcp.tool()
def aladin_book_collect(
    terms: List[str],
    max_items_per_term: int = 30,
    query_type: str = "Keyword",
    search_target: str = "Book",
    sort: str = "Accuracy",
    opt_lookup: bool = False,
    export_dir: Optional[str] = None,
    export_formats: Optional[List[str]] = None,
) -> dict:
    """다중 검색어로 도서를 대량 수집하고, 중복 제거 후 xlsx, csv, json, sqlite 파일로 저장합니다.

    Args:
        terms: 수집할 검색어 목록 (예: ['인공지능', '머신러닝'])
        max_items_per_term: 검색어당 최대 수집 건수 (기본 30)
        query_type: 검색 필드 ('Keyword', 'Title', 'Author', 'Publisher')
        search_target: 검색 대상 ('Book', 'eBook', 'All' 등)
        sort: 정렬 순서 ('Accuracy', 'PublishTime', 'SalesPoint')
        opt_lookup: True 설정 시 각 도서별 목차/원서명/쪽수 상세 정보(ItemLookUp)까지 추가 조회
        export_dir: 파일 저장 폴더 경로 (미지정 시 파일 저장 안 함)
        export_formats: 저장 포맷 리스트 (['xlsx', 'csv', 'json', 'sqlite'] 중 선택)
    """
    client = AladinBookClient()
    items = client.collect(
        terms=terms,
        max_per_term=max_items_per_term,
        query_type=query_type,
        search_target=search_target,
        sort=sort,
        opt_lookup=opt_lookup,
    )

    saved_files = {}
    if export_dir and items:
        saved_files = export_data(
            items=items,
            output_dir=export_dir,
            base_name="aladin_collected_books",
            formats=export_formats or ["xlsx", "csv", "json"],
        )

    return {
        "terms": terms,
        "total_collected": len(items),
        "saved_files": saved_files,
        "sample_items": [it.model_dump() for it in items[:5]],
    }


def main():
    mcp.run()


if __name__ == "__main__":
    main()

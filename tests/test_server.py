from unittest.mock import patch, MagicMock
from aladin_book_mcp.server import (
    aladin_book_status,
    aladin_book_search,
    aladin_book_lookup,
    aladin_book_list,
    aladin_book_collect,
)


def test_server_status():
    res = aladin_book_status()
    assert "configured" in res
    assert "key_masked" in res
    assert "probe_ok" in res


def test_server_search_mock():
    mock_search_res = MagicMock()
    mock_search_res.model_dump.return_value = {
        "query": "파이썬",
        "totalResults": 1,
        "items": [{"title": "테스트 도서"}]
    }

    with patch("aladin_book_mcp.server.AladinBookClient.search", return_value=mock_search_res):
        out = aladin_book_search(query="파이썬")
        assert out["query"] == "파이썬"
        assert out["totalResults"] == 1


def test_server_lookup_mock():
    mock_lookup_res = MagicMock()
    mock_lookup_res.model_dump.return_value = {
        "itemId": "9781234567890",
        "items": [{"title": "상세 도서", "subInfo": {"itemPage": 300}}]
    }

    with patch("aladin_book_mcp.server.AladinBookClient.lookup", return_value=mock_lookup_res):
        out = aladin_book_lookup(item_id="9781234567890")
        assert out["itemId"] == "9781234567890"


def test_server_list_mock():
    mock_list_res = MagicMock()
    mock_list_res.model_dump.return_value = {
        "queryType": "Bestseller",
        "totalResults": 10,
        "items": []
    }

    with patch("aladin_book_mcp.server.AladinBookClient.list_items", return_value=mock_list_res):
        out = aladin_book_list(query_type="Bestseller")
        assert out["queryType"] == "Bestseller"

from unittest.mock import patch, MagicMock
from aladin_book_mcp.client import AladinBookClient


def test_client_configured():
    client = AladinBookClient(ttb_key="ttbtestkey1234")
    assert client.is_configured() is True
    assert client.mask_key() == "ttb...34"


def test_client_search_mock():
    client = AladinBookClient(ttb_key="ttbtestkey1234")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "version": "20131101",
        "totalResults": 1,
        "startIndex": 1,
        "itemsPerPage": 10,
        "item": [
            {
                "title": "모의 도서",
                "author": "모의 저자",
                "isbn13": "9781234567890",
                "priceSales": 10000,
            }
        ]
    }

    with patch.object(client._client, "get", return_value=mock_resp):
        res = client.search(query="파이썬")
        assert res.totalResults == 1
        assert len(res.items) == 1
        assert res.items[0].title == "모의 도서"


def test_client_lookup_mock():
    client = AladinBookClient(ttb_key="ttbtestkey1234")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "item": [
            {
                "title": "상세 도서",
                "isbn13": "9781234567890",
                "subInfo": {
                    "originalTitle": "Mock Original",
                    "itemPage": 450,
                    "toc": "목차 내용"
                }
            }
        ]
    }

    with patch.object(client._client, "get", return_value=mock_resp):
        res = client.lookup(item_id="9781234567890")
        assert len(res.items) == 1
        assert res.items[0].subInfo.originalTitle == "Mock Original"
        assert res.items[0].subInfo.itemPage == 450

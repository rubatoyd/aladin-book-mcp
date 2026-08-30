from aladin_book_mcp.models import (
    AladinBookItem,
    SubInfo,
    PackingInfo,
    UsedList,
    UsedShopDetail,
    AladinSearchResult,
    AladinLookUpResult,
    AladinListResult,
)


def test_models_parsing():
    raw_item = {
        "title": "테스트 도서",
        "link": "https://aladin.co.kr/test",
        "author": "홍길동 (지은이)",
        "pubDate": "2024-01-01",
        "description": "설명",
        "isbn": "1234567890",
        "isbn13": "9781234567890",
        "itemId": 999999,
        "priceSales": 18000,
        "priceStandard": 20000,
        "mileage": 1000,
        "cover": "https://image.aladin.co.kr/test.jpg",
        "categoryName": "국내도서>컴퓨터",
        "publisher": "테스트출판",
        "salesPoint": 5000,
        "adult": False,
        "fixedPrice": True,
        "customerReviewRank": 9,
        "seriesInfo": {
            "seriesId": 123,
            "seriesName": "테스트 시리즈",
        },
        "subInfo": {
            "subTitle": "부제목",
            "originalTitle": "Original Title",
            "itemPage": 300,
            "toc": "1장. 시작하기\n2장. 활용하기",
            "packing": {
                "styleDesc": "반양장본",
                "weight": 500,
                "sizeWidth": 150,
                "sizeHeight": 220,
            },
            "usedList": {
                "userUsed": {"itemCount": 5, "minPrice": 12000}
            },
            "ebookList": [
                {"itemId": 888888, "isbn13": "9791111111111", "priceSales": 14000}
            ]
        }
    }

    item = AladinBookItem.model_validate(raw_item)
    assert item.title == "테스트 도서"
    assert item.subInfo.originalTitle == "Original Title"
    assert item.subInfo.itemPage == 300
    assert item.subInfo.packing.styleDesc == "반양장본"
    assert item.subInfo.usedList.userUsed.itemCount == 5
    assert len(item.subInfo.ebookList) == 1
    assert item.seriesInfo.seriesName == "테스트 시리즈"

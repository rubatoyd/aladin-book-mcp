import json
import sqlite3
import pandas as pd
from pathlib import Path
from aladin_book_mcp.models import AladinBookItem, SubInfo, PackingInfo
from aladin_book_mcp.exporters import export_data


def test_export_data(tmp_path: Path):
    item = AladinBookItem(
        title="수출 도서",
        author="저자",
        publisher="출판사",
        pubDate="2024-01-01",
        isbn13="9781234567890",
        priceSales=15000,
        subInfo=SubInfo(
            originalTitle="Export Book",
            itemPage=320,
            packing=PackingInfo(styleDesc="양장본", weight=600),
        )
    )

    saved = export_data(
        items=[item],
        output_dir=tmp_path,
        base_name="test_books",
        formats=["xlsx", "csv", "json", "sqlite"]
    )

    assert "xlsx" in saved and Path(saved["xlsx"]).exists()
    assert "csv" in saved and Path(saved["csv"]).exists()
    assert "json" in saved and Path(saved["json"]).exists()
    assert "sqlite" in saved and Path(saved["sqlite"]).exists()

    # Verify JSON
    with open(saved["json"], "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["title"] == "수출 도서"

    # Verify SQLite
    conn = sqlite3.connect(saved["sqlite"])
    df = pd.read_sql("SELECT * FROM books", conn)
    conn.close()
    assert len(df) == 1
    assert df.iloc[0]["originalTitle"] == "Export Book"
    assert df.iloc[0]["itemPage"] == 320

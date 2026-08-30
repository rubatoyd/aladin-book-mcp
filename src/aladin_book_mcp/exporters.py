"""Export utilities for Aladin book collections."""

from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Union
import pandas as pd
from .models import AladinBookItem


def items_to_dicts(items: List[AladinBookItem]) -> List[Dict[str, Any]]:
    """Flatten AladinBookItem objects into tabular dictionary format."""
    rows = []
    for it in items:
        row: Dict[str, Any] = {
            "title": it.title,
            "author": it.author,
            "publisher": it.publisher,
            "pubDate": it.pubDate,
            "isbn13": it.isbn13,
            "isbn": it.isbn,
            "itemId": it.itemId,
            "priceStandard": it.priceStandard,
            "priceSales": it.priceSales,
            "mileage": it.mileage,
            "categoryName": it.categoryName,
            "salesPoint": it.salesPoint,
            "customerReviewRank": it.customerReviewRank,
            "fixedPrice": it.fixedPrice,
            "adult": it.adult,
            "link": it.link,
            "cover": it.cover,
            "description": it.description,
            "seriesName": it.seriesInfo.seriesName if it.seriesInfo else "",
            "subTitle": "",
            "originalTitle": "",
            "itemPage": None,
            "toc": "",
            "styleDesc": "",
            "weight": None,
            "size": "",
            "aladinUsedCount": 0,
            "aladinUsedMinPrice": 0,
            "userUsedCount": 0,
            "userUsedMinPrice": 0,
            "ebookIsbn13": "",
            "ebookPriceSales": 0,
        }

        if it.subInfo:
            sub = it.subInfo
            row["subTitle"] = sub.subTitle or ""
            row["originalTitle"] = sub.originalTitle or ""
            row["itemPage"] = sub.itemPage
            row["toc"] = sub.toc or ""
            if sub.packing:
                p = sub.packing
                row["styleDesc"] = p.styleDesc or ""
                row["weight"] = p.weight
                if p.sizeWidth and p.sizeHeight:
                    row["size"] = f"{p.sizeWidth}x{p.sizeHeight}x{p.sizeDepth or 0}mm"
            if sub.usedList:
                u = sub.usedList
                if u.aladinUsed:
                    row["aladinUsedCount"] = u.aladinUsed.itemCount
                    row["aladinUsedMinPrice"] = u.aladinUsed.minPrice
                if u.userUsed:
                    row["userUsedCount"] = u.userUsed.itemCount
                    row["userUsedMinPrice"] = u.userUsed.minPrice
            if sub.ebookList and len(sub.ebookList) > 0:
                eb = sub.ebookList[0]
                row["ebookIsbn13"] = eb.isbn13 or ""
                row["ebookPriceSales"] = eb.priceSales or 0

        rows.append(row)
    return rows


def export_data(
    items: List[AladinBookItem],
    output_dir: Union[str, Path],
    base_name: str = "aladin_books",
    formats: List[str] = None,
) -> Dict[str, str]:
    """Export items to xlsx, csv, json, sqlite formats."""
    if formats is None:
        formats = ["xlsx", "csv", "json"]

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    rows = items_to_dicts(items)
    df = pd.DataFrame(rows)

    saved_files = {}

    for fmt in formats:
        fmt = fmt.lower().strip().lstrip(".")
        target_file = out_path / f"{base_name}.{fmt}"

        if fmt == "xlsx":
            df.to_excel(target_file, index=False, engine="openpyxl")
            saved_files["xlsx"] = str(target_file)
        elif fmt == "csv":
            df.to_csv(target_file, index=False, encoding="utf-8-sig")
            saved_files["csv"] = str(target_file)
        elif fmt == "json":
            with open(target_file, "w", encoding="utf-8") as f:
                json.dump([it.model_dump() for it in items], f, indent=2, ensure_ascii=False)
            saved_files["json"] = str(target_file)
        elif fmt in ("sqlite", "db"):
            target_db = out_path / f"{base_name}.sqlite"
            conn = sqlite3.connect(target_db)
            df.to_sql("books", conn, if_exists="replace", index=False)
            conn.close()
            saved_files["sqlite"] = str(target_db)

    return saved_files

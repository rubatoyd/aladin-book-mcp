"""Pydantic data models for Aladin OpenAPI."""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SeriesInfo(BaseModel):
    seriesId: Optional[int] = None
    seriesName: Optional[str] = None
    seriesLink: Optional[str] = None


class PackingInfo(BaseModel):
    styleDesc: Optional[str] = None
    weight: Optional[int] = None
    sizeWidth: Optional[int] = None
    sizeHeight: Optional[int] = None
    sizeDepth: Optional[int] = None


class UsedShopDetail(BaseModel):
    itemCount: int = 0
    minPrice: int = 0
    link: Optional[str] = None


class UsedList(BaseModel):
    aladinUsed: Optional[UsedShopDetail] = None
    userUsed: Optional[UsedShopDetail] = None
    spaceUsed: Optional[UsedShopDetail] = None


class EbookItem(BaseModel):
    itemId: Optional[int] = None
    isbn: Optional[str] = None
    isbn13: Optional[str] = None
    priceSales: Optional[int] = None
    link: Optional[str] = None


class SubInfo(BaseModel):
    subTitle: Optional[str] = ""
    originalTitle: Optional[str] = ""
    itemPage: Optional[int] = None
    toc: Optional[str] = ""
    story: Optional[str] = ""
    previewUrl: Optional[str] = ""
    packing: Optional[PackingInfo] = None
    usedList: Optional[UsedList] = None
    ebookList: List[EbookItem] = Field(default_factory=list)


class AladinBookItem(BaseModel):
    title: str = ""
    link: str = ""
    author: str = ""
    pubDate: str = ""
    description: str = ""
    isbn: str = ""
    isbn13: str = ""
    itemId: int = 0
    priceSales: int = 0
    priceStandard: int = 0
    mileage: int = 0
    cover: str = ""
    categoryId: Optional[int] = None
    categoryName: str = ""
    publisher: str = ""
    salesPoint: int = 0
    adult: bool = False
    fixedPrice: bool = False
    customerReviewRank: int = 0
    seriesInfo: Optional[SeriesInfo] = None
    subInfo: Optional[SubInfo] = None


class AladinSearchResult(BaseModel):
    query: str
    totalResults: int
    startIndex: int
    itemsPerPage: int
    truncated: bool = False
    cap_hit: bool = False
    items: List[AladinBookItem] = Field(default_factory=list)


class AladinLookUpResult(BaseModel):
    itemId: str
    items: List[AladinBookItem] = Field(default_factory=list)


class AladinListResult(BaseModel):
    queryType: str
    totalResults: int
    startIndex: int
    itemsPerPage: int
    items: List[AladinBookItem] = Field(default_factory=list)


class AladinStatusResult(BaseModel):
    configured: bool
    key_masked: str
    probe_ok: bool
    probe_message: str
    probe_latency_ms: float

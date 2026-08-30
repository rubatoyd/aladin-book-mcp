"""Rich CLI interface for Aladin Book Search & Collection."""

from __future__ import annotations
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from .client import AladinBookClient
from .exporters import export_data


console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """알라딘(Aladin) OpenAPI 도서 검색 및 대량 수집 CLI 도구"""
    pass


@cli.command()
def status():
    """인증키 상태 및 알라딘 API 연결 상태를 점검합니다."""
    client = AladinBookClient()
    res = client.status_probe()

    color = "green" if res.probe_ok else "red"
    console.print(
        Panel(
            f"[bold]인증키 설정:[/bold] {'[green]설정됨' if res.configured else '[red]미설정'}\n"
            f"[bold]마스킹 키:[/bold] {res.key_masked}\n"
            f"[bold]연결 상태:[/bold] [{color}]{'정상' if res.probe_ok else '실패'}[/{color}]\n"
            f"[bold]응답 메시지:[/bold] {res.probe_message}\n"
            f"[bold]지연 시간:[/bold] {res.probe_latency_ms} ms",
            title="[bold cyan]알라딘 OpenAPI 상태 점검[/bold cyan]",
            border_style=color,
        )
    )


@cli.command()
@click.argument("query")
@click.option("--type", "query_type", default="Keyword", type=click.Choice(["Keyword", "Title", "Author", "Publisher"]), help="검색 필드")
@click.option("--target", "search_target", default="Book", help="검색 대상 (Book, Foreign, eBook, All)")
@click.option("--start", default=1, help="시작 페이지")
@click.option("--size", "max_results", default=10, help="출력 건수")
@click.option("--sort", default="Accuracy", type=click.Choice(["Accuracy", "PublishTime", "Title", "SalesPoint", "CustomerRating"]), help="정렬")
def search(query: str, query_type: str, search_target: str, start: int, max_results: int, sort: str):
    """키워드로 알라딘 도서를 검색합니다."""
    client = AladinBookClient()
    try:
        res = client.search(
            query=query,
            query_type=query_type,
            search_target=search_target,
            start=start,
            max_results=max_results,
            sort=sort,
        )
    except Exception as e:
        console.print(f"[bold red]검색 실패:[/bold red] {e}")
        return

    console.print(f"\n[bold green]✔ 검색어:[/bold green] '{query}' | [bold]총 {res.totalResults:,}건[/bold] (페이지 {res.startIndex})")

    table = Table(title="알라딘 도서 검색 결과", show_lines=True)
    table.add_column("No", justify="right", style="cyan", width=4)
    table.add_column("제목", style="bold white", width=36)
    table.add_column("저자", style="yellow", width=18)
    table.add_column("출판사", style="magenta", width=14)
    table.add_column("출간일", justify="center", width=10)
    table.add_column("판매가", justify="right", style="green", width=10)
    table.add_column("ISBN13", justify="center", width=14)

    for i, it in enumerate(res.items, 1):
        price_str = f"{it.priceSales:,}원" if it.priceSales else "-"
        table.add_row(
            str(i),
            it.title[:34] + ("..." if len(it.title) > 34 else ""),
            it.author[:16] + ("..." if len(it.author) > 16 else ""),
            it.publisher[:12] + ("..." if len(it.publisher) > 12 else ""),
            it.pubDate,
            price_str,
            it.isbn13,
        )

    console.print(table)


@cli.command()
@click.argument("item_id")
@click.option("--type", "item_id_type", default="ISBN13", help="식별자 종류 (ISBN13, ISBN, ItemId)")
def lookup(item_id: str, item_id_type: str):
    """ISBN13 또는 상품ID로 도서 상세(원서명, 목차, 쪽수, 판형, 중고가)를 조회합니다."""
    client = AladinBookClient()
    try:
        res = client.lookup(item_id=item_id, item_id_type=item_id_type)
    except Exception as e:
        console.print(f"[bold red]상세 조회 실패:[/bold red] {e}")
        return

    if not res.items:
        console.print(f"[yellow]조회된 도서가 없습니다 (ID: {item_id})[/yellow]")
        return

    it = res.items[0]
    sub = it.subInfo

    info_text = (
        f"[bold cyan]제목:[/bold cyan] {it.title}\n"
        f"[bold cyan]부제:[/bold cyan] {sub.subTitle if sub else '-'}\n"
        f"[bold cyan]원서명:[/bold cyan] {sub.originalTitle if sub and sub.originalTitle else '-'}\n"
        f"[bold cyan]저자:[/bold cyan] {it.author}\n"
        f"[bold cyan]출판사/출간일:[/bold cyan] {it.publisher} / {it.pubDate}\n"
        f"[bold cyan]ISBN13 / ID:[/bold cyan] {it.isbn13} / {it.itemId}\n"
        f"[bold cyan]정가 / 판매가:[/bold cyan] {it.priceStandard:,}원 / [green]{it.priceSales:,}원[/green] (마일리지 {it.mileage:,}원)\n"
        f"[bold cyan]카테고리:[/bold cyan] {it.categoryName}\n"
        f"[bold cyan]쪽수 / 판형:[/bold cyan] {sub.itemPage if sub and sub.itemPage else '-'}쪽 / {sub.packing.styleDesc if sub and sub.packing else '-'}\n"
        f"[bold cyan]판매지수 / 평점:[/bold cyan] {it.salesPoint:,} / ★ {it.customerReviewRank}/10\n"
    )

    if sub and sub.usedList and sub.usedList.userUsed and sub.usedList.userUsed.itemCount > 0:
        info_text += f"[bold cyan]중고 매물:[/bold cyan] {sub.usedList.userUsed.itemCount}건 (최저 {sub.usedList.userUsed.minPrice:,}원)\n"

    if sub and sub.toc:
        toc_snippet = sub.toc[:300] + ("..." if len(sub.toc) > 300 else "")
        info_text += f"\n[bold yellow][목차 요약][/bold yellow]\n{toc_snippet}"

    console.print(Panel(info_text, title="[bold]알라딘 도서 상세 서지 정보[/bold]", border_style="blue"))


@cli.command("list")
@click.option("--type", "query_type", default="Bestseller", type=click.Choice(["Bestseller", "ItemNewAll", "ItemNewSpecial", "ItemEditorChoice", "BlogBest"]), help="리스트 종류")
@click.option("--target", "search_target", default="Book", help="대상 (Book, Foreign, eBook, All)")
@click.option("--size", "max_results", default=10, help="출력 건수")
def list_books(query_type: str, search_target: str, max_results: int):
    """베스트셀러, 신간, 추천도서 목록을 조회합니다."""
    client = AladinBookClient()
    try:
        res = client.list_items(query_type=query_type, search_target=search_target, max_results=max_results)
    except Exception as e:
        console.print(f"[bold red]리스트 조회 실패:[/bold red] {e}")
        return

    table = Table(title=f"알라딘 {query_type} 목록", show_lines=True)
    table.add_column("순위", justify="right", style="cyan", width=4)
    table.add_column("제목", style="bold white", width=40)
    table.add_column("저자", style="yellow", width=20)
    table.add_column("출판사", style="magenta", width=14)
    table.add_column("판매가", justify="right", style="green", width=10)

    for i, it in enumerate(res.items, 1):
        price_str = f"{it.priceSales:,}원" if it.priceSales else "-"
        table.add_row(
            str(i),
            it.title[:38] + ("..." if len(it.title) > 38 else ""),
            it.author[:18] + ("..." if len(it.author) > 18 else ""),
            it.publisher[:12] + ("..." if len(it.publisher) > 12 else ""),
            price_str,
        )

    console.print(table)


@cli.command()
@click.option("--terms", "-t", multiple=True, required=True, help="수집할 검색어 (여러 개 지정 가능)")
@click.option("--max", "max_per_term", default=30, help="검색어당 최대 수집 건수")
@click.option("--lookup", is_flag=True, default=False, help="목차/원서명/쪽수 등 상세 서지(LookUp)까지 추가 수집")
@click.option("--out", "output_dir", default="./output", help="저장 디렉토리")
@click.option("--format", "-f", "formats", multiple=True, default=["xlsx", "csv", "json"], help="저장 포맷 (xlsx, csv, json, sqlite)")
def collect(terms: tuple[str, ...], max_per_term: int, lookup: bool, output_dir: str, formats: tuple[str, ...]):
    """다중 검색어로 도서를 대량 자동 수집하고 파일로 저장합니다."""
    client = AladinBookClient()
    console.print(f"[bold cyan]🔍 {len(terms)}개 검색어 수집 시작...[/bold cyan] (단어당 최대 {max_per_term}건, 상세LookUp: {lookup})")

    try:
        items = client.collect(
            terms=list(terms),
            max_per_term=max_per_term,
            opt_lookup=lookup,
        )
    except Exception as e:
        console.print(f"[bold red]수집 실패:[/bold red] {e}")
        return

    console.print(f"[bold green]✔ 총 {len(items):,}건 도서 수집 완료 (중복 제거됨)[/bold green]")

    if items:
        saved = export_data(
            items=items,
            output_dir=output_dir,
            base_name="aladin_collected_books",
            formats=list(formats),
        )
        for fmt, path in saved.items():
            console.print(f"  💾 [{fmt.upper()}] {path}")


if __name__ == "__main__":
    cli()

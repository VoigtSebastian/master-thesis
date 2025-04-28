import re
from dataclasses import dataclass
from os import environ

import structlog
from bs4 import BeautifulSoup
from httpx import AsyncClient

log = structlog.get_logger(emitter="confluence_client")


# DTO


@dataclass
class QueryResult:
    title: str
    id: str
    web_ui: str
    self_url: str


@dataclass
class Page:
    title: str
    body: str
    web_ui: str


# Confluence Client with necessary API calls implemented


class ConfluenceClient:
    def __init__(
        self,
        token,
        max_pages_limit: int = 100,
        step_size: int = 25,
    ):
        self.base_url = environ["CONFLUENCE_URL"]
        headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
        self.client = AsyncClient(headers=headers)

        self.max_pages_limit = max_pages_limit
        self.step_size = step_size

    async def get_page(self, query_result: QueryResult) -> Page | None:
        try:
            result = await self.content_body(query_result.self_url)
            body = result["body"]["storage"]["value"]
            body = self.clean_confluence_html(body)

            return Page(
                body=body,
                title=query_result.title,
                web_ui=query_result.web_ui,
            )
        except:
            log.exception("could not retrieve body", url=query_result.self_url)

        return None

    async def cql_all(self, cql: str) -> list[QueryResult]:
        n: int = (await self.cql(cql=cql, start=0, limit=0))["totalSize"]
        log.info("number of pages for element determined", cql=cql, n=n)

        # Retrieve data form API
        start = 0
        results: list[dict] = []
        while start < n and start < self.max_pages_limit:
            result = await self.cql(
                cql=cql,
                start=start,
                limit=self.step_size,
            )
            results.extend(result["results"])
            start += self.step_size

        # Prase API output
        pages: list[QueryResult] = []
        for result in results:
            if query_result := self.parse_query_result(result):
                pages.append(query_result)

        return pages

    def parse_query_result(self, result: dict) -> QueryResult | None:
        try:
            title = result["content"]["title"]
            url = result["content"]["_links"]["webui"]
            self_url = result["content"]["_links"]["self"]
            content_id = result["content"]["id"]

            return QueryResult(
                title=title,
                id=content_id,
                web_ui=f"{self.base_url}{url}",
                self_url=self_url,
            )
        except:
            log.exception("could not parse query result", result=result)
        return None

    def clean_confluence_html(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    async def content_body(self, self_url: str, expand="body.storage") -> dict:
        params = {"expand": expand}

        response = await self.client.get(self_url, params=params)
        response.raise_for_status()

        return response.json()

    async def cql(self, cql: str, start: int, limit: int) -> dict:
        params = {"cql": cql, "start": start, "limit": limit}
        url = f"{self.base_url}/rest/api/search"

        response = await self.client.get(url, params=params)
        response.raise_for_status()

        return response.json()

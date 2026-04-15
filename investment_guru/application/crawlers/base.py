from beanie import Document
from abc import ABC, abstractmethod


class BaseCrawler(ABC):
    model: Document

    @abstractmethod
    def fetch(self, ticker: str) -> list[Document]:
        # Fetches documents for a ticker
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        # Returns the name of the source
        pass

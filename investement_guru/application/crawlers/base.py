import logging
from abc import ABC, abstractmethod
from beanie import Document
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    model: Document

    @abstractmethod
    def fetch(self, ticker: str) -> list[Document]:
        """Fetches documents for a ticker from an external source."""
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Returns the name of the source (e.g. 'stocks', 'rss', 'sec_edgar')."""
        pass

    async def save(self, documents: list[Document]) -> int:
        """
        Upsert documents into MongoDB smoothly.

        Uses the document model's `upsert_fields` directly to look up
        an existing document, and `upsert_mode` to decide whether to 
        'replace' (useful for updating daily stock info) or 'skip' 
        (useful for avoiding duplicate news or SEC filings).

        Returns
        -------
        int
            Number of documents successfully saved or updated.
        """
        if not documents:
            return 0

        saved = 0
        upsert_mode = getattr(self.model, "upsert_mode", "skip")
        upsert_fields = getattr(self.model, "upsert_fields", [])

        if not upsert_fields:
            logger.warning("No upsert_fields on %s, default saving", self.model.__name__)

        for doc in documents:
            if not upsert_fields:
                await doc.save()
                saved += 1
                continue

            query = {field: getattr(doc, field) for field in upsert_fields}
            
            existing_doc = await self.model.find_one(query)

            if existing_doc:
                if upsert_mode == "replace":
                    doc_dict = doc.model_dump(exclude={"id", "revision_id"})
                    for key, val in doc_dict.items():
                        setattr(existing_doc, key, val)
                    try:
                        await existing_doc.save()
                        saved += 1
                    except DuplicateKeyError:
                        pass
                else:
                    logger.debug("Skipping existing document: %s", query)
            else:
                try:
                    await doc.save()
                    saved += 1
                except DuplicateKeyError:
                    pass

        logger.info(
            "[%s] Saved %d / %d documents", self.get_source_name(), saved, len(documents)
        )
        return saved

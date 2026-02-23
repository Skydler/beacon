"""Database module for tracking seen articles."""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

Base = declarative_base()
logger = logging.getLogger(__name__)


class Article(Base):
    """Article model for tracking seen news articles."""

    __tablename__ = "seen_articles"

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    scraped_at = Column(DateTime, default=datetime.now(tz=timezone.utc))
    relevance_score = Column(Integer)
    notified = Column(Boolean, default=False)
    reason = Column(String, nullable=True)
    source_name = Column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<Article(url='{self.url}', title='{self.title}', score={self.relevance_score})>"


class Database:
    """Database manager for article tracking."""

    def __init__(self, db_path: str):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file or ":memory:" for in-memory DB
        """
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        logger.info(f"Database initialized at {db_path}")

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self.Session()

    def is_article_seen(self, url: str) -> bool:
        """Check if an article URL has been seen before.

        Args:
            url: The article URL to check

        Returns:
            True if article exists in database, False otherwise
        """
        session = self._get_session()
        try:
            article = session.query(Article).filter_by(url=url).first()
            return article is not None
        finally:
            session.close()

    def mark_article_seen(
        self,
        url: str,
        title: str,
        relevance_score: Optional[int] = None,
        reason: Optional[str] = None,
        source_name: Optional[str] = None,
    ) -> None:
        """Mark an article as seen and store in database.

        Args:
            url: Article URL
            title: Article title
            relevance_score: Optional relevance score from LLM (1-10)
            reason: Optional LLM explanation for the score
            source_name: Optional name of the configured source this article came from
        """
        session = self._get_session()
        try:
            article = Article(
                url=url,
                title=title,
                relevance_score=relevance_score,
                notified=(relevance_score is not None),
                reason=reason,
                source_name=source_name,
            )
            session.add(article)
            session.commit()
            logger.debug(f"Marked article as seen: {title}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to mark article as seen: {e}")
            raise
        finally:
            session.close()

    def get_recent_articles(self, days: int = 7) -> List[Dict[str, any]]:
        """Get articles seen in the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of article dictionaries
        """
        session = self._get_session()
        try:
            from datetime import timedelta

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            articles = (
                session.query(Article)
                .filter(Article.scraped_at >= cutoff_date)
                .order_by(Article.scraped_at.desc())
                .all()
            )

            return [
                {
                    "url": a.url,
                    "title": a.title,
                    "scraped_at": a.scraped_at,
                    "relevance_score": a.relevance_score,
                    "notified": a.notified,
                    "reason": a.reason,
                    "source_name": a.source_name,
                }
                for a in articles
            ]
        finally:
            session.close()

    def get_article_count(self) -> int:
        """Get total count of articles in database.

        Returns:
            Total number of articles
        """
        session = self._get_session()
        try:
            return session.query(Article).count()
        finally:
            session.close()

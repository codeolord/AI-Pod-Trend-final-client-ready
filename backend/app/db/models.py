from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from .session import Base


class Trend(Base):
    __tablename__ = "trends"

    id = Column(Integer, primary_key=True, index=True)
    marketplace = Column(String(50), index=True, nullable=False)
    product_title = Column(Text, nullable=False)
    niche = Column(String(255), index=True, nullable=False)
    score = Column(Float, index=True, nullable=False)
    demand_level = Column(String(50), index=True, nullable=False)
    competition_level = Column(String(50), index=True, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    sample_image_url = Column(Text, nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class TrendItem(Base):
    """A raw trend/news item ingested from RSS or other sources."""

    __tablename__ = "trend_items"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(255), index=True, nullable=False)
    source_url = Column(Text, nullable=True)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False, unique=True)
    summary = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)

    raw_json = Column(Text, nullable=True)

    ai_score_0_100 = Column(Integer, index=True, nullable=True)
    ai_niche = Column(String(255), index=True, nullable=True)
    ai_json = Column(Text, nullable=True)

    ai_status = Column(String(50), default="pending", nullable=False)
    ai_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class DesignIdea(Base):
    """Design prompts/ideas generated from a TrendItem."""

    __tablename__ = "design_ideas"

    id = Column(Integer, primary_key=True, index=True)
    trend_item_id = Column(Integer, ForeignKey("trend_items.id"), nullable=False, index=True)
    provider = Column(String(50), default="openai", nullable=False)
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    trend_item = relationship("TrendItem")


class MarketplaceProduct(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    marketplace = Column(String(50), index=True, nullable=False)
    external_id = Column(String(128), index=True, nullable=False)
    url = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    niche = Column(String(255), index=True, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    snapshots = relationship("ProductSnapshot", back_populates="product", cascade="all, delete-orphan")
    embeddings = relationship("ProductEmbedding", back_populates="product", cascade="all, delete-orphan")
    trend_scores = relationship("TrendScore", back_populates="product", cascade="all, delete-orphan")
    audiences = relationship("AudienceProfile", back_populates="product", cascade="all, delete-orphan")
    price_recommendations = relationship("PriceRecommendation", back_populates="product", cascade="all, delete-orphan")
    design_assets = relationship("DesignAsset", back_populates="product", cascade="all, delete-orphan")


class ProductSnapshot(Base):
    __tablename__ = "product_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    captured_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    price = Column(Float, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    rank = Column(Integer, nullable=True)
    review_count = Column(Integer, nullable=True)
    rating = Column(Float, nullable=True)
    estimated_sales = Column(Float, nullable=True)

    product = relationship("MarketplaceProduct", back_populates="snapshots")


class ProductEmbedding(Base):
    __tablename__ = "product_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    dim = Column(Integer, nullable=False)
    vector_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("MarketplaceProduct", back_populates="embeddings")


class TrendScore(Base):
    __tablename__ = "trend_scores"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    snapshot_id = Column(Integer, ForeignKey("product_snapshots.id"), nullable=True)

    overall_score = Column(Float, index=True, nullable=False)
    demand_score = Column(Float, nullable=False)
    competition_score = Column(Float, nullable=False)
    momentum_score = Column(Float, nullable=True)

    cluster_label = Column(String(64), index=True, nullable=True)
    niche = Column(String(255), index=True, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("MarketplaceProduct", back_populates="trend_scores")
    snapshot = relationship("ProductSnapshot")


class AudienceProfile(Base):
    __tablename__ = "audience_profiles"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    segment_name = Column(String(255), nullable=False)
    demographics = Column(Text, nullable=True)
    interests = Column(Text, nullable=True)
    tone = Column(String(64), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("MarketplaceProduct", back_populates="audiences")


class PriceRecommendation(Base):
    __tablename__ = "price_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    recommended_min = Column(Float, nullable=False)
    recommended_max = Column(Float, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    rationale = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("MarketplaceProduct", back_populates="price_recommendations")


class DesignAsset(Base):
    __tablename__ = "design_assets"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    provider = Column(String(50), nullable=False)
    image_url = Column(Text, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    status = Column(String(50), default="pending", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("MarketplaceProduct", back_populates="design_assets")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

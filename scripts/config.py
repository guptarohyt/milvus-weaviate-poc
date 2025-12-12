#!/usr/bin/env python3
"""
Centralized Configuration for Vector Database Benchmarking

This module provides a single source of truth for all database connection
parameters. It loads configuration from environment variables with sensible
defaults for local Docker development.

Usage:
    from config import config

    # Access Milvus config
    host = config.milvus.host
    port = config.milvus.port

    # Access PostgreSQL config
    conn_str = config.postgresql.connection_string

    # Access SQL Server config
    conn_str = config.sqlserver.connection_string

For Azure deployments, set environment variables or create a .env file.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Load environment variables from .env file if it exists
from dotenv import load_dotenv

# Look for .env file in project root
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    # Also try current directory
    load_dotenv()


@dataclass
class MilvusConfig:
    """Milvus connection configuration."""
    host: str
    port: int

    @classmethod
    def from_env(cls, prefix: str = "MILVUS") -> "MilvusConfig":
        return cls(
            host=os.getenv(f"{prefix}_HOST", "localhost"),
            port=int(os.getenv(f"{prefix}_PORT", "19530"))
        )


@dataclass
class Milvus24Config:
    """Milvus 2.4 connection configuration (for comparison)."""
    host: str
    port: int

    @classmethod
    def from_env(cls) -> "Milvus24Config":
        return cls(
            host=os.getenv("MILVUS_24_HOST", "localhost"),
            port=int(os.getenv("MILVUS_24_PORT", "19531"))
        )


@dataclass
class WeaviateConfig:
    """Weaviate connection configuration."""
    host: str
    port: int
    grpc_port: int

    @property
    def url(self) -> str:
        """Get the HTTP URL for Weaviate."""
        return f"http://{self.host}:{self.port}"

    @classmethod
    def from_env(cls) -> "WeaviateConfig":
        return cls(
            host=os.getenv("WEAVIATE_HOST", "localhost"),
            port=int(os.getenv("WEAVIATE_PORT", "8080")),
            grpc_port=int(os.getenv("WEAVIATE_GRPC_PORT", "50051"))
        )


@dataclass
class PostgreSQLConfig:
    """PostgreSQL connection configuration."""
    host: str
    port: int
    user: str
    password: str
    database: str

    @property
    def connection_string(self) -> str:
        """Get psycopg2-compatible connection string."""
        return f"host={self.host} port={self.port} dbname={self.database} user={self.user} password={self.password}"

    @property
    def dsn(self) -> str:
        """Get DSN-style connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @classmethod
    def from_env(cls) -> "PostgreSQLConfig":
        return cls(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            database=os.getenv("POSTGRES_DB", "vectordb")
        )


@dataclass
class SQLServerConfig:
    """SQL Server connection configuration."""
    host: str
    port: int
    user: str
    password: str
    database: str
    driver: str
    trust_cert: str

    @property
    def connection_string(self) -> str:
        """Get pyodbc-compatible connection string."""
        return (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.host},{self.port};"
            f"DATABASE={self.database};"
            f"UID={self.user};"
            f"PWD={self.password};"
            f"TrustServerCertificate={self.trust_cert};"
        )

    @property
    def connection_string_no_db(self) -> str:
        """Get connection string without database (for initial connection)."""
        return (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.host},{self.port};"
            f"UID={self.user};"
            f"PWD={self.password};"
            f"TrustServerCertificate={self.trust_cert};"
        )

    @classmethod
    def from_env(cls) -> "SQLServerConfig":
        return cls(
            host=os.getenv("SQLSERVER_HOST", "localhost"),
            port=int(os.getenv("SQLSERVER_PORT", "1433")),
            user=os.getenv("SQLSERVER_USER", "sa"),
            password=os.getenv("SQLSERVER_PASSWORD", "YourStrong@Passw0rd"),
            database=os.getenv("SQLSERVER_DB", "vectordb"),
            driver=os.getenv("SQLSERVER_DRIVER", "ODBC Driver 18 for SQL Server"),
            trust_cert=os.getenv("SQLSERVER_TRUST_CERT", "yes")
        )


@dataclass
class EmbeddingConfig:
    """Embedding model configuration."""
    text_model: str
    text_dim: int
    image_model: str
    image_dim: int

    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        return cls(
            text_model=os.getenv("TEXT_EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            text_dim=int(os.getenv("TEXT_EMBEDDING_DIM", "384")),
            image_model=os.getenv("IMAGE_EMBEDDING_MODEL", "openai/clip-vit-base-patch32"),
            image_dim=int(os.getenv("IMAGE_EMBEDDING_DIM", "512"))
        )


@dataclass
class DataConfig:
    """Data directory configuration."""
    output_dir: str
    _project_root: Path = None

    def __post_init__(self):
        # Store project root for path resolution
        self._project_root = Path(__file__).parent.parent

    @property
    def path(self) -> Path:
        """Get the data output directory as a Path object, resolved relative to project root."""
        p = Path(self.output_dir)
        if not p.is_absolute():
            return self._project_root / p
        return p

    @property
    def processed_dir(self) -> Path:
        """Get the processed data subdirectory."""
        return self.path / "processed"

    @classmethod
    def from_env(cls) -> "DataConfig":
        return cls(
            output_dir=os.getenv("DATA_OUTPUT_DIR", "./data/multimodal")
        )


@dataclass
class BenchmarkConfig:
    """Benchmark execution configuration."""
    num_queries: int
    batch_size: int

    @classmethod
    def from_env(cls) -> "BenchmarkConfig":
        return cls(
            num_queries=int(os.getenv("BENCHMARK_NUM_QUERIES", "10")),
            batch_size=int(os.getenv("BATCH_SIZE", "1000"))
        )


@dataclass
class Config:
    """Main configuration container for all database connections."""
    milvus: MilvusConfig
    milvus_24: Milvus24Config
    weaviate: WeaviateConfig
    postgresql: PostgreSQLConfig
    sqlserver: SQLServerConfig
    embedding: EmbeddingConfig
    data: DataConfig
    benchmark: BenchmarkConfig

    @classmethod
    def from_env(cls) -> "Config":
        """Load all configuration from environment variables."""
        return cls(
            milvus=MilvusConfig.from_env(),
            milvus_24=Milvus24Config.from_env(),
            weaviate=WeaviateConfig.from_env(),
            postgresql=PostgreSQLConfig.from_env(),
            sqlserver=SQLServerConfig.from_env(),
            embedding=EmbeddingConfig.from_env(),
            data=DataConfig.from_env(),
            benchmark=BenchmarkConfig.from_env()
        )

    def print_config(self, show_passwords: bool = False):
        """Print current configuration (useful for debugging)."""
        print("\n" + "=" * 60)
        print("CURRENT CONFIGURATION")
        print("=" * 60)

        print(f"\n[Milvus 2.5]")
        print(f"  Host: {self.milvus.host}")
        print(f"  Port: {self.milvus.port}")

        print(f"\n[Milvus 2.4]")
        print(f"  Host: {self.milvus_24.host}")
        print(f"  Port: {self.milvus_24.port}")

        print(f"\n[Weaviate]")
        print(f"  Host: {self.weaviate.host}")
        print(f"  Port: {self.weaviate.port}")
        print(f"  URL: {self.weaviate.url}")

        print(f"\n[PostgreSQL]")
        print(f"  Host: {self.postgresql.host}")
        print(f"  Port: {self.postgresql.port}")
        print(f"  User: {self.postgresql.user}")
        print(f"  Database: {self.postgresql.database}")
        if show_passwords:
            print(f"  Password: {self.postgresql.password}")

        print(f"\n[SQL Server]")
        print(f"  Host: {self.sqlserver.host}")
        print(f"  Port: {self.sqlserver.port}")
        print(f"  User: {self.sqlserver.user}")
        print(f"  Database: {self.sqlserver.database}")
        print(f"  Driver: {self.sqlserver.driver}")
        if show_passwords:
            print(f"  Password: {self.sqlserver.password}")

        print(f"\n[Embeddings]")
        print(f"  Text Model: {self.embedding.text_model}")
        print(f"  Text Dimensions: {self.embedding.text_dim}")
        print(f"  Image Model: {self.embedding.image_model}")
        print(f"  Image Dimensions: {self.embedding.image_dim}")

        print(f"\n[Data]")
        print(f"  Output Directory: {self.data.output_dir}")

        print(f"\n[Benchmark]")
        print(f"  Queries per test: {self.benchmark.num_queries}")
        print(f"  Batch size: {self.benchmark.batch_size}")

        print("\n" + "=" * 60)


# Global configuration instance (loaded once at import time)
config = Config.from_env()


# Convenience functions for backward compatibility
def get_milvus_config() -> MilvusConfig:
    """Get Milvus configuration."""
    return config.milvus


def get_weaviate_config() -> WeaviateConfig:
    """Get Weaviate configuration."""
    return config.weaviate


def get_postgresql_config() -> PostgreSQLConfig:
    """Get PostgreSQL configuration."""
    return config.postgresql


def get_sqlserver_config() -> SQLServerConfig:
    """Get SQL Server configuration."""
    return config.sqlserver


def get_data_config() -> DataConfig:
    """Get data directory configuration."""
    return config.data


if __name__ == "__main__":
    # When run directly, print current configuration
    print("\nVector Database Benchmark Configuration")
    print("=" * 50)
    print("\nLoading configuration from environment variables...")
    print("(Set values in .env file or environment for custom config)")

    config.print_config(show_passwords=False)

    print("\nTo use in your code:")
    print("  from config import config")
    print("  host = config.milvus.host")
    print("  conn_str = config.sqlserver.connection_string")

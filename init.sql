CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    text TEXT,
    embedding VECTOR(384),
    metadata JSONB DEFAULT '{}'
);

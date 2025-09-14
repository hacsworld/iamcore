CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS particles (
  id bigserial PRIMARY KEY,
  name text,
  pos vector(3),        -- (x,y,z)
  freq vector(128)      -- embedding ядра (любой размер, пример: 128)
);

-- демо-данные
INSERT INTO particles (name, pos, freq) VALUES
('p1', '[0,0,0]',        '[0.9,0.1,0,  ' || repeat('0,',125) || '0]'),
('p2', '[1,0,0]',        '[0.88,0.12,0,' || repeat('0,',125) || '0]'),
('p3', '[0,1,0]',        '[-0.2,0.98,0,' || repeat('0,',125) || '0]');

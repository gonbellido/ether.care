-- ============================================================
-- EsoterSystem — Creación de bases de datos
-- Se ejecuta antes del esquema principal
-- ============================================================

-- Base de datos para n8n (separada del CRM)
CREATE DATABASE n8n
    WITH ENCODING = 'UTF8'
    LC_COLLATE = 'es_ES.UTF-8'
    LC_CTYPE = 'es_ES.UTF-8'
    TEMPLATE = template0;

-- La base de datos principal 'esotersystem' ya se crea
-- via POSTGRES_DB en docker-compose.yml

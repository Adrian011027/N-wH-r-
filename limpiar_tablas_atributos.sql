-- Script para eliminar tablas del sistema antiguo de atributos
-- Ejecutar con: psql -U nowhere_root -d nowhere_db -f limpiar_tablas_atributos.sql

-- Desactivar restricciones temporalmente
BEGIN;

-- Eliminar tablas del sistema antiguo (orden importa por foreign keys)
DROP TABLE IF EXISTS store_varianteatributo CASCADE;
DROP TABLE IF EXISTS store_atributovalor CASCADE;
DROP TABLE IF EXISTS store_atributo CASCADE;

-- Eliminar secuencias asociadas
DROP SEQUENCE IF EXISTS store_varianteatributo_id_seq CASCADE;
DROP SEQUENCE IF EXISTS store_atributovalor_id_seq CASCADE;
DROP SEQUENCE IF EXISTS store_atributo_id_seq CASCADE;

COMMIT;

-- Verificar que se eliminaron
\echo '✅ Tablas antiguas eliminadas. Verificando...'
\dt store_atributo*
\dt store_varianteatributo*

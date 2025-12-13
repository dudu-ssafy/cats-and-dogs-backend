FROM pgvector/pgvector:pg16

# Copy initialization scripts
COPY create_vector_extension.sql /docker-entrypoint-initdb.d/
-- Initialize pgduck_server with MinIO credentials
CREATE SECRET IF NOT EXISTS s3_minio (
    TYPE S3,
    KEY_ID 'minioadmin',
    SECRET 'minioadmin',
    ENDPOINT 'minio:9000',
    SCOPE 's3://warehouse',
    URL_STYLE 'path',
    USE_SSL false
);


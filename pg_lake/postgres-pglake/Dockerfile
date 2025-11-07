FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PG_VERSION=17
ENV PG_HOME=/usr/local/pgsql
ENV PGDATA=/var/lib/postgresql/data
ENV PATH=/usr/local/bin:$PG_HOME/bin:$PATH

# Install build dependencies
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    libreadline-dev \
    zlib1g-dev \
    flex \
    bison \
    libxml2-dev \
    libxslt1-dev \
    libicu-dev \
    libssl-dev \
    libgeos-dev \
    libproj-dev \
    libgdal-dev \
    libjson-c-dev \
    libprotobuf-c-dev \
    protobuf-c-compiler \
    diffutils \
    uuid-dev \
    libossp-uuid-dev \
    liblz4-dev \
    liblzma-dev \
    libsnappy-dev \
    perl \
    libtool \
    libjansson-dev \
    libcurl4-openssl-dev \
    curl \
    zip \
    unzip \
    tar \
    patch \
    g++ \
    libipc-run-perl \
    jq \
    git \
    wget \
    ca-certificates \
    sudo \
    pkg-config \
    autoconf \
    automake \
    && rm -rf /var/lib/apt/lists/*

# Build PostgreSQL 17 from source
WORKDIR /tmp
RUN git clone --branch REL_17_STABLE --depth 1 https://github.com/postgres/postgres.git && \
    cd postgres && \
    ./configure \
    --prefix=$PG_HOME \
    --enable-debug \
    --enable-cassert \
    --enable-depend \
    CFLAGS="-ggdb -Og -g3 -fno-omit-frame-pointer" \
    --with-openssl \
    --with-libxml \
    --with-libxslt \
    --with-icu \
    --with-uuid=ossp \
    --with-lz4 && \
    make -j$(nproc) && \
    make install && \
    # Install contrib modules (including btree_gist)
    cd contrib && \
    make -j$(nproc) && \
    make install && \
    cd ../.. && \
    rm -rf postgres

# Install vcpkg dependencies
WORKDIR /tmp
ENV VCPKG_VERSION=2025.01.13
ENV VCPKG_TOOLCHAIN_PATH=/tmp/vcpkg/scripts/buildsystems/vcpkg.cmake
RUN git clone https://github.com/Microsoft/vcpkg.git && \
    cd vcpkg && \
    git checkout ${VCPKG_VERSION} && \
    ./bootstrap-vcpkg.sh && \
    ./vcpkg install azure-identity-cpp azure-storage-blobs-cpp azure-storage-files-datalake-cpp openssl

# Clone and build pg_lake
WORKDIR /tmp
RUN git clone --recursive https://github.com/snowflake-labs/pg_lake.git && \
    cd pg_lake && \
    git submodule update --init --recursive && \
    cd duckdb_pglake && \
    make && \
    make install && \
    cd .. && \
    make install-avro-local && \
    make fast && \
    make install-fast && \
    cd .. && \
    # Debug: Show what was built
    echo "=== Searching for pgduck_server ===" && \
    find /tmp/pg_lake -name "pgduck_server" -type f && \
    echo "=== Searching for pg_extension_base ===" && \
    find $PG_HOME/lib -name "*pg_extension_base*" 2>/dev/null || find /usr/local/pgsql/lib -name "*pg_extension_base*" 2>/dev/null && \
    # Copy pgduck_server to PATH
    find /tmp/pg_lake/duckdb_pglake -name "pgduck_server" -executable -type f -exec cp {} /usr/local/bin/ \; && \
    chmod +x /usr/local/bin/pgduck_server && \
    # Verify pgduck_server was copied
    echo "=== Verifying pgduck_server ===" && \
    ls -la /usr/local/bin/pgduck_server && \
    which pgduck_server && \
    # Copy Avro library to system library path
    cp -r /tmp/pg_lake/avro/lang/c/build/avrolib/lib/* /usr/local/lib/ 2>/dev/null || true && \
    cp -r /tmp/pg_lake/avro/lang/c/build/avrolib/lib64/* /usr/local/lib/ 2>/dev/null || true && \
    # Verify pg_extension_base was installed
    echo "=== Verifying pg_extension_base ===" && \
    ls -la $PG_HOME/lib/pg_extension_base.* || ls -la /usr/local/pgsql/lib/pg_extension_base.* && \
    # List all installed extension libraries
    echo "=== All pg_lake libraries ===" && \
    ls -la $PG_HOME/lib/*pg_lake* $PG_HOME/lib/*pg_extension* 2>/dev/null || true && \
    # Update library cache
    ldconfig && \
    cd .. && \
    rm -rf pg_lake vcpkg

# Create postgres user and directories
RUN useradd -m -d /var/lib/postgresql -s /bin/bash postgres && \
    mkdir -p $PGDATA && \
    mkdir -p /var/run/postgresql && \
    chown -R postgres:postgres /var/lib/postgresql /var/run/postgresql $PG_HOME

USER postgres

# Initialize PostgreSQL database
RUN initdb -D $PGDATA -k --locale=C.UTF-8

# Configure PostgreSQL to load pg_extension_base
RUN echo "shared_preload_libraries = 'pg_extension_base'" >> $PGDATA/postgresql.conf && \
    echo "listen_addresses = '*'" >> $PGDATA/postgresql.conf && \
    echo "port = 5432" >> $PGDATA/postgresql.conf && \
    echo "host all all 0.0.0.0/0 md5" >> $PGDATA/pg_hba.conf

# Create startup script
USER root
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh && \
    chown postgres:postgres /usr/local/bin/entrypoint.sh

USER postgres
EXPOSE 5432 5332

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]


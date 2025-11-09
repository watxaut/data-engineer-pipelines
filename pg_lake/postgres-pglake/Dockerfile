# Multi-stage Dockerfile for pg_lake and pgduck_server
# Based on official pg_lake Docker setup from https://github.com/Snowflake-Labs/pg_lake/tree/main/docker

ARG BASE_IMAGE_OS=almalinux
ARG BASE_IMAGE_TAG=9

# Stage 1: Build base with all dependencies and pg_lake
FROM ${BASE_IMAGE_OS}:${BASE_IMAGE_TAG} AS base

# Install EPEL repository for additional packages
RUN yum install -y epel-release && yum clean all

# Install build dependencies
# Note: --allowerasing is needed to replace curl-minimal with full curl package
RUN yum install -y --allowerasing \
    gcc \
    gcc-c++ \
    make \
    cmake \
    git \
    wget \
    curl \
    libcurl-devel \
    tar \
    gzip \
    bzip2 \
    xz \
    zip \
    unzip \
    patch \
    diffutils \
    perl \
    python3 \
    python3-pip \
    readline-devel \
    zlib-devel \
    flex \
    bison \
    libxml2-devel \
    libxslt-devel \
    openssl-devel \
    libicu-devel \
    libuuid-devel \
    lz4-devel \
    xz-devel \
    systemd-devel \
    && yum clean all

# Set environment variables
ENV PG_VERSION=17
ENV PG_HOME=/usr/local/pgsql
ENV PGDATA=/var/lib/postgresql/data
ENV PATH=/usr/local/bin:$PG_HOME/bin:$PATH

# Build PostgreSQL from source
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
    --with-uuid=e2fs \
    --with-lz4 && \
    make -j$(nproc) && \
    make install && \
    cd contrib && \
    make -j$(nproc) && \
    make install && \
    cd ../.. && \
    rm -rf postgres

# Build Ninja (required by vcpkg)
WORKDIR /tmp
RUN git clone https://github.com/ninja-build/ninja.git && \
    cd ninja && \
    git checkout release && \
    cmake -Bbuild-cmake && \
    cmake --build build-cmake && \
    cp build-cmake/ninja /usr/local/bin/ && \
    chmod +x /usr/local/bin/ninja && \
    cd .. && \
    rm -rf ninja

# Build jansson from source (required by Avro, not available as -devel in AlmaLinux 9)
WORKDIR /tmp
RUN git clone https://github.com/akheron/jansson.git && \
    cd jansson && \
    mkdir build && \
    cd build && \
    cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local && \
    make && \
    make install && \
    ldconfig && \
    cd ../.. && \
    rm -rf jansson

# Set PKG_CONFIG_PATH so Avro can find jansson
ENV PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH

# Install vcpkg dependencies (required even for S3/MinIO)
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
    # Copy pgduck_server to PATH (it's installed to $PG_HOME/bin by make install-fast)
    cp $PG_HOME/bin/pgduck_server /usr/local/bin/ && \
    chmod +x /usr/local/bin/pgduck_server && \
    # Verify installations
    echo "=== Verifying pgduck_server ===" && \
    ls -la /usr/local/bin/pgduck_server && \
    echo "=== Verifying pg_extension_base ===" && \
    ls -la $PG_HOME/lib/pg_extension_base.* && \
    echo "=== All pg_lake libraries ===" && \
    ls -la $PG_HOME/lib/*pg_lake* $PG_HOME/lib/*pg_extension* 2>/dev/null || true && \
    # Copy Avro libraries
    find /tmp/pg_lake/avro -name "*.so*" -exec cp {} /usr/local/lib/ \; 2>/dev/null || true && \
    ldconfig && \
    # Cleanup
    cd .. && \
    rm -rf pg_lake vcpkg

# Create postgres user and directories
RUN useradd -m -d /var/lib/postgresql -s /bin/bash postgres && \
    mkdir -p $PGDATA && \
    mkdir -p /var/run/postgresql && \
    mkdir -p /home/postgres/pgduck_socket_dir && \
    chown -R postgres:postgres /var/lib/postgresql /var/run/postgresql /home/postgres $PG_HOME

# Stage 2: pgduck_server container
FROM base AS pgduck_server

USER postgres
WORKDIR /home/postgres

# Configure pgduck_server to run on Unix socket
ENV PGDUCK_PORT=5332
ENV PGDUCK_SOCKET_DIR=/home/postgres/pgduck_socket_dir

EXPOSE 5332

# The actual command will be provided by entrypoint script
CMD ["/bin/bash"]

# Stage 3: PostgreSQL with pg_lake container
FROM base AS pg_lake_postgres

USER postgres
WORKDIR /home/postgres

# Initialize PostgreSQL (will be done by entrypoint if not exists)
ENV POSTGRES_USER=postgres
ENV POSTGRES_DB=postgres
ENV PGDATA=/var/lib/postgresql/data

EXPOSE 5432

# The actual command will be provided by entrypoint script
CMD ["/bin/bash"]

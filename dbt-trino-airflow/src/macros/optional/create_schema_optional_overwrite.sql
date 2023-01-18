{#
    Overrides macros in
    https://github.com/dbt-labs/dbt-core/blob/main/core/dbt/include/global_project/macros/adapters/schema.sql

    Potentially if new versions of dbt-trino or dbt-core are released we might need to adapt this code
#}
{% macro create_schema_optional_overwrite(relation) -%}
  {{ adapter.dispatch('create_schema_optional_overwrite', 'dbt')(relation) }}
{% endmacro %}


{% macro default__create_schema_optional_overwrite(relation) -%}

    {# Replace folder/data_product_id with whatever you want #}

  {%- call statement('create_schema_optional_overwrite') -%}
    CREATE SCHEMA IF NOT EXISTS {{ relation.without_identifier() }}
        WITH ( LOCATION = 's3://declarative-data-storage-prod-ec127bf4/{{ folder }}/{{ data_product_id }}' )
  {% endcall %}
{% endmacro %}

{#
    Overwrites generate_schema_name_for_env in dbt 
    (https://github.com/fishtown-analytics/dbt/blob/master/core/dbt/include/global_project/macros/etc/get_custom_schema.sql)

    Renders a schema name given a target (prod, local) and a node (model).

    - target=production: this will use the production instance and will render the schema as specified in the model or in dbt_project.yml folder configuration.
    - target=xxx-sandbox: this will be using the DEV/PROD instance, but creating the tables in central_sandbox_xxxx
    - target=local: this will use localhost to create the models, as well as creating models in schemas as if it were production

    If the target does not match any of the above, the default schema specified in the active
    target schema is used (as in local profile).

    IF THE NODE DOES NOT HAVE ANY SCHEMA SPECIFIED EITHER IN THE dbt_project.yml or in the model itself, it will
    render in the profiles default schema.

    Arguments:
    custom_schema_name: The custom schema name specified for a model, or none
    node: The node the schema is being generated for

#}

{% macro generate_schema_name_for_env(custom_schema_name, node) -%}

    {%- set default_schema = target.schema -%}
    {%- if target.name == 'production' and custom_schema_name is not none -%}

        {{ custom_schema_name | trim }}

    {%- elif target.name == 'production-sandbox' and custom_schema_name is not none -%}

        {{ default_schema }}

    {%- elif target.name == 'development-sandbox' and custom_schema_name is not none -%}

        {{ default_schema }}

    {%- elif target.name.startswith('local') and custom_schema_name is not none -%}

        {{ custom_schema_name | trim }}

    {%- else -%}

        {{ default_schema }}

    {%- endif -%}

{%- endmacro %}
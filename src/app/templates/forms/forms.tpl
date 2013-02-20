{%- macro children (el) %}
	{%- for child in el.children %}
		{{ element (child) }}
	{%- endfor %}
{%- endmacro %}

{%- macro errors (el) -%}
	{%- if el.errors -%}
		<ul class="form-errors">
		{%- for message in el.errors %}
			<li>{{ message }}</li>
		{%- endfor %}
		</ul>
	{%- endif %}
{%- endmacro %}

{%- macro is_required (el) -%}
{%- if el.is_required %}<span class="form-required">*</span> {% endif -%}
{%- endmacro -%}

{%- macro element (el, path = 'forms/elements') %}
	{%- include ''.join ( (path, '/', el.__class__.__name__, '.tpl') ) %}
{%- endmacro %}

{%- block begin %}
<tr>
{%- endblock -%}

{%- block children %}
	{%- if el.children %}
		<table>
		{{- children (el) }}
		</table>
	{%- endif %}
{%- endblock %}

{%- block end %}
</tr>
{%- endblock %}

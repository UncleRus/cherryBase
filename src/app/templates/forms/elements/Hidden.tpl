{%- extends 'forms/element.tpl' -%}
{%- block begin %}
	{{- super () }}
	<input type="hidden" id="{{ el.name }}" name="{{ el.name }}" value="{{ el.value }}" />
{%- endblock %}
{% extends 'forms/element.tpl' %}
{%- block begin %}
	{{ super () }}
	<td colspan="2" class="form-line">
		<fieldset id="{{ el.name }}">
			<legend class="form-legend">{{ el.caption }}</legend>
{%- endblock %}
{%- block end %}
		</fieldset>
	</td>
	{{ super () }}
{%- endblock %}

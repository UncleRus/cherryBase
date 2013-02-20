{% extends 'forms/element.tpl' %}
{%- block begin %}
	{{- super () }}
<tr class = "form-line">
	<td class = "form-caption"><label for="{{ el.name }}">{{ el.caption }}</label></td>
	<td style = "padding-right: 12px;">
		<div style = "border: 1px dashed #C5C5C5; width: 100%; padding: 2px">{{ el.value }}</div>
	</td>
</tr>
{%- endblock %}
{% extends 'forms/element.tpl' %}
{%- block begin %}
	{{- super () }}
	<td class="form-caption">
		<label for="{{ el.name }}">{{ is_required (el) }}{{ el.caption }}</label>
	</td>
	<td>
		<input
			class="input-text"
			type="{{ 'password' if el.is_password else 'text' }}"
			id="{{ el.name }}"
			name="{{ el.name }}"
			value="{{ '' if el.is_password else el.value }}"
			{% if el.max_length > 0 %}maxlength="{{ el.max_length }}"{% endif %}
		/>
		{{ errors (el) }}
	</td>
{%- endblock %}
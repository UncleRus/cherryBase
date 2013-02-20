{% extends 'forms/element.tpl' %}
{%- block begin %}
	{{- super () }}
	<td class="form-caption">
		<label for="{{ el.name }}">{{ is_required (el) }}{{ el.caption }}</label>
	</td>
	<td>
		<input
			type = "text"
			name = "{{ el.name }}"
			id = "{{ el.name }}"
			class = "input-text {{ el.name }}"
			{% if el.value %}value = "{{ el.value }}"{% endif %}
		/>
		<script type="text/javascript">
			$(document).ready (function ()
			{
				$("#{{ el.name }}").mask("{{ el.format }}");
			});
		</script>
		{{ errors (el) }}
	</td>
{%- endblock %}
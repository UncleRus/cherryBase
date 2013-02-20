{% extends 'forms/element.tpl' %}
{%- block begin %}
	{{- super () }}
<tr class = "form-line">
	<td class = "form-caption">
		<label for="{{ el.name }}">{{ is_required (el) }}{{ el.caption }}</label>
	</td>
	<td>
		<select class = "input-text" id = "{{ el.name }}" name = "{{ el.name }}">
		{%- for item in el.listItems %}
			<option value = "{{ item [0] }}" {% if item [0] == el.value %}selected{% endif %}>{{ item [1] }}</option>
		{%- endfor %}
		</select>
		{{ errors (el) }}
	</td>
</tr>
{%- endblock %}
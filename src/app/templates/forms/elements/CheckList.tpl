{% extends 'forms/element.tpl' %}
{%- block begin %}
	{{- super () }}
<tr class = "form-line">
	<td class = "form-caption">
		<label for="{{ el.name }}">{{ is_required (el) }}{{ el.caption }}</label>
	</td>
	<td id = "{{ el.name }}">
		{%- for item in el.items %}
			<input type = "checkbox"
				name = "{{ item [0] }}"
				{% if item in el.value %}checked{% endif %}
			/>{{ item [1] }}<br />
		{%- endfor %}
		<div style = "font-size: 10px; padding-left: 20px;">
			<a id = "{{ el.name }}_check" style = "cursor: pointer; text-decoration: none; color: #949494;">Select all</a>
				&nbsp;&nbsp;&nbsp;
			<a id = "{{ el.name }}_uncheck" style = "cursor: pointer; text-decoration: none; color: #949494;">Clear selection</a>
		</div>
		<script>
			$("#{{ el.name }}_check").click (function ()
			{
				$("#{{ el.name }} > input").attr ("checked", true);
			});
			$("#{{ el.name }}_uncheck").click (function ()
			{
				$("#{{ el.name }} > input").removeAttr ("checked");
			});
		</script>
	</td>
</tr>
{%- endblock %}
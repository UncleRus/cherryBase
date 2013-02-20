{% extends 'forms/element.tpl' %}
{%- block begin %}
	{{- super () }}
<tr class="form-line">
	<td colspan="2">
		<table>
			<tr>
				<td>&nbsp;</td>
				<td>
					<img id="{{ el.name }}__img" src="{{ el.imageSrc }}" style="border: 1px solid gray;"/>
					<img id="{{ el.name }}_refresh" src="/static/images/refresh.png" style="cursor: pointer; width: 32px; height: 32px;" title="Refresh" alt="Refresh" />
				</td>
			</tr>
			<tr>
				<td class="form-caption">
					<label for="{{ el.name }}">{{ is_required (el) }}{{ el.caption }}</label>
				</td>
				<td>
					<input class="input-text" type="text" id="{{ el.name }}" name="{{ el.name }}" />{{ errors (el) }}
				</td>
			</tr>
		</table>
	</td>
	<script type="text/javascript">
		$('#{{ el.name }}_refresh').click (function ()
		{
			$('#{{ el.name }}__img').attr ('src', '{{ el.imageSrc }}?' + Math.random ());
		});
	</script>
</tr>
{%- endblock %}
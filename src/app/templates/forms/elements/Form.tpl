{% extends 'forms/element.tpl' %}

{% block begin %}
<form name="{{ el.name }}" method="post">
	<input type="hidden" name="{{ el.flag }}" value="yes" />
{% endblock %}

{% block end %}
	<table class="form-submit">
		<td><input type="submit" class="input-submit" {% if el.submit %}value="{{ el.submit }}"{% endif %} /></td>
		{% if el.cancel %}
			<td><input type="button" class="input-submit" value="{{ el.cancel }}" onclick="javascript: location.href = '{{ el.cancel_link }}';"/></td>
		{% endif %}
	</table>
</form>
{% endblock %}

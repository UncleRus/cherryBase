{% extends 'page.tpl' %}

{% block title %}Тест формы{% endblock %}

{% block main %}
	{% if form %}
		{% import 'forms/forms.tpl' as forms %}
		{{ forms.element (form) }}
	{% endif %}

{% endblock %}

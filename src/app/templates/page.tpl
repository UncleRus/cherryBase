{% extends 'base.tpl' %}

{% block content %}
<div>
	{% block main %}{% endblock %}
</div>
<div>
	<h3>Объекты сайта, зона left</h3>
	{{ __siteObjects__.left if __siteObjects__ else '' }}
</div>
<div>
	<h3>Объекты сайта, зона right</h3>
	{{ __siteObjects__.right if __siteObjects__ else '' }}
</div>
{% endblock %}

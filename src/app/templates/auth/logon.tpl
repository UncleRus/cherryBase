{% extends 'base.tpl' %}

{% block title %}Please logon{% endblock %}

{% block content %}
	<center>
		<div style="width: 600px;">
			<img src="/static/images/logo.png" alt="CherryPack" /><br /><br />
			{% if message %}
				<div class="ui-widget" style="margin-left: 5px; margin-right: 5px;">
					<div class="ui-state-error ui-corner-all" style="padding: 0pt 0.7em;">
						<p>
							<span style="float: left; margin-right: 0.3em;" class="ui-icon ui-icon-alert"></span>
							{{ message }}
						</p>
					</div>
				</div>
			{% endif %}
			<div style="text-align: left;">
			{% if form %}
				{% import 'forms/forms.tpl' as forms %}
				{{ forms.element (form) }}
			{% endif %}
			</div>
		</div>
	</center>
{% endblock %}
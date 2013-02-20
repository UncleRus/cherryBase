{%- extends 'forms/element.tpl' -%}
{%- block begin %}
	{{- super () }}
	<td class="form-caption">
		<label for="{{ el.name }}">{{ isRequired (el) }}{{ el.caption }}</label>
	</td>
	<td>

		<input type="file" id="{{ el.name }}" name="{{ el.name }}__upload__files__" />
		{{ errors (el) }}
		<div id="{{ el.name }}_filesList"></div>
		<div id="{{ el.name }}_progress"></div>
		<script src="/static/lib/jquery-fileupload.js"></script>
		<script src="/static/lib/file.uploader.js"></script>
		<script type="text/javascript">
		$(document).ready (function ()
		{
			fileUploader (
				$('#{{ el.name }}'),
				{
					urlUpload: '{{ el.uploadUrl }}',
					urlDelete: '{{ el.deleteUrl }}',
					formData: {'fieldName': '{{ el.name }}__upload__files__'},
					maxNumberOfFiles: {{ el.maxUploadFiles }},
					maxFileSize: {{ el.maxFileSize }},
					matchFileExtensions: {{ el.matchFileExtensions }},
					incomingFilesInfo: {{ el.incomingFilesInfo }}
				}
			);
		});
		</script>
	</td>

{%- endblock %}
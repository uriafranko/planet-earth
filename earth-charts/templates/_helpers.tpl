{{- define "planet-earth.env" -}}
{{- if .Values.postgres.enabled }}
- name: DATABASE_URL
  value: "postgresql+psycopg://{{ .Values.postgres.username }}:{{ .Values.postgres.password }}@postgres:5432/{{ .Values.postgres.database }}"
{{- else }}
- name: DATABASE_URL
  value: "{{ .Values.postgres.url }}"
{{- end }}
{{- if .Values.redis.enabled }}
- name: REDIS_URL
  value: "redis://:{{ .Values.redis.password }}@redis:6379/0"
{{- else }}
- name: REDIS_URL
  value: "{{ .Values.redis.url }}"
{{- end }}
- name: LOG_LEVEL
  value: "{{ .Values.backend.logLevel }}"
{{- end }}

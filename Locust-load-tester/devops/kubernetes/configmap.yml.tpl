apiVersion: v1
kind: ConfigMap
metadata:
  namespace: #{applicationCode}#
  name: cm-#{appRegistrationPurpose}#
data:
  .env: |-
    APPLICATION_ID=#{APPLICATION_ID}#
    APPLICATION_SECRET=#{APPLICATION_SECRET}#
    APPLICATION_SIGNATURE_KEY="sdlkfjzqmioejfmi8!dfè!qilmj'mz'kj(msildji"
    BACKEND_APPLICATION_SCOPE=api://#{applicationCode}#-#{environment}#-#{appName}#-be/Default
    ENVIRONMENT=#{environment}#
    OEP_SCORE_URL=https://oep-agfu-agfu-#{purposeInitial}#-#{environment}#-sdc-1.swedencentral.inference.ml.azure.com/score
  loggingConfig.yml: |-
    version: 1
    handlers:
      standard_output:
        class: logging.StreamHandler
        stream: ext://sys.stdout
    loggers:
      tokens:
        level: DEBUG
      app:
        level: DEBUG
    root:
      level: INFO
      handlers: [standard_output]

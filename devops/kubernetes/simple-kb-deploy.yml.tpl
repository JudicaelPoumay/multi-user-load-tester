# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: #{appRegistrationPurpose}#

spec:
  selector:
    matchLabels:
      app: #{appRegistrationPurpose}#
  template: # This is the template of the pod inside the deployment
    metadata:
      labels:
        app: #{appRegistrationPurpose}#
        containerVersion: '#{appVersion}#'
        environment: '#{environment}#'
        appversion: '#{appVersion}#'
        version: 'v1'
    spec:
      nodeSelector:
        kubernetes.io/os: linux
      containers:
        - image: '#{kubernetesContainer}#:#{appVersion}#'
          name: #{appRegistrationPurpose}#
          env:
            - name: DOTENV_LOCATION
              value: /config/.env
            - name: LOGGING_CONFIG_FILE
              value: /config/loggingConfig.yml
            - name: OAUTHLIB_RELAX_TOKEN_SCOPE
              value: '1'
          resources:
            requests:
              cpu: 300m
              memory: 1Gi
            limits:
              cpu: 2
              memory: 4Gi
          ports:
            - containerPort: #{appServicePort}#
              name: http # We named that port "http" so we can refer to it later
          volumeMounts:
            - name: config-vol
              mountPath: /config
      volumes:
        - name: config-vol
          configMap:
            name: cm-#{appRegistrationPurpose}#


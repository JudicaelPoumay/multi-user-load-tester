kind: Service
apiVersion: v1
metadata:
  namespace: #{applicationCode}#
  name: #{appRegistrationPurpose}#
spec:
  type: ClusterIP
  selector:
    app: #{appRegistrationPurpose}#
    appversion: '#{appVersion}#'
    version: 'v1'
  ports:
    - name: http-application
      protocol: TCP
      port: #{destinationPort}#
      targetPort: #{appServicePort}#
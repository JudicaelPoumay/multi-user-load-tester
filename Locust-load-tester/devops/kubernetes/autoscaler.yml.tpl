apiVersion: autoscaling/v1
kind: HorizontalPodAutoscaler
metadata:
  namespace: #{applicationCode}#
  name: #{appRegistrationPurpose}#
spec:
  minReplicas: 1
  maxReplicas: 1
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: #{appRegistrationPurpose}#
  targetCPUUtilizationPercentage: 80

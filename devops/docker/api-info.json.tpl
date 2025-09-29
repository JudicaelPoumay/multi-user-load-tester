{
    "applicationCode": "#{applicationCode}#",
    "serviceName": "#{appRegistrationPurpose}#", 
    "contactEmail": "judicael.poumay@belfius.be",
    "serviceVersion": "#{apilongversion}#",
    "containerName": "#{appRegistrationPurpose}#", 
    "containerVersion": "#{appVersion}#", 
    "apis": [
      {
        "version": "#{apilongversion}#",
        "identifier": "#{apiname}#", 
        "endpoints": [
          {
            "path": "/response",
            "realPath": "/response",
            "method": "GET",
            "contentType": [
              "application/json"
            ]
          }
        ]
      }
    ]
  }
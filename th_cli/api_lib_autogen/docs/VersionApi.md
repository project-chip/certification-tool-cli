# api_lib_autogen.VersionApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_test_harness_backend_version_api_v1_version_get**](VersionApi.md#get_test_harness_backend_version_api_v1_version_get) | **GET** /api/v1/version | Get Test Harness Backend Version


# **get_test_harness_backend_version_api_v1_version_get**
> TestHarnessBackendVersion get_test_harness_backend_version_api_v1_version_get()

Get Test Harness Backend Version

Retrieve version of the Test Engine.

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.test_harness_backend_version import TestHarnessBackendVersion
from api_lib_autogen.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = api_lib_autogen.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with api_lib_autogen.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = api_lib_autogen.VersionApi(api_client)

    try:
        # Get Test Harness Backend Version
        api_response = api_instance.get_test_harness_backend_version_api_v1_version_get()
        print("The response of VersionApi->get_test_harness_backend_version_api_v1_version_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling VersionApi->get_test_harness_backend_version_api_v1_version_get: %s\n" % e)
```



### Parameters
This endpoint does not need any parameter.

### Return type

[**TestHarnessBackendVersion**](TestHarnessBackendVersion.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)


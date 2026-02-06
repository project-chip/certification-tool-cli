# api_lib_autogen.TestCollectionsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**read_test_collections_api_v1_test_collections_get**](TestCollectionsApi.md#read_test_collections_api_v1_test_collections_get) | **GET** /api/v1/test_collections/ | Read Test Collections


# **read_test_collections_api_v1_test_collections_get**
> TestCollections read_test_collections_api_v1_test_collections_get()

Read Test Collections

Retrieve available test collections.

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.test_collections import TestCollections
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
    api_instance = api_lib_autogen.TestCollectionsApi(api_client)

    try:
        # Read Test Collections
        api_response = api_instance.read_test_collections_api_v1_test_collections_get()
        print("The response of TestCollectionsApi->read_test_collections_api_v1_test_collections_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestCollectionsApi->read_test_collections_api_v1_test_collections_get: %s\n" % e)
```



### Parameters
This endpoint does not need any parameter.

### Return type

[**TestCollections**](TestCollections.md)

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


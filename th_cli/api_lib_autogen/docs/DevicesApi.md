# api_lib_autogen.DevicesApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**add_device_config_api_v1_devices_put**](DevicesApi.md#add_device_config_api_v1_devices_put) | **PUT** /api/v1/devices/ | Add Device Config
[**get_device_configs_api_v1_devices_get**](DevicesApi.md#get_device_configs_api_v1_devices_get) | **GET** /api/v1/devices/ | Get Device Configs


# **add_device_config_api_v1_devices_put**
> Any add_device_config_api_v1_devices_put(body)

Add Device Config

### Example

```python
import time
import os
import api_lib_autogen
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
    api_instance = api_lib_autogen.DevicesApi(api_client)
    body = {'key': api_lib_autogen.Any()} # Any | 

    try:
        # Add Device Config
        api_response = api_instance.add_device_config_api_v1_devices_put(body)
        print("The response of DevicesApi->add_device_config_api_v1_devices_put:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DevicesApi->add_device_config_api_v1_devices_put: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | **Any**|  | 

### Return type

[**Any**](Any.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_device_configs_api_v1_devices_get**
> Any get_device_configs_api_v1_devices_get()

Get Device Configs

### Example

```python
import time
import os
import api_lib_autogen
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
    api_instance = api_lib_autogen.DevicesApi(api_client)

    try:
        # Get Device Configs
        api_response = api_instance.get_device_configs_api_v1_devices_get()
        print("The response of DevicesApi->get_device_configs_api_v1_devices_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DevicesApi->get_device_configs_api_v1_devices_get: %s\n" % e)
```



### Parameters
This endpoint does not need any parameter.

### Return type

[**Any**](Any.md)

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


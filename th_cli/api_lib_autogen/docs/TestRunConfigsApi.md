# api_lib_autogen.TestRunConfigsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_test_run_config_api_v1_test_run_configs_post**](TestRunConfigsApi.md#create_test_run_config_api_v1_test_run_configs_post) | **POST** /api/v1/test_run_configs/ | Create Test Run Config
[**read_test_run_config_api_v1_test_run_configs_id_get**](TestRunConfigsApi.md#read_test_run_config_api_v1_test_run_configs_id_get) | **GET** /api/v1/test_run_configs/{id} | Read Test Run Config
[**read_test_run_configs_api_v1_test_run_configs_get**](TestRunConfigsApi.md#read_test_run_configs_api_v1_test_run_configs_get) | **GET** /api/v1/test_run_configs/ | Read Test Run Configs
[**update_test_run_config_api_v1_test_run_configs_id_put**](TestRunConfigsApi.md#update_test_run_config_api_v1_test_run_configs_id_put) | **PUT** /api/v1/test_run_configs/{id} | Update Test Run Config


# **create_test_run_config_api_v1_test_run_configs_post**
> TestRunConfig create_test_run_config_api_v1_test_run_configs_post(test_run_config_create)

Create Test Run Config

Create new test run config.

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.test_run_config import TestRunConfig
from api_lib_autogen.models.test_run_config_create import TestRunConfigCreate
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
    api_instance = api_lib_autogen.TestRunConfigsApi(api_client)
    test_run_config_create = api_lib_autogen.TestRunConfigCreate() # TestRunConfigCreate | 

    try:
        # Create Test Run Config
        api_response = api_instance.create_test_run_config_api_v1_test_run_configs_post(test_run_config_create)
        print("The response of TestRunConfigsApi->create_test_run_config_api_v1_test_run_configs_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunConfigsApi->create_test_run_config_api_v1_test_run_configs_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **test_run_config_create** | [**TestRunConfigCreate**](TestRunConfigCreate.md)|  | 

### Return type

[**TestRunConfig**](TestRunConfig.md)

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

# **read_test_run_config_api_v1_test_run_configs_id_get**
> TestRunConfig read_test_run_config_api_v1_test_run_configs_id_get(id)

Read Test Run Config

Get test run config by ID.

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.test_run_config import TestRunConfig
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
    api_instance = api_lib_autogen.TestRunConfigsApi(api_client)
    id = 56 # int | 

    try:
        # Read Test Run Config
        api_response = api_instance.read_test_run_config_api_v1_test_run_configs_id_get(id)
        print("The response of TestRunConfigsApi->read_test_run_config_api_v1_test_run_configs_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunConfigsApi->read_test_run_config_api_v1_test_run_configs_id_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 

### Return type

[**TestRunConfig**](TestRunConfig.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **read_test_run_configs_api_v1_test_run_configs_get**
> List[TestRunConfig] read_test_run_configs_api_v1_test_run_configs_get(skip=skip, limit=limit)

Read Test Run Configs

Retrieve test_run_configs.

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.test_run_config import TestRunConfig
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
    api_instance = api_lib_autogen.TestRunConfigsApi(api_client)
    skip = 0 # int |  (optional) (default to 0)
    limit = 100 # int |  (optional) (default to 100)

    try:
        # Read Test Run Configs
        api_response = api_instance.read_test_run_configs_api_v1_test_run_configs_get(skip=skip, limit=limit)
        print("The response of TestRunConfigsApi->read_test_run_configs_api_v1_test_run_configs_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunConfigsApi->read_test_run_configs_api_v1_test_run_configs_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **skip** | **int**|  | [optional] [default to 0]
 **limit** | **int**|  | [optional] [default to 100]

### Return type

[**List[TestRunConfig]**](TestRunConfig.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_test_run_config_api_v1_test_run_configs_id_put**
> TestRunConfig update_test_run_config_api_v1_test_run_configs_id_put(id, test_run_config_update)

Update Test Run Config

Update a test run config.

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.test_run_config import TestRunConfig
from api_lib_autogen.models.test_run_config_update import TestRunConfigUpdate
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
    api_instance = api_lib_autogen.TestRunConfigsApi(api_client)
    id = 56 # int | 
    test_run_config_update = api_lib_autogen.TestRunConfigUpdate() # TestRunConfigUpdate | 

    try:
        # Update Test Run Config
        api_response = api_instance.update_test_run_config_api_v1_test_run_configs_id_put(id, test_run_config_update)
        print("The response of TestRunConfigsApi->update_test_run_config_api_v1_test_run_configs_id_put:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunConfigsApi->update_test_run_config_api_v1_test_run_configs_id_put: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 
 **test_run_config_update** | [**TestRunConfigUpdate**](TestRunConfigUpdate.md)|  | 

### Return type

[**TestRunConfig**](TestRunConfig.md)

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


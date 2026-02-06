# api_lib_autogen.TestRunExecutionsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**abort_testing_api_v1_test_run_executions_abort_testing_post**](TestRunExecutionsApi.md#abort_testing_api_v1_test_run_executions_abort_testing_post) | **POST** /api/v1/test_run_executions/abort-testing | Abort Testing
[**archive_api_v1_test_run_executions_id_archive_post**](TestRunExecutionsApi.md#archive_api_v1_test_run_executions_id_archive_post) | **POST** /api/v1/test_run_executions/{id}/archive | Archive
[**create_cli_test_run_execution_api_v1_test_run_executions_cli_post**](TestRunExecutionsApi.md#create_cli_test_run_execution_api_v1_test_run_executions_cli_post) | **POST** /api/v1/test_run_executions/cli | Create Cli Test Run Execution
[**create_test_run_execution_api_v1_test_run_executions_post**](TestRunExecutionsApi.md#create_test_run_execution_api_v1_test_run_executions_post) | **POST** /api/v1/test_run_executions/ | Create Test Run Execution
[**download_grouped_log_api_v1_test_run_executions_id_grouped_log_get**](TestRunExecutionsApi.md#download_grouped_log_api_v1_test_run_executions_id_grouped_log_get) | **GET** /api/v1/test_run_executions/{id}/grouped-log | Download Grouped Log
[**download_log_api_v1_test_run_executions_id_log_get**](TestRunExecutionsApi.md#download_log_api_v1_test_run_executions_id_log_get) | **GET** /api/v1/test_run_executions/{id}/log | Download Log
[**export_test_run_execution_api_v1_test_run_executions_id_export_get**](TestRunExecutionsApi.md#export_test_run_execution_api_v1_test_run_executions_id_export_get) | **GET** /api/v1/test_run_executions/{id}/export | Export Test Run Execution
[**generate_summary_log_api_v1_test_run_executions_id_performance_summary_post**](TestRunExecutionsApi.md#generate_summary_log_api_v1_test_run_executions_id_performance_summary_post) | **POST** /api/v1/test_run_executions/{id}/performance_summary | Generate Summary Log
[**get_chip_server_info_api_v1_test_run_executions_chip_server_info_get**](TestRunExecutionsApi.md#get_chip_server_info_api_v1_test_run_executions_chip_server_info_get) | **GET** /api/v1/test_run_executions/chip-server/info | Get Chip Server Info
[**get_test_runner_status_api_v1_test_run_executions_status_get**](TestRunExecutionsApi.md#get_test_runner_status_api_v1_test_run_executions_status_get) | **GET** /api/v1/test_run_executions/status | Get Test Runner Status
[**import_test_run_execution_api_v1_test_run_executions_import_post**](TestRunExecutionsApi.md#import_test_run_execution_api_v1_test_run_executions_import_post) | **POST** /api/v1/test_run_executions/import | Import Test Run Execution
[**read_test_run_execution_api_v1_test_run_executions_id_get**](TestRunExecutionsApi.md#read_test_run_execution_api_v1_test_run_executions_id_get) | **GET** /api/v1/test_run_executions/{id} | Read Test Run Execution
[**read_test_run_executions_api_v1_test_run_executions_get**](TestRunExecutionsApi.md#read_test_run_executions_api_v1_test_run_executions_get) | **GET** /api/v1/test_run_executions/ | Read Test Run Executions
[**remove_test_run_execution_api_v1_test_run_executions_id_delete**](TestRunExecutionsApi.md#remove_test_run_execution_api_v1_test_run_executions_id_delete) | **DELETE** /api/v1/test_run_executions/{id} | Remove Test Run Execution
[**rename_test_run_execution_api_v1_test_run_executions_id_rename_put**](TestRunExecutionsApi.md#rename_test_run_execution_api_v1_test_run_executions_id_rename_put) | **PUT** /api/v1/test_run_executions/{id}/rename | Rename Test Run Execution
[**repeat_test_run_execution_api_v1_test_run_executions_id_repeat_post**](TestRunExecutionsApi.md#repeat_test_run_execution_api_v1_test_run_executions_id_repeat_post) | **POST** /api/v1/test_run_executions/{id}/repeat | Repeat Test Run Execution
[**start_test_run_execution_api_v1_test_run_executions_id_start_post**](TestRunExecutionsApi.md#start_test_run_execution_api_v1_test_run_executions_id_start_post) | **POST** /api/v1/test_run_executions/{id}/start | Start Test Run Execution
[**unarchive_api_v1_test_run_executions_id_unarchive_post**](TestRunExecutionsApi.md#unarchive_api_v1_test_run_executions_id_unarchive_post) | **POST** /api/v1/test_run_executions/{id}/unarchive | Unarchive
[**upload_file_api_v1_test_run_executions_file_upload_post**](TestRunExecutionsApi.md#upload_file_api_v1_test_run_executions_file_upload_post) | **POST** /api/v1/test_run_executions/file_upload/ | Upload File


# **abort_testing_api_v1_test_run_executions_abort_testing_post**
> Dict[str, str] abort_testing_api_v1_test_run_executions_abort_testing_post()

Abort Testing

Cancel the current testing

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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)

    try:
        # Abort Testing
        api_response = api_instance.abort_testing_api_v1_test_run_executions_abort_testing_post()
        print("The response of TestRunExecutionsApi->abort_testing_api_v1_test_run_executions_abort_testing_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->abort_testing_api_v1_test_run_executions_abort_testing_post: %s\n" % e)
```



### Parameters
This endpoint does not need any parameter.

### Return type

**Dict[str, str]**

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

# **archive_api_v1_test_run_executions_id_archive_post**
> TestRunExecution archive_api_v1_test_run_executions_id_archive_post(id)

Archive

Archive test run execution by id.  Args:     id (int): test run execution id  Raises:     HTTPException: if no test run execution exists for provided id  Returns:     TestRunExecution: test run execution record that was archived

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.test_run_execution import TestRunExecution
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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    id = 56 # int | 

    try:
        # Archive
        api_response = api_instance.archive_api_v1_test_run_executions_id_archive_post(id)
        print("The response of TestRunExecutionsApi->archive_api_v1_test_run_executions_id_archive_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->archive_api_v1_test_run_executions_id_archive_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 

### Return type

[**TestRunExecution**](TestRunExecution.md)

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

# **create_cli_test_run_execution_api_v1_test_run_executions_cli_post**
> TestRunExecutionWithChildren create_cli_test_run_execution_api_v1_test_run_executions_cli_post(body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post)

Create Cli Test Run Execution

Creates a new test run execution on CLI request.    Attention: if both config and execution_config are provided,    only config will be persisted, while execution_config will be for    this execution only.  Args:     test_run_execution_in: Test run execution data     selected_tests: Selected tests to run     config: Configuration parameters that update project (optional, persists)     execution_config: Execution-specific config override (optional, temporary)     pics: PICS configuration (optional)

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post import BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost
from api_lib_autogen.models.test_run_execution_with_children import TestRunExecutionWithChildren
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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post = api_lib_autogen.BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost() # BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost | 

    try:
        # Create Cli Test Run Execution
        api_response = api_instance.create_cli_test_run_execution_api_v1_test_run_executions_cli_post(body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post)
        print("The response of TestRunExecutionsApi->create_cli_test_run_execution_api_v1_test_run_executions_cli_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->create_cli_test_run_execution_api_v1_test_run_executions_cli_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post** | [**BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost**](BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost.md)|  | 

### Return type

[**TestRunExecutionWithChildren**](TestRunExecutionWithChildren.md)

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

# **create_test_run_execution_api_v1_test_run_executions_post**
> TestRunExecutionWithChildren create_test_run_execution_api_v1_test_run_executions_post(body_create_test_run_execution_api_v1_test_run_executions_post, certification_mode=certification_mode)

Create Test Run Execution

Create a new test run execution.

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.body_create_test_run_execution_api_v1_test_run_executions_post import BodyCreateTestRunExecutionApiV1TestRunExecutionsPost
from api_lib_autogen.models.test_run_execution_with_children import TestRunExecutionWithChildren
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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    body_create_test_run_execution_api_v1_test_run_executions_post = api_lib_autogen.BodyCreateTestRunExecutionApiV1TestRunExecutionsPost() # BodyCreateTestRunExecutionApiV1TestRunExecutionsPost | 
    certification_mode = False # bool |  (optional) (default to False)

    try:
        # Create Test Run Execution
        api_response = api_instance.create_test_run_execution_api_v1_test_run_executions_post(body_create_test_run_execution_api_v1_test_run_executions_post, certification_mode=certification_mode)
        print("The response of TestRunExecutionsApi->create_test_run_execution_api_v1_test_run_executions_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->create_test_run_execution_api_v1_test_run_executions_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body_create_test_run_execution_api_v1_test_run_executions_post** | [**BodyCreateTestRunExecutionApiV1TestRunExecutionsPost**](BodyCreateTestRunExecutionApiV1TestRunExecutionsPost.md)|  | 
 **certification_mode** | **bool**|  | [optional] [default to False]

### Return type

[**TestRunExecutionWithChildren**](TestRunExecutionWithChildren.md)

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

# **download_grouped_log_api_v1_test_run_executions_id_grouped_log_get**
> download_grouped_log_api_v1_test_run_executions_id_grouped_log_get(id)

Download Grouped Log

Download the logs from a test run, grouped by test case state.  Args:     id (int): ID of the TestRunExectution the log is requested for  Raises:     HTTPException: If there's no TestRunExectution with the given ID  Returns:     StreamingResponse: .zip file containing: one file with the list of test cases     for each state; one file with the logs from the executed test suites; one file     per state with the logs from all test cases that finished with that state

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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    id = 56 # int | 

    try:
        # Download Grouped Log
        api_instance.download_grouped_log_api_v1_test_run_executions_id_grouped_log_get(id)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->download_grouped_log_api_v1_test_run_executions_id_grouped_log_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 

### Return type

void (empty response body)

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

# **download_log_api_v1_test_run_executions_id_log_get**
> download_log_api_v1_test_run_executions_id_log_get(id, json_entries=json_entries, download=download)

Download Log

Download the logs from a test run.   Args:     id (int): Id of the TestRunExectution the log is requested for     json_entries (bool, optional): When set, return each log line as a json object     download (bool, optional): When set, return as attachment

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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    id = 56 # int | 
    json_entries = False # bool |  (optional) (default to False)
    download = False # bool |  (optional) (default to False)

    try:
        # Download Log
        api_instance.download_log_api_v1_test_run_executions_id_log_get(id, json_entries=json_entries, download=download)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->download_log_api_v1_test_run_executions_id_log_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 
 **json_entries** | **bool**|  | [optional] [default to False]
 **download** | **bool**|  | [optional] [default to False]

### Return type

void (empty response body)

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

# **export_test_run_execution_api_v1_test_run_executions_id_export_get**
> ExportedTestRunExecution export_test_run_execution_api_v1_test_run_executions_id_export_get(id, download=download)

Export Test Run Execution

Exports a test run execution by the given ID.

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.exported_test_run_execution import ExportedTestRunExecution
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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    id = 56 # int | 
    download = False # bool |  (optional) (default to False)

    try:
        # Export Test Run Execution
        api_response = api_instance.export_test_run_execution_api_v1_test_run_executions_id_export_get(id, download=download)
        print("The response of TestRunExecutionsApi->export_test_run_execution_api_v1_test_run_executions_id_export_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->export_test_run_execution_api_v1_test_run_executions_id_export_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 
 **download** | **bool**|  | [optional] [default to False]

### Return type

[**ExportedTestRunExecution**](ExportedTestRunExecution.md)

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

# **generate_summary_log_api_v1_test_run_executions_id_performance_summary_post**
> Any generate_summary_log_api_v1_test_run_executions_id_performance_summary_post(id, project_id)

Generate Summary Log

Imports a test run execution to the the given project_id.

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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    id = 56 # int | 
    project_id = 56 # int | 

    try:
        # Generate Summary Log
        api_response = api_instance.generate_summary_log_api_v1_test_run_executions_id_performance_summary_post(id, project_id)
        print("The response of TestRunExecutionsApi->generate_summary_log_api_v1_test_run_executions_id_performance_summary_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->generate_summary_log_api_v1_test_run_executions_id_performance_summary_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 
 **project_id** | **int**|  | 

### Return type

**Any**

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

# **get_chip_server_info_api_v1_test_run_executions_chip_server_info_get**
> ChipServerInfo get_chip_server_info_api_v1_test_run_executions_chip_server_info_get(discriminator=discriminator, setup_pin_code=setup_pin_code, version=version, vendor_id=vendor_id, product_id=product_id)

Get Chip Server Info

Retrieve ChipServer node ID information and generate manual pairing code.  Note: Manual pairing code generation requires the SDK container to be running. If called before the SDK container starts, manual_pairing_code will be None.  Args:     discriminator: Device discriminator (optional)     setup_pin_code: Setup PIN code (optional)     version: Version number (default: 0)     vendor_id: Vendor ID (default: 0)     product_id: Product ID (default: 0)  Returns:     ChipServerInfo: Contains node_id, node_id_hex, and optional manual_pairing_code.

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.chip_server_info import ChipServerInfo
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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    discriminator = 'discriminator_example' # str |  (optional)
    setup_pin_code = 'setup_pin_code_example' # str |  (optional)
    version = 0 # int |  (optional) (default to 0)
    vendor_id = 0 # int |  (optional) (default to 0)
    product_id = 0 # int |  (optional) (default to 0)

    try:
        # Get Chip Server Info
        api_response = api_instance.get_chip_server_info_api_v1_test_run_executions_chip_server_info_get(discriminator=discriminator, setup_pin_code=setup_pin_code, version=version, vendor_id=vendor_id, product_id=product_id)
        print("The response of TestRunExecutionsApi->get_chip_server_info_api_v1_test_run_executions_chip_server_info_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->get_chip_server_info_api_v1_test_run_executions_chip_server_info_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **discriminator** | **str**|  | [optional] 
 **setup_pin_code** | **str**|  | [optional] 
 **version** | **int**|  | [optional] [default to 0]
 **vendor_id** | **int**|  | [optional] [default to 0]
 **product_id** | **int**|  | [optional] [default to 0]

### Return type

[**ChipServerInfo**](ChipServerInfo.md)

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

# **get_test_runner_status_api_v1_test_run_executions_status_get**
> TestRunnerStatus get_test_runner_status_api_v1_test_run_executions_status_get()

Get Test Runner Status

Retrieve status of the Test Engine.  When the Test Engine is actively running the status will include the current test_run and the details of the states.

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.test_runner_status import TestRunnerStatus
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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)

    try:
        # Get Test Runner Status
        api_response = api_instance.get_test_runner_status_api_v1_test_run_executions_status_get()
        print("The response of TestRunExecutionsApi->get_test_runner_status_api_v1_test_run_executions_status_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->get_test_runner_status_api_v1_test_run_executions_status_get: %s\n" % e)
```



### Parameters
This endpoint does not need any parameter.

### Return type

[**TestRunnerStatus**](TestRunnerStatus.md)

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

# **import_test_run_execution_api_v1_test_run_executions_import_post**
> TestRunExecutionWithChildren import_test_run_execution_api_v1_test_run_executions_import_post(project_id, import_file)

Import Test Run Execution

Imports a test run execution to the the given project_id.

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.test_run_execution_with_children import TestRunExecutionWithChildren
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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    project_id = 56 # int | 
    import_file = api_lib_autogen.IO() # IO | 

    try:
        # Import Test Run Execution
        api_response = api_instance.import_test_run_execution_api_v1_test_run_executions_import_post(project_id, import_file)
        print("The response of TestRunExecutionsApi->import_test_run_execution_api_v1_test_run_executions_import_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->import_test_run_execution_api_v1_test_run_executions_import_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_id** | **int**|  | 
 **import_file** | **IO**|  | 

### Return type

[**TestRunExecutionWithChildren**](TestRunExecutionWithChildren.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **read_test_run_execution_api_v1_test_run_executions_id_get**
> TestRunExecutionWithChildren read_test_run_execution_api_v1_test_run_executions_id_get(id)

Read Test Run Execution

Get test run by ID, including state on all children

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.test_run_execution_with_children import TestRunExecutionWithChildren
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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    id = 56 # int | 

    try:
        # Read Test Run Execution
        api_response = api_instance.read_test_run_execution_api_v1_test_run_executions_id_get(id)
        print("The response of TestRunExecutionsApi->read_test_run_execution_api_v1_test_run_executions_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->read_test_run_execution_api_v1_test_run_executions_id_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 

### Return type

[**TestRunExecutionWithChildren**](TestRunExecutionWithChildren.md)

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

# **read_test_run_executions_api_v1_test_run_executions_get**
> List[TestRunExecutionWithStats] read_test_run_executions_api_v1_test_run_executions_get(project_id=project_id, archived=archived, search_query=search_query, skip=skip, limit=limit, sort_order=sort_order)

Read Test Run Executions

Retrieve test runs, including statistics.  Args:     project_id: Filter test runs by project.     archived: Get archived test runs, when true will return archived         test runs only, when false only non-archived test runs are returned.     skip: Pagination offset.     limit: Max number of records to return. Set to 0 to return all results.     sort_order: Sort order for results. Either \"asc\" or \"desc\". Defaults to \"asc\".         Results are sorted by ID.  Returns:     List of test runs with execution statistics.

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.test_run_execution_with_stats import TestRunExecutionWithStats
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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    project_id = 56 # int |  (optional)
    archived = False # bool |  (optional) (default to False)
    search_query = 'search_query_example' # str |  (optional)
    skip = 0 # int |  (optional) (default to 0)
    limit = 100 # int |  (optional) (default to 100)
    sort_order = 'asc' # str |  (optional) (default to 'asc')

    try:
        # Read Test Run Executions
        api_response = api_instance.read_test_run_executions_api_v1_test_run_executions_get(project_id=project_id, archived=archived, search_query=search_query, skip=skip, limit=limit, sort_order=sort_order)
        print("The response of TestRunExecutionsApi->read_test_run_executions_api_v1_test_run_executions_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->read_test_run_executions_api_v1_test_run_executions_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_id** | **int**|  | [optional] 
 **archived** | **bool**|  | [optional] [default to False]
 **search_query** | **str**|  | [optional] 
 **skip** | **int**|  | [optional] [default to 0]
 **limit** | **int**|  | [optional] [default to 100]
 **sort_order** | **str**|  | [optional] [default to &#39;asc&#39;]

### Return type

[**List[TestRunExecutionWithStats]**](TestRunExecutionWithStats.md)

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

# **remove_test_run_execution_api_v1_test_run_executions_id_delete**
> TestRunExecutionInDBBase remove_test_run_execution_api_v1_test_run_executions_id_delete(id)

Remove Test Run Execution

Remove test run execution

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.test_run_execution_in_db_base import TestRunExecutionInDBBase
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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    id = 56 # int | 

    try:
        # Remove Test Run Execution
        api_response = api_instance.remove_test_run_execution_api_v1_test_run_executions_id_delete(id)
        print("The response of TestRunExecutionsApi->remove_test_run_execution_api_v1_test_run_executions_id_delete:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->remove_test_run_execution_api_v1_test_run_executions_id_delete: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 

### Return type

[**TestRunExecutionInDBBase**](TestRunExecutionInDBBase.md)

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

# **rename_test_run_execution_api_v1_test_run_executions_id_rename_put**
> TestRunExecutionWithChildren rename_test_run_execution_api_v1_test_run_executions_id_rename_put(id, new_execution_name)

Rename Test Run Execution

Rename the name of a test run execution.

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.test_run_execution_with_children import TestRunExecutionWithChildren
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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    id = 56 # int | 
    new_execution_name = 'new_execution_name_example' # str | 

    try:
        # Rename Test Run Execution
        api_response = api_instance.rename_test_run_execution_api_v1_test_run_executions_id_rename_put(id, new_execution_name)
        print("The response of TestRunExecutionsApi->rename_test_run_execution_api_v1_test_run_executions_id_rename_put:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->rename_test_run_execution_api_v1_test_run_executions_id_rename_put: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 
 **new_execution_name** | **str**|  | 

### Return type

[**TestRunExecutionWithChildren**](TestRunExecutionWithChildren.md)

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

# **repeat_test_run_execution_api_v1_test_run_executions_id_repeat_post**
> TestRunExecutionWithChildren repeat_test_run_execution_api_v1_test_run_executions_id_repeat_post(id, title=title)

Repeat Test Run Execution

Repeat a test run execution by id.  Args:     id (int): test run execution id     title (str): Optional title to the repeated test run execution. If not provided,         the old title will be used with the date and time updated.  Raises:     HTTPException: if no test run execution exists for the provided id  Returns:     TestRunExecution: new test run execution with the same test cases from id

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.test_run_execution_with_children import TestRunExecutionWithChildren
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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    id = 56 # int | 
    title = 'title_example' # str |  (optional)

    try:
        # Repeat Test Run Execution
        api_response = api_instance.repeat_test_run_execution_api_v1_test_run_executions_id_repeat_post(id, title=title)
        print("The response of TestRunExecutionsApi->repeat_test_run_execution_api_v1_test_run_executions_id_repeat_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->repeat_test_run_execution_api_v1_test_run_executions_id_repeat_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 
 **title** | **str**|  | [optional] 

### Return type

[**TestRunExecutionWithChildren**](TestRunExecutionWithChildren.md)

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

# **start_test_run_execution_api_v1_test_run_executions_id_start_post**
> TestRunExecutionWithChildren start_test_run_execution_api_v1_test_run_executions_id_start_post(id)

Start Test Run Execution

Start a test run by ID

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.test_run_execution_with_children import TestRunExecutionWithChildren
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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    id = 56 # int | 

    try:
        # Start Test Run Execution
        api_response = api_instance.start_test_run_execution_api_v1_test_run_executions_id_start_post(id)
        print("The response of TestRunExecutionsApi->start_test_run_execution_api_v1_test_run_executions_id_start_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->start_test_run_execution_api_v1_test_run_executions_id_start_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 

### Return type

[**TestRunExecutionWithChildren**](TestRunExecutionWithChildren.md)

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

# **unarchive_api_v1_test_run_executions_id_unarchive_post**
> TestRunExecution unarchive_api_v1_test_run_executions_id_unarchive_post(id)

Unarchive

Unarchive test run execution by id.  Args:     id (int): test run execution id  Raises:     HTTPException: if no test run execution exists for provided id  Returns:     TestRunExecution: test run execution record that was unarchived

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.test_run_execution import TestRunExecution
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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    id = 56 # int | 

    try:
        # Unarchive
        api_response = api_instance.unarchive_api_v1_test_run_executions_id_unarchive_post(id)
        print("The response of TestRunExecutionsApi->unarchive_api_v1_test_run_executions_id_unarchive_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->unarchive_api_v1_test_run_executions_id_unarchive_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 

### Return type

[**TestRunExecution**](TestRunExecution.md)

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

# **upload_file_api_v1_test_run_executions_file_upload_post**
> Any upload_file_api_v1_test_run_executions_file_upload_post(file)

Upload File

Upload a file to the specified path of the current test run.  Args:     file: The file to upload.

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
    api_instance = api_lib_autogen.TestRunExecutionsApi(api_client)
    file = api_lib_autogen.IO() # IO | 

    try:
        # Upload File
        api_response = api_instance.upload_file_api_v1_test_run_executions_file_upload_post(file)
        print("The response of TestRunExecutionsApi->upload_file_api_v1_test_run_executions_file_upload_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TestRunExecutionsApi->upload_file_api_v1_test_run_executions_file_upload_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **file** | **IO**|  | 

### Return type

**Any**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)


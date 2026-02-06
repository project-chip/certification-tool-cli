# api_lib_autogen.ProjectsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**applicable_test_cases_api_v1_projects_id_applicable_test_cases_get**](ProjectsApi.md#applicable_test_cases_api_v1_projects_id_applicable_test_cases_get) | **GET** /api/v1/projects/{id}/applicable_test_cases | Applicable Test Cases
[**archive_project_api_v1_projects_id_archive_post**](ProjectsApi.md#archive_project_api_v1_projects_id_archive_post) | **POST** /api/v1/projects/{id}/archive | Archive Project
[**create_project_api_v1_projects_post**](ProjectsApi.md#create_project_api_v1_projects_post) | **POST** /api/v1/projects/ | Create Project
[**default_config_api_v1_projects_default_config_get**](ProjectsApi.md#default_config_api_v1_projects_default_config_get) | **GET** /api/v1/projects/default_config | Default Config
[**delete_project_api_v1_projects_id_delete**](ProjectsApi.md#delete_project_api_v1_projects_id_delete) | **DELETE** /api/v1/projects/{id} | Delete Project
[**export_project_config_api_v1_projects_id_export_get**](ProjectsApi.md#export_project_config_api_v1_projects_id_export_get) | **GET** /api/v1/projects/{id}/export | Export Project Config
[**importproject_config_api_v1_projects_import_post**](ProjectsApi.md#importproject_config_api_v1_projects_import_post) | **POST** /api/v1/projects/import | Importproject Config
[**read_project_api_v1_projects_id_get**](ProjectsApi.md#read_project_api_v1_projects_id_get) | **GET** /api/v1/projects/{id} | Read Project
[**read_projects_api_v1_projects_get**](ProjectsApi.md#read_projects_api_v1_projects_get) | **GET** /api/v1/projects/ | Read Projects
[**remove_pics_cluster_type_api_v1_projects_id_pics_cluster_type_delete**](ProjectsApi.md#remove_pics_cluster_type_api_v1_projects_id_pics_cluster_type_delete) | **DELETE** /api/v1/projects/{id}/pics_cluster_type | Remove Pics Cluster Type
[**unarchive_project_api_v1_projects_id_unarchive_post**](ProjectsApi.md#unarchive_project_api_v1_projects_id_unarchive_post) | **POST** /api/v1/projects/{id}/unarchive | Unarchive Project
[**update_project_api_v1_projects_id_put**](ProjectsApi.md#update_project_api_v1_projects_id_put) | **PUT** /api/v1/projects/{id} | Update Project
[**upload_pics_api_v1_projects_id_upload_pics_put**](ProjectsApi.md#upload_pics_api_v1_projects_id_upload_pics_put) | **PUT** /api/v1/projects/{id}/upload_pics | Upload Pics


# **applicable_test_cases_api_v1_projects_id_applicable_test_cases_get**
> PICSApplicableTestCases applicable_test_cases_api_v1_projects_id_applicable_test_cases_get(id)

Applicable Test Cases

Retrieve list of applicable test cases based on project identifier.  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     PICSApplicableTestCases: List of applicable test cases

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.pics_applicable_test_cases import PICSApplicableTestCases
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
    api_instance = api_lib_autogen.ProjectsApi(api_client)
    id = 56 # int | 

    try:
        # Applicable Test Cases
        api_response = api_instance.applicable_test_cases_api_v1_projects_id_applicable_test_cases_get(id)
        print("The response of ProjectsApi->applicable_test_cases_api_v1_projects_id_applicable_test_cases_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ProjectsApi->applicable_test_cases_api_v1_projects_id_applicable_test_cases_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 

### Return type

[**PICSApplicableTestCases**](PICSApplicableTestCases.md)

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

# **archive_project_api_v1_projects_id_archive_post**
> Project archive_project_api_v1_projects_id_archive_post(id)

Archive Project

Archive project by id.  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: project record that was archived

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.project import Project
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
    api_instance = api_lib_autogen.ProjectsApi(api_client)
    id = 56 # int | 

    try:
        # Archive Project
        api_response = api_instance.archive_project_api_v1_projects_id_archive_post(id)
        print("The response of ProjectsApi->archive_project_api_v1_projects_id_archive_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ProjectsApi->archive_project_api_v1_projects_id_archive_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 

### Return type

[**Project**](Project.md)

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

# **create_project_api_v1_projects_post**
> Project create_project_api_v1_projects_post(project_create)

Create Project

Create new project  Args:     project_in (ProjectCreate): Parameters for new project,  see schema for details  Returns:     Project: newly created project record

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.project import Project
from api_lib_autogen.models.project_create import ProjectCreate
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
    api_instance = api_lib_autogen.ProjectsApi(api_client)
    project_create = api_lib_autogen.ProjectCreate() # ProjectCreate | 

    try:
        # Create Project
        api_response = api_instance.create_project_api_v1_projects_post(project_create)
        print("The response of ProjectsApi->create_project_api_v1_projects_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ProjectsApi->create_project_api_v1_projects_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_create** | [**ProjectCreate**](ProjectCreate.md)|  | 

### Return type

[**Project**](Project.md)

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

# **default_config_api_v1_projects_default_config_get**
> ResponseDefaultConfigApiV1ProjectsDefaultConfigGet default_config_api_v1_projects_default_config_get()

Default Config

Return default configuration for projects.  Returns:     List[Project]: List of projects

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.response_default_config_api_v1_projects_default_config_get import ResponseDefaultConfigApiV1ProjectsDefaultConfigGet
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
    api_instance = api_lib_autogen.ProjectsApi(api_client)

    try:
        # Default Config
        api_response = api_instance.default_config_api_v1_projects_default_config_get()
        print("The response of ProjectsApi->default_config_api_v1_projects_default_config_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ProjectsApi->default_config_api_v1_projects_default_config_get: %s\n" % e)
```



### Parameters
This endpoint does not need any parameter.

### Return type

[**ResponseDefaultConfigApiV1ProjectsDefaultConfigGet**](ResponseDefaultConfigApiV1ProjectsDefaultConfigGet.md)

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

# **delete_project_api_v1_projects_id_delete**
> Project delete_project_api_v1_projects_id_delete(id)

Delete Project

Delete project by id  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: project record that was deleted

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.project import Project
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
    api_instance = api_lib_autogen.ProjectsApi(api_client)
    id = 56 # int | 

    try:
        # Delete Project
        api_response = api_instance.delete_project_api_v1_projects_id_delete(id)
        print("The response of ProjectsApi->delete_project_api_v1_projects_id_delete:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ProjectsApi->delete_project_api_v1_projects_id_delete: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 

### Return type

[**Project**](Project.md)

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

# **export_project_config_api_v1_projects_id_export_get**
> ProjectCreate export_project_config_api_v1_projects_id_export_get(id)

Export Project Config

Exports the project config by id.  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     JSONResponse: json representation of the project with the informed project id

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.project_create import ProjectCreate
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
    api_instance = api_lib_autogen.ProjectsApi(api_client)
    id = 56 # int | 

    try:
        # Export Project Config
        api_response = api_instance.export_project_config_api_v1_projects_id_export_get(id)
        print("The response of ProjectsApi->export_project_config_api_v1_projects_id_export_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ProjectsApi->export_project_config_api_v1_projects_id_export_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 

### Return type

[**ProjectCreate**](ProjectCreate.md)

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

# **importproject_config_api_v1_projects_import_post**
> Project importproject_config_api_v1_projects_import_post(import_file)

Importproject Config

Imports the project config  Args:     import_file : The project config file to be imported  Raises:     ValidationError: if the imported project config contains invalid information  Returns:     Project: newly created project record

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.project import Project
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
    api_instance = api_lib_autogen.ProjectsApi(api_client)
    import_file = api_lib_autogen.IO() # IO | 

    try:
        # Importproject Config
        api_response = api_instance.importproject_config_api_v1_projects_import_post(import_file)
        print("The response of ProjectsApi->importproject_config_api_v1_projects_import_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ProjectsApi->importproject_config_api_v1_projects_import_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **import_file** | **IO**|  | 

### Return type

[**Project**](Project.md)

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

# **read_project_api_v1_projects_id_get**
> Project read_project_api_v1_projects_id_get(id)

Read Project

Lookup project by id  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: project record

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.project import Project
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
    api_instance = api_lib_autogen.ProjectsApi(api_client)
    id = 56 # int | 

    try:
        # Read Project
        api_response = api_instance.read_project_api_v1_projects_id_get(id)
        print("The response of ProjectsApi->read_project_api_v1_projects_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ProjectsApi->read_project_api_v1_projects_id_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 

### Return type

[**Project**](Project.md)

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

# **read_projects_api_v1_projects_get**
> List[Project] read_projects_api_v1_projects_get(archived=archived, skip=skip, limit=limit)

Read Projects

Retrieve list of projects  Args:     archived (bool, optional): Get archived projects, when true will; get archived         projects only, when false only non-archived projects are returned.         Defaults to false.     skip (int, optional): Pagination offset. Defaults to 0.     limit (int, optional): max number of records to return. Defaults to 100.  Returns:     List[Project]: List of projects

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.project import Project
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
    api_instance = api_lib_autogen.ProjectsApi(api_client)
    archived = False # bool |  (optional) (default to False)
    skip = 0 # int |  (optional) (default to 0)
    limit = 100 # int |  (optional) (default to 100)

    try:
        # Read Projects
        api_response = api_instance.read_projects_api_v1_projects_get(archived=archived, skip=skip, limit=limit)
        print("The response of ProjectsApi->read_projects_api_v1_projects_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ProjectsApi->read_projects_api_v1_projects_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **archived** | **bool**|  | [optional] [default to False]
 **skip** | **int**|  | [optional] [default to 0]
 **limit** | **int**|  | [optional] [default to 100]

### Return type

[**List[Project]**](Project.md)

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

# **remove_pics_cluster_type_api_v1_projects_id_pics_cluster_type_delete**
> Project remove_pics_cluster_type_api_v1_projects_id_pics_cluster_type_delete(id, cluster_name)

Remove Pics Cluster Type

Removes cluster based on given cluster name  Args:     id (int): ID of Project     cluster_name (str): Name of the cluster to delete  Raises:     HTTPException: if no project exists for provided project id  Returns:     models.Project: Project with updated PICS entry

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.project import Project
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
    api_instance = api_lib_autogen.ProjectsApi(api_client)
    id = 56 # int | 
    cluster_name = 'cluster_name_example' # str | 

    try:
        # Remove Pics Cluster Type
        api_response = api_instance.remove_pics_cluster_type_api_v1_projects_id_pics_cluster_type_delete(id, cluster_name)
        print("The response of ProjectsApi->remove_pics_cluster_type_api_v1_projects_id_pics_cluster_type_delete:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ProjectsApi->remove_pics_cluster_type_api_v1_projects_id_pics_cluster_type_delete: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 
 **cluster_name** | **str**|  | 

### Return type

[**Project**](Project.md)

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

# **unarchive_project_api_v1_projects_id_unarchive_post**
> Project unarchive_project_api_v1_projects_id_unarchive_post(id)

Unarchive Project

Unarchive project by id.  Args:     id (int): project id  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: project record that was unarchived

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.project import Project
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
    api_instance = api_lib_autogen.ProjectsApi(api_client)
    id = 56 # int | 

    try:
        # Unarchive Project
        api_response = api_instance.unarchive_project_api_v1_projects_id_unarchive_post(id)
        print("The response of ProjectsApi->unarchive_project_api_v1_projects_id_unarchive_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ProjectsApi->unarchive_project_api_v1_projects_id_unarchive_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 

### Return type

[**Project**](Project.md)

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

# **update_project_api_v1_projects_id_put**
> Project update_project_api_v1_projects_id_put(id, project_update)

Update Project

Update an existing project  Args:     id (int): project id     project_in (schemas.ProjectUpdate): projects parameters to be updated  Raises:     HTTPException: if no project exists for provided project id  Returns:     Project: updated project record

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.project import Project
from api_lib_autogen.models.project_update import ProjectUpdate
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
    api_instance = api_lib_autogen.ProjectsApi(api_client)
    id = 56 # int | 
    project_update = api_lib_autogen.ProjectUpdate() # ProjectUpdate | 

    try:
        # Update Project
        api_response = api_instance.update_project_api_v1_projects_id_put(id, project_update)
        print("The response of ProjectsApi->update_project_api_v1_projects_id_put:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ProjectsApi->update_project_api_v1_projects_id_put: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 
 **project_update** | [**ProjectUpdate**](ProjectUpdate.md)|  | 

### Return type

[**Project**](Project.md)

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

# **upload_pics_api_v1_projects_id_upload_pics_put**
> Project upload_pics_api_v1_projects_id_upload_pics_put(id, file)

Upload Pics

Upload PICS or dmp-test-skip.xml file of a project based on project identifier.  Args:     id (int): project id     file : the PICS or dmp-test-skip.xml file to upload  Raises:     HTTPException: if no project exists for provided project id (or)                    if the PICS file is invalid  Returns:     Project: project record that was updated with the PICS and dmp_test_skip     information.

### Example

```python
import time
import os
import api_lib_autogen
from api_lib_autogen.models.project import Project
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
    api_instance = api_lib_autogen.ProjectsApi(api_client)
    id = 56 # int | 
    file = api_lib_autogen.IO() # IO | 

    try:
        # Upload Pics
        api_response = api_instance.upload_pics_api_v1_projects_id_upload_pics_put(id, file)
        print("The response of ProjectsApi->upload_pics_api_v1_projects_id_upload_pics_put:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ProjectsApi->upload_pics_api_v1_projects_id_upload_pics_put: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**|  | 
 **file** | **IO**|  | 

### Return type

[**Project**](Project.md)

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


<!--
 *
 * Copyright (c) 2023 Project CHIP Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
-->
# client.UserApi

All URIs are relative to *https://petstore.swagger.io/v2*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_user**](UserApi.md#create_user) | **POST** /user | Create user
[**create_users_with_array_input**](UserApi.md#create_users_with_array_input) | **POST** /user/createWithArray | Creates list of users with given input array
[**create_users_with_list_input**](UserApi.md#create_users_with_list_input) | **POST** /user/createWithList | Creates list of users with given input array
[**delete_user**](UserApi.md#delete_user) | **DELETE** /user/{username} | Delete user
[**get_user_by_name**](UserApi.md#get_user_by_name) | **GET** /user/{username} | Get user by user name
[**login_user**](UserApi.md#login_user) | **GET** /user/login | Logs user into the system
[**logout_user**](UserApi.md#logout_user) | **GET** /user/logout | Logs out current logged in user session
[**update_user**](UserApi.md#update_user) | **PUT** /user/{username} | Updated user


# **create_user**
> create_user(body)

Create user

This can only be done by the logged in user.

### Example

```python
from __future__ import print_function
import time
import client
from client.rest import ApiException
from pprint import pprint

# Create an instance of the API class
api_instance = client.UserApi()
body = client.User() # User | Created user object

try:
    # Create user
    api_instance.create_user(body)
except ApiException as e:
    print("Exception when calling UserApi->create_user: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**User**](User.md)| Created user object | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**0** | successful operation |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_users_with_array_input**
> create_users_with_array_input(body)

Creates list of users with given input array

### Example

```python
from __future__ import print_function
import time
import client
from client.rest import ApiException
from pprint import pprint

# Create an instance of the API class
api_instance = client.UserApi()
body = [client.User()] # List[User] | List of user object

try:
    # Creates list of users with given input array
    api_instance.create_users_with_array_input(body)
except ApiException as e:
    print("Exception when calling UserApi->create_users_with_array_input: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**List[User]**](User.md)| List of user object | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**0** | successful operation |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_users_with_list_input**
> create_users_with_list_input(body)

Creates list of users with given input array

### Example

```python
from __future__ import print_function
import time
import client
from client.rest import ApiException
from pprint import pprint

# Create an instance of the API class
api_instance = client.UserApi()
body = [client.User()] # List[User] | List of user object

try:
    # Creates list of users with given input array
    api_instance.create_users_with_list_input(body)
except ApiException as e:
    print("Exception when calling UserApi->create_users_with_list_input: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**List[User]**](User.md)| List of user object | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**0** | successful operation |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_user**
> delete_user(username)

Delete user

This can only be done by the logged in user.

### Example

```python
from __future__ import print_function
import time
import client
from client.rest import ApiException
from pprint import pprint

# Create an instance of the API class
api_instance = client.UserApi()
username = 'username_example' # str | The name that needs to be deleted

try:
    # Delete user
    api_instance.delete_user(username)
except ApiException as e:
    print("Exception when calling UserApi->delete_user: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **username** | **str**| The name that needs to be deleted | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**400** | Invalid username supplied |  -  |
**404** | User not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_user_by_name**
> User get_user_by_name(username)

Get user by user name

### Example

```python
from __future__ import print_function
import time
import client
from client.rest import ApiException
from pprint import pprint

# Create an instance of the API class
api_instance = client.UserApi()
username = 'username_example' # str | The name that needs to be fetched. Use user1 for testing. 

try:
    # Get user by user name
    api_response = api_instance.get_user_by_name(username)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UserApi->get_user_by_name: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **username** | **str**| The name that needs to be fetched. Use user1 for testing.  | 

### Return type

[**User**](User.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json, application/xml

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  -  |
**400** | Invalid username supplied |  -  |
**404** | User not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **login_user**
> str login_user(username, password)

Logs user into the system

### Example

```python
from __future__ import print_function
import time
import client
from client.rest import ApiException
from pprint import pprint

# Create an instance of the API class
api_instance = client.UserApi()
username = 'username_example' # str | The user name for login
password = 'password_example' # str | The password for login in clear text

try:
    # Logs user into the system
    api_response = api_instance.login_user(username, password)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UserApi->login_user: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **username** | **str**| The user name for login | 
 **password** | **str**| The password for login in clear text | 

### Return type

**str**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json, application/xml

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  * X-Rate-Limit - calls per hour allowed by the user <br>  * X-Expires-After - date in UTC when token expires <br>  |
**400** | Invalid username/password supplied |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **logout_user**
> logout_user()

Logs out current logged in user session

### Example

```python
from __future__ import print_function
import time
import client
from client.rest import ApiException
from pprint import pprint

# Create an instance of the API class
api_instance = client.UserApi()

try:
    # Logs out current logged in user session
    api_instance.logout_user()
except ApiException as e:
    print("Exception when calling UserApi->logout_user: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**0** | successful operation |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_user**
> update_user(username, body)

Updated user

This can only be done by the logged in user.

### Example

```python
from __future__ import print_function
import time
import client
from client.rest import ApiException
from pprint import pprint

# Create an instance of the API class
api_instance = client.UserApi()
username = 'username_example' # str | name that need to be updated
body = client.User() # User | Updated user object

try:
    # Updated user
    api_instance.update_user(username, body)
except ApiException as e:
    print("Exception when calling UserApi->update_user: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **username** | **str**| name that need to be updated | 
 **body** | [**User**](User.md)| Updated user object | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**400** | Invalid user supplied |  -  |
**404** | User not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)


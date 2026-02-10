# BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**test_run_execution_in** | [**TestRunExecutionCreate**](TestRunExecutionCreate.md) |  | 
**selected_tests** | **Dict[str, Dict[str, Dict[str, int]]]** |  | 
**config** | [**Any**](.md) |  | [optional] 
**execution_config** | [**Any**](.md) |  | [optional] 
**pics** | [**Any**](.md) |  | [optional] 

## Example

```python
from api_lib_autogen.models.body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post import BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost

# TODO update the JSON string below
json = "{}"
# create an instance of BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost from a JSON string
body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post_instance = BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost.from_json(json)
# print the JSON string representation of the object
print BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost.to_json()

# convert the object into a dict
body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post_dict = body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post_instance.to_dict()
# create an instance of BodyCreateCliTestRunExecutionApiV1TestRunExecutionsCliPost from a dict
body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post_form_dict = body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post.from_dict(body_create_cli_test_run_execution_api_v1_test_run_executions_cli_post_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



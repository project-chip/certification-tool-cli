# BodyCreateTestRunExecutionApiV1TestRunExecutionsPost


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**test_run_execution_in** | [**TestRunExecutionCreate**](TestRunExecutionCreate.md) |  | 
**selected_tests** | **Dict[str, Dict[str, Dict[str, int]]]** |  | 

## Example

```python
from api_lib_autogen.models.body_create_test_run_execution_api_v1_test_run_executions_post import BodyCreateTestRunExecutionApiV1TestRunExecutionsPost

# TODO update the JSON string below
json = "{}"
# create an instance of BodyCreateTestRunExecutionApiV1TestRunExecutionsPost from a JSON string
body_create_test_run_execution_api_v1_test_run_executions_post_instance = BodyCreateTestRunExecutionApiV1TestRunExecutionsPost.from_json(json)
# print the JSON string representation of the object
print BodyCreateTestRunExecutionApiV1TestRunExecutionsPost.to_json()

# convert the object into a dict
body_create_test_run_execution_api_v1_test_run_executions_post_dict = body_create_test_run_execution_api_v1_test_run_executions_post_instance.to_dict()
# create an instance of BodyCreateTestRunExecutionApiV1TestRunExecutionsPost from a dict
body_create_test_run_execution_api_v1_test_run_executions_post_form_dict = body_create_test_run_execution_api_v1_test_run_executions_post.from_dict(body_create_test_run_execution_api_v1_test_run_executions_post_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



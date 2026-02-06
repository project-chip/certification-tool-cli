# TestRunExecutionCreate


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**title** | **str** |  | 
**description** | **str** |  | [optional] 
**execution_config** | [**Any**](.md) |  | [optional] 
**certification_mode** | **bool** |  | [optional] [default to False]
**test_run_config_id** | **int** |  | [optional] 
**project_id** | **int** |  | [optional] 
**operator_id** | **int** |  | [optional] 

## Example

```python
from api_lib_autogen.models.test_run_execution_create import TestRunExecutionCreate

# TODO update the JSON string below
json = "{}"
# create an instance of TestRunExecutionCreate from a JSON string
test_run_execution_create_instance = TestRunExecutionCreate.from_json(json)
# print the JSON string representation of the object
print TestRunExecutionCreate.to_json()

# convert the object into a dict
test_run_execution_create_dict = test_run_execution_create_instance.to_dict()
# create an instance of TestRunExecutionCreate from a dict
test_run_execution_create_form_dict = test_run_execution_create.from_dict(test_run_execution_create_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



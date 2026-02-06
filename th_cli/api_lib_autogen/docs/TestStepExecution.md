# TestStepExecution


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**state** | [**TestStateEnum**](TestStateEnum.md) |  | 
**title** | **str** |  | 
**execution_index** | **int** |  | 
**id** | **int** |  | 
**test_case_execution_id** | **int** |  | 
**started_at** | **datetime** |  | [optional] 
**completed_at** | **datetime** |  | [optional] 
**errors** | **List[str]** |  | [optional] 
**failures** | **List[str]** |  | [optional] 

## Example

```python
from api_lib_autogen.models.test_step_execution import TestStepExecution

# TODO update the JSON string below
json = "{}"
# create an instance of TestStepExecution from a JSON string
test_step_execution_instance = TestStepExecution.from_json(json)
# print the JSON string representation of the object
print TestStepExecution.to_json()

# convert the object into a dict
test_step_execution_dict = test_step_execution_instance.to_dict()
# create an instance of TestStepExecution from a dict
test_step_execution_form_dict = test_step_execution.from_dict(test_step_execution_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



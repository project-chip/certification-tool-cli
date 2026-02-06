# TestStepExecutionToExport


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**state** | [**TestStateEnum**](TestStateEnum.md) |  | 
**title** | **str** |  | 
**execution_index** | **int** |  | 
**started_at** | **datetime** |  | [optional] 
**completed_at** | **datetime** |  | [optional] 
**errors** | **List[str]** |  | [optional] 
**failures** | **List[str]** |  | [optional] 
**created_at** | **datetime** |  | 

## Example

```python
from api_lib_autogen.models.test_step_execution_to_export import TestStepExecutionToExport

# TODO update the JSON string below
json = "{}"
# create an instance of TestStepExecutionToExport from a JSON string
test_step_execution_to_export_instance = TestStepExecutionToExport.from_json(json)
# print the JSON string representation of the object
print TestStepExecutionToExport.to_json()

# convert the object into a dict
test_step_execution_to_export_dict = test_step_execution_to_export_instance.to_dict()
# create an instance of TestStepExecutionToExport from a dict
test_step_execution_to_export_form_dict = test_step_execution_to_export.from_dict(test_step_execution_to_export_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



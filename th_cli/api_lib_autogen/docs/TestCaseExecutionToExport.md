# TestCaseExecutionToExport


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**state** | [**TestStateEnum**](TestStateEnum.md) |  | 
**public_id** | **str** |  | 
**execution_index** | **int** |  | 
**started_at** | **datetime** |  | [optional] 
**completed_at** | **datetime** |  | [optional] 
**errors** | **List[str]** |  | [optional] 
**test_case_metadata** | [**TestCaseMetadataBase**](TestCaseMetadataBase.md) |  | 
**test_step_executions** | [**List[TestStepExecutionToExport]**](TestStepExecutionToExport.md) |  | 
**created_at** | **datetime** |  | 

## Example

```python
from api_lib_autogen.models.test_case_execution_to_export import TestCaseExecutionToExport

# TODO update the JSON string below
json = "{}"
# create an instance of TestCaseExecutionToExport from a JSON string
test_case_execution_to_export_instance = TestCaseExecutionToExport.from_json(json)
# print the JSON string representation of the object
print TestCaseExecutionToExport.to_json()

# convert the object into a dict
test_case_execution_to_export_dict = test_case_execution_to_export_instance.to_dict()
# create an instance of TestCaseExecutionToExport from a dict
test_case_execution_to_export_form_dict = test_case_execution_to_export.from_dict(test_case_execution_to_export_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



# TestSuiteExecutionToExport


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**state** | [**TestStateEnum**](TestStateEnum.md) |  | 
**public_id** | **str** |  | 
**execution_index** | **int** |  | 
**collection_id** | **str** |  | 
**mandatory** | **bool** |  | [optional] [default to False]
**started_at** | **datetime** |  | [optional] 
**completed_at** | **datetime** |  | [optional] 
**errors** | **List[str]** |  | [optional] 
**test_case_executions** | [**List[TestCaseExecutionToExport]**](TestCaseExecutionToExport.md) |  | 
**test_suite_metadata** | [**TestSuiteMetadataBase**](TestSuiteMetadataBase.md) |  | 
**created_at** | **datetime** |  | 

## Example

```python
from api_lib_autogen.models.test_suite_execution_to_export import TestSuiteExecutionToExport

# TODO update the JSON string below
json = "{}"
# create an instance of TestSuiteExecutionToExport from a JSON string
test_suite_execution_to_export_instance = TestSuiteExecutionToExport.from_json(json)
# print the JSON string representation of the object
print TestSuiteExecutionToExport.to_json()

# convert the object into a dict
test_suite_execution_to_export_dict = test_suite_execution_to_export_instance.to_dict()
# create an instance of TestSuiteExecutionToExport from a dict
test_suite_execution_to_export_form_dict = test_suite_execution_to_export.from_dict(test_suite_execution_to_export_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



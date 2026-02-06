# TestRunExecutionToExport


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**title** | **str** |  | 
**description** | **str** |  | [optional] 
**execution_config** | [**Any**](.md) |  | [optional] 
**certification_mode** | **bool** |  | [optional] [default to False]
**state** | [**TestStateEnum**](TestStateEnum.md) |  | 
**started_at** | **datetime** |  | [optional] 
**completed_at** | **datetime** |  | [optional] 
**archived_at** | **datetime** |  | [optional] 
**test_suite_executions** | [**List[TestSuiteExecutionToExport]**](TestSuiteExecutionToExport.md) |  | [optional] 
**created_at** | **datetime** |  | 
**log** | [**List[TestRunLogEntry]**](TestRunLogEntry.md) |  | 
**operator** | [**OperatorToExport**](OperatorToExport.md) |  | [optional] 
**test_run_config** | [**TestRunConfigToExport**](TestRunConfigToExport.md) |  | [optional] 

## Example

```python
from api_lib_autogen.models.test_run_execution_to_export import TestRunExecutionToExport

# TODO update the JSON string below
json = "{}"
# create an instance of TestRunExecutionToExport from a JSON string
test_run_execution_to_export_instance = TestRunExecutionToExport.from_json(json)
# print the JSON string representation of the object
print TestRunExecutionToExport.to_json()

# convert the object into a dict
test_run_execution_to_export_dict = test_run_execution_to_export_instance.to_dict()
# create an instance of TestRunExecutionToExport from a dict
test_run_execution_to_export_form_dict = test_run_execution_to_export.from_dict(test_run_execution_to_export_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



# ExportedTestRunExecution


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**db_revision** | **str** |  | 
**test_run_execution** | [**TestRunExecutionToExport**](TestRunExecutionToExport.md) |  | 

## Example

```python
from api_lib_autogen.models.exported_test_run_execution import ExportedTestRunExecution

# TODO update the JSON string below
json = "{}"
# create an instance of ExportedTestRunExecution from a JSON string
exported_test_run_execution_instance = ExportedTestRunExecution.from_json(json)
# print the JSON string representation of the object
print ExportedTestRunExecution.to_json()

# convert the object into a dict
exported_test_run_execution_dict = exported_test_run_execution_instance.to_dict()
# create an instance of ExportedTestRunExecution from a dict
exported_test_run_execution_form_dict = exported_test_run_execution.from_dict(exported_test_run_execution_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



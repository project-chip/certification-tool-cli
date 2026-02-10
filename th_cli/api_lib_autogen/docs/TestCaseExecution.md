# TestCaseExecution


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**state** | [**TestStateEnum**](TestStateEnum.md) |  | 
**public_id** | **str** |  | 
**execution_index** | **int** |  | 
**id** | **int** |  | 
**test_suite_execution_id** | **int** |  | 
**test_case_metadata_id** | **int** |  | 
**started_at** | **datetime** |  | [optional] 
**completed_at** | **datetime** |  | [optional] 
**errors** | **List[str]** |  | [optional] 
**test_case_metadata** | [**TestCaseMetadata**](TestCaseMetadata.md) |  | 
**test_step_executions** | [**List[TestStepExecution]**](TestStepExecution.md) |  | 

## Example

```python
from api_lib_autogen.models.test_case_execution import TestCaseExecution

# TODO update the JSON string below
json = "{}"
# create an instance of TestCaseExecution from a JSON string
test_case_execution_instance = TestCaseExecution.from_json(json)
# print the JSON string representation of the object
print TestCaseExecution.to_json()

# convert the object into a dict
test_case_execution_dict = test_case_execution_instance.to_dict()
# create an instance of TestCaseExecution from a dict
test_case_execution_form_dict = test_case_execution.from_dict(test_case_execution_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



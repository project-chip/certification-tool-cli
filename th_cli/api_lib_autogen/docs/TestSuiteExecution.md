# TestSuiteExecution


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**state** | [**TestStateEnum**](TestStateEnum.md) |  | 
**public_id** | **str** |  | 
**execution_index** | **int** |  | 
**collection_id** | **str** |  | 
**mandatory** | **bool** |  | [optional] [default to False]
**id** | **int** |  | 
**test_run_execution_id** | **int** |  | 
**test_suite_metadata_id** | **int** |  | 
**started_at** | **datetime** |  | [optional] 
**completed_at** | **datetime** |  | [optional] 
**errors** | **List[str]** |  | [optional] 
**test_case_executions** | [**List[TestCaseExecution]**](TestCaseExecution.md) |  | 
**test_suite_metadata** | [**TestSuiteMetadata**](TestSuiteMetadata.md) |  | 

## Example

```python
from api_lib_autogen.models.test_suite_execution import TestSuiteExecution

# TODO update the JSON string below
json = "{}"
# create an instance of TestSuiteExecution from a JSON string
test_suite_execution_instance = TestSuiteExecution.from_json(json)
# print the JSON string representation of the object
print TestSuiteExecution.to_json()

# convert the object into a dict
test_suite_execution_dict = test_suite_execution_instance.to_dict()
# create an instance of TestSuiteExecution from a dict
test_suite_execution_form_dict = test_suite_execution.from_dict(test_suite_execution_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



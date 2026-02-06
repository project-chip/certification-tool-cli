# TestRunExecutionWithStats


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**title** | **str** |  | 
**description** | **str** |  | [optional] 
**execution_config** | [**Any**](.md) |  | [optional] 
**certification_mode** | **bool** |  | [optional] [default to False]
**test_run_config_id** | **int** |  | [optional] 
**project_id** | **int** |  | [optional] 
**id** | **int** |  | 
**state** | [**TestStateEnum**](TestStateEnum.md) |  | 
**started_at** | **datetime** |  | [optional] 
**completed_at** | **datetime** |  | [optional] 
**imported_at** | **datetime** |  | [optional] 
**archived_at** | **datetime** |  | [optional] 
**operator** | [**Operator**](Operator.md) |  | [optional] 
**test_case_stats** | [**TestRunExecutionStats**](TestRunExecutionStats.md) |  | 

## Example

```python
from api_lib_autogen.models.test_run_execution_with_stats import TestRunExecutionWithStats

# TODO update the JSON string below
json = "{}"
# create an instance of TestRunExecutionWithStats from a JSON string
test_run_execution_with_stats_instance = TestRunExecutionWithStats.from_json(json)
# print the JSON string representation of the object
print TestRunExecutionWithStats.to_json()

# convert the object into a dict
test_run_execution_with_stats_dict = test_run_execution_with_stats_instance.to_dict()
# create an instance of TestRunExecutionWithStats from a dict
test_run_execution_with_stats_form_dict = test_run_execution_with_stats.from_dict(test_run_execution_with_stats_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



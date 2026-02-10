# TestRunExecutionStats


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**test_case_count** | **int** |  | [optional] [default to 0]
**states** | **Dict[str, int]** |  | [optional] 

## Example

```python
from api_lib_autogen.models.test_run_execution_stats import TestRunExecutionStats

# TODO update the JSON string below
json = "{}"
# create an instance of TestRunExecutionStats from a JSON string
test_run_execution_stats_instance = TestRunExecutionStats.from_json(json)
# print the JSON string representation of the object
print TestRunExecutionStats.to_json()

# convert the object into a dict
test_run_execution_stats_dict = test_run_execution_stats_instance.to_dict()
# create an instance of TestRunExecutionStats from a dict
test_run_execution_stats_form_dict = test_run_execution_stats.from_dict(test_run_execution_stats_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



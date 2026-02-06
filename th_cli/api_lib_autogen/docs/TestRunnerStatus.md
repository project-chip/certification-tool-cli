# TestRunnerStatus


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**state** | [**TestRunnerState**](TestRunnerState.md) |  | 
**test_run_execution_id** | **int** |  | [optional] 

## Example

```python
from api_lib_autogen.models.test_runner_status import TestRunnerStatus

# TODO update the JSON string below
json = "{}"
# create an instance of TestRunnerStatus from a JSON string
test_runner_status_instance = TestRunnerStatus.from_json(json)
# print the JSON string representation of the object
print TestRunnerStatus.to_json()

# convert the object into a dict
test_runner_status_dict = test_runner_status_instance.to_dict()
# create an instance of TestRunnerStatus from a dict
test_runner_status_form_dict = test_runner_status.from_dict(test_runner_status_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



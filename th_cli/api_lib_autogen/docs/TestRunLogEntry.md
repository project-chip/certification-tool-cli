# TestRunLogEntry


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**level** | **str** |  | 
**timestamp** | **float** |  | 
**message** | **str** |  | 
**test_suite_execution_index** | **int** |  | [optional] 
**test_case_execution_index** | **int** |  | [optional] 
**test_step_execution_index** | **int** |  | [optional] 

## Example

```python
from api_lib_autogen.models.test_run_log_entry import TestRunLogEntry

# TODO update the JSON string below
json = "{}"
# create an instance of TestRunLogEntry from a JSON string
test_run_log_entry_instance = TestRunLogEntry.from_json(json)
# print the JSON string representation of the object
print TestRunLogEntry.to_json()

# convert the object into a dict
test_run_log_entry_dict = test_run_log_entry_instance.to_dict()
# create an instance of TestRunLogEntry from a dict
test_run_log_entry_form_dict = test_run_log_entry.from_dict(test_run_log_entry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



# TestRunConfig


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**dut_name** | **str** |  | 
**selected_tests** | **Dict[str, Dict[str, Dict[str, int]]]** |  | [optional] 
**id** | **int** |  | 

## Example

```python
from api_lib_autogen.models.test_run_config import TestRunConfig

# TODO update the JSON string below
json = "{}"
# create an instance of TestRunConfig from a JSON string
test_run_config_instance = TestRunConfig.from_json(json)
# print the JSON string representation of the object
print TestRunConfig.to_json()

# convert the object into a dict
test_run_config_dict = test_run_config_instance.to_dict()
# create an instance of TestRunConfig from a dict
test_run_config_form_dict = test_run_config.from_dict(test_run_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



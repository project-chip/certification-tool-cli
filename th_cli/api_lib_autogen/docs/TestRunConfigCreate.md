# TestRunConfigCreate


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**dut_name** | **str** |  | 
**selected_tests** | **Dict[str, Dict[str, Dict[str, int]]]** |  | [optional] 

## Example

```python
from api_lib_autogen.models.test_run_config_create import TestRunConfigCreate

# TODO update the JSON string below
json = "{}"
# create an instance of TestRunConfigCreate from a JSON string
test_run_config_create_instance = TestRunConfigCreate.from_json(json)
# print the JSON string representation of the object
print TestRunConfigCreate.to_json()

# convert the object into a dict
test_run_config_create_dict = test_run_config_create_instance.to_dict()
# create an instance of TestRunConfigCreate from a dict
test_run_config_create_form_dict = test_run_config_create.from_dict(test_run_config_create_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



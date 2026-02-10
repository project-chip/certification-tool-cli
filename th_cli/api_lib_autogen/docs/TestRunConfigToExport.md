# TestRunConfigToExport


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**dut_name** | **str** |  | 
**selected_tests** | **Dict[str, Dict[str, Dict[str, int]]]** |  | [optional] 
**created_at** | **datetime** |  | 

## Example

```python
from api_lib_autogen.models.test_run_config_to_export import TestRunConfigToExport

# TODO update the JSON string below
json = "{}"
# create an instance of TestRunConfigToExport from a JSON string
test_run_config_to_export_instance = TestRunConfigToExport.from_json(json)
# print the JSON string representation of the object
print TestRunConfigToExport.to_json()

# convert the object into a dict
test_run_config_to_export_dict = test_run_config_to_export_instance.to_dict()
# create an instance of TestRunConfigToExport from a dict
test_run_config_to_export_form_dict = test_run_config_to_export.from_dict(test_run_config_to_export_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



# TestCaseMetadataBase


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**public_id** | **str** |  | 
**title** | **str** |  | 
**description** | **str** |  | 
**version** | **str** |  | 
**source_hash** | **str** |  | 
**mandatory** | **bool** |  | [optional] [default to False]

## Example

```python
from api_lib_autogen.models.test_case_metadata_base import TestCaseMetadataBase

# TODO update the JSON string below
json = "{}"
# create an instance of TestCaseMetadataBase from a JSON string
test_case_metadata_base_instance = TestCaseMetadataBase.from_json(json)
# print the JSON string representation of the object
print TestCaseMetadataBase.to_json()

# convert the object into a dict
test_case_metadata_base_dict = test_case_metadata_base_instance.to_dict()
# create an instance of TestCaseMetadataBase from a dict
test_case_metadata_base_form_dict = test_case_metadata_base.from_dict(test_case_metadata_base_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



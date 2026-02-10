# TestCaseMetadata


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**public_id** | **str** |  | 
**title** | **str** |  | 
**description** | **str** |  | 
**version** | **str** |  | 
**source_hash** | **str** |  | 
**mandatory** | **bool** |  | [optional] [default to False]
**id** | **int** |  | 

## Example

```python
from api_lib_autogen.models.test_case_metadata import TestCaseMetadata

# TODO update the JSON string below
json = "{}"
# create an instance of TestCaseMetadata from a JSON string
test_case_metadata_instance = TestCaseMetadata.from_json(json)
# print the JSON string representation of the object
print TestCaseMetadata.to_json()

# convert the object into a dict
test_case_metadata_dict = test_case_metadata_instance.to_dict()
# create an instance of TestCaseMetadata from a dict
test_case_metadata_form_dict = test_case_metadata.from_dict(test_case_metadata_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



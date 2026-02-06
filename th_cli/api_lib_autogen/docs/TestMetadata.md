# TestMetadata


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**public_id** | **str** |  | 
**version** | **str** |  | 
**title** | **str** |  | 
**description** | **str** |  | 
**mandatory** | **bool** |  | [optional] [default to False]

## Example

```python
from api_lib_autogen.models.test_metadata import TestMetadata

# TODO update the JSON string below
json = "{}"
# create an instance of TestMetadata from a JSON string
test_metadata_instance = TestMetadata.from_json(json)
# print the JSON string representation of the object
print TestMetadata.to_json()

# convert the object into a dict
test_metadata_dict = test_metadata_instance.to_dict()
# create an instance of TestMetadata from a dict
test_metadata_form_dict = test_metadata.from_dict(test_metadata_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



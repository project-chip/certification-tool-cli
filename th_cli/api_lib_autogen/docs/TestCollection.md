# TestCollection


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**path** | **str** |  | 
**test_suites** | [**Dict[str, TestSuite]**](TestSuite.md) |  | 

## Example

```python
from api_lib_autogen.models.test_collection import TestCollection

# TODO update the JSON string below
json = "{}"
# create an instance of TestCollection from a JSON string
test_collection_instance = TestCollection.from_json(json)
# print the JSON string representation of the object
print TestCollection.to_json()

# convert the object into a dict
test_collection_dict = test_collection_instance.to_dict()
# create an instance of TestCollection from a dict
test_collection_form_dict = test_collection.from_dict(test_collection_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



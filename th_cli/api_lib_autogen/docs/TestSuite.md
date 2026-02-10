# TestSuite


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metadata** | [**TestMetadata**](TestMetadata.md) |  | 
**test_cases** | [**Dict[str, TestCase]**](TestCase.md) |  | 

## Example

```python
from api_lib_autogen.models.test_suite import TestSuite

# TODO update the JSON string below
json = "{}"
# create an instance of TestSuite from a JSON string
test_suite_instance = TestSuite.from_json(json)
# print the JSON string representation of the object
print TestSuite.to_json()

# convert the object into a dict
test_suite_dict = test_suite_instance.to_dict()
# create an instance of TestSuite from a dict
test_suite_form_dict = test_suite.from_dict(test_suite_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



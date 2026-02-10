# Operator

Default schema, used when return data to API clients

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**id** | **int** |  | 

## Example

```python
from api_lib_autogen.models.operator import Operator

# TODO update the JSON string below
json = "{}"
# create an instance of Operator from a JSON string
operator_instance = Operator.from_json(json)
# print the JSON string representation of the object
print Operator.to_json()

# convert the object into a dict
operator_dict = operator_instance.to_dict()
# create an instance of Operator from a dict
operator_form_dict = operator.from_dict(operator_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



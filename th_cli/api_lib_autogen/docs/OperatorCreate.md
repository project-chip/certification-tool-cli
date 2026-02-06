# OperatorCreate

Create schema.  Name is required for new Operators.

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 

## Example

```python
from api_lib_autogen.models.operator_create import OperatorCreate

# TODO update the JSON string below
json = "{}"
# create an instance of OperatorCreate from a JSON string
operator_create_instance = OperatorCreate.from_json(json)
# print the JSON string representation of the object
print OperatorCreate.to_json()

# convert the object into a dict
operator_create_dict = operator_create_instance.to_dict()
# create an instance of OperatorCreate from a dict
operator_create_form_dict = operator_create.from_dict(operator_create_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



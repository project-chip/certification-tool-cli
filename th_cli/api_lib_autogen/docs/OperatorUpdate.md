# OperatorUpdate

Update Schema.  Same as the base schema, only name can be changed

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional] 

## Example

```python
from api_lib_autogen.models.operator_update import OperatorUpdate

# TODO update the JSON string below
json = "{}"
# create an instance of OperatorUpdate from a JSON string
operator_update_instance = OperatorUpdate.from_json(json)
# print the JSON string representation of the object
print OperatorUpdate.to_json()

# convert the object into a dict
operator_update_dict = operator_update_instance.to_dict()
# create an instance of OperatorUpdate from a dict
operator_update_form_dict = operator_update.from_dict(operator_update_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



# OperatorToExport

Base schema for Operator, with shared properties.

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 

## Example

```python
from api_lib_autogen.models.operator_to_export import OperatorToExport

# TODO update the JSON string below
json = "{}"
# create an instance of OperatorToExport from a JSON string
operator_to_export_instance = OperatorToExport.from_json(json)
# print the JSON string representation of the object
print OperatorToExport.to_json()

# convert the object into a dict
operator_to_export_dict = operator_to_export_instance.to_dict()
# create an instance of OperatorToExport from a dict
operator_to_export_form_dict = operator_to_export.from_dict(operator_to_export_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



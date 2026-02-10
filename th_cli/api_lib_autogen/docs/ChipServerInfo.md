# ChipServerInfo

Schema for ChipServer information.

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**node_id** | **int** |  | 
**node_id_hex** | **str** |  | 
**manual_pairing_code** | **str** |  | [optional] 

## Example

```python
from api_lib_autogen.models.chip_server_info import ChipServerInfo

# TODO update the JSON string below
json = "{}"
# create an instance of ChipServerInfo from a JSON string
chip_server_info_instance = ChipServerInfo.from_json(json)
# print the JSON string representation of the object
print ChipServerInfo.to_json()

# convert the object into a dict
chip_server_info_dict = chip_server_info_instance.to_dict()
# create an instance of ChipServerInfo from a dict
chip_server_info_form_dict = chip_server_info.from_dict(chip_server_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



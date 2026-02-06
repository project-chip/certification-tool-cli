# PICSCluster


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**items** | [**Dict[str, PICSItem]**](PICSItem.md) |  | [optional] 

## Example

```python
from api_lib_autogen.models.pics_cluster import PICSCluster

# TODO update the JSON string below
json = "{}"
# create an instance of PICSCluster from a JSON string
pics_cluster_instance = PICSCluster.from_json(json)
# print the JSON string representation of the object
print PICSCluster.to_json()

# convert the object into a dict
pics_cluster_dict = pics_cluster_instance.to_dict()
# create an instance of PICSCluster from a dict
pics_cluster_form_dict = pics_cluster.from_dict(pics_cluster_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



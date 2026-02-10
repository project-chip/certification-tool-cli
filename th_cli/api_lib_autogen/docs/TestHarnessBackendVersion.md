# TestHarnessBackendVersion


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**version** | **str** |  | 
**sha** | **str** |  | 
**sdk_sha** | **str** |  | 
**sdk_docker_tag** | **str** |  | 
**db_revision** | **str** |  | 

## Example

```python
from api_lib_autogen.models.test_harness_backend_version import TestHarnessBackendVersion

# TODO update the JSON string below
json = "{}"
# create an instance of TestHarnessBackendVersion from a JSON string
test_harness_backend_version_instance = TestHarnessBackendVersion.from_json(json)
# print the JSON string representation of the object
print TestHarnessBackendVersion.to_json()

# convert the object into a dict
test_harness_backend_version_dict = test_harness_backend_version_instance.to_dict()
# create an instance of TestHarnessBackendVersion from a dict
test_harness_backend_version_form_dict = test_harness_backend_version.from_dict(test_harness_backend_version_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



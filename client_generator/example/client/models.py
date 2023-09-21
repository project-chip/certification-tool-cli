#
# Copyright (c) 2023 Project CHIP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from datetime import datetime
from typing import Any  # noqa
from typing import List, Optional

from pydantic import BaseModel, Field
from typing_extensions import Literal


class ApiResponse(BaseModel):
    code: "Optional[int]" = Field(None, alias="code")
    type: "Optional[str]" = Field(None, alias="type")
    message: "Optional[str]" = Field(None, alias="message")


class Category(BaseModel):
    id: "Optional[int]" = Field(None, alias="id")
    name: "Optional[str]" = Field(None, alias="name")


class Order(BaseModel):
    id: "Optional[int]" = Field(None, alias="id")
    pet_id: "Optional[int]" = Field(None, alias="petId")
    quantity: "Optional[int]" = Field(None, alias="quantity")
    ship_date: "Optional[datetime]" = Field(None, alias="shipDate")
    status: "Literal['placed', 'approved', 'delivered']" = Field(None, alias="status")
    complete: "Optional[bool]" = Field(None, alias="complete")


class Pet(BaseModel):
    id: "Optional[int]" = Field(None, alias="id")
    category: "Optional[Category]" = Field(None, alias="category")
    name: "str" = Field(..., alias="name")
    photo_urls: "List[str]" = Field(..., alias="photoUrls")
    tags: "Optional[List[Tag]]" = Field(None, alias="tags")
    status: "Literal['available', 'pending', 'sold']" = Field(None, alias="status")


class Tag(BaseModel):
    id: "Optional[int]" = Field(None, alias="id")
    name: "Optional[str]" = Field(None, alias="name")


class User(BaseModel):
    id: "Optional[int]" = Field(None, alias="id")
    username: "Optional[str]" = Field(None, alias="username")
    first_name: "Optional[str]" = Field(None, alias="firstName")
    last_name: "Optional[str]" = Field(None, alias="lastName")
    email: "Optional[str]" = Field(None, alias="email")
    password: "Optional[str]" = Field(None, alias="password")
    phone: "Optional[str]" = Field(None, alias="phone")
    user_status: "Optional[int]" = Field(None, alias="userStatus")
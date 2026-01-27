# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# For usage please contact the developer.
#
# This file is Copyright-protected.

# Description: data types for api
# Status: VERSION 1.0
# FileID: Ap-x-0003

import re
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"  # admin
    ORGANIZATION_MANAGER = "organization_manager"  # manager of an organization
    USER = "user"  # normal user

    def __lt__(self, other):
        if isinstance(other, UserRole):
            members = list(self.__class__)
            return members.index(other) < members.index(self)
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, UserRole):
            members = list(self.__class__)
            return members.index(other) > members.index(self)
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, UserRole):
            members = list(self.__class__)
            return members.index(other) <= members.index(self)
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, UserRole):
            members = list(self.__class__)
            return members.index(other) >= members.index(self)
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, UserRole):
            return self.value == other.value
        return NotImplemented


def get_leq_roles(role: UserRole):
    return [r for r in UserRole if r <= role]


def is_valid_role(value):
    return value in UserRole._value2member_map_


class Email:
    pattern = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

    def __init__(self, email: str):
        if not isinstance(email, str) or not self.pattern.match(email):
            raise ValueError("Invalid email format")
        self.email = email

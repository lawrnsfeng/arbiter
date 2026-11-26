---
id: R8
title: Subclass third-party types instead of wrapping them in free functions
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler Refactoring catalog "Combine Functions into Class" (https://refactoring.com/catalog/combineFunctionsIntoClass.html), HTTPX "Clients" (https://www.python-httpx.org/advanced/clients/), requests "Session Objects" (https://requests.readthedocs.io/en/latest/user/advanced/#session-objects)
---
## Rule

- Do not wrap a third-party type in free functions that create or use it internally (for example a function that
  opens a third-party client or connection and operates on it). (C1)
- Subclass the third-party type and put the operations on the subclass as methods. (C2)

## Incorrect

- A free function entering a third-party HTTP client in a `with` block and calling the API through it.
- A free function obtaining a cloud storage client from a `client(...)` factory and uploading through it.
- A free function building a cache handle with a `from_url` classmethod factory, using it and closing it.
- A free function building an SSH client and running a remote command on it.
- A free function receiving an already-built third-party client and operating on it (model only).

## Correct

- `LibraryApi(httpx.Client)` and `WaitList(Redis)` subclasses with the operations as methods.
- Look-alikes: a function that builds and returns a configured client, value types (a data frame, a parsed HTML
  document) used locally, a stdlib hash object.

## Detection

`check.py` looks, in undecorated module-level functions, for a local bound (by assignment or `with ... as`) to a
third-party type built in the function: `Type(...)` / `mod.Type(...)` with a CapWords name, a `connect` / `client` /
`session` / `resource` factory, or a classmethod factory `Type.from_*(...)`. Third-party means imported from a
top-level package that is neither stdlib nor one of the scanned project's packages. It reports the binding when a
method is then called on the local, the local is not returned, and the object is a resource: bound by `with`, closed
with `.close()`, built by a `connect` / `client` / `session` / `resource` factory, or of a type named like a handle
(`...Client`, `...Session`, `...Connection`, `...Pool`, `...Transport`, `...Channel`, `...Producer`, `...Consumer`,
`...Driver`, `...Engine`, `...Socket`, ...) (C1). A `Type.from_*(...)` build is reported only through one of those
signals (`with`, `.close()`, a handle-like type name), since such factories also build value types. The fix it names
is a subclass (C2).

## LLM scan

- Report free functions that take an existing third-party object (a client, connection, session, cursor) as a
  parameter and operate on it, when several such functions form an API around that type (C1, C2).
- Report free functions wrapping third-party handle types whose names the detector does not recognise (C1).
- Report handles built by a classmethod factory (`Type.from_url(...)`, `Type.from_env()`) and used in a free function
  without `with` or `.close()`, where the type is a client or connection the detector's name list misses (C1).
- Report wrapper classes that hold a third-party instance as an attribute and only forward to it, where subclassing
  would do (C2).
- Do not flag one-off scripts' `main`, adapters that deliberately hide a vendor behind a project interface, value
  types (data frames, parsed documents, numbers), or types that the library documents as not subclassable.

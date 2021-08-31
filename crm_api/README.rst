Authenticate
---------------

Call api:

url: web_domain/web/session/authenticate

type: json

method: post

params:

{

    "jsonrpc": "2.0",

    "params":
    {

        "login": "your account",

        "password": "your account password",

        "db": "your db name"

    }

}

Result:

information about user, session, db, version....

ex:

.. image:: /crm_api/static/src/img/authen.PNG


Create CRM
----------------------
Call api:

url: web_domain/crm/create

type: json

method: post

params:

{

    "jsonrpc": "2.0",

    "params": {

        "name": "test",

        "probability": 10,

        "planned_revenue": 10

    }

}

NOTE: field name must be mapping with crm.lead model.

Result: id of records

ex:

.. image:: /crm_api/static/src/img/create.PNG


Update CRM
----------------------
Call api:

url: web_domain/crm/create

type: json

method: post

params:

{

    "jsonrpc": "2.0",

    "params": {

        "crm_ids": [1402, 1403],

        "name": "test",

        "probability": 10,

        "planned_revenue": 10

    }

}

crm_ids: can have 1 id only, can have multiple ids

NOTE: field name must be mapping with crm.lead model.

Result: True

ex:

.. image:: /crm_api/static/src/img/create.PNG


List CRM
----------------------
Call api:

url: web_domain/crm/create

type: json

method: post

params:

{

    "jsonrpc": "2.0",

    "params": {

        "domain": [["name", "like", "test"]],

        "fields": ["name", "partner_id"],

        "offset": 1,

        "limit": 2,

        "order": "name desc"

    }

}

NOTE: domain, fields, offset, limit, order not required field (can be empty)

Result: List records

ex:

.. image:: /crm_api/static/src/img/list.PNG

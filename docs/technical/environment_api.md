# Clusterous Environment File API Spec

This document describes the Clusterous server API which runs on the Controller of each cluster. Currently the API covers starting, stopping and scaling an environment.

## POST /v1/environment
**Create a new environment**
Assuming no environment is already running, it creates a new environment based on the provided JSON.

The JSON has three top level fields: `name`, `components` and `tunnel`. The `name` and `components` exactly correspond to the fields in the user's environment file. The `tunnel` field is a list corresponding to the `expose_tunnel` field in the environment file.

Example
```JSON
{
    "name": "myenv",
    "components": {
        "master": {
            "machine": "master",
            "cpu": "auto",
            "image": "registry:5000/basic-python",
            "cmd": "/bin/bash /home/data/launch_scripts/launch_master.sh",
            "ports": "8888"
        },
        "...": "..."
    },
    "tunnels": [
        {
            "service": "8888:master:8888",
            "message": "To access the master, use this URL: {url}"
        }
    ]
}
```

If the request is valid, it responds with 202 Accepted:

```JSON
{
    "name": "myenv",
    "status": "launching"
}
```

## GET /v1/environment
**Get info about current environment**

Example response:

```JSON
{
    "name": "myenv",
    "status": "launching"
}
```

## GET /v1/environment/{envname}
Get information about the running environment. The "status" field can either be "launching" or "launched".

```JSON
{
    "name": "myenv",
    "components": {
        "master": {
            "machine": "master",
            "cpu": "auto",
            "image": "registry:5000/basic-python",
            "cmd": "/bin/bash /home/data/launch_scripts/launch_master.sh",
            "ports": "8888"
        },
        "...": "..."
    },
    "tunnels": [
        {
            "service": "8888:master:8888",
            "message": "To access the master, use this URL: {url}"
        }
    ],
    "nodes": {
        "master": [
            {
                "app_id": "/master",
                "instance_count": "1"
            }
        ],
        "worker": [
            {
                "app_id": "engine",
                "instance_count": "4"
            }
        ]
    },
    "status": "launching"
}
```

## DELETE /v1/environment/{envname}
Delete (destroy) the current environment. Returns 200 OK.

"""
    ProxLB API
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


import threading
try:
    import uvicorn
    UVICORN_PRESENT = True
except ImportError:
    UVICORN_PRESENT = False
import utils.version
try:
    from fastapi import FastAPI, HTTPException, Depends, Header, HTTPException, status
    FASTAPI_PRESENT = True
except ImportError:
    FASTAPI_PRESENT = False
from utils.helper import Helper
from utils.logger import SystemdLogger
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import Dict, Any

logger = SystemdLogger()


if not UVICORN_PRESENT:
    print("Error: The required library 'uvicorn' is not installed. ProxLB API cannot be used.")

if not FASTAPI_PRESENT:
    print("Error: The required library 'fastapi' is not installed. ProxLB API cannot be used.")


class ProxlbApi:
    """
    ProxLB API
    """
    def __init__(self, proxlb_config):
        """
        Initializes the API class with the ProxLB API object.
        """
        logger.debug("Starting: ProxLB API.")

        # ProxLB API Object
        self.proxlb_api = FastAPI()

        # ProxLB API Model
        class Node(BaseModel):
            name: str = ""
            wol_mac: str = ""
            guest_count: int = 0
            mode_patch: bool = False
            mode_dpm: bool = False
            release: bool = False
            processed: bool = False
        # ProxLB API Data
        nodes = {}

        # ProxLB API Routes
        @self.proxlb_api.get("/")
        async def root():
            return {"Application": "ProxLB", "version": f"{utils.version.__version__}", "status": "healthy"}

        @self.proxlb_api.get("/status")
        async def status():
            self.api_exec_status()
            return {"message": "status"}

        @self.proxlb_api.get("/reboot")
        async def reboot():
            self.api_exec_reboot()
            return {"message": "reboot"}

        @self.proxlb_api.get("/shutdown")
        async def shutdown():
            self.api_exec_shutdown()
            return {"message": "shutdown"}

        @self.proxlb_api.get("/wol")
        async def wol():
            self.api_exec_wol()
            return {"message": "wol"}

        @self.proxlb_api.get("/update")
        async def update():
            self.api_exec_update()
            return {"message": "update"}

        @self.proxlb_api.get("/nodes", dependencies=[Depends(self.get_api_key_dependency(proxlb_config))])
        async def get_node_items():
            keys = []
            for k, v in nodes.items():
                keys.append(k)
            return keys

        @self.proxlb_api.get("/nodes/{item_id}", response_model=Node)
        async def get_node_items(item_id: str):
            if item_id not in nodes:
                raise HTTPException(status_code=404, detail=f"Node with ID '{item_id}' not found")
            return nodes[item_id]

        @self.proxlb_api.patch("/nodes/{item_id}", response_model=Node, dependencies=[Depends(self.get_api_key_dependency(proxlb_config))])
        async def update_node_items(item_id: str, item: Node):
            stored_item_data = nodes[item_id]
            stored_item_model = Node(**stored_item_data)
            update_data = item.dict(exclude_unset=True)
            updated_item = stored_item_model.copy(update=update_data)
            nodes[item_id] = jsonable_encoder(updated_item)
            return updated_item

        @self.proxlb_api.post("/nodes/{item_id}", response_model=Node, dependencies=[Depends(self.get_api_key_dependency(proxlb_config))])
        async def set_node_items(item_id: str, item: Node):
            if item_id in nodes:
                raise HTTPException(status_code=400, detail=f"Node: {item_id} already exists.")
            nodes[item_id] = jsonable_encoder(item)
            return item

        logger.debug("Finalized: ProxLB API.")

    # ProxLB API Server API Key validation
    def get_api_key_dependency(self, proxlb_config: Dict[str, str]):
        def get_api_key(auth_header: str = Header(..., alias="Authorization")):
            auth_header = auth_header.replace("Bearer ", "")
            if auth_header not in proxlb_config.get("proxlb_api", {}).get("allowed_api_keys", []):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Error: Invalid or missing API Key.",
                )
        return get_api_key

    # ProxLB API Context Path Actions
    def api_exec_reboot(self):
        logger.debug("Rebooting system.")
        print("Rebooting system.")

    def api_exec_shutdown(self):
        logger.debug("Shutting down system.")
        print("Shutting down system.")

    def api_exec_wol(self):
        logger.debug("Sending WOL signal.")
        print("Sending WOL signal.")

    def api_exec_update(self):
        logger.debug("Updating system.")
        print("Updating system.")

    # ProxLB API Uvicorn Server
    def server(self, proxlb_config):
        """
        """
        def exec_api_server():
            """
            """
            # Define a custom formatter to match ProxLB logging syntax
            log_config = {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "()": "uvicorn.logging.DefaultFormatter",
                        "fmt": "%(asctime)s - ProxLB API - INFO - %(message)s",
                        "datefmt": "%Y-%m-%d %H:%M:%S,100",
                    },
                    "access": {
                        "()": "uvicorn.logging.AccessFormatter",
                        "fmt": "%(asctime)s - ProxLB API - ACCESS -  %(client_addr)s - \"%(request_line)s\" %(status_code)s",
                        "datefmt": "%Y-%m-%d %H:%M:%S,100",
                    },
                },
                "handlers": {
                    "default": {
                        "formatter": "default",
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                    },
                    "access": {
                        "formatter": "access",
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                    },
                },
                "loggers": {
                    "uvicorn": {"handlers": ["default"], "level": "INFO"},
                    "uvicorn.error": {"handlers": ["default"], "level": "INFO", "propagate": True},
                    "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
                },
            }

            # Run ProxLB API via Uvicorn with custom log formatter
            proxlb_api_listener = proxlb_config.get("proxlb_api", {}).get("listen_address", "127.0.0.1")
            proxlb_api_port = proxlb_config.get("proxlb_api", {}).get("port", 8008)
            proxlb_api_log_verbosity = proxlb_config.get("service", {}).get("log_level", "info")
            logger.debug(f"Starting ProxLB API Server on {proxlb_api_listener}:{proxlb_api_port}.")
            uvicorn.run(self.proxlb_api, host=proxlb_api_listener, port=proxlb_api_port, log_level=proxlb_api_log_verbosity.lower(), log_config=log_config)

        # Execute the Uvicorn in a threaded action to avoid blocking
        if proxlb_config.get("proxlb_api", {}).get("enable", False):
            logger.debug("ProxLB API Server is enabled. Starting API server...")
            server_thread = threading.Thread(target=exec_api_server, daemon=True)
            server_thread.start()
        else:
            logger.debug("ProxLB API Server is not enabled.")


### Example:
# INSERT
    # curl -X POST "http://127.0.0.1:8008/nodes/virt01" -H "Content-Type: application/json" -H "Authorization: Bearer RatpmrqUbmXqV7kmcoNu9w4y4ParWyAbYgky94b9" -d '{
    #             "name": "virt01",
    #             "wol_mac": "virt01",
    #             "mode_patch": false,
    #             "mode_dpm": false,
    #             "released": false,
    #             "processed": false
    
    #         }'

# # GET
# curl -X GET "http://127.0.0.1:8008/status" \
#   -H "Authorization: Bearer RatpmrqUbmXqV7kmcoNu9w4y4ParWyAbYgky94b9"



# curl -X POST "http://127.0.0.1:8008/nodes/virt01" -H "Content-Type: application/json" -H "Authorization: Bearer RatpmrqUbmXqV7kmcoNu9w4y4ParWyAbYgky94b9" -d '{
#                 "name": "virt01",
#                 "wol_mac": "virt01",
#                 "mode_patch": false,
#                 "mode_dpm": false,
#                 "released": false,
#                 "processed": false

#             }'

# curl -X POST "http://127.0.0.1:8008/nodes/virt02" -H "Content-Type: application/json" -H "Authorization: Bearer RatpmrqUbmXqV7kmcoNu9w4y4ParWyAbYgky94b9" -d '{
#                 "name": "virt02",
#                 "wol_mac": "virt02",
#                 "mode_patch": false,
#                 "mode_dpm": false,
#                 "released": false,
#                 "processed": false

#             }'

# curl -X POST "http://127.0.0.1:8008/nodes/virt03" -H "Content-Type: application/json" -H "Authorization: Bearer RatpmrqUbmXqV7kmcoNu9w4y4ParWyAbYgky94b9" -d '{
#                 "name": "virt03",
#                 "wol_mac": "virt03",
#                 "mode_patch": false,
#                 "mode_dpm": false,
#                 "released": false,
#                 "processed": false

#             }'
"""
ProxLB API
"""


__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


import threading
import uvicorn
import utils.version
from fastapi import FastAPI, HTTPException
from utils.logger import SystemdLogger
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import Dict, Any

logger = SystemdLogger()


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
            locked: bool = False
            ignore: bool = False
        # ProxLB API Data
        nodes = {}

        # ProxLB API Context Paths
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

        @self.proxlb_api.get("/nodes")
        async def get_node_items():
            keys = []
            for k, v in nodes.items():
                keys.append(k)
            return keys

        @self.proxlb_api.get("/nodes/{item_id}", response_model=Node)
        async def get_node_items(item_id: str):
            return nodes[item_id]

        @self.proxlb_api.patch("/nodes/{item_id}", response_model=Node)
        async def update_node_items(item_id: str, item: Node):
            stored_item_data = nodes[item_id]
            stored_item_model = Node(**stored_item_data)
            update_data = item.dict(exclude_unset=True)
            updated_item = stored_item_model.copy(update=update_data)
            nodes[item_id] = jsonable_encoder(updated_item)
            return updated_item

        @self.proxlb_api.post("/nodes/{item_id}", response_model=Node)
        async def set_node_items(item_id: str, item: Node):
            if item_id in nodes:
                raise HTTPException(status_code=400, detail=f"Node: {item_id} already exists.")
            print(item)
            nodes[item_id] = jsonable_encoder(item)
            return item

        # CLI example
        # curl -X POST "http://127.0.0.1:8000/nodes/virt01" -H "Content-Type: application/json" -d '{
        #             "name": "virt01",
        #             "wol_mac": "virt01",
        #             "locked": false,
        #             "ignore": false
        #         }'

        logger.debug("Finalized: ProxLB API.")

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
    def run(self, proxlb_config):
        """
        """
        def exec_api_server():
            """
            """
            # Define a custom formatter for match ProxLB logging syntax
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
            uvicorn.run(self.proxlb_api, host="0.0.0.0", port=8000, log_level="info", log_config=log_config)

        # Execute the Uvicorn in a threaded action to avoid blocking
        if proxlb_config.get("api_server", {}).get("enable", False):
            logger.debug("ProxLB API Server is enabled. Starting API server...")
            server_thread = threading.Thread(target=exec_api_server, daemon=True)
            server_thread.start()
        else:
            logger.debug("ProxLB API Server is not enabled.")

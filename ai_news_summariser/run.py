import uvicorn
from rest_api.configs import ConfigModel

be_config = ConfigModel.from_json_file("rest_api/configs/be_config.json")

if __name__ == "__main__":
    uvicorn.run(
        f"{be_config.server_config.path}",  # use module-style path
        host=f"{be_config.server_config.host}",
        port= be_config.server_config.port,
        reload=False,
        log_level="info"
    )
import sys

from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit

import my_action
import my_reco

# 导入自定义 actions
from custom.action import map_cleanup, select_map, select_job_character


def main():
    Toolkit.init_option("./")

    if len(sys.argv) < 2:
        print("Usage: python main.py <socket_id>")
        print("socket_id is provided by AgentIdentifier.")
        sys.exit(1)
        
    socket_id = sys.argv[-1]

    AgentServer.start_up(socket_id)
    AgentServer.join()
    AgentServer.shut_down()


if __name__ == "__main__":
    main()

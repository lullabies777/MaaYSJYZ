from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
import json

@AgentServer.custom_action("SelectMap")
class SelectMap(CustomAction):
    """
    根据配置中的 map 参数和坐标配置，点击对应的地图区域
    
    坐标配置可以通过两种方式提供：
    1. 通过 pipeline_override 中的 SelectMapByParam 节点配置：
       {
           "SelectMapByParam": {
               "map": "EastContinent",
               "map_click_x": 100,
               "map_click_y": 200
           }
       }
    
    2. 通过 FreeDungeonTask 的配置：
       {
           "FreeDungeonTask": {
               "map": "EastContinent",
               "map_click_x": 100,
               "map_click_y": 200
           }
       }
    
    3. 如果都没有，则使用默认坐标映射（作为后备方案）
    """
    def __init__(self):
        super().__init__()
        self.DEFAULT_MAP_COORDINATES = {
            "EastContinent": [360, 665],      
            "VoidRealm": [360, 710],          
            "FrozenContinent": [360, 755],    
            "ElementalLand": [360, 800],      
            "MistyContinent": [360, 847],     
            "ShadowContinent": [360, 893],    
            "LegionDomain": [360, 940],       
            "StormIsles": [360, 989],         
        }

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        map_name = None
        
        try:
            custom_action_param = json.loads(argv.custom_action_param)
            map_name = custom_action_param.get("map","")
            click_x, click_y = self.DEFAULT_MAP_COORDINATES[map_name]
                
        except Exception as e:
            print(f"[SelectMap] Error: {e}")
            return CustomAction.RunResult(success=False)

        print(f"[SelectMap] Clicking map '{map_name}' at ({click_x}, {click_y})")

        # 执行点击
        click_job = context.tasker.controller.post_click(click_x, click_y)
        click_job.wait()

        return CustomAction.RunResult(success=True)

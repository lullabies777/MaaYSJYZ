from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction


@AgentServer.custom_action("select_map")
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

    # 默认地图坐标映射（作为后备方案，如果 pipeline_override 中没有提供）
    # 格式: [x, y]
    DEFAULT_MAP_COORDINATES = {
        "EastContinent": [100, 200],
        "VoidRealm": [200, 200],
        "FrozenContinent": [300, 200],
        "ElementalLand": [100, 300],
        "MistyContinent": [200, 300],
        "ShadowContinent": [300, 300],
        "LegionDomain": [100, 400],
        "StormIsles": [200, 400],
    }

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        map_name = None
        click_x = None
        click_y = None
        
        # 从 context.config 读取配置（pipeline_override 会合并到这里）
        if hasattr(context, "config") and isinstance(context.config, dict):
            # 方式1: 优先从 SelectMapByParam 节点配置读取
            select_map_config = context.config.get("SelectMapByParam", {})
            if isinstance(select_map_config, dict):
                map_name = select_map_config.get("map")
                click_x = select_map_config.get("map_click_x")
                click_y = select_map_config.get("map_click_y")
            
            # 方式2: 从 FreeDungeonTask 的配置读取
            if not map_name:
                task_config = context.config.get("FreeDungeonTask", {})
                if isinstance(task_config, dict):
                    map_name = task_config.get("map")
                    if not click_x:
                        click_x = task_config.get("map_click_x")
                    if not click_y:
                        click_y = task_config.get("map_click_y")
            
            # 方式3: 从顶层配置读取
            if not map_name:
                map_name = context.config.get("map")
                if not click_x:
                    click_x = context.config.get("map_click_x")
                if not click_y:
                    click_y = context.config.get("map_click_y")
        
        # 方式4: 从任务名推断（如果任务名就是地图名）
        if not map_name and hasattr(argv, "task_name"):
            task_name = argv.task_name
            if task_name in self.DEFAULT_MAP_COORDINATES:
                map_name = task_name

        if not map_name:
            print(f"[SelectMap] Error: map parameter not found")
            return CustomAction.RunResult(success=False)

        # 如果 pipeline_override 中没有提供坐标，使用默认坐标
        if click_x is None or click_y is None:
            if map_name in self.DEFAULT_MAP_COORDINATES:
                default_coord = self.DEFAULT_MAP_COORDINATES[map_name]
                click_x = click_x if click_x is not None else default_coord[0]
                click_y = click_y if click_y is not None else default_coord[1]
                print(f"[SelectMap] Using default coordinates for '{map_name}'")
            else:
                print(f"[SelectMap] Error: unknown map '{map_name}' and no coordinates provided")
                return CustomAction.RunResult(success=False)
        else:
            print(f"[SelectMap] Using coordinates from pipeline_override for '{map_name}'")

        print(f"[SelectMap] Clicking map '{map_name}' at ({click_x}, {click_y})")

        # 执行点击
        click_job = context.tasker.controller.post_click(click_x, click_y)
        click_job.wait()

        return CustomAction.RunResult(success=True)

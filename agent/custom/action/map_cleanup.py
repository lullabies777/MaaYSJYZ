from typing import Dict, List

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction


@AgentServer.custom_action("map_cleanup")
class MapCleanup(CustomAction):
    """
    通用地图清理动作：
    - 当前地图通过任务名 / entry 名区分（例如 EastContinent、VoidRealm 等）
    - 职业开关来自 interface 中对该 entry 的 pipeline_override（use_xxx）
    - 在这里统一遍历所有勾选的职业并逐个执行清理逻辑
    """

    # 地图名称到点击坐标的映射
    # 格式: {"map_name": [x, y]}
    # 这些坐标用于在地图选择界面点击对应的地图
    MAP_CLICK_COORDINATES = {
        "EastContinent": [100, 200],      # TODO: 替换为东方大陆的真实坐标
        "VoidRealm": [200, 200],          # TODO: 替换为虚空领域的真实坐标
        "FrozenContinent": [300, 200],    # TODO: 替换为冰封大陆的真实坐标
        "ElementalLand": [100, 300],      # TODO: 替换为元素之地的真实坐标
        "MistyContinent": [200, 300],     # TODO: 替换为迷雾大陆的真实坐标
        "ShadowContinent": [300, 300],    # TODO: 替换为暗影大陆的真实坐标
        "LegionDomain": [100, 400],       # TODO: 替换为军团领域的真实坐标
        "StormIsles": [200, 400],         # TODO: 替换为风暴群岛的真实坐标
    }

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        # 任务名就是 entry 名（例如 EastContinent / VoidRealm / ...）
        current_map = argv.task_name

        # 读取该 entry 对应的配置（pipeline_override 已经合并进 context.config）
        # 不同项目版本里字段名可能略有差异，这里使用通用 dict 读取方式。
        map_config: Dict = {}
        if hasattr(context, "config") and isinstance(context.config, dict):
            map_config = context.config.get(current_map, {}) or {}

        # 收集所有已开启的职业
        enabled_jobs = self._collect_enabled_jobs(map_config)

        print(f"[MapCleanup] map={current_map}, jobs={enabled_jobs}")

        # 逐个职业执行清理
        for job in enabled_jobs:
            ok = self._run_one_job(context, current_map, job)
            if not ok:
                print(f"[MapCleanup] job {job} failed on {current_map}")
                return False

        return True

    @staticmethod
    def _collect_enabled_jobs(cfg: Dict) -> List[str]:
        """
        根据 use_xxx 布尔字段收集需要执行的职业。
        这些字段来自 interface.json 的 pipeline_override。
        """
        job_keys = {
            "use_warrior": "warrior",
            "use_mage": "mage",
            "use_rogue": "rogue",
            "use_hunter": "hunter",
            "use_paladin": "paladin",
            "use_warlock": "warlock",
            "use_druid": "druid",
            "use_shaman": "shaman",
            "use_priest": "priest",
            "use_death_knight": "death_knight",
            "use_monk": "monk",
            "use_demon_hunter": "demon_hunter",
        }
        enabled = []
        for key, name in job_keys.items():
            if cfg.get(key, False):
                enabled.append(name)
        return enabled

    def _run_one_job(self, context: Context, map_name: str, job_name: str) -> bool:
        """
        单个职业的执行逻辑：
        - 通过 pipeline_override 将 map / job 信息写入通用子流水线 MapJobCommon
        - 然后调用该子流水线，让复杂流程都在 pipeline 里实现
        """
        print(f"[MapCleanup] dispatch job={job_name} on map={map_name} -> MapJobCommon")

        # 获取该地图的点击坐标
        # 优先从 pipeline_override 读取（允许在 interface.json 中覆盖）
        map_click_x = None
        map_click_y = None
        
        # 尝试从 pipeline_override 读取坐标覆盖
        if isinstance(map_config, dict):
            map_click_x = map_config.get("map_click_x")
            map_click_y = map_config.get("map_click_y")
        
        # 如果 pipeline_override 中没有提供，使用默认坐标
        if map_click_x is None or map_click_y is None:
            default_coord = self.MAP_CLICK_COORDINATES.get(map_name)
            if default_coord:
                map_click_x = map_click_x if map_click_x is not None else default_coord[0]
                map_click_y = map_click_y if map_click_y is not None else default_coord[1]
                print(f"[MapCleanup] Using default coordinates for '{map_name}'")
            else:
                print(f"[MapCleanup] Warning: no coordinates for map '{map_name}', Exit")
                return False
                # map_click_x = map_click_x if map_click_x is not None else 0
                # map_click_y = map_click_y if map_click_y is not None else 0
        else:
            print(f"[MapCleanup] Using coordinates from pipeline_override for '{map_name}'")

        # 将当前 map / job 信息和地图坐标写入通用子流水线配置
        # 同时也要写入 FreeDungeonTask 和 SelectMapByParam，因为 select_map action 需要从那里读取
        context.override_pipeline(
            {
                "MapJobCommon": {
                    "map": map_name,
                    "job": job_name,
                },
                "SelectJobCharacter": {
                    "job": job_name,
                },
                "RecognizeJobCharacter": {
                    "job": job_name,
                },
                "FreeDungeonTask": {
                    "map": map_name,
                    "job": job_name,
                    "map_click_x": map_click_x,
                    "map_click_y": map_click_y,
                },
                "SelectMapByParam": {
                    "map": map_name,
                    "map_click_x": map_click_x,
                    "map_click_y": map_click_y,
                }
            }
        )

        # 运行通用子流水线，由它内部决定如何 OCR / 点击 / 刷图
        try:
            context.run_task("MapJobCommon")
        except Exception as e:
            print(f"[MapCleanup] MapJobCommon failed for {map_name}/{job_name}: {e}")
            return False

        return True
